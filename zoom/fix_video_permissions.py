"""
既存の動画ファイル（Google Drive）の閲覧権限を一括変更するスクリプト
シートからURLを取得し、「リンクを知っている全員が閲覧可能」に設定
"""

import os
import re
import time
from dotenv import load_dotenv

load_dotenv()

# Google API
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import gspread


def get_google_credentials():
    """Google API認証情報を取得"""
    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON") or os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    creds_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    if creds_json:
        creds_dict = json.loads(creds_json)
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    elif creds_file:
        credentials = Credentials.from_service_account_file(creds_file, scopes=scopes)
    else:
        raise ValueError("GOOGLE_CREDENTIALS_JSON or GOOGLE_SERVICE_ACCOUNT_FILE must be set")

    return credentials


# スプレッドシート設定
SPREADSHEET_ID = os.getenv("ZOOM_KEYS_SPREADSHEET_ID", "1R5oMbJ7E-QfDFhHR164y8JKs6XLnkJcw8zBm2IPSn8E")
SHEET_NAMES = ["Zoom相談一覧", "Zoom相談一覧 データ格納"]
VIDEO_URL_COLUMN = 8  # H列 = 8（動画URL）


def extract_file_id(url: str) -> str | None:
    """Google DriveのURLからファイルIDを抽出"""
    if not url:
        return None

    # https://drive.google.com/file/d/FILE_ID/view
    match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1)

    # https://drive.google.com/open?id=FILE_ID
    match = re.search(r'[?&]id=([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1)

    return None


def get_all_video_urls_from_sheet(spreadsheet_id: str, sheet_name: str) -> list[str]:
    """シートからすべての動画URLを取得"""
    credentials = get_google_credentials()
    gc = gspread.authorize(credentials)

    try:
        spreadsheet = gc.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)

        # H列のすべての値を取得（ヘッダー除く）
        col_values = worksheet.col_values(VIDEO_URL_COLUMN)

        # ヘッダーをスキップしてURLのみ取得
        urls = [url for url in col_values[1:] if url and 'drive.google.com' in url]
        return urls

    except gspread.exceptions.WorksheetNotFound:
        print(f"シート '{sheet_name}' が見つかりません")
        return []


def main(dry_run: bool = False):
    """メイン処理"""
    print("=" * 60)
    print("動画ファイル 権限一括変更スクリプト")
    print("=" * 60)

    if dry_run:
        print("【DRY RUN モード】実際の変更は行いません\n")

    credentials = get_google_credentials()
    drive_service = build('drive', 'v3', credentials=credentials)

    # 全シートからURLを収集
    all_urls = []
    for sheet_name in SHEET_NAMES:
        print(f"\nシート '{sheet_name}' からURL取得中...")
        urls = get_all_video_urls_from_sheet(SPREADSHEET_ID, sheet_name)
        print(f"  → {len(urls)}件のURLを取得")
        all_urls.extend(urls)

    # 重複を除去
    unique_urls = list(set(all_urls))
    print(f"\n合計: {len(unique_urls)}件のユニークな動画ファイル")

    # ファイルIDを抽出
    file_ids = []
    for url in unique_urls:
        file_id = extract_file_id(url)
        if file_id:
            file_ids.append((file_id, url))

    print(f"有効なファイルID: {len(file_ids)}件\n")

    if not file_ids:
        print("処理対象の動画ファイルがありません")
        return

    # 権限変更
    success_count = 0
    skip_count = 0
    error_count = 0

    print("-" * 60)
    for i, (file_id, url) in enumerate(file_ids, 1):
        print(f"[{i}/{len(file_ids)}] {file_id[:20]}...")

        if dry_run:
            print("   → [DRY RUN] スキップ")
            continue

        try:
            # 既存の権限を確認
            permissions = drive_service.permissions().list(
                fileId=file_id,
                fields='permissions(id, type, role)'
            ).execute()

            # すでにanyoneの権限があるか確認
            already_public = any(
                perm.get('type') == 'anyone'
                for perm in permissions.get('permissions', [])
            )

            if already_public:
                print("   → 既に公開設定済み（スキップ）")
                skip_count += 1
            else:
                # 権限を追加
                drive_service.permissions().create(
                    fileId=file_id,
                    body={
                        'type': 'anyone',
                        'role': 'reader'
                    }
                ).execute()
                print("   → 権限変更完了 ✓")
                success_count += 1

            # レート制限対策
            time.sleep(0.5)

        except Exception as e:
            print(f"   → エラー: {e}")
            error_count += 1

    # 結果サマリー
    print("\n" + "=" * 60)
    print("処理結果")
    print("=" * 60)
    print(f"  成功（権限変更）: {success_count}件")
    print(f"  スキップ（既に公開）: {skip_count}件")
    print(f"  エラー: {error_count}件")
    print(f"  合計: {len(file_ids)}件")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="動画ファイルの権限を一括変更")
    parser.add_argument("--dry-run", action="store_true", help="実際の変更を行わない（確認のみ）")
    args = parser.parse_args()

    main(dry_run=args.dry_run)
