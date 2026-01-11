"""
Google Drive / Docs クライアント
文字起こしをGoogle Docsに保存、動画をDriveにアップロード
"""

import os
import json
import requests
import subprocess
import shutil
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# GAS Web App URL（Google Docs作成用、環境変数から取得）
GAS_WEBAPP_URL = os.getenv("GAS_WEBAPP_URL")

try:
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    print("Warning: google-api-python-client not installed. Run: pip install google-api-python-client")


def compress_video(input_path: str, output_path: str = None) -> Optional[str]:
    """
    動画を720pに圧縮

    Args:
        input_path: 入力動画のパス
        output_path: 出力動画のパス（省略時は入力ファイル名_compressed.mp4）

    Returns:
        圧縮後のファイルパス（失敗時はNone）
    """
    # ffmpegが利用可能かチェック
    if not shutil.which("ffmpeg"):
        print("   ffmpegが見つかりません。圧縮をスキップします。")
        return None

    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_compressed{ext}"

    try:
        # 720p、CRF 28（品質と圧縮率のバランス）、音声は128kbps
        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-vf", "scale=-2:720",  # 720pにリサイズ（アスペクト比維持）
            "-c:v", "libx264",
            "-crf", "28",  # 品質（23=高品質、28=中品質、35=低品質）
            "-preset", "fast",  # エンコード速度
            "-c:a", "aac",
            "-b:a", "128k",
            "-y",  # 上書き確認なし
            output_path
        ]

        print(f"   動画を圧縮中...")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10分タイムアウト
        )

        if result.returncode == 0 and os.path.exists(output_path):
            # 圧縮結果を表示
            original_size = os.path.getsize(input_path) / (1024 * 1024)
            compressed_size = os.path.getsize(output_path) / (1024 * 1024)
            ratio = (1 - compressed_size / original_size) * 100

            print(f"   圧縮完了: {original_size:.1f}MB → {compressed_size:.1f}MB ({ratio:.0f}%削減)")
            return output_path
        else:
            print(f"   圧縮エラー: {result.stderr[:200] if result.stderr else 'Unknown error'}")
            return None

    except subprocess.TimeoutExpired:
        print("   圧縮タイムアウト（10分超過）")
        return None
    except Exception as e:
        print(f"   圧縮エラー: {e}")
        return None


def get_google_credentials():
    """Google API認証情報を取得"""
    if not GOOGLE_API_AVAILABLE:
        raise ImportError("google-api-python-client is required")

    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON") or os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    creds_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/documents"
    ]

    if creds_json:
        creds_dict = json.loads(creds_json)
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    elif creds_file:
        credentials = Credentials.from_service_account_file(creds_file, scopes=scopes)
    else:
        raise ValueError("GOOGLE_CREDENTIALS_JSON or GOOGLE_SERVICE_ACCOUNT_FILE must be set")

    return credentials


def create_transcript_doc(
    transcript: str,
    assignee: str,
    customer_name: str,
    meeting_date: str,
    folder_id: Optional[str] = None
) -> str:
    """
    文字起こしをGoogle Docsに保存（GAS経由）

    Args:
        transcript: 文字起こしテキスト
        assignee: 担当者名
        customer_name: 顧客名
        meeting_date: 面談日
        folder_id: 保存先フォルダID（未使用、GAS側で設定済み）

    Returns:
        Google DocsのURL
    """
    # GAS Web Appにリクエスト送信
    payload = {
        "transcript": transcript,
        "assignee": assignee,
        "customer_name": customer_name,
        "meeting_date": meeting_date
    }

    try:
        response = requests.post(
            GAS_WEBAPP_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120  # 2分タイムアウト（長い文字起こしに対応）
        )
        response.raise_for_status()

        result = response.json()

        if result.get("success"):
            doc_url = result.get("url")
            print(f"   文字起こしDoc作成: {doc_url}")
            return doc_url
        else:
            error_msg = result.get("error", "Unknown error")
            raise Exception(f"GAS error: {error_msg}")

    except requests.exceptions.RequestException as e:
        raise Exception(f"GAS request failed: {str(e)}")


def download_video_from_zoom(mp4_url: str, access_token: str, output_path: str) -> bool:
    """
    Zoomから動画をダウンロード

    Args:
        mp4_url: Zoom動画のURL
        access_token: Zoomアクセストークン
        output_path: 保存先パス

    Returns:
        成功したかどうか
    """
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(mp4_url, headers=headers, stream=True, timeout=600)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"   動画ダウンロード完了: {output_path}")
        return True
    except Exception as e:
        print(f"   動画ダウンロードエラー: {str(e)}")
        return False


def upload_video_to_drive_temp(video_path: str, file_name: str) -> Optional[str]:
    """
    動画をサービスアカウントのDriveに一時アップロード

    Args:
        video_path: 動画ファイルのパス
        file_name: ファイル名

    Returns:
        アップロードしたファイルのID（失敗時はNone）
    """
    try:
        credentials = get_google_credentials()
        drive_service = build('drive', 'v3', credentials=credentials)

        file_metadata = {'name': file_name}

        media = MediaFileUpload(
            video_path,
            mimetype='video/mp4',
            resumable=True
        )

        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        file_id = file['id']

        # GASからアクセスできるように共有設定
        drive_service.permissions().create(
            fileId=file_id,
            body={
                'type': 'anyone',
                'role': 'reader'
            }
        ).execute()

        print(f"   一時アップロード完了: {file_id}")
        return file_id

    except Exception as e:
        print(f"   一時アップロードエラー: {str(e)}")
        return None


def copy_video_via_gas(video_file_id: str, video_title: str) -> Optional[str]:
    """
    GAS経由で動画をコピー（ユーザー所有になる）

    Args:
        video_file_id: サービスアカウントがアップロードした動画のファイルID
        video_title: コピー後のファイル名

    Returns:
        コピーされた動画のURL（失敗時はNone）
    """
    try:
        payload = {
            "action": "copy_video",
            "video_file_id": video_file_id,
            "video_title": video_title
        }

        response = requests.post(
            GAS_WEBAPP_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=300  # 5分タイムアウト（動画コピーは時間がかかる場合あり）
        )
        response.raise_for_status()

        result = response.json()

        if result.get("success"):
            video_url = result.get("url")
            print(f"   GASコピー完了: {video_url}")
            return video_url
        else:
            error_msg = result.get("error", "Unknown error")
            print(f"   GASコピーエラー: {error_msg}")
            return None

    except Exception as e:
        print(f"   GASコピーリクエストエラー: {str(e)}")
        return None


def delete_file_from_drive(file_id: str) -> bool:
    """
    サービスアカウントのDriveからファイルを削除

    Args:
        file_id: 削除するファイルのID

    Returns:
        成功したかどうか
    """
    try:
        credentials = get_google_credentials()
        drive_service = build('drive', 'v3', credentials=credentials)

        drive_service.files().delete(fileId=file_id).execute()
        print(f"   元ファイル削除完了: {file_id}")
        return True

    except Exception as e:
        print(f"   ファイル削除エラー: {str(e)}")
        return False


def upload_video_with_copy(
    video_path: str,
    assignee: str,
    customer_name: str,
    meeting_date: str
) -> Optional[str]:
    """
    動画をアップロードし、GAS経由でコピーして元を削除
    （サービスアカウントの容量を消費しない）

    Args:
        video_path: 動画ファイルのパス
        assignee: 担当者名
        customer_name: 顧客名
        meeting_date: 面談日

    Returns:
        コピーされた動画のURL（ユーザー所有）
    """
    file_name = f"【面談動画】{customer_name}_{assignee}_{meeting_date}.mp4"

    # 1. サービスアカウントのDriveに一時アップロード
    print("→ 動画を一時アップロード中...")
    file_id = upload_video_to_drive_temp(video_path, file_name)
    if not file_id:
        return None

    # 2. GAS経由でコピー（ユーザー所有になる）
    print("→ GAS経由でコピー中...")
    video_url = copy_video_via_gas(file_id, file_name)

    # 3. 元ファイルを削除（コピー成功/失敗に関わらず削除して容量解放）
    print("→ 元ファイルを削除中...")
    delete_file_from_drive(file_id)

    return video_url


def upload_video_to_drive(
    video_path: str,
    assignee: str,
    customer_name: str,
    meeting_date: str,
    folder_id: Optional[str] = None
) -> str:
    """
    動画をGoogle Driveにアップロード（後方互換性のため残す）

    Args:
        video_path: 動画ファイルのパス
        assignee: 担当者名
        customer_name: 顧客名
        meeting_date: 面談日
        folder_id: 保存先フォルダID（オプション）

    Returns:
        Google DriveのURL
    """
    # 新しい方式を使用
    result = upload_video_with_copy(video_path, assignee, customer_name, meeting_date)
    if result:
        return result

    # フォールバック: 従来の方式
    credentials = get_google_credentials()
    drive_service = build('drive', 'v3', credentials=credentials)

    file_name = f"【面談動画】{customer_name}_{assignee}_{meeting_date}.mp4"
    file_metadata = {'name': file_name}
    if folder_id:
        file_metadata['parents'] = [folder_id]

    media = MediaFileUpload(
        video_path,
        mimetype='video/mp4',
        resumable=True
    )

    file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink'
    ).execute()

    file_id = file['id']

    drive_service.permissions().create(
        fileId=file_id,
        body={
            'type': 'anyone',
            'role': 'reader'
        }
    ).execute()

    file_info = drive_service.files().get(
        fileId=file_id,
        fields='webViewLink'
    ).execute()

    video_url = file_info.get('webViewLink', f"https://drive.google.com/file/d/{file_id}/view")
    print(f"   動画アップロード完了: {video_url}")

    return video_url


def get_or_create_folder(folder_name: str, parent_id: Optional[str] = None) -> str:
    """
    フォルダを取得（なければ作成）

    Args:
        folder_name: フォルダ名
        parent_id: 親フォルダID

    Returns:
        フォルダID
    """
    credentials = get_google_credentials()
    drive_service = build('drive', 'v3', credentials=credentials)

    # フォルダ検索
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"

    results = drive_service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name)'
    ).execute()

    files = results.get('files', [])

    if files:
        return files[0]['id']

    # フォルダ作成
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_id:
        file_metadata['parents'] = [parent_id]

    folder = drive_service.files().create(
        body=file_metadata,
        fields='id'
    ).execute()

    print(f"   フォルダ作成: {folder_name}")
    return folder['id']
