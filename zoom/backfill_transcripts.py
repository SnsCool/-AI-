#!/usr/bin/env python3
"""
文字起こしバックフィルスクリプト（Drive動画 + Zoomリンク両対応）

Zoom相談一覧 / データ格納シートの動画URLあり＆文字起こしなしの行を処理:
  - Google Drive URL → Driveからダウンロード → Gemini文字起こし
  - Zoom共有リンク   → Zoom APIでMP4取得    → Gemini文字起こし
  → Google Docsに保存 → シートG列更新

Usage:
    python backfill_transcripts.py                         # 両シート全件
    python backfill_transcripts.py --sheet zoom-list       # Zoom相談一覧のみ
    python backfill_transcripts.py --sheet data-storage    # データ格納のみ
    python backfill_transcripts.py --limit 10              # 最大10件
    python backfill_transcripts.py --dry-run               # 確認のみ
"""

import os
import sys
import re
import json
import time
import tempfile
import argparse
import traceback
import functools
from datetime import datetime, timedelta
from typing import Optional

from dotenv import load_dotenv

load_dotenv(override=True)

# ──────────────────────────────────────────────
# 定数
# ──────────────────────────────────────────────
DESTINATION_SPREADSHEET_ID = "1R5oMbJ7E-QfDFhHR164y8JKs6XLnkJcw8zBm2IPSn8E"
ZOOM_LIST_SHEET = "Zoom相談一覧"
DATA_STORAGE_SHEET = "Zoom相談一覧 データ格納"

# 待機時間
SHEET_API_DELAY = 1.5
BETWEEN_ROWS_DELAY = 3
ZOOM_API_DELAY = 1.0

# Zoom API 検索月数
ZOOM_SEARCH_MONTHS = 6

# ログ
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
LOG_FILE = os.path.join(LOG_DIR, f"backfill_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")


# ──────────────────────────────────────────────
# ロガー
# ──────────────────────────────────────────────
class Logger:
    def __init__(self, log_file: str):
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        self.log_file = log_file
        self.fh = open(log_file, "a", encoding="utf-8")

    def log(self, msg: str):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {msg}"
        print(line, flush=True)
        self.fh.write(line + "\n")
        self.fh.flush()

    def close(self):
        self.fh.close()


_logger: Optional[Logger] = None


def log(msg: str):
    if _logger:
        _logger.log(msg)
    else:
        print(msg, flush=True)


# ──────────────────────────────────────────────
# Google認証
# ──────────────────────────────────────────────
def get_google_credentials():
    from google.oauth2.service_account import Credentials
    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON") or os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    creds_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/documents",
    ]
    if creds_json:
        creds_dict = json.loads(creds_json)
        return Credentials.from_service_account_info(creds_dict, scopes=scopes)
    elif creds_file:
        return Credentials.from_service_account_file(creds_file, scopes=scopes)
    raise ValueError("GOOGLE_CREDENTIALS_JSON or GOOGLE_SERVICE_ACCOUNT_FILE must be set")


def get_sheets_client():
    import gspread
    return gspread.authorize(get_google_credentials())


def get_drive_service():
    from googleapiclient.discovery import build
    return build("drive", "v3", credentials=get_google_credentials())


# ──────────────────────────────────────────────
# Zoom認証情報キャッシュ
# ──────────────────────────────────────────────
_zoom_creds_cache: dict = {}
_zoom_recordings_cache: dict = {}


def load_zoom_credentials() -> dict:
    """zoom_credentials.json から認証情報を読み込み"""
    global _zoom_creds_cache
    if _zoom_creds_cache:
        return _zoom_creds_cache

    json_path = os.path.join(os.path.dirname(__file__), "zoom_credentials.json")
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            accounts = json.load(f)
        for acc in accounts:
            if acc.get("account_id") and acc.get("client_id") and acc.get("client_secret"):
                _zoom_creds_cache[acc["assignee"]] = acc
        log(f"Zoom認証情報: {len(_zoom_creds_cache)}アカウント読み込み")
    except Exception as e:
        log(f"Zoom認証情報読み込みエラー: {e}")
    return _zoom_creds_cache


def find_zoom_creds(assignee: str) -> Optional[dict]:
    """担当者名からZoom認証情報を検索（表記揺れ対応）"""
    creds = load_zoom_credentials()
    if assignee in creds:
        return creds[assignee]
    # 部分一致
    for name, acc in creds.items():
        if name in assignee or assignee in name:
            return acc
    return None


# ──────────────────────────────────────────────
# Zoom API
# ──────────────────────────────────────────────
def get_zoom_access_token(account_id: str, client_id: str, client_secret: str) -> str:
    """Zoom OAuth アクセストークン取得"""
    import requests
    import base64
    url = "https://zoom.us/oauth/token"
    encoded = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    headers = {"Authorization": f"Basic {encoded}", "Content-Type": "application/x-www-form-urlencoded"}
    data = {"grant_type": "account_credentials", "account_id": account_id}

    for attempt in range(3):
        try:
            resp = requests.post(url, headers=headers, data=data, timeout=30)
            resp.raise_for_status()
            return resp.json()["access_token"]
        except Exception as e:
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
            else:
                raise


def get_zoom_recordings(access_token: str, months: int = 6) -> list[dict]:
    """Zoom録画一覧を取得（最大6ヶ月分）"""
    import requests
    all_recordings = []
    today = datetime.now()
    months = min(months, 6)

    for i in range(months):
        month_end = today - timedelta(days=30 * i)
        month_start = month_end - timedelta(days=30)
        from_str = month_start.strftime("%Y-%m-%d")
        to_str = month_end.strftime("%Y-%m-%d")

        try:
            url = "https://api.zoom.us/v2/users/me/recordings"
            headers = {"Authorization": f"Bearer {access_token}"}
            params = {"from": from_str, "to": to_str, "page_size": 300}
            resp = requests.get(url, headers=headers, params=params, timeout=30)
            resp.raise_for_status()
            meetings = resp.json().get("meetings", [])

            for meeting in meetings:
                mp4_file = None
                for f in meeting.get("recording_files", []):
                    if f.get("file_type") == "MP4":
                        mp4_file = f
                        break
                all_recordings.append({
                    "topic": meeting.get("topic", ""),
                    "start_time": meeting.get("start_time", ""),
                    "duration": meeting.get("duration", 0),
                    "mp4_url": mp4_file.get("download_url") if mp4_file else None,
                    "share_url": meeting.get("share_url", ""),
                })
        except Exception as e:
            log(f"   Zoom API {from_str}〜{to_str} エラー: {e}")
            continue
        time.sleep(ZOOM_API_DELAY)

    return all_recordings


def download_from_zoom(mp4_url: str, access_token: str, save_path: str) -> bool:
    """Zoom APIからMP4をダウンロード"""
    import requests
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        resp = requests.get(mp4_url, headers=headers, stream=True, timeout=300)
        resp.raise_for_status()
        with open(save_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=65536):
                f.write(chunk)
        size_mb = os.path.getsize(save_path) / (1024 * 1024)
        log(f"   Zoomダウンロード完了: {size_mb:.1f}MB")
        return True
    except Exception as e:
        log(f"   Zoomダウンロードエラー: {e}")
        return False


def find_matching_recording(recordings: list[dict], meeting_datetime: str) -> Optional[dict]:
    """日時でマッチする録画を検索（UTC/JST両方試行、±45分許容）

    batch_zoom.pyはUTC時刻をそのままシートに保存するため、
    シート時刻がUTCかJSTか不定。両方の解釈でマッチを試みる。
    """
    if not meeting_datetime:
        return None

    target_str = meeting_datetime[:16]  # "YYYY-MM-DD HH:MM"
    best_match = None
    best_diff = 9999999

    for rec in recordings:
        rec_start = rec.get("start_time", "")
        if not rec_start:
            continue

        try:
            utc_dt = datetime.fromisoformat(rec_start.replace("Z", "+00:00"))
            utc_naive = utc_dt.replace(tzinfo=None)
            jst_dt = utc_dt + timedelta(hours=9)
            jst_naive = jst_dt.replace(tzinfo=None)
            utc_str = utc_naive.strftime("%Y-%m-%d %H:%M")
            jst_str = jst_naive.strftime("%Y-%m-%d %H:%M")

            # 完全一致（UTC解釈 or JST解釈）
            if utc_str == target_str or jst_str == target_str:
                if rec.get("mp4_url"):
                    return rec
                log(f"   注意: 日時一致だがMP4なし")
                continue

            # ±45分以内の最近マッチ（両方の解釈で試行）
            target_dt = datetime.strptime(target_str, "%Y-%m-%d %H:%M")
            for candidate in [utc_naive, jst_naive]:
                diff = abs((candidate - target_dt).total_seconds())
                if diff < 2700 and diff < best_diff and rec.get("mp4_url"):
                    best_diff = diff
                    best_match = rec
        except Exception:
            pass

    return best_match


# ──────────────────────────────────────────────
# シート操作
# ──────────────────────────────────────────────
def get_missing_transcript_rows(sheet_name: str) -> list[dict]:
    """動画あり & 文字起こしなしの行を最新順で取得"""
    client = get_sheets_client()
    spreadsheet = client.open_by_key(DESTINATION_SPREADSHEET_ID)
    worksheet = spreadsheet.worksheet(sheet_name)
    all_values = worksheet.get_all_values()

    missing = []
    for i, row in enumerate(all_values[1:], start=2):
        has_video = len(row) > 7 and row[7].strip()
        has_transcript = len(row) > 6 and row[6].strip() and "docs.google.com" in row[6]

        if has_video and not has_transcript:
            video_url = row[7].strip()
            url_type = "drive" if ("drive.google.com" in video_url or "docs.google.com/open" in video_url) else "zoom" if "zoom.us" in video_url else "other"

            if url_type in ("drive", "zoom"):
                missing.append({
                    "row_num": i,
                    "customer_name": row[0] if len(row) > 0 else "",
                    "assignee": row[1] if len(row) > 1 else "",
                    "meeting_datetime": row[2] if len(row) > 2 else "",
                    "video_url": video_url,
                    "url_type": url_type,
                })
    return missing


def update_transcript_url(sheet_name: str, row_num: int, transcript_url: str) -> bool:
    """シートG列を更新"""
    for attempt in range(5):
        try:
            client = get_sheets_client()
            spreadsheet = client.open_by_key(DESTINATION_SPREADSHEET_ID)
            worksheet = spreadsheet.worksheet(sheet_name)
            worksheet.update(f"G{row_num}", [[transcript_url]])
            try:
                worksheet.update(f"K{row_num}", [[datetime.now().strftime("%Y-%m-%d %H:%M")]])
            except Exception:
                pass
            return True
        except Exception as e:
            if "429" in str(e) or "Quota exceeded" in str(e):
                delay = 2.0 * (2 ** attempt)
                log(f"   シートAPI制限、{delay:.0f}秒待機... ({attempt+1}/5)")
                time.sleep(delay)
            else:
                log(f"   シート更新エラー: {e}")
                return False
    return False


def update_video_url(sheet_name: str, row_num: int, drive_url: str) -> bool:
    """シートH列を更新（Zoom→Drive URL置換）"""
    for attempt in range(5):
        try:
            client = get_sheets_client()
            spreadsheet = client.open_by_key(DESTINATION_SPREADSHEET_ID)
            worksheet = spreadsheet.worksheet(sheet_name)
            worksheet.update(f"H{row_num}", [[drive_url]])
            return True
        except Exception as e:
            if "429" in str(e) or "Quota exceeded" in str(e):
                delay = 2.0 * (2 ** attempt)
                time.sleep(delay)
            else:
                log(f"   動画URL更新エラー: {e}")
                return False
    return False


# ──────────────────────────────────────────────
# Google Drive
# ──────────────────────────────────────────────
def extract_file_id(url: str) -> Optional[str]:
    if not url:
        return None
    m = re.search(r"/file/d/([a-zA-Z0-9_-]+)", url)
    if m:
        return m.group(1)
    m = re.search(r"[?&]id=([a-zA-Z0-9_-]+)", url)
    if m:
        return m.group(1)
    return None


def download_from_drive(file_id: str, save_path: str) -> bool:
    from googleapiclient.http import MediaIoBaseDownload
    drive_service = get_drive_service()
    try:
        meta = drive_service.files().get(fileId=file_id, fields="name,size,mimeType").execute()
        size_mb = int(meta.get("size", 0)) / (1024 * 1024)
        log(f"   Drive: {meta.get('name')} ({size_mb:.1f}MB)")
    except Exception as e:
        log(f"   Driveメタデータ取得エラー: {e}")
        return False
    try:
        request = drive_service.files().get_media(fileId=file_id)
        with open(save_path, "wb") as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
        return True
    except Exception as e:
        log(f"   ダウンロードエラー: {e}")
        return False


def upload_to_drive(video_path: str, assignee: str, customer_name: str, meeting_date: str) -> Optional[str]:
    """動画をGoogle Driveにアップロードし、URLを返す"""
    from googleapiclient.http import MediaFileUpload
    sys.path.insert(0, os.path.dirname(__file__))
    from services.google_drive_client import upload_video_with_copy

    try:
        result_url = upload_video_with_copy(
            video_path=video_path,
            assignee=assignee,
            customer_name=customer_name,
            meeting_date=meeting_date,
        )
        return result_url
    except Exception as e:
        log(f"   Driveアップロードエラー: {e}")
        return None


# ──────────────────────────────────────────────
# Groq Whisper 文字起こし
# ──────────────────────────────────────────────
def transcribe_video_with_groq(video_path: str) -> Optional[str]:
    from services.groq_transcribe import transcribe_video
    log("   Groq Whisperで文字起こし中...")
    try:
        return transcribe_video(video_path)
    except Exception as e:
        log(f"   Groq文字起こしエラー: {e}")
        return None


# ──────────────────────────────────────────────
# Google Docs 作成
# ──────────────────────────────────────────────
def create_transcript_doc(transcript: str, assignee: str, customer_name: str, meeting_date: str) -> Optional[str]:
    sys.path.insert(0, os.path.dirname(__file__))
    from services.google_drive_client import create_transcript_doc as _create_doc
    try:
        return _create_doc(
            transcript=transcript, assignee=assignee,
            customer_name=customer_name, meeting_date=meeting_date,
            folder_id=os.getenv("GOOGLE_DRIVE_FOLDER_ID"),
        )
    except Exception as e:
        log(f"   Docs作成エラー: {e}")
        return None


# ──────────────────────────────────────────────
# 1行処理: Drive動画
# ──────────────────────────────────────────────
def process_drive_row(row: dict, sheet_name: str) -> str:
    """Drive動画行を処理。返り値: 'success' / 'failed' / 'skipped'"""
    file_id = extract_file_id(row["video_url"])
    if not file_id:
        log("   スキップ: DriveファイルID抽出不可")
        return "skipped"

    tmp_video = None
    try:
        tmp_fd, tmp_video = tempfile.mkstemp(suffix=".mp4")
        os.close(tmp_fd)

        log("   Driveからダウンロード中...")
        if not download_from_drive(file_id, tmp_video):
            return "failed"

        if os.path.getsize(tmp_video) < 10000:
            log("   スキップ: ファイルが小さすぎます")
            return "skipped"

        return _transcribe_and_save(tmp_video, row, sheet_name)
    except Exception as e:
        log(f"   エラー: {e}")
        traceback.print_exc()
        return "failed"
    finally:
        if tmp_video and os.path.exists(tmp_video):
            try: os.remove(tmp_video)
            except Exception: pass


# ──────────────────────────────────────────────
# 1行処理: Zoom動画
# ──────────────────────────────────────────────
def process_zoom_row(row: dict, sheet_name: str) -> str:
    """Zoomリンク行を処理。返り値: 'success' / 'failed' / 'skipped'"""
    assignee = row["assignee"]
    zoom_creds = find_zoom_creds(assignee)
    if not zoom_creds:
        log(f"   スキップ: {assignee} のZoom認証情報なし")
        return "skipped"

    tmp_video = None
    try:
        # アクセストークン取得
        access_token = get_zoom_access_token(
            zoom_creds["account_id"], zoom_creds["client_id"], zoom_creds["client_secret"]
        )

        # 録画一覧取得（キャッシュ）
        cache_key = assignee
        if cache_key not in _zoom_recordings_cache:
            log(f"   Zoom API: {assignee} の録画一覧取得中（{ZOOM_SEARCH_MONTHS}ヶ月分）...")
            _zoom_recordings_cache[cache_key] = get_zoom_recordings(access_token, months=ZOOM_SEARCH_MONTHS)
            log(f"   → {len(_zoom_recordings_cache[cache_key])}件の録画")

        recordings = _zoom_recordings_cache[cache_key]
        matching = find_matching_recording(recordings, row["meeting_datetime"])

        if not matching:
            log("   スキップ: 対応する録画が見つかりません")
            return "skipped"

        if not matching.get("mp4_url"):
            log("   スキップ: MP4 URLがありません")
            return "skipped"

        # MP4ダウンロード
        tmp_fd, tmp_video = tempfile.mkstemp(suffix=".mp4")
        os.close(tmp_fd)

        log("   ZoomからMP4ダウンロード中...")
        if not download_from_zoom(matching["mp4_url"], access_token, tmp_video):
            return "failed"

        if os.path.getsize(tmp_video) < 10000:
            log("   スキップ: ファイルが小さすぎます")
            return "skipped"

        # Google Driveにもアップロード（H列更新）
        meeting_date = row["meeting_datetime"][:10] if len(row["meeting_datetime"]) >= 10 else ""
        log("   Google Driveにアップロード中...")
        drive_url = upload_to_drive(tmp_video, assignee, row["customer_name"], meeting_date)
        if drive_url:
            update_video_url(sheet_name, row["row_num"], drive_url)
            log(f"   Drive URL更新: {drive_url[:60]}...")

        return _transcribe_and_save(tmp_video, row, sheet_name)
    except Exception as e:
        log(f"   エラー: {e}")
        traceback.print_exc()
        return "failed"
    finally:
        if tmp_video and os.path.exists(tmp_video):
            try: os.remove(tmp_video)
            except Exception: pass


# ──────────────────────────────────────────────
# 共通: 文字起こし → Docs → シート更新
# ──────────────────────────────────────────────
def _transcribe_and_save(video_path: str, row: dict, sheet_name: str) -> str:
    transcript = transcribe_video_with_groq(video_path)

    if not transcript or len(transcript) < 50:
        log(f"   失敗: 文字起こし不十分 (len={len(transcript) if transcript else 0})")
        return "failed"

    log(f"   文字起こし完了: {len(transcript)}文字")

    meeting_date = row["meeting_datetime"][:10] if len(row["meeting_datetime"]) >= 10 else ""
    log("   Google Docsを作成中...")
    doc_url = create_transcript_doc(transcript, row["assignee"], row["customer_name"], meeting_date)
    if not doc_url:
        return "failed"

    log(f"   シート更新中... → {doc_url}")
    if update_transcript_url(sheet_name, row["row_num"], doc_url):
        log("   完了!")
        return "success"
    return "failed"


# ──────────────────────────────────────────────
# メイン処理
# ──────────────────────────────────────────────
def process_sheet(sheet_name: str, limit: int = 0, offset: int = 0, dry_run: bool = False) -> dict:
    log(f"\n{'='*60}")
    log(f"シート: {sheet_name}")
    log(f"{'='*60}")

    log("対象行を取得中...")
    missing_rows = get_missing_transcript_rows(sheet_name)

    drive_rows = [r for r in missing_rows if r["url_type"] == "drive"]
    zoom_rows = [r for r in missing_rows if r["url_type"] == "zoom"]
    log(f"対象: Drive {len(drive_rows)}件 + Zoom {len(zoom_rows)}件 = {len(missing_rows)}件")

    if not missing_rows:
        log("処理対象なし")
        return {"success": 0, "failed": 0, "skipped": 0, "total": 0}

    # Drive行を先に処理（Zoom API不要で確実）
    missing_rows = drive_rows + zoom_rows

    if offset > 0:
        missing_rows = missing_rows[offset:]
        log(f"オフセット: {offset}件スキップ")

    if limit > 0:
        missing_rows = missing_rows[:limit]
        log(f"処理上限: {limit}件に制限")

    if dry_run:
        log("\n[DRY RUN] 対象行一覧:")
        for row in missing_rows:
            log(f"  行{row['row_num']}: [{row['url_type']}] {row['assignee']} / {row['customer_name']} / {row['meeting_datetime']}")
        return {"success": 0, "failed": 0, "skipped": 0, "total": len(missing_rows)}

    stats = {"success": 0, "failed": 0, "skipped": 0, "total": len(missing_rows)}

    for idx, row in enumerate(missing_rows):
        log(f"\n[{idx+1}/{len(missing_rows)}] 行{row['row_num']}: [{row['url_type']}] {row['customer_name']} / {row['assignee']}")
        log(f"   日時: {row['meeting_datetime']}")

        if row["url_type"] == "drive":
            result = process_drive_row(row, sheet_name)
        else:
            result = process_zoom_row(row, sheet_name)

        stats[result] = stats.get(result, 0) + 1

        if idx < len(missing_rows) - 1:
            time.sleep(BETWEEN_ROWS_DELAY)

    return stats


def main():
    global _logger

    parser = argparse.ArgumentParser(description="文字起こしバックフィル（Drive + Zoom対応）")
    parser.add_argument("--sheet", choices=["both", "zoom-list", "data-storage"], default="both")
    parser.add_argument("--limit", type=int, default=0, help="処理上限件数 (0=無制限)")
    parser.add_argument("--offset", type=int, default=0, help="開始オフセット（並列処理用）")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    _logger = Logger(LOG_FILE)
    log(f"バックフィル開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"対象: {args.sheet}, 上限: {args.limit or '無制限'}, offset: {args.offset}, dry-run: {args.dry_run}")
    log(f"ログ: {LOG_FILE}")

    missing_env = []
    if not (os.getenv("GOOGLE_CREDENTIALS_JSON") or os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")):
        missing_env.append("GOOGLE_CREDENTIALS_JSON")
    if not os.getenv("GEMINI_API_KEY"):
        missing_env.append("GEMINI_API_KEY")
    if missing_env:
        log(f"ERROR: 環境変数未設定: {', '.join(missing_env)}")
        sys.exit(1)

    start_time = datetime.now()
    total_stats = {"success": 0, "failed": 0, "skipped": 0, "total": 0}

    sheets_to_process = []
    if args.sheet in ("both", "zoom-list"):
        sheets_to_process.append(ZOOM_LIST_SHEET)
    if args.sheet in ("both", "data-storage"):
        sheets_to_process.append(DATA_STORAGE_SHEET)

    for sheet_name in sheets_to_process:
        stats = process_sheet(sheet_name, limit=args.limit, offset=args.offset, dry_run=args.dry_run)
        for key in total_stats:
            total_stats[key] += stats[key]

    elapsed = (datetime.now() - start_time).total_seconds()
    log(f"\n{'='*60}")
    log(f"全処理完了")
    log(f"{'='*60}")
    log(f"対象: {total_stats['total']}件")
    log(f"成功: {total_stats['success']}件")
    log(f"失敗: {total_stats['failed']}件")
    log(f"スキップ: {total_stats['skipped']}件")
    log(f"所要時間: {elapsed/60:.1f}分")
    log(f"ログ: {LOG_FILE}")

    _logger.close()


if __name__ == "__main__":
    main()
