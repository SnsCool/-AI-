#!/usr/bin/env python3
"""
サービスアカウントのDrive容量管理ツール

1. ゴミ箱を空にして容量回復
2. SA所有ファイルを指定フォルダに移動（ファイルID維持＝URL書き換え不要）

Usage:
    python migrate_to_shared_drive.py --empty-trash              # ゴミ箱を空にする
    python migrate_to_shared_drive.py --empty-trash --dry-run    # ゴミ箱の中身を確認
    python migrate_to_shared_drive.py --dry-run                  # 移行対象の一覧表示
    python migrate_to_shared_drive.py                            # 全件移行
    python migrate_to_shared_drive.py --limit 5                  # 5件だけ移行
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


def print_storage_info(drive_service):
    """SA情報とストレージ使用量を表示"""
    about = drive_service.about().get(fields="user, storageQuota").execute()
    email = about["user"]["emailAddress"]
    quota = about.get("storageQuota", {})
    usage = int(quota.get("usage", 0))
    usage_in_trash = int(quota.get("usageInDriveTrash", 0))
    limit = quota.get("limit")

    print(f"サービスアカウント: {email}")
    print(f"使用量: {format_size(usage)}" + (f" / {format_size(int(limit))}" if limit else ""))
    if usage_in_trash > 0:
        print(f"ゴミ箱内: {format_size(usage_in_trash)}")
    print()
    return usage, usage_in_trash


def list_trashed_files(drive_service):
    """ゴミ箱内のファイルを取得"""
    files = []
    page_token = None

    while True:
        resp = drive_service.files().list(
            q="trashed = true",
            fields="nextPageToken, files(id, name, mimeType, size, trashedTime)",
            pageSize=100,
            pageToken=page_token,
        ).execute()

        files.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    return files


def empty_trash(drive_service, dry_run=False):
    """ゴミ箱を空にする"""
    print("=" * 50)
    print("ゴミ箱クリーンアップ")
    print("=" * 50)

    trashed = list_trashed_files(drive_service)

    if not trashed:
        print("ゴミ箱は空です")
        return

    total_size = 0
    for f in trashed:
        size = int(f.get("size", 0))
        total_size += size
        trashed_time = (f.get("trashedTime") or "")[:19].replace("T", " ")
        print(f"  {trashed_time}  {format_size(size):>10}  {f['name']}")

    print()
    print(f"ゴミ箱内: {len(trashed)}件, {format_size(total_size)}")

    if dry_run:
        print()
        print("[DRY-RUN] 削除はスキップしました")
        return

    # ゴミ箱を一括で空にする
    print()
    print("ゴミ箱を空にしています...")
    try:
        drive_service.files().emptyTrash().execute()
        print(f"完了: {len(trashed)}件削除, {format_size(total_size)} 解放")
    except Exception as e:
        print(f"エラー: {e}")

    # 使用量を再確認
    print()
    print_storage_info(drive_service)


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


def move_file(drive_service, file_id, file_name, target_folder_id):
    """ファイルを指定フォルダに移動（ファイルIDは維持される）"""
    try:
        file_info = drive_service.files().get(
            fileId=file_id,
            fields="parents",
            supportsAllDrives=True,
        ).execute()
        current_parents = ",".join(file_info.get("parents", []))

        drive_service.files().update(
            fileId=file_id,
            addParents=target_folder_id,
            removeParents=current_parents,
            supportsAllDrives=True,
        ).execute()

        return True
    except Exception as e:
        print(f"    エラー: {file_name} - {e}")
        return False


def migrate_files(drive_service, dry_run=False, limit=0):
    """SA所有ファイルを移行"""
    target_id = os.getenv("SHARED_DRIVE_ID")
    if not target_id:
        print("SHARED_DRIVE_ID が設定されていないため、ファイル移行をスキップ")
        return

    print("=" * 50)
    print("ファイル移行")
    print("=" * 50)

    # 移行先へのアクセス確認
    try:
        # 共有ドライブとして試す
        drive_info = drive_service.drives().get(driveId=target_id).execute()
        target_name = drive_info.get("name", "(不明)")
        print(f"移行先（共有ドライブ）: {target_name}")
    except Exception:
        # 通常フォルダとして試す
        try:
            folder_info = drive_service.files().get(
                fileId=target_id,
                fields="name",
                supportsAllDrives=True,
            ).execute()
            target_name = folder_info.get("name", "(不明)")
            print(f"移行先（フォルダ）: {target_name}")
        except Exception as e:
            print(f"エラー: 移行先にアクセスできません - {e}")
            return
    print()

    # SA所有ファイル一覧
    print("ファイル一覧を取得中...")
    files = list_sa_files(drive_service)
    if not files:
        print("移行対象のファイルはありません")
        return

    total_size = 0
    for f in files:
        size = int(f.get("size", 0))
        total_size += size
        created = f["createdTime"][:19].replace("T", " ")
        print(f"  {created}  {format_size(size):>10}  {f['name']}")

    print()
    print(f"合計: {len(files)}件, {format_size(total_size)}")

    if dry_run:
        print()
        print("[DRY-RUN] 移動はスキップしました")
        return

    targets = files
    if limit > 0:
        targets = files[:limit]
        print(f"--limit {limit} により先頭 {len(targets)} 件のみ移行")

    print()
    moved = 0
    failed = 0
    moved_size = 0

    for i, f in enumerate(targets, 1):
        file_name = f["name"]
        file_size = int(f.get("size", 0))
        print(f"[{i}/{len(targets)}] Moving: {file_name}...", end=" ", flush=True)

        if move_file(drive_service, f["id"], file_name, target_id):
            print("OK")
            moved += 1
            moved_size += file_size
        else:
            failed += 1

    print()
    print(f"移行完了: {moved}件, 失敗: {failed}件, 移行サイズ: {format_size(moved_size)}")


def main():
    parser = argparse.ArgumentParser(description="SA Drive容量管理ツール")
    parser.add_argument("--dry-run", action="store_true", help="一覧表示のみ（実行しない）")
    parser.add_argument("--empty-trash", action="store_true", help="ゴミ箱を空にする")
    parser.add_argument("--limit", type=int, default=0, help="移行するファイル数の上限（0=全件）")
    args = parser.parse_args()

    credentials = get_google_credentials()
    drive_service = build("drive", "v3", credentials=credentials)

    # ストレージ情報表示
    print_storage_info(drive_service)

    if args.empty_trash:
        empty_trash(drive_service, dry_run=args.dry_run)
    else:
        migrate_files(drive_service, dry_run=args.dry_run, limit=args.limit)


if __name__ == "__main__":
    main()
