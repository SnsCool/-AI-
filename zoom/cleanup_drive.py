"""
サービスアカウントの Google Drive クリーンアップ

GAS経由コピー後に削除しきれなかった一時ファイルを検出・削除する。
"""

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))
from services.google_drive_client import get_google_credentials

from googleapiclient.discovery import build


def list_files(drive_service):
    """サービスアカウントが所有する全ファイルを取得"""
    files = []
    page_token = None

    while True:
        resp = drive_service.files().list(
            q="'me' in owners and trashed = false",
            fields="nextPageToken, files(id, name, mimeType, size, createdTime)",
            pageSize=100,
            pageToken=page_token,
        ).execute()

        files.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    return files


def format_size(size_bytes):
    if size_bytes is None:
        return "N/A"
    size = int(size_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}TB"


def main():
    parser = argparse.ArgumentParser(description="サービスアカウントDriveクリーンアップ")
    parser.add_argument("--dry-run", action="store_true", help="一覧表示のみ（削除しない）")
    parser.add_argument("--older-than", type=int, default=1, help="N時間以上前のファイルのみ対象（デフォルト: 1）")
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

    # ファイル一覧取得
    files = list_files(drive_service)
    if not files:
        print("残留ファイルなし")
        return

    # フィルタ: older-than
    cutoff = datetime.now(timezone.utc) - timedelta(hours=args.older_than)
    targets = []
    for f in files:
        created = datetime.fromisoformat(f["createdTime"].replace("Z", "+00:00"))
        if created < cutoff:
            targets.append(f)

    print(f"全ファイル数: {len(files)}")
    print(f"対象（{args.older_than}時間以上前）: {len(targets)}件")
    print()

    if not targets:
        print("削除対象なし")
        return

    # 一覧表示
    total_size = 0
    for f in targets:
        size = int(f.get("size", 0))
        total_size += size
        created = f["createdTime"][:19].replace("T", " ")
        print(f"  {created}  {format_size(size):>10}  {f['name']}")

    print()
    print(f"合計: {len(targets)}件, {format_size(total_size)}")

    if args.dry_run:
        print()
        print("[DRY-RUN] 削除はスキップしました")
        return

    # バッチ削除（100件ずつ）
    print()
    deleted = 0
    failed = 0
    BATCH_SIZE = 100

    for i in range(0, len(targets), BATCH_SIZE):
        batch = drive_service.new_batch_http_request()
        chunk = targets[i:i + BATCH_SIZE]

        def make_callback(file_name):
            def callback(request_id, response, exception):
                nonlocal deleted, failed
                if exception:
                    print(f"  削除エラー: {file_name} - {exception}")
                    failed += 1
                else:
                    deleted += 1
            return callback

        for f in chunk:
            batch.add(
                drive_service.files().delete(fileId=f["id"]),
                callback=make_callback(f["name"]),
            )

        batch.execute()
        print(f"  バッチ {i // BATCH_SIZE + 1}: {deleted}/{len(targets)}件処理済み")

    print()
    print(f"削除完了: {deleted}件, 失敗: {failed}件, 解放: {format_size(total_size)}")


if __name__ == "__main__":
    main()
