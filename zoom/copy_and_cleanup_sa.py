#!/usr/bin/env python3
"""
SA所有ファイルを指定フォルダに移動し、所有権をkiyotong0612@gmail.comに移転してSA容量を解放する。
ファイルIDが変わらないのでスプレッドシートのURL書き換えは不要。

Usage:
    python copy_and_cleanup_sa.py --dry-run        # 対象一覧表示のみ
    python copy_and_cleanup_sa.py                   # 全件処理
    python copy_and_cleanup_sa.py --limit 5         # 5件だけ処理
"""

import argparse
import json
import os
import re
import sys
import time

from dotenv import load_dotenv

load_dotenv()

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


SPREADSHEET_ID = "1R5oMbJ7E-QfDFhHR164y8JKs6XLnkJcw8zBm2IPSn8E"
SHEET_NAME = "Zoom相談一覧"

# 移動先フォルダ
VIDEO_FOLDER_ID = "1gKBpZ1vKRu5LdpTAI_r0qTM_x2Ft1irl"
DOC_FOLDER_ID = "1nV5Ftw9IY4XyFAW1f1zjhrZvDS8SHYNE"

# 所有権移転先
TRANSFER_OWNER_EMAIL = "kiyotong0612@gmail.com"


def get_credentials():
    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON") or os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    creds_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
    scopes = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]
    if creds_json:
        return Credentials.from_service_account_info(json.loads(creds_json), scopes=scopes)
    elif creds_file:
        return Credentials.from_service_account_file(creds_file, scopes=scopes)
    raise ValueError("GOOGLE_CREDENTIALS_JSON or GOOGLE_SERVICE_ACCOUNT_FILE must be set")


def format_size(size_bytes):
    if size_bytes is None:
        return "N/A"
    size = int(size_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}TB"


def get_storage_usage(drive_service):
    about = drive_service.about().get(fields="user, storageQuota").execute()
    email = about["user"]["emailAddress"]
    quota = about.get("storageQuota", {})
    usage = int(quota.get("usage", 0))
    limit_val = quota.get("limit")
    print(f"アカウント: {email}")
    print(f"使用量: {format_size(usage)}" + (f" / {format_size(int(limit_val))}" if limit_val else ""))
    return email, usage


def move_and_transfer(drive_service, file_id, dest_folder_id):
    """
    ファイルを指定フォルダに移動し、所有権を移転する。
    1. フォルダ移動（addParents/removeParents）
    2. 所有権移転（transferOwnership）
    """
    # 1. フォルダ移動（既に移動済みならスキップ）
    file_info = drive_service.files().get(
        fileId=file_id, fields="parents", supportsAllDrives=True
    ).execute()
    current_parents = file_info.get("parents", [])
    if dest_folder_id not in current_parents:
        drive_service.files().update(
            fileId=file_id,
            addParents=dest_folder_id,
            removeParents=",".join(current_parents),
            supportsAllDrives=True,
        ).execute()

    # 2. 所有権移転
    drive_service.permissions().create(
        fileId=file_id,
        body={
            "type": "user",
            "role": "owner",
            "emailAddress": TRANSFER_OWNER_EMAIL,
        },
        transferOwnership=True,
        supportsAllDrives=True,
    ).execute()


def main():
    parser = argparse.ArgumentParser(description="SA所有ファイルを移動＋所有権移転")
    parser.add_argument("--dry-run", action="store_true", help="一覧表示のみ")
    parser.add_argument("--limit", type=int, default=0, help="処理数上限（0=全件）")
    args = parser.parse_args()

    credentials = get_credentials()
    drive_service = build("drive", "v3", credentials=credentials)
    sheets_service = build("sheets", "v4", credentials=credentials)

    print("=" * 60)
    print("SA所有ファイル → フォルダ移動＋所有権移転")
    print(f"移転先: {TRANSFER_OWNER_EMAIL}")
    print("=" * 60)
    print()
    print("[処理前]")
    sa_email, usage_before = get_storage_usage(drive_service)
    print()

    # スプレッドシートのG列・H列を読み取り
    print("スプレッドシートからURL一覧を取得中...")
    entries = []
    for col_letter, dest_folder, file_type in [
        ("G", DOC_FOLDER_ID, "文字起こし"),
        ("H", VIDEO_FOLDER_ID, "動画"),
    ]:
        range_notation = f"'{SHEET_NAME}'!{col_letter}:{col_letter}"
        try:
            result = sheets_service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID, range=range_notation
            ).execute()
        except Exception as e:
            print(f"  警告: {col_letter}列の読み取り失敗: {e}")
            continue

        for row_idx, row in enumerate(result.get("values", [])):
            if not row:
                continue
            url = row[0]
            if "drive.google.com" not in url and "docs.google.com" not in url:
                continue
            match = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
            if not match:
                continue
            entries.append({
                "col_letter": col_letter,
                "row_num": row_idx + 1,
                "file_id": match.group(1),
                "dest_folder": dest_folder,
                "file_type": file_type,
            })

    print(f"Drive URL: {len(entries)}件")
    print()

    # SA所有チェック
    print("所有者チェック中...")
    targets = []
    skipped = 0
    errors = 0

    for entry in entries:
        try:
            file_info = drive_service.files().get(
                fileId=entry["file_id"],
                fields="id, name, owners, size, parents",
                supportsAllDrives=True,
            ).execute()
        except Exception as e:
            errors += 1
            continue

        owners = file_info.get("owners", [])
        owner_email = owners[0].get("emailAddress", "") if owners else ""

        if owner_email != sa_email:
            skipped += 1
            continue

        targets.append({**entry, "file_info": file_info})

    print(f"移動＋移転対象（SA所有）: {len(targets)}件, スキップ: {skipped}件, エラー: {errors}件")
    print()

    if not targets:
        print("処理対象のファイルはありません")
        return

    # 一覧表示
    total_size = 0
    for i, t in enumerate(targets, 1):
        fi = t["file_info"]
        size = int(fi.get("size", 0))
        total_size += size
        print(f"  {i}. [{t['file_type']}] {t['col_letter']}{t['row_num']}: {fi['name']} ({format_size(size)})")

    print(f"\n合計: {len(targets)}件, {format_size(total_size)}")

    if args.dry_run:
        print(f"\n[DRY-RUN] 処理はスキップしました")
        return

    if args.limit > 0:
        targets = targets[:args.limit]
        print(f"\n--limit {args.limit} により先頭 {len(targets)} 件のみ処理")

    # 実行
    print()
    moved = 0
    failed = 0

    for i, t in enumerate(targets, 1):
        fi = t["file_info"]
        print(f"[{i}/{len(targets)}] {t['file_type']}: {fi['name']}...", end=" ", flush=True)

        try:
            move_and_transfer(drive_service, t["file_id"], t["dest_folder"])
            print("OK")
            moved += 1
        except Exception as e:
            print(f"FAILED ({e})")
            failed += 1

        time.sleep(0.5)

    # 結果
    print()
    print("=" * 60)
    print(f"完了: {moved}件成功, {failed}件失敗")
    print("=" * 60)
    print()
    print("[処理後]")
    _, usage_after = get_storage_usage(drive_service)
    diff = usage_before - usage_after
    if diff > 0:
        print(f"解放: {format_size(diff)}")


if __name__ == "__main__":
    main()
