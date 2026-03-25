#!/usr/bin/env python3
"""SA がフォルダにアクセスできるかテスト"""
import json, os
from dotenv import load_dotenv
load_dotenv()
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON") or os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
creds = Credentials.from_service_account_info(
    json.loads(creds_json),
    scopes=["https://www.googleapis.com/auth/drive"]
)
drive = build("drive", "v3", credentials=creds)

folders = {
    "動画": "1gKBpZ1vKRu5LdpTAI_r0qTM_x2Ft1irl",
    "文字起こし": "1nV5Ftw9IY4XyFAW1f1zjhrZvDS8SHYNE",
}

for name, fid in folders.items():
    try:
        info = drive.files().get(fileId=fid, fields="name", supportsAllDrives=True).execute()
        print(f"{name}: アクセス成功 - {info['name']}")
    except Exception as e:
        print(f"{name}: アクセス失敗 - {e}")
