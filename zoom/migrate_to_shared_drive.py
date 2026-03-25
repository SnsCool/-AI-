#!/usr/bin/env python3
"""
サービスアカウントのファイルを共有ドライブに移行

SA所有のファイルを共有ドライブに移動する。
ファイルIDが変わらないため、スプレッドシートのURL書き換えは不要。

Usage:
    python migrate_to_shared_drive.py --dry-run     # 対象一覧のみ表示
    python migrate_to_shared_drive.py               # 実行
    python migrate_to_shared_drive.py --limit 5     # 5件だけ移行
"""

import argparse
import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


def get_google_credentials():
    """Google API認証情報を取得"""
    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON") or os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    creds_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")

    scopes = [
        "https://www.googleapis.com/auth/drive",
    ]

    if creds_json:
        creds_dict = json.loads(creds_json)
        return Credentials.from_service_account_info(creds_dict, scopes=scopes)
    elif creds_file:
        return Credentials.from_service_account_file(creds_file, scopes=scopes)
    else:
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


def list_sa_files(drive_service):
    """サービスアカウントが所有する全ファイルを取得"""
    files = []
    page_token = None

    while True:
        resp = drive_service.files().list(
            q="'me' in owners and trashed = false",
            fields="nextPageToken, files(id, name, mimeType, size, createdTime, parents)",
            pageSize=100,
            pageToken=page_token,
        ).execute()

        files.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    return files


def move_to_shared_drive(drive_service, file_id, file_name, shared_drive_id):
    """ファイルを共有ドライブに移動（ファイルIDは維持される）"""
    try:
        # 現在の親フォルダを取得
        file_info = drive_service.files().get(
            fileId=file_id,
            fields="parents",
            supportsAllDrives=True,
        ).execute()
        current_parents = ",".join(file_info.get("parents", []))

        # 共有ドライブに移動
        drive_service.files().update(
            fileId=file_id,
            addParents=shared_drive_id,
            removeParents=current_parents,
            supportsAllDrives=True,
        ).execute()

        return True
    except Exception as e:
        print(f"    エラー: {file_name} - {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="SA所有ファイルを共有ドライブに移行")
    parser.add_argument("--dry-run", action="store_true", help="対象一覧のみ表示（移動しない）")
    parser.add_argument("--limit", type=int, default=0, help="移行するファイル数の上限（0=全件）")
    args = parser.parse_args()

    credentials = get_google_credentials()
    drive_service = build("drive", "v3", credentials=credentials)

    # サービスアカウント情報
    about = drive_service.about().get(fields="user, storageQuota").execute()
    email = about["user"]["emailAddress"]
    quota = about.get("storageQuota", {})
    usage = int(quota.get("usage", 0))
    print(f"サービスアカウント: {email}")
    print(f"現在の使用量: {format_size(usage)}")
    print()

    # 共有ドライブID確認
    shared_drive_id = os.getenv("SHARED_DRIVE_ID")
    if not shared_drive_id:
        print("エラー: 環境変数 SHARED_DRIVE_ID が設定されていません")
        sys.exit(1)

    # 共有ドライブへのアクセス確認
    try:
        drive_info = drive_service.drives().get(driveId=shared_drive_id).execute()
        drive_name = drive_info.get("name", "(不明)")
        print(f"共有ドライブ: {drive_name} ({shared_drive_id})")
    except Exception as e:
        print(f"エラー: 共有ドライブにアクセスできません - {e}")
        sys.exit(1)
    print()

    # SA所有ファイル一覧取得
    print("ファイル一覧を取得中...")
    files = list_sa_files(drive_service)
    if not files:
        print("移行対象のファイルはありません")
        return

    # 一覧表示
    total_size = 0
    for f in files:
        size = int(f.get("size", 0))
        total_size += size
        created = f["createdTime"][:19].replace("T", " ")
        print(f"  {created}  {format_size(size):>10}  {f['name']}")

    print()
    print(f"合計: {len(files)}件, {format_size(total_size)}")

    if args.dry_run:
        print()
        print("[DRY-RUN] 移動はスキップしました")
        return

    # 移動対象の決定
    targets = files
    if args.limit > 0:
        targets = files[:args.limit]
        print(f"--limit {args.limit} が指定されたため、先頭 {len(targets)} 件のみ移行します")

    # 移動実行
    print()
    moved = 0
    failed = 0
    moved_size = 0

    for i, f in enumerate(targets, 1):
        file_name = f["name"]
        file_size = int(f.get("size", 0))
        print(f"[{i}/{len(targets)}] Moving: {file_name}...", end=" ", flush=True)

        if move_to_shared_drive(drive_service, f["id"], file_name, shared_drive_id):
            print("OK")
            moved += 1
            moved_size += file_size
        else:
            failed += 1

    # 結果サマリ
    print()
    print("=" * 50)
    print(f"移行完了: {moved}件, 失敗: {failed}件, 移行サイズ: {format_size(moved_size)}")


if __name__ == "__main__":
    main()
