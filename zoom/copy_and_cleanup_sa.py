#!/usr/bin/env python3
"""
SA所有ファイルをGAS経由でsales@アカウントにコピーし、スプレッドシートURLを更新、SA側を削除する。

Usage:
    python copy_and_cleanup_sa.py --dry-run        # SA所有ファイルの一覧表示のみ
    python copy_and_cleanup_sa.py                   # 全件処理
    python copy_and_cleanup_sa.py --limit 5         # 5件だけ処理
"""

import argparse
import json
import os
import re
import sys
import time

import requests
from dotenv import load_dotenv

load_dotenv()

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


SPREADSHEET_ID = "1R5oMbJ7E-QfDFhHR164y8JKs6XLnkJcw8zBm2IPSn8E"
SHEET_NAME = "Zoom相談一覧"
# G列 = 文字起こしDocURL (index 6), H列 = 面談動画URL (index 7)
COL_G = 6  # 0-indexed
COL_H = 7  # 0-indexed
FILE_ID_PATTERN = re.compile(r"/d/([a-zA-Z0-9_-]+)")


def get_credentials():
    """Google API認証情報を取得"""
    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON") or os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    creds_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")

    scopes = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/spreadsheets",
    ]

    if creds_json:
        return Credentials.from_service_account_info(json.loads(creds_json), scopes=scopes)
    elif creds_file:
        return Credentials.from_service_account_file(creds_file, scopes=scopes)
    raise ValueError("GOOGLE_CREDENTIALS_JSON or GOOGLE_SERVICE_ACCOUNT_FILE must be set")


def extract_file_id(url):
    """Google DriveのURLからファイルIDを抽出"""
    if not url:
        return None
    match = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
    return match.group(1) if match else None


def format_size(size_bytes):
    """バイト数を読みやすいサイズ文字列に変換"""
    if size_bytes is None:
        return "N/A"
    size = int(size_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}TB"


def get_storage_usage(drive_service):
    """SA情報とストレージ使用量を表示し、使用量バイト数を返す"""
    about = drive_service.about().get(fields="user, storageQuota").execute()
    email = about["user"]["emailAddress"]
    quota = about.get("storageQuota", {})
    usage = int(quota.get("usage", 0))
    limit_val = quota.get("limit")

    print(f"アカウント: {email}")
    print(f"使用量: {format_size(usage)}" + (f" / {format_size(int(limit_val))}" if limit_val else ""))
    return email, usage


def read_sheet_urls(sheets_service):
    """
    スプレッドシートのG列・H列を読み、各セルのURL情報を返す。
    Returns: list of dict with keys: col_index, col_letter, row_num, url, file_id
    """
    entries = []
    col_map = {"G": COL_G, "H": COL_H}

    for col_letter, col_index in col_map.items():
        range_notation = f"'{SHEET_NAME}'!{col_letter}:{col_letter}"
        try:
            result = sheets_service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID,
                range=range_notation,
            ).execute()
        except Exception as e:
            print(f"  警告: {SHEET_NAME} {col_letter}列の読み取りに失敗: {e}")
            continue

        for row_idx, row in enumerate(result.get("values", [])):
            if not row:
                continue
            url = row[0]
            if "drive.google.com" not in url and "docs.google.com" not in url:
                continue
            file_id = extract_file_id(url)
            if not file_id:
                continue
            entries.append({
                "col_index": col_index,
                "col_letter": col_letter,
                "row_num": row_idx + 1,  # 1-indexed
                "url": url,
                "file_id": file_id,
            })

    return entries


def check_owner(drive_service, file_id, sa_email):
    """ファイルの所有者がSAかどうかを確認。SA所有ならファイル情報を返し、そうでなければNone。"""
    try:
        file_info = drive_service.files().get(
            fileId=file_id,
            fields="id, name, owners, mimeType, size",
        ).execute()
    except Exception as e:
        return None, str(e)

    owners = file_info.get("owners", [])
    owner_email = owners[0].get("emailAddress", "") if owners else ""

    if owner_email == sa_email:
        return file_info, None
    return None, None  # 所有者がSAではない (エラーなし)


def copy_via_gas(gas_url, col_letter, file_id, file_name):
    """
    GAS webappにPOSTしてファイルをコピーする。
    G列(transcript doc) → action: copy_doc
    H列(video) → action: copy_video
    Returns: (success, new_url, error_message)
    """
    if col_letter == "G":
        payload = {
            "action": "copy_doc",
            "doc_file_id": file_id,
            "doc_title": file_name,
            "assignee": "",
            "customer_name": "",
        }
        timeout = 60
    else:  # H
        payload = {
            "action": "copy_video",
            "video_file_id": file_id,
            "video_title": file_name,
            "assignee": "",
            "customer_name": "",
        }
        timeout = 300  # 動画はコピーに時間がかかる

    try:
        resp = requests.post(gas_url, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        if data.get("success"):
            return True, data.get("url", ""), None
        return False, None, data.get("error", "GAS returned success=false")
    except requests.exceptions.Timeout:
        return False, None, "GAS request timed out"
    except Exception as e:
        return False, None, str(e)


def main():
    parser = argparse.ArgumentParser(description="SA所有ファイルをGAS経由でコピー＆クリーンアップ")
    parser.add_argument("--dry-run", action="store_true", help="SA所有ファイルの一覧表示のみ（コピー・削除しない）")
    parser.add_argument("--limit", type=int, default=0, help="処理するファイル数の上限（0=全件）")
    args = parser.parse_args()

    gas_url = os.getenv("GAS_WEBAPP_URL")
    if not gas_url and not args.dry_run:
        print("エラー: GAS_WEBAPP_URL が設定されていません")
        sys.exit(1)

    credentials = get_credentials()
    drive_service = build("drive", "v3", credentials=credentials)
    sheets_service = build("sheets", "v4", credentials=credentials)

    # ストレージ使用量（処理前）
    print("=" * 60)
    print("SA所有ファイル コピー＆クリーンアップ")
    print("=" * 60)
    print()
    print("[処理前]")
    sa_email, usage_before = get_storage_usage(drive_service)
    print()

    # スプレッドシートからURL一覧を取得
    print("スプレッドシートからURL一覧を取得中...")
    entries = read_sheet_urls(sheets_service)
    print(f"URL参照: {len(entries)}件")
    print()

    # 各ファイルの所有者チェック
    print("所有者チェック中...")
    targets = []
    skipped = 0
    errors = 0

    for entry in entries:
        file_info, err = check_owner(drive_service, entry["file_id"], sa_email)
        if err:
            errors += 1
            continue
        if file_info is None:
            # 所有者がSAではない → スキップ
            skipped += 1
            continue
        targets.append({**entry, "file_info": file_info})

    print(f"SA所有: {len(targets)}件, 非SA所有(スキップ): {skipped}件, エラー: {errors}件")
    print()

    if not targets:
        print("処理対象のSA所有ファイルはありません")
        return

    # 一覧表示
    for i, t in enumerate(targets, 1):
        fi = t["file_info"]
        size = int(fi.get("size", 0))
        col_type = "transcript" if t["col_letter"] == "G" else "video"
        print(f"  {i}. [{col_type}] {t['col_letter']}{t['row_num']}: {fi['name']} ({format_size(size)})")

    print()

    if args.dry_run:
        print(f"[DRY-RUN] {len(targets)}件のSA所有ファイルが見つかりました。コピー・削除はスキップしました。")
        return

    if args.limit > 0:
        targets = targets[:args.limit]
        print(f"--limit {args.limit} により先頭 {len(targets)} 件のみ処理")
        print()

    # 処理実行
    copied = 0
    failed = 0
    total = len(targets)

    for i, t in enumerate(targets, 1):
        fi = t["file_info"]
        file_id = t["file_id"]
        file_name = fi["name"]
        col_type = "transcript" if t["col_letter"] == "G" else "video"

        print(f"[{i}/{total}] {col_type}: {file_name}...", end=" ", flush=True)

        # 1. GAS経由でコピー
        success, new_url, err = copy_via_gas(gas_url, t["col_letter"], file_id, file_name)
        if not success:
            print(f"copy FAILED ({err})")
            failed += 1
            time.sleep(1)
            continue
        print("copy OK,", end=" ", flush=True)

        # 2. スプレッドシートのURL更新
        cell = f"'{SHEET_NAME}'!{t['col_letter']}{t['row_num']}"
        try:
            sheets_service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=cell,
                valueInputOption="RAW",
                body={"values": [[new_url]]},
            ).execute()
        except Exception as e:
            print(f"sheet update FAILED ({e}), skipping delete")
            failed += 1
            time.sleep(1)
            continue

        # 3. SA側の元ファイルを削除
        try:
            drive_service.files().delete(fileId=file_id).execute()
            print("delete OK")
        except Exception as e:
            print(f"delete FAILED ({e})")
            # コピーとURL更新は成功しているのでカウントは成功扱い

        copied += 1
        time.sleep(1)

    # 結果サマリー
    print()
    print("=" * 60)
    print(f"処理完了: {copied}件成功, {failed}件失敗 / 全{total}件")
    print("=" * 60)
    print()

    # ストレージ使用量（処理後）
    print("[処理後]")
    _, usage_after = get_storage_usage(drive_service)
    diff = usage_before - usage_after
    if diff > 0:
        print(f"解放された容量: {format_size(diff)}")
    print()


if __name__ == "__main__":
    main()
