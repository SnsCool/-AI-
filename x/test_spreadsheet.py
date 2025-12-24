#!/usr/bin/env python3
"""Test Google Spreadsheet connection."""

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

load_dotenv()

def get_env(name: str) -> str | None:
    value = os.getenv(name)
    return value.strip() if value else None

GCP_SA_KEY_JSON = get_env("GCP_SA_KEY_JSON")
SPREADSHEET_ID = get_env("SPREADSHEET_ID")

def test_connection():
    print("=" * 50)
    print("Google Spreadsheet Connection Test")
    print("=" * 50)
    print()
    
    # Check environment variables
    if not GCP_SA_KEY_JSON:
        print("✗ GCP_SA_KEY_JSON not set")
        return False
    print("✓ GCP_SA_KEY_JSON found")
    
    if not SPREADSHEET_ID:
        print("✗ SPREADSHEET_ID not set")
        return False
    print(f"✓ SPREADSHEET_ID: {SPREADSHEET_ID[:20]}...")
    
    # Parse credentials
    try:
        credentials_info = json.loads(GCP_SA_KEY_JSON)
        print(f"✓ Service account: {credentials_info.get('client_email', 'unknown')}")
    except json.JSONDecodeError as e:
        print(f"✗ Failed to parse GCP_SA_KEY_JSON: {e}")
        return False
    
    # Create service
    try:
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        service = build("sheets", "v4", credentials=credentials)
        print("✓ Google Sheets API service created")
    except Exception as e:
        print(f"✗ Failed to create service: {e}")
        return False
    
    # Test read access
    try:
        result = service.spreadsheets().get(
            spreadsheetId=SPREADSHEET_ID
        ).execute()
        print(f"✓ Spreadsheet title: {result.get('properties', {}).get('title', 'unknown')}")
        
        sheets = result.get('sheets', [])
        sheet_names = [s.get('properties', {}).get('title') for s in sheets]
        print(f"✓ Sheets: {sheet_names}")
        
        if "投稿ログ" not in sheet_names:
            print("⚠ Warning: Sheet '投稿ログ' not found. Please create it.")
    except Exception as e:
        print(f"✗ Failed to read spreadsheet: {e}")
        return False
    
    # Test write access (append test row)
    try:
        test_row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "テスト",
            "@test_account",
            "接続テスト",
            "接続テスト - このメッセージは削除可能です",
            "",
            ""
        ]
        
        body = {"values": [test_row]}
        
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range="投稿ログ!A:G",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body=body
        ).execute()
        
        print("✓ Test row appended successfully!")
        print()
        print("=" * 50)
        print("CONNECTION TEST PASSED!")
        print("=" * 50)
        print()
        print("スプレッドシートを確認して、テスト行が追加されていることを確認してください。")
        return True
        
    except Exception as e:
        print(f"✗ Failed to write to spreadsheet: {e}")
        return False

if __name__ == "__main__":
    test_connection()
