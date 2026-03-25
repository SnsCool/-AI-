#!/usr/bin/env python3
"""
サービスアカウントのDrive容量管理ツール

1. --empty-trash: ゴミ箱を空にして容量回復
2. --migrate: SA所有ファイルを委任ユーザーにコピー＋スプレッドシートURL書き換え＋SA削除

Usage:
    python migrate_to_shared_drive.py --empty-trash              # ゴミ箱を空にする
    python migrate_to_shared_drive.py --empty-trash --dry-run    # ゴミ箱の中身を確認のみ
    python migrate_to_shared_drive.py --migrate --dry-run        # 移行対象の一覧表示
    python migrate_to_shared_drive.py --migrate                  # 全件移行
    python migrate_to_shared_drive.py --migrate --limit 5        # 5件だけ移行
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
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
import io


SPREADSHEET_ID = "1R5oMbJ7E-QfDFhHR164y8JKs6XLnkJcw8zBm2IPSn8E"
SHEET_NAMES = ["Zoom相談一覧"]
# G列 = 文字起こしDocURL, H列 = 面談動画URL
URL_COLUMNS = {"G": 6, "H": 7}  # 0-indexed
FILE_ID_PATTERN = re.compile(r"/d/([a-zA-Z0-9_-]+)")


def get_credentials(scopes, delegate_email=None):
    """Google API認証情報を取得"""
    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON") or os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    creds_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")

    if creds_json:
        creds_dict = json.loads(creds_json)
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    elif creds_file:
        credentials = Credentials.from_service_account_file(creds_file, scopes=scopes)
    else:
        raise ValueError("GOOGLE_CREDENTIALS_JSON or GOOGLE_SERVICE_ACCOUNT_FILE must be set")

    if delegate_email:
        credentials = credentials.with_subject(delegate_email)

    return credentials


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
    limit_val = quota.get("limit")

    print(f"アカウント: {email}")
    print(f"使用量: {format_size(usage)}" + (f" / {format_size(int(limit_val))}" if limit_val else ""))
    if usage_in_trash > 0:
        print(f"ゴミ箱内: {format_size(usage_in_trash)}")
    print()
    return usage


# =============================================================
# ゴミ箱クリーンアップ
# =============================================================

def list_trashed_files(drive_service):
    """ゴミ箱内のファイルを取得"""
    files = []
    page_token = None
    while True:
        resp = drive_service.files().list(
            q="trashed = true",
            fields="nextPageToken, files(id, name, size, trashedTime)",
            pageSize=100,
            pageToken=page_token,
        ).execute()
        files.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return files


def cmd_empty_trash(drive_service, dry_run=False):
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
        t = (f.get("trashedTime") or "")[:19].replace("T", " ")
        print(f"  {t}  {format_size(size):>10}  {f['name']}")

    print(f"\nゴミ箱内: {len(trashed)}件, {format_size(total_size)}")

    if dry_run:
        print("\n[DRY-RUN] 削除はスキップしました")
        return

    print("\nゴミ箱を空にしています...")
    try:
        drive_service.files().emptyTrash().execute()
        print(f"完了: {len(trashed)}件削除, {format_size(total_size)} 解放")
    except Exception as e:
        print(f"エラー: {e}")

    print()
    print_storage_info(drive_service)


# =============================================================
# ファイル移行（SA → 委任ユーザー）
# =============================================================

def list_sa_files(drive_service):
    """SA所有の全ファイルを取得"""
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


def build_file_id_to_sheet_location(sheets_service):
    """
    スプレッドシートのG列・H列を読み、ファイルID → (sheet_name, col, row_num) のマッピングを作成
    """
    mapping = {}
    for sheet_name in SHEET_NAMES:
        for col_letter, col_idx in URL_COLUMNS.items():
            range_notation = f"'{sheet_name}'!{col_letter}:{col_letter}"
            try:
                result = sheets_service.spreadsheets().values().get(
                    spreadsheetId=SPREADSHEET_ID,
                    range=range_notation,
                ).execute()
            except Exception as e:
                print(f"  警告: {sheet_name} {col_letter}列の読み取り失敗: {e}")
                continue

            for row_idx, row in enumerate(result.get("values", [])):
                if not row:
                    continue
                url = row[0]
                match = FILE_ID_PATTERN.search(url)
                if match:
                    file_id = match.group(1)
                    row_num = row_idx + 1  # 1-indexed
                    mapping[file_id] = {
                        "sheet_name": sheet_name,
                        "col_letter": col_letter,
                        "row_num": row_num,
                        "original_url": url,
                    }
    return mapping


def copy_file_as_delegate(sa_drive, delegate_drive, file_id, file_name, mime_type):
    """
    SAのファイルを委任ユーザーのDriveにコピー。
    Google Docs/SheetsはAPI copyで、動画はダウンロード→再アップロード。
    Returns: 新しいファイルID or None
    """
    google_doc_types = [
        "application/vnd.google-apps.document",
        "application/vnd.google-apps.spreadsheet",
        "application/vnd.google-apps.presentation",
    ]

    try:
        if mime_type in google_doc_types:
            # Google Docs系: files().copy()で一発コピー
            # SA側でまず委任ユーザーに閲覧権限を付与
            sa_drive.permissions().create(
                fileId=file_id,
                body={"type": "anyone", "role": "reader"},
            ).execute()

            copied = delegate_drive.files().copy(
                fileId=file_id,
                body={"name": file_name},
            ).execute()
            return copied["id"]
        else:
            # 動画等のバイナリファイル: ダウンロード → 再アップロード
            # SA側でファイル内容を取得
            request = sa_drive.files().get_media(fileId=file_id)
            buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(buffer, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()

            buffer.seek(0)

            # 委任ユーザーとしてアップロード
            media = MediaIoBaseUpload(buffer, mimetype=mime_type, resumable=True)
            uploaded = delegate_drive.files().create(
                body={"name": file_name},
                media_body=media,
                fields="id",
            ).execute()
            return uploaded["id"]

    except Exception as e:
        print(f"    コピーエラー: {e}")
        return None


def build_new_url(old_url, new_file_id):
    """元のURLのファイルIDを新しいIDに置き換え"""
    old_match = FILE_ID_PATTERN.search(old_url)
    if old_match:
        return old_url.replace(old_match.group(1), new_file_id)
    return f"https://drive.google.com/file/d/{new_file_id}/view"


def cmd_migrate(sa_drive, delegate_drive, sheets_service, dry_run=False, limit=0):
    """SA所有ファイルを委任ユーザーにコピー＋スプレッドシート更新＋SA削除"""
    print("=" * 50)
    print("ファイル移行（SA → 委任ユーザー）")
    print("=" * 50)

    # 1. SA所有ファイル一覧
    print("SA所有ファイルを取得中...")
    sa_files = list_sa_files(sa_drive)
    if not sa_files:
        print("移行対象のファイルはありません")
        return

    # 2. スプレッドシートのファイルID → セル位置マッピング
    print("スプレッドシートからURL参照を取得中...")
    file_id_map = build_file_id_to_sheet_location(sheets_service)
    print(f"スプレッドシート参照: {len(file_id_map)}件")

    # 3. 移行対象（スプレッドシートで参照されているファイルのみ）
    targets = []
    total_size = 0
    for f in sa_files:
        if f["id"] in file_id_map:
            size = int(f.get("size", 0))
            total_size += size
            targets.append(f)
            created = f["createdTime"][:19].replace("T", " ")
            loc = file_id_map[f["id"]]
            print(f"  {created}  {format_size(size):>10}  {loc['col_letter']}{loc['row_num']}  {f['name']}")

    print(f"\n移行対象: {len(targets)}件, {format_size(total_size)}")
    print(f"参照なし（移行不要）: {len(sa_files) - len(targets)}件")

    if dry_run:
        print("\n[DRY-RUN] 移行はスキップしました")
        return

    if limit > 0:
        targets = targets[:limit]
        print(f"--limit {limit} により先頭 {len(targets)} 件のみ移行")

    # 4. 移行実行
    print()
    migrated = 0
    failed = 0
    migrated_size = 0

    for i, f in enumerate(targets, 1):
        file_id = f["id"]
        file_name = f["name"]
        mime_type = f.get("mimeType", "application/octet-stream")
        file_size = int(f.get("size", 0))
        loc = file_id_map[file_id]

        print(f"[{i}/{len(targets)}] {file_name}")

        # 4a. コピー
        print(f"  コピー中...", end=" ", flush=True)
        new_file_id = copy_file_as_delegate(sa_drive, delegate_drive, file_id, file_name, mime_type)
        if not new_file_id:
            failed += 1
            continue
        print(f"OK ({new_file_id})")

        # 4b. スプレッドシートURL更新
        new_url = build_new_url(loc["original_url"], new_file_id)
        cell = f"'{loc['sheet_name']}'!{loc['col_letter']}{loc['row_num']}"
        try:
            sheets_service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=cell,
                valueInputOption="RAW",
                body={"values": [[new_url]]},
            ).execute()
            print(f"  URL更新: {cell} → {new_url[:60]}...")
        except Exception as e:
            print(f"  URL更新エラー: {e}")
            # URL更新失敗時はSA側のファイルを削除しない
            failed += 1
            continue

        # 4c. SA側の元ファイルを削除
        try:
            sa_drive.files().delete(fileId=file_id).execute()
            print(f"  SA側削除: OK")
        except Exception as e:
            print(f"  SA側削除エラー: {e}")

        migrated += 1
        migrated_size += file_size

        # API レート制限回避
        time.sleep(1)

    print()
    print("=" * 50)
    print(f"移行完了: {migrated}件, 失敗: {failed}件, 解放: {format_size(migrated_size)}")


def main():
    parser = argparse.ArgumentParser(description="SA Drive容量管理ツール")
    parser.add_argument("--dry-run", action="store_true", help="一覧表示のみ（実行しない）")
    parser.add_argument("--empty-trash", action="store_true", help="ゴミ箱を空にする")
    parser.add_argument("--migrate", action="store_true", help="ファイルを委任ユーザーに移行")
    parser.add_argument("--limit", type=int, default=0, help="移行するファイル数の上限（0=全件）")
    args = parser.parse_args()

    if not args.empty_trash and not args.migrate:
        parser.error("--empty-trash または --migrate を指定してください")

    scopes = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/spreadsheets",
    ]

    # SA自身の認証情報
    sa_credentials = get_credentials(scopes)
    sa_drive = build("drive", "v3", credentials=sa_credentials)

    # ストレージ情報表示
    print_storage_info(sa_drive)

    if args.empty_trash:
        cmd_empty_trash(sa_drive, dry_run=args.dry_run)
        return

    if args.migrate:
        delegate_email = os.getenv("GOOGLE_DELEGATE_EMAIL")
        if not delegate_email:
            print("エラー: GOOGLE_DELEGATE_EMAIL が設定されていません")
            print("  例: GOOGLE_DELEGATE_EMAIL=sales@levela.co.jp")
            sys.exit(1)

        # 委任ユーザーの認証情報
        delegate_credentials = get_credentials(scopes, delegate_email=delegate_email)
        delegate_drive = build("drive", "v3", credentials=delegate_credentials)

        # 委任ユーザー情報表示
        print(f"委任先: {delegate_email}")
        print_storage_info(delegate_drive)

        # Sheets API
        sheets_service = build("sheets", "v4", credentials=sa_credentials)

        cmd_migrate(sa_drive, delegate_drive, sheets_service, dry_run=args.dry_run, limit=args.limit)


if __name__ == "__main__":
    main()
