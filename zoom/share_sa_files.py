#!/usr/bin/env python3
"""SA所有ファイルをkiyotong0612@gmail.comに共有する"""
import json, os, re, time
from dotenv import load_dotenv
load_dotenv()
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SPREADSHEET_ID = "1R5oMbJ7E-QfDFhHR164y8JKs6XLnkJcw8zBm2IPSn8E"
SHEET_NAME = "Zoom相談一覧"
SHARE_EMAIL = "kiyotong0612@gmail.com"

creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON") or os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
creds = Credentials.from_service_account_info(
    json.loads(creds_json),
    scopes=["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]
)
drive = build("drive", "v3", credentials=creds)
sheets = build("sheets", "v4", credentials=creds)

about = drive.about().get(fields="user").execute()
sa_email = about["user"]["emailAddress"]
print(f"SA: {sa_email}")

shared = 0
skipped = 0
failed = 0

for col in ["G", "H"]:
    result = sheets.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=f"'{SHEET_NAME}'!{col}:{col}"
    ).execute()
    for row in result.get("values", []):
        if not row:
            continue
        url = row[0]
        match = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
        if not match:
            continue
        file_id = match.group(1)
        try:
            info = drive.files().get(fileId=file_id, fields="owners").execute()
            owner = info.get("owners", [{}])[0].get("emailAddress", "")
            if owner != sa_email:
                skipped += 1
                continue
            drive.permissions().create(
                fileId=file_id,
                body={"type": "user", "role": "reader", "emailAddress": SHARE_EMAIL},
                sendNotificationEmail=False,
            ).execute()
            shared += 1
            print(f"共有: {file_id}")
            time.sleep(0.3)
        except Exception as e:
            if "already" in str(e).lower():
                skipped += 1
            else:
                failed += 1
                print(f"エラー: {file_id} - {e}")

print(f"\n完了: 共有{shared}件, スキップ{skipped}件, 失敗{failed}件")
