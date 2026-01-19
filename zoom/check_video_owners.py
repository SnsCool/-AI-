"""
動画ファイルの所有者を確認するスクリプト
サービスアカウント所有 vs ユーザーアカウント所有を判別
"""

import os
import re
from dotenv import load_dotenv

load_dotenv()

import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import gspread


def get_google_credentials():
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


SPREADSHEET_ID = os.getenv("ZOOM_KEYS_SPREADSHEET_ID", "1R5oMbJ7E-QfDFhHR164y8JKs6XLnkJcw8zBm2IPSn8E")


def extract_file_id(url: str) -> str | None:
    if not url:
        return None
    match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1)
    match = re.search(r'[?&]id=([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1)
    return None


def main():
    credentials = get_google_credentials()
    gc = gspread.authorize(credentials)
    drive_service = build('drive', 'v3', credentials=credentials)

    # サービスアカウントのメールアドレスを取得
    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON") or os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if creds_json:
        sa_email = json.loads(creds_json).get("client_email", "")
    else:
        sa_email = "サービスアカウント"

    print(f"サービスアカウント: {sa_email}\n")

    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    worksheet = spreadsheet.worksheet("Zoom相談一覧")

    # A列（顧客名）、C列（日付）、H列（動画URL）を取得
    all_data = worksheet.get_all_values()

    print("=" * 80)
    print("動画ファイルの所有者確認")
    print("=" * 80)

    sa_owned = []
    user_owned = []
    errors = []

    for i, row in enumerate(all_data[1:], start=2):  # ヘッダースキップ
        if len(row) < 8:
            continue

        customer_name = row[0] if len(row) > 0 else ""
        meeting_date = row[2] if len(row) > 2 else ""
        video_url = row[7] if len(row) > 7 else ""

        if not video_url or 'drive.google.com' not in video_url:
            continue

        file_id = extract_file_id(video_url)
        if not file_id:
            continue

        try:
            file_info = drive_service.files().get(
                fileId=file_id,
                fields='name, owners'
            ).execute()

            owners = file_info.get('owners', [])
            owner_email = owners[0].get('emailAddress', '') if owners else 'unknown'

            if sa_email in owner_email:
                sa_owned.append((i, customer_name, meeting_date, owner_email))
                status = "⚠️  SA所有"
            else:
                user_owned.append((i, customer_name, meeting_date, owner_email))
                status = "✓ ユーザー所有"

            print(f"[行{i}] {customer_name} ({meeting_date}) - {status}")

        except Exception as e:
            errors.append((i, customer_name, str(e)))
            print(f"[行{i}] {customer_name} - ❌ エラー: {e}")

    print("\n" + "=" * 80)
    print("サマリー")
    print("=" * 80)
    print(f"  サービスアカウント所有（再生不可の可能性）: {len(sa_owned)}件")
    print(f"  ユーザーアカウント所有（再生可能）: {len(user_owned)}件")
    print(f"  エラー: {len(errors)}件")

    if sa_owned:
        print("\n⚠️  サービスアカウント所有の動画:")
        for row_num, name, date, owner in sa_owned:
            print(f"  - 行{row_num}: {name} ({date})")


if __name__ == "__main__":
    main()
