"""
Google Drive / Docs クライアント
文字起こしをGoogle Docsに保存、動画をDriveにアップロード
"""

import os
import json
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

try:
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    print("Warning: google-api-python-client not installed. Run: pip install google-api-python-client")


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
    文字起こしをGoogle Docsに保存

    Args:
        transcript: 文字起こしテキスト
        assignee: 担当者名
        customer_name: 顧客名
        meeting_date: 面談日
        folder_id: 保存先フォルダID（オプション）

    Returns:
        Google DocsのURL
    """
    credentials = get_google_credentials()

    # Docs APIでドキュメント作成
    docs_service = build('docs', 'v1', credentials=credentials)
    drive_service = build('drive', 'v3', credentials=credentials)

    # ドキュメントタイトル
    title = f"【文字起こし】{customer_name}_{assignee}_{meeting_date}"

    # 空のドキュメントを作成
    doc = docs_service.documents().create(body={'title': title}).execute()
    doc_id = doc['documentId']

    # ドキュメントに内容を挿入
    content_text = f"""面談文字起こし

担当者: {assignee}
顧客名: {customer_name}
面談日: {meeting_date}
作成日: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

{"=" * 50}

{transcript}
"""

    requests = [
        {
            'insertText': {
                'location': {'index': 1},
                'text': content_text
            }
        }
    ]

    docs_service.documents().batchUpdate(
        documentId=doc_id,
        body={'requests': requests}
    ).execute()

    # フォルダに移動（指定された場合）
    if folder_id:
        drive_service.files().update(
            fileId=doc_id,
            addParents=folder_id,
            removeParents='root',
            fields='id, parents'
        ).execute()

    # 共有設定（リンクを知っている人が閲覧可能）
    drive_service.permissions().create(
        fileId=doc_id,
        body={
            'type': 'anyone',
            'role': 'reader'
        }
    ).execute()

    doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
    print(f"   文字起こしDoc作成: {doc_url}")

    return doc_url


def upload_video_to_drive(
    video_path: str,
    assignee: str,
    customer_name: str,
    meeting_date: str,
    folder_id: Optional[str] = None
) -> str:
    """
    動画をGoogle Driveにアップロード

    Args:
        video_path: 動画ファイルのパス
        assignee: 担当者名
        customer_name: 顧客名
        meeting_date: 面談日
        folder_id: 保存先フォルダID（オプション）

    Returns:
        Google DriveのURL
    """
    credentials = get_google_credentials()
    drive_service = build('drive', 'v3', credentials=credentials)

    # ファイル名
    file_name = f"【面談動画】{customer_name}_{assignee}_{meeting_date}.mp4"

    # ファイルメタデータ
    file_metadata = {'name': file_name}
    if folder_id:
        file_metadata['parents'] = [folder_id]

    # アップロード
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

    # 共有設定（リンクを知っている人が閲覧可能）
    drive_service.permissions().create(
        fileId=file_id,
        body={
            'type': 'anyone',
            'role': 'reader'
        }
    ).execute()

    # 共有リンクを取得
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
