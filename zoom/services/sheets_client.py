"""
Google Sheets クライアント
分析結果をスプレッドシートに書き込む
"""

import os
import json
import time
import functools
import re
import unicodedata
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Google Sheets APIを使用
try:
    import gspread
    from google.oauth2.service_account import Credentials
    SHEETS_AVAILABLE = True
except ImportError:
    SHEETS_AVAILABLE = False
    print("Warning: gspread not installed. Run: pip install gspread google-auth")


def retry_on_quota_error(max_retries: int = 5, initial_delay: float = 2.0):
    """
    Google Sheets APIのクォータエラー(429)時にリトライするデコレータ

    Args:
        max_retries: 最大リトライ回数
        initial_delay: 初回待機時間（秒）、リトライごとに2倍になる
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_str = str(e)
                    # 429エラー（クォータ超過）の場合のみリトライ
                    if "429" in error_str or "Quota exceeded" in error_str:
                        last_exception = e
                        if attempt < max_retries:
                            print(f"   API制限エラー、{delay:.1f}秒後にリトライ... ({attempt + 1}/{max_retries})")
                            time.sleep(delay)
                            delay *= 2  # 指数バックオフ
                        continue
                    # その他のエラーはそのまま発生させる
                    raise

            # 全リトライ失敗
            raise last_exception
        return wrapper
    return decorator


# 新しいスプレッドシートID（セミナー管理シート）
DEFAULT_SPREADSHEET_ID = "1Cm3OR4C42kj4A2I-p9L1dMKuXaibAPADdTq0YMP45Z8"
DEFAULT_SHEET_NAME = "Zoom相談一覧"


def get_sheets_client():
    """Google Sheets クライアントを取得"""
    if not SHEETS_AVAILABLE:
        raise ImportError("gspread and google-auth are required")

    # サービスアカウントの認証情報
    # 環境変数から取得（JSON文字列）またはファイルパス
    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON") or os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    creds_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/documents"
    ]

    if creds_json:
        # JSON文字列から認証情報を作成
        creds_dict = json.loads(creds_json)
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    elif creds_file:
        # ファイルから認証情報を作成
        credentials = Credentials.from_service_account_file(creds_file, scopes=scopes)
    else:
        raise ValueError(
            "GOOGLE_SERVICE_ACCOUNT_JSON or GOOGLE_SERVICE_ACCOUNT_FILE must be set"
        )

    return gspread.authorize(credentials)


@retry_on_quota_error(max_retries=5, initial_delay=2.0)
def get_or_create_sheet(client, spreadsheet_id: str, sheet_name: str):
    """
    シートを取得（なければ作成）

    Args:
        client: gspread client
        spreadsheet_id: スプレッドシートID
        sheet_name: シート名（担当者名など）

    Returns:
        worksheet
    """
    spreadsheet = client.open_by_key(spreadsheet_id)

    try:
        worksheet = spreadsheet.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        # シートが存在しない場合は作成
        worksheet = spreadsheet.add_worksheet(
            title=sheet_name,
            rows=1000,
            cols=20
        )
        # ヘッダー行を追加
        headers = [
            "面談日",
            "顧客名",
            "クロージング結果",
            "営業発話率",
            "顧客発話率",
            "ヒアリング課題",
            "提案内容",
            "分析・フィードバック",
            "処理日時"
        ]
        worksheet.update("A1:I1", [headers])
        # ヘッダー行を太字に
        worksheet.format("A1:I1", {"textFormat": {"bold": True}})

    return worksheet


def write_analysis_result(
    spreadsheet_id: str,
    assignee: str,
    meeting_date: str,
    customer_name: str,
    analysis: dict,
    feedback: str,
    video_analysis: Optional[dict] = None
) -> bool:
    """
    分析結果をスプレッドシートに書き込む

    Args:
        spreadsheet_id: スプレッドシートID
        assignee: 担当者名（シート名として使用）
        meeting_date: 面談日
        customer_name: 顧客名
        analysis: 文字起こし分析結果
        feedback: 統合フィードバック
        video_analysis: 動画分析結果（オプション）

    Returns:
        成功したかどうか
    """
    try:
        client = get_sheets_client()
        worksheet = get_or_create_sheet(client, spreadsheet_id, assignee)

        # 行データを作成
        talk_ratio = analysis.get("talk_ratio", {})
        issues = ", ".join(analysis.get("issues_heard", []))
        proposals = ", ".join(analysis.get("proposal", []))

        row = [
            meeting_date,
            customer_name or "不明",
            analysis.get("closing_result", "不明"),
            f"{talk_ratio.get('sales', '?')}%",
            f"{talk_ratio.get('customer', '?')}%",
            issues,
            proposals,
            feedback,  # #で区切られた統合フィードバック
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ]

        # 次の空行を見つける
        all_values = worksheet.get_all_values()
        next_row = len(all_values) + 1

        # データを追加
        worksheet.update(f"A{next_row}:I{next_row}", [row])

        print(f"シート '{assignee}' の行 {next_row} に書き込み完了")
        return True

    except Exception as e:
        print(f"シート書き込みエラー: {e}")
        return False


def get_spreadsheet_url(spreadsheet_id: str) -> str:
    """スプレッドシートのURLを生成"""
    return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"


def parse_datetime_flexible(date_str: str) -> Optional[datetime]:
    """
    様々な日時フォーマットをパース

    対応フォーマット:
    - 2024/1/7 10:00
    - 2024-01-07 10:00
    - 2024/01/07
    - 1/7 10:00
    - 2025年8月16日(土) 14:30～16:00  ← 日本語形式
    など
    """
    import re

    if not date_str or not isinstance(date_str, str):
        return None

    date_str = date_str.strip()
    if not date_str:
        return None

    # 日本語形式: 2025年8月16日(土) 14:30～16:00
    jp_pattern = r'(\d{4})年(\d{1,2})月(\d{1,2})日.*?(\d{1,2}):(\d{2})'
    jp_match = re.search(jp_pattern, date_str)
    if jp_match:
        year = int(jp_match.group(1))
        month = int(jp_match.group(2))
        day = int(jp_match.group(3))
        hour = int(jp_match.group(4))
        minute = int(jp_match.group(5))
        return datetime(year, month, day, hour, minute)

    # 日本語形式（時間なし）: 2025年8月16日
    jp_date_pattern = r'(\d{4})年(\d{1,2})月(\d{1,2})日'
    jp_date_match = re.search(jp_date_pattern, date_str)
    if jp_date_match:
        year = int(jp_date_match.group(1))
        month = int(jp_date_match.group(2))
        day = int(jp_date_match.group(3))
        return datetime(year, month, day)

    # 様々なフォーマットを試す
    formats = [
        "%Y/%m/%d %H:%M",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d",
        "%Y-%m-%d",
        "%m/%d %H:%M",
        "%m/%d",
    ]

    for fmt in formats:
        try:
            parsed = datetime.strptime(date_str, fmt)
            # 年がない場合は現在の年を使用
            if parsed.year == 1900:
                parsed = parsed.replace(year=datetime.now().year)
            return parsed
        except ValueError:
            continue

    return None


def load_all_customer_sheets_data(spreadsheet_id: str) -> dict:
    """
    顧客管理シートの全担当者シートデータを一括読み込み

    Args:
        spreadsheet_id: スプレッドシートID

    Returns:
        {担当者名: [(row_num, customer_name, scheduled_time_str, status, result_status), ...], ...}
    """
    from datetime import timedelta

    all_data = {}

    try:
        client = get_sheets_client()
        spreadsheet = client.open_by_key(spreadsheet_id)

        # 全シート（担当者）を取得
        worksheets = spreadsheet.worksheets()

        for idx, worksheet in enumerate(worksheets):
            assignee = worksheet.title

            # システムシートはスキップ
            if assignee in ['Zoomキー', 'マスタ', 'テンプレート']:
                continue

            # レート制限対策: シート読み込み前に少し待機（最初の3シートはスキップ）
            if idx >= 3:
                time.sleep(0.5)

            # リトライロジック付きでシートデータを取得
            all_values = None
            for retry in range(3):
                try:
                    all_values = worksheet.get_all_values()
                    break
                except Exception as e:
                    error_str = str(e)
                    if "429" in error_str or "Quota exceeded" in error_str:
                        if retry < 2:
                            wait_time = (retry + 1) * 2
                            print(f"   シート '{assignee}' レート制限、{wait_time}秒待機...")
                            time.sleep(wait_time)
                            continue
                    print(f"   シート '{assignee}' の読み込みエラー: {e}")
                    break

            if not all_values:
                continue

            # ヘッダー行を探す
            header_row_idx = None
            for i, row in enumerate(all_values[:10]):
                if 'お名前' in row:
                    header_row_idx = i
                    break

            if header_row_idx is None:
                continue

            # 列インデックスを特定
            headers = all_values[header_row_idx]
            name_col = 0  # A列: お名前
            date_col = None
            status_col = 6  # G列: 事前キャンセル
            result_status_col = 7  # H列: 初回/実施後ステータス

            for j, col in enumerate(headers):
                if '初回実施日' in col or '初回' in col:
                    date_col = j
                    break

            if date_col is None:
                continue

            # データを収集
            rows_data = []
            for i, row in enumerate(all_values[header_row_idx + 1:], start=header_row_idx + 2):
                if len(row) <= max(name_col, date_col):
                    continue

                customer_name = row[name_col] if len(row) > name_col else ""
                scheduled_time_str = row[date_col] if len(row) > date_col else ""
                status = row[status_col].strip() if len(row) > status_col and row[status_col] else ""
                result_status = row[result_status_col].strip() if len(row) > result_status_col and row[result_status_col] else ""

                if not scheduled_time_str:
                    continue

                # 日時をパース
                scheduled_time = parse_datetime_flexible(scheduled_time_str)
                if scheduled_time:
                    rows_data.append({
                        'row_num': i,
                        'customer_name': customer_name,
                        'scheduled_time_str': scheduled_time_str,
                        'scheduled_time': scheduled_time,
                        'status': status,
                        'result_status': result_status
                    })

            all_data[assignee] = rows_data

        print(f"   顧客管理シート読み込み完了: {len(all_data)}シート")
        return all_data

    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "Quota exceeded" in error_str:
            raise
        print(f"   顧客管理シート一括読み込みエラー: {e}")
        return {}


def find_matching_row_in_memory(
    all_customer_data: dict,
    assignee: str,
    zoom_start_time: datetime,
    tolerance_minutes: int = 45
) -> Optional[dict]:
    """
    メモリ上の顧客データから時間でマッチする行を検索

    Args:
        all_customer_data: load_all_customer_sheets_dataで読み込んだデータ
        assignee: 担当者名
        zoom_start_time: Zoom録画の開始時間（UTC）
        tolerance_minutes: 時間の許容誤差（分）

    Returns:
        マッチした行の情報、見つからない場合はNone
    """
    from datetime import timedelta

    if assignee not in all_customer_data:
        print(f"   シート '{assignee}' が見つかりません")
        return None

    rows = all_customer_data[assignee]

    # Zoom時間をJSTに変換（UTCから+9時間）
    zoom_jst = zoom_start_time + timedelta(hours=9)
    tolerance = timedelta(minutes=tolerance_minutes)

    for row_data in rows:
        scheduled_time = row_data['scheduled_time']

        # 時間がない場合は日付のみで比較
        if scheduled_time.hour == 0 and scheduled_time.minute == 0:
            if scheduled_time.date() == zoom_jst.date():
                return {
                    'row_num': row_data['row_num'],
                    'customer_name': row_data['customer_name'],
                    'scheduled_time': row_data['scheduled_time_str'],
                    'match_type': 'date_only',
                    'status': row_data['status'],
                    'result_status': row_data['result_status']
                }
        else:
            # 時間も含めて±tolerance分以内かチェック
            time_diff = abs((zoom_jst.replace(tzinfo=None) - scheduled_time).total_seconds())
            if time_diff <= tolerance.total_seconds():
                return {
                    'row_num': row_data['row_num'],
                    'customer_name': row_data['customer_name'],
                    'scheduled_time': row_data['scheduled_time_str'],
                    'match_type': 'exact_time',
                    'status': row_data['status'],
                    'result_status': row_data['result_status']
                }

    return None


@retry_on_quota_error(max_retries=5, initial_delay=2.0)
def find_matching_row_by_time(
    spreadsheet_id: str,
    assignee: str,
    zoom_start_time: datetime,
    tolerance_minutes: int = 45
) -> Optional[dict]:
    """
    担当者シートから、Zoom録画時間と一致する行を検索

    シート構造:
    - 行3: ヘッダー（お名前, 担当者, 流入経路, 流入, 初回実施日, 紹介者, 事前キャンセル, 初回/実施後ステータス, ...）
    - 行4以降: データ
    - A列(0): お名前
    - E列(4): 初回実施日（例: 2025年8月16日(土) 14:30～16:00）
    - G列(6): 事前キャンセル（ステータス: 着座/飛び/リスケ等）
    - H列(7): 初回/実施後ステータス（成約/失注/保留等）

    Args:
        spreadsheet_id: スプレッドシートID
        assignee: 担当者名（シート名）
        zoom_start_time: Zoom録画の開始時間（UTC）
        tolerance_minutes: 時間の許容誤差（分）

    Returns:
        マッチした行の情報 {
            "row_num": int,
            "customer_name": str,
            "scheduled_time": str,
            "match_type": str,
            "status": str,  # G列のステータス（着座/飛び/リスケ等）
            "result_status": str  # H列の初回/実施後ステータス（成約/失注/保留等）
        }
        見つからない場合はNone
    """
    from datetime import timedelta

    try:
        client = get_sheets_client()
        spreadsheet = client.open_by_key(spreadsheet_id)

        # 担当者名でシートを探す
        try:
            worksheet = spreadsheet.worksheet(assignee)
        except gspread.exceptions.WorksheetNotFound:
            print(f"   シート '{assignee}' が見つかりません")
            return None

        # 全データを取得
        all_values = worksheet.get_all_values()

        # ヘッダー行を探す（「お名前」を含む行）
        header_row_idx = None
        for i, row in enumerate(all_values[:10]):
            if 'お名前' in row:
                header_row_idx = i
                break

        if header_row_idx is None:
            print(f"   ヘッダー行が見つかりません")
            return None

        # 列インデックスを特定
        headers = all_values[header_row_idx]
        name_col = 0  # A列: お名前
        date_col = None
        status_col = 6  # G列: 事前キャンセル（ステータス）
        result_status_col = 7  # H列: 初回/実施後ステータス

        for j, col in enumerate(headers):
            if '初回実施日' in col or '初回' in col:
                date_col = j
                break

        if date_col is None:
            print(f"   初回実施日列が見つかりません")
            return None

        # Zoom時間をJSTに変換（UTCから+9時間）
        zoom_jst = zoom_start_time + timedelta(hours=9)

        tolerance = timedelta(minutes=tolerance_minutes)

        # データ行を検索（ヘッダーの次の行から）
        for i, row in enumerate(all_values[header_row_idx + 1:], start=header_row_idx + 2):
            if len(row) <= max(name_col, date_col):
                continue

            customer_name = row[name_col] if len(row) > name_col else ""
            scheduled_time_str = row[date_col] if len(row) > date_col else ""
            status = row[status_col].strip() if len(row) > status_col and row[status_col] else ""
            result_status = row[result_status_col].strip() if len(row) > result_status_col and row[result_status_col] else ""

            # 初回実施日が空白の場合はスキップ
            if not scheduled_time_str:
                continue

            # 日時をパース
            scheduled_time = parse_datetime_flexible(scheduled_time_str)
            if not scheduled_time:
                continue

            # 時間がない場合は日付のみで比較
            if scheduled_time.hour == 0 and scheduled_time.minute == 0:
                # 同じ日付かチェック
                if scheduled_time.date() == zoom_jst.date():
                    return {
                        "row_num": i,
                        "customer_name": customer_name,
                        "scheduled_time": scheduled_time_str,
                        "match_type": "date_only",
                        "status": status,
                        "result_status": result_status
                    }
            else:
                # 時間も含めて±tolerance分以内かチェック
                # scheduled_timeはJSTと仮定
                time_diff = abs((zoom_jst.replace(tzinfo=None) - scheduled_time).total_seconds())
                if time_diff <= tolerance.total_seconds():
                    return {
                        "row_num": i,
                        "customer_name": customer_name,
                        "scheduled_time": scheduled_time_str,
                        "match_type": "exact_time",
                        "status": status,
                        "result_status": result_status
                    }

        return None

    except Exception as e:
        # 429エラーはリトライのために再送出
        error_str = str(e)
        if "429" in error_str or "Quota exceeded" in error_str:
            raise
        print(f"   行検索エラー: {e}")
        import traceback
        traceback.print_exc()
        return None


@retry_on_quota_error(max_retries=5, initial_delay=2.0)
def find_matching_row_in_customer_list(
    spreadsheet_id: str,
    sheet_name: str,
    assignee: str,
    zoom_start_time: datetime,
    tolerance_minutes: int = 45
) -> Optional[dict]:
    """
    顧客一覧シートから、担当者名とZoom録画時間で一致する行を検索

    シート構造（1行目がヘッダー）:
    - A列(0): お名前
    - B列(1): 担当者
    - E列(4): 初回実施日（例: 2026年1月15日(木) 14:30～16:00）
    - G列(6): 事前キャンセル（ステータス: 着座/飛び/リスケ等）
    - H列(7): 初回/実施後ステータス（成約/失注/保留等）

    Args:
        spreadsheet_id: スプレッドシートID
        sheet_name: シート名（例: "顧客一覧"）
        assignee: 担当者名
        zoom_start_time: Zoom録画の開始時間（UTC）
        tolerance_minutes: 時間の許容誤差（分）

    Returns:
        マッチした行の情報 or None
    """
    from datetime import timedelta

    try:
        client = get_sheets_client()
        spreadsheet = client.open_by_key(spreadsheet_id)

        try:
            worksheet = spreadsheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            print(f"   シート '{sheet_name}' が見つかりません")
            return None

        # 全データを取得
        all_values = worksheet.get_all_values()

        if len(all_values) < 2:
            return None

        # ヘッダー行（1行目）
        headers = all_values[0]

        # 列インデックスを特定
        name_col = 0       # A列: お名前
        assignee_col = 1   # B列: 担当者
        date_col = 4       # E列: 初回実施日
        status_col = 6     # G列: 事前キャンセル
        result_status_col = 7  # H列: 初回/実施後ステータス

        # ヘッダーから列を動的に探す（最初に見つかったものを使用）
        for j, col in enumerate(headers):
            col_clean = col.strip()
            if '担当者' in col_clean and assignee_col == 1:
                assignee_col = j
            elif '初回実施日' in col_clean and date_col == 4:
                date_col = j
            elif '事前キャンセル' in col_clean and status_col == 6:
                status_col = j
            elif col_clean == '初回/実施後ステータス':
                # 完全一致で検索（2回目/実施後ステータス などを除外）
                result_status_col = j

        # Zoom時間をJSTに変換（UTCから+9時間）
        zoom_jst = zoom_start_time + timedelta(hours=9)
        tolerance = timedelta(minutes=tolerance_minutes)

        # データ行を検索（2行目から）
        for i, row in enumerate(all_values[1:], start=2):
            if len(row) <= max(name_col, assignee_col, date_col):
                continue

            row_assignee = row[assignee_col] if len(row) > assignee_col else ""

            # 担当者名が一致しない場合はスキップ（柔軟なマッチング）
            if not match_assignee_name(assignee, row_assignee):
                continue

            customer_name = row[name_col] if len(row) > name_col else ""
            scheduled_time_str = row[date_col] if len(row) > date_col else ""
            status = row[status_col].strip() if len(row) > status_col and row[status_col] else ""
            result_status = row[result_status_col].strip() if len(row) > result_status_col and row[result_status_col] else ""

            # 初回実施日が空白の場合はスキップ
            if not scheduled_time_str:
                continue

            # 日時をパース
            scheduled_time = parse_datetime_flexible(scheduled_time_str)
            if not scheduled_time:
                continue

            # 時間がない場合は日付のみで比較
            if scheduled_time.hour == 0 and scheduled_time.minute == 0:
                if scheduled_time.date() == zoom_jst.date():
                    return {
                        "row_num": i,
                        "customer_name": customer_name,
                        "scheduled_time": scheduled_time_str,
                        "match_type": "date_only",
                        "status": status,
                        "result_status": result_status
                    }
            else:
                # 時間も含めて±tolerance分以内かチェック
                time_diff = abs((zoom_jst.replace(tzinfo=None) - scheduled_time).total_seconds())
                if time_diff <= tolerance.total_seconds():
                    return {
                        "row_num": i,
                        "customer_name": customer_name,
                        "scheduled_time": scheduled_time_str,
                        "match_type": "exact_time",
                        "status": status,
                        "result_status": result_status
                    }

        return None

    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "Quota exceeded" in error_str:
            raise
        print(f"   顧客一覧検索エラー: {e}")
        import traceback
        traceback.print_exc()
        return None


def normalize_name(name: str) -> str:
    """名前を正規化（スペース削除、全角→半角、小文字化）"""
    if not name:
        return ""
    # 全角スペースを半角に
    name = name.replace('　', ' ')
    # スペースを削除
    name = name.replace(' ', '')
    # 全角英数を半角に
    name = unicodedata.normalize('NFKC', name)
    # 小文字化
    name = name.lower()
    return name


# 担当者名のエイリアス（Zoom認証名 → 顧客一覧名）
ASSIGNEE_ALIASES = {
    "長谷川こなつ": "長谷川小夏",
    "播磨谷 彩": "播磨谷　彩",
    "栗原瑠人": "栗原日向子",  # 必要に応じて確認
    "長谷川太一": "長谷川小夏",  # 必要に応じて確認
}

# 逆引きマッピングも作成
ASSIGNEE_ALIASES_REVERSE = {v: k for k, v in ASSIGNEE_ALIASES.items()}


def match_assignee_name(zoom_name: str, customer_name: str) -> bool:
    """
    担当者名が一致するかチェック（柔軟なマッチング）

    マッチング方法:
    1. 正規化した名前で完全一致
    2. エイリアス（別名）でマッチ
    3. スペースを無視してマッチ

    Args:
        zoom_name: Zoom認証の担当者名
        customer_name: 顧客一覧の担当者名

    Returns:
        一致する場合True
    """
    if not zoom_name or not customer_name:
        return False

    # 1. 正規化して比較
    norm_zoom = normalize_name(zoom_name)
    norm_customer = normalize_name(customer_name)

    if norm_zoom == norm_customer:
        return True

    # 2. エイリアスでチェック
    # Zoom名のエイリアスが顧客名と一致するか
    alias = ASSIGNEE_ALIASES.get(zoom_name)
    if alias and normalize_name(alias) == norm_customer:
        return True

    # 顧客名のエイリアスがZoom名と一致するか
    alias_reverse = ASSIGNEE_ALIASES_REVERSE.get(customer_name)
    if alias_reverse and normalize_name(alias_reverse) == norm_zoom:
        return True

    # 3. 正規化したエイリアスでもチェック
    for zoom_alias, customer_alias in ASSIGNEE_ALIASES.items():
        if normalize_name(zoom_alias) == norm_zoom and normalize_name(customer_alias) == norm_customer:
            return True

    return False


def get_customer_name_from_zoom(zoom_name: str) -> str:
    """
    Zoom認証の担当者名から顧客一覧の担当者名を取得

    Args:
        zoom_name: Zoom認証の担当者名

    Returns:
        顧客一覧で使用する担当者名
    """
    # エイリアスがあればそれを返す
    if zoom_name in ASSIGNEE_ALIASES:
        return ASSIGNEE_ALIASES[zoom_name]
    return zoom_name


@retry_on_quota_error(max_retries=5, initial_delay=2.0)
def update_row_with_analysis(
    spreadsheet_id: str,
    assignee: str,
    row_num: int,
    transcript_doc_url: str,
    video_drive_url: Optional[str],
    feedback: str,
    status: str = None
) -> bool:
    """
    指定行に分析結果を書き込む

    Args:
        spreadsheet_id: スプレッドシートID
        assignee: 担当者名（シート名）
        row_num: 行番号（1-indexed）
        transcript_doc_url: 文字起こしDocのURL
        video_drive_url: 動画DriveのURL
        feedback: フィードバック
        status: ステータス（成約/失注など）

    Returns:
        成功したかどうか
    """
    try:
        client = get_sheets_client()
        spreadsheet = client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(assignee)

        # F列: 文字起こし、G列: 動画、H列: FB
        updates = []

        if transcript_doc_url:
            worksheet.update(f"F{row_num}", [[transcript_doc_url]])

        if video_drive_url:
            worksheet.update(f"G{row_num}", [[video_drive_url]])

        if feedback:
            worksheet.update(f"H{row_num}", [[feedback]])

        if status:
            worksheet.update(f"E{row_num}", [[status]])

        print(f"   行 {row_num} を更新しました")
        return True

    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "Quota exceeded" in error_str:
            raise
        print(f"   行更新エラー: {e}")
        return False


@retry_on_quota_error(max_retries=5, initial_delay=2.0)
def get_all_assignee_sheets(spreadsheet_id: str) -> list[str]:
    """
    スプレッドシートの全シート名（担当者名）を取得

    Args:
        spreadsheet_id: スプレッドシートID

    Returns:
        シート名のリスト
    """
    try:
        client = get_sheets_client()
        spreadsheet = client.open_by_key(spreadsheet_id)
        return [ws.title for ws in spreadsheet.worksheets()]
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "Quota exceeded" in error_str:
            raise
        print(f"シート一覧取得エラー: {e}")
        return []


@retry_on_quota_error(max_retries=5, initial_delay=2.0)
def find_row_by_customer_and_assignee(
    worksheet,
    customer_name: str,
    assignee: str
) -> Optional[int]:
    """
    顧客名と担当者で行を検索

    Args:
        worksheet: ワークシート
        customer_name: 顧客名（A列: お名前）
        assignee: 担当者名（B列: 担当者）

    Returns:
        行番号（1-indexed）、見つからない場合はNone
    """
    try:
        all_values = worksheet.get_all_values()

        for i, row in enumerate(all_values):
            if len(row) >= 2:
                # A列（お名前）とB列（担当者）でマッチング
                if row[0] == customer_name and row[1] == assignee:
                    return i + 1  # 1-indexed

        return None
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "Quota exceeded" in error_str:
            raise
        print(f"行検索エラー: {e}")
        return None


def write_meeting_data(
    spreadsheet_id: str,
    sheet_name: str,
    customer_name: str,
    assignee: str,
    meeting_datetime: str,
    duration_minutes: int,
    transcript_doc_url: str,
    video_drive_url: Optional[str],
    feedback: str
) -> bool:
    """
    面談データをスプレッドシートに書き込む（F, G, H列を更新）

    Args:
        spreadsheet_id: スプレッドシートID
        sheet_name: シート名
        customer_name: 顧客名（マッチング用）
        assignee: 担当者名（マッチング用）
        meeting_datetime: 面談日時
        duration_minutes: 所要時間（分）
        transcript_doc_url: 文字起こしGoogle DocsのURL
        video_drive_url: 動画Google DriveのURL
        feedback: フィードバック

    Returns:
        成功したかどうか
    """
    try:
        client = get_sheets_client()
        spreadsheet = client.open_by_key(spreadsheet_id)

        # シートを取得
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
        except:
            worksheet = spreadsheet.sheet1  # デフォルトシート

        # 顧客名と担当者で行を検索
        row_num = find_row_by_customer_and_assignee(worksheet, customer_name, assignee)

        if row_num:
            # 既存行を更新（F, G, H列）
            # F列: 文字起こしDocリンク
            # G列: 動画Driveリンク
            # H列: フィードバック
            worksheet.update(f"F{row_num}", [[transcript_doc_url]])
            if video_drive_url:
                worksheet.update(f"G{row_num}", [[video_drive_url]])
            worksheet.update(f"H{row_num}", [[feedback]])

            print(f"   行 {row_num} を更新: {customer_name} / {assignee}")
            return True
        else:
            # 見つからない場合は新しい行を追加
            print(f"   顧客 '{customer_name}' / 担当者 '{assignee}' が見つかりません")
            print(f"   → 新しい行を追加します")

            all_values = worksheet.get_all_values()
            next_row = len(all_values) + 1

            # 新規行: A=顧客名, B=担当者, C=空, D=空, E=空, F=文字起こし, G=動画, H=FB
            new_row = [
                customer_name,
                assignee,
                "",  # 流入経路
                "",  # 流入
                meeting_datetime,  # 初回実施日
                transcript_doc_url,  # F列
                video_drive_url or "",  # G列
                feedback  # H列
            ]

            worksheet.update(f"A{next_row}:H{next_row}", [new_row])
            print(f"   行 {next_row} に新規追加")
            return True

    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "Quota exceeded" in error_str:
            raise
        print(f"シート書き込みエラー: {e}")
        import traceback
        traceback.print_exc()
        return False


def normalize_text_for_match(text: str) -> str:
    """
    検索用に文字列を正規化
    - 全角→半角に統一（NFKC正規化）
    - 小文字に統一
    - すべての空白を除去

    Args:
        text: 正規化する文字列

    Returns:
        正規化された文字列
    """
    if not text:
        return ""
    # 全角→半角、文字の正規化（NFKC）
    text = unicodedata.normalize('NFKC', text)
    # 小文字に統一
    text = text.lower()
    # すべての空白を除去（スペースの有無を無視）
    text = re.sub(r'\s+', '', text)
    return text


@retry_on_quota_error(max_retries=5, initial_delay=2.0)
def find_existing_row_in_zoom_sheet(
    worksheet,
    customer_name: str,
    assignee: str,
    meeting_datetime: str = None
) -> Optional[int]:
    """
    Zoom相談一覧シートで、顧客名+担当者が一致する行を検索

    マッチング条件:
    - 顧客名と担当者が一致する行を検索
    - 同じ顧客+担当者の組み合わせは1行のみ（リスケで日付が変わっても同じ行を更新）

    Args:
        worksheet: ワークシート
        customer_name: 顧客名（A列）
        assignee: 担当者名（B列）
        meeting_datetime: 面談日時（C列）- 未使用（互換性のため残す）

    Returns:
        行番号（1-indexed）、見つからない場合はNone
    """
    try:
        all_values = worksheet.get_all_values()

        # 検索用に正規化
        search_customer = normalize_text_for_match(customer_name)
        search_assignee = normalize_text_for_match(assignee)

        # ヘッダー行をスキップして検索（2行目以降）
        for i, row in enumerate(all_values[1:], start=2):
            if len(row) >= 2:
                row_customer = normalize_text_for_match(row[0])
                row_assignee = normalize_text_for_match(row[1])

                # 正規化した顧客名と担当者でマッチング
                if row_customer == search_customer and row_assignee == search_assignee:
                    return i

        return None

    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "Quota exceeded" in error_str:
            raise
        print(f"   既存行検索エラー: {e}")
        return None


@retry_on_quota_error(max_retries=5, initial_delay=2.0)
def write_to_zoom_sheet(
    spreadsheet_id: str,
    customer_name: str,
    assignee: str,
    meeting_datetime: str,
    duration_minutes: int,
    cancel_status: str,
    result_status: str,
    transcript_doc_url: str,
    video_drive_url: Optional[str],
    feedback: str,
    sheet_name: str = None
) -> bool:
    """
    Zoom相談一覧シートに書き込む
    - 同じ顧客名+担当者の行が既にある場合:
      - 新しい録画の日時 > 既存レコードの日時 → 更新する
      - 新しい録画の日時 <= 既存レコードの日時 → スキップ（既存を保持）
    - ない場合は新規行を追加

    列構成:
    A: 顧客名
    B: 担当者
    C: 面談日時
    D: 所要時間
    E: 事前キャンセル（顧客管理シートG列: 着座/飛び/リスケ等）
    F: 初回/実施後ステータス（顧客管理シートH列: 成約/失注/保留等）
    G: 文字起こし（Google Docリンク）
    H: 面談動画（Google Driveリンク）
    I: FB

    Args:
        spreadsheet_id: スプレッドシートID
        customer_name: 顧客名
        assignee: 担当者名
        meeting_datetime: 面談日時
        duration_minutes: 所要時間（分）
        cancel_status: 事前キャンセルステータス（顧客管理シートG列: 着座/飛び/リスケ等）
        result_status: 初回/実施後ステータス（顧客管理シートH列: 成約/失注/保留等）
        transcript_doc_url: 文字起こしGoogle DocsのURL
        video_drive_url: 動画Google DriveのURL
        feedback: フィードバック

    Returns:
        成功したかどうか
    """
    try:
        client = get_sheets_client()
        spreadsheet = client.open_by_key(spreadsheet_id)

        # シートを取得
        target_sheet = sheet_name or DEFAULT_SHEET_NAME
        try:
            worksheet = spreadsheet.worksheet(target_sheet)
        except:
            worksheet = spreadsheet.sheet1

        # 既存行を検索（顧客名 + 担当者 + 面談日でマッチング）
        existing_row = find_existing_row_in_zoom_sheet(worksheet, customer_name, assignee, meeting_datetime)

        if existing_row:
            # 既存行の値を取得
            existing_values = worksheet.row_values(existing_row)
            existing_datetime_str = existing_values[2] if len(existing_values) > 2 else ""  # C列 (0-indexed: 2)
            existing_transcript = existing_values[6] if len(existing_values) > 6 else ""  # G列 (0-indexed: 6)
            existing_video = existing_values[7] if len(existing_values) > 7 else ""  # H列 (0-indexed: 7)

            # 日時を比較: 新しい録画の日時 > 既存レコードの日時 の場合のみ更新
            from datetime import datetime as dt
            new_dt = None
            existing_dt = None
            try:
                # 新しい日時をパース
                new_dt = dt.strptime(meeting_datetime[:19], "%Y-%m-%d %H:%M:%S")
            except:
                try:
                    new_dt = dt.strptime(meeting_datetime[:16], "%Y-%m-%d %H:%M")
                except:
                    pass
            try:
                # 既存の日時をパース
                existing_dt = dt.strptime(existing_datetime_str[:19], "%Y-%m-%d %H:%M:%S")
            except:
                try:
                    existing_dt = dt.strptime(existing_datetime_str[:16], "%Y-%m-%d %H:%M")
                except:
                    pass

            # 日時比較: 新しい日時が既存より後でなければスキップ
            if new_dt and existing_dt and new_dt <= existing_dt:
                print(f"   → スキップ: 既存レコードの方が新しい ({existing_datetime_str} >= {meeting_datetime})")
                return True  # 成功扱いで終了

            # 既存行を更新（全列を更新）
            print(f"   → 既存行 {existing_row} を更新: {customer_name} / {assignee}")

            # 既存のGoogle Docsリンクがあれば保持（上書きしない）
            final_transcript_url = existing_transcript if existing_transcript and "docs.google.com" in existing_transcript else transcript_doc_url
            # 既存のDriveリンクがあれば保持（Zoom共有リンクで上書きしない）
            final_video_url = existing_video if existing_video and "drive.google.com" in existing_video else (video_drive_url or "")

            # K列に更新日時を記録（2回目以降の更新時のみ）
            update_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

            # C列〜I列を更新 + K列に更新日
            update_data = [
                meeting_datetime,  # C: 面談日時
                f"{duration_minutes}分",  # D: 所要時間
                cancel_status,  # E: 事前キャンセル
                result_status,  # F: 初回/実施後ステータス
                final_transcript_url,  # G: 文字起こし（既存があれば保持）
                final_video_url,  # H: 面談動画（既存があれば保持）
                feedback  # I: FB
            ]
            worksheet.update(f"C{existing_row}:I{existing_row}", [update_data])

            # K列（更新日）を別途更新
            worksheet.update(f"K{existing_row}", [[update_timestamp]])

            print(f"   → 更新完了（C〜I列を上書き、K列に更新日記録）")
            return True
        else:
            # 新規行を追加
            all_values = worksheet.get_all_values()
            next_row = len(all_values) + 1

            # 行データを作成
            row_data = [
                customer_name,  # A: 顧客名
                assignee,  # B: 担当者
                meeting_datetime,  # C: 面談日時
                f"{duration_minutes}分",  # D: 所要時間
                cancel_status,  # E: 事前キャンセル
                result_status,  # F: 初回/実施後ステータス
                transcript_doc_url,  # G: 文字起こし
                video_drive_url or "",  # H: 面談動画
                feedback  # I: FB
            ]

            worksheet.update(values=[row_data], range_name=f"A{next_row}:I{next_row}")

            print(f"   → 新規行 {next_row} に追加: {customer_name} / {assignee}")
            return True

    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "Quota exceeded" in error_str:
            raise
        print(f"シート書き込みエラー: {e}")
        import traceback
        traceback.print_exc()
        return False


@retry_on_quota_error(max_retries=5, initial_delay=2.0)
def write_error_to_zoom_sheet(
    spreadsheet_id: str,
    customer_name: str,
    assignee: str,
    meeting_datetime: str,
    error_message: str,
    sheet_name: str = None
) -> bool:
    """
    Zoom相談一覧シートにエラー情報を書き込む

    J列にエラーメッセージを記録。エラーがある行は後で再処理可能。

    Args:
        spreadsheet_id: スプレッドシートID
        customer_name: 顧客名
        assignee: 担当者名
        meeting_datetime: 面談日時
        error_message: エラーメッセージ
        sheet_name: シート名

    Returns:
        成功したかどうか
    """
    try:
        client = get_sheets_client()
        spreadsheet = client.open_by_key(spreadsheet_id)

        target_sheet = sheet_name or DEFAULT_SHEET_NAME
        try:
            worksheet = spreadsheet.worksheet(target_sheet)
        except:
            worksheet = spreadsheet.sheet1

        # 既存行を検索（顧客名 + 担当者 + 面談日でマッチング）
        existing_row = find_existing_row_in_zoom_sheet(worksheet, customer_name, assignee, meeting_datetime)

        # エラーメッセージを短縮（100文字まで）
        short_error = error_message[:100] if len(error_message) > 100 else error_message
        timestamp = datetime.now().strftime("%m/%d %H:%M")
        error_text = f"[{timestamp}] {short_error}"

        if existing_row:
            # 既存行のJ列にエラーを記録
            worksheet.update(f"J{existing_row}", [[error_text]])
            print(f"   → エラー記録（行{existing_row}）: {short_error[:50]}...")
            return True
        else:
            # 新規行を追加（最小限の情報 + エラー）
            all_values = worksheet.get_all_values()
            next_row = len(all_values) + 1

            row_data = [
                customer_name,  # A: 顧客名
                assignee,  # B: 担当者
                meeting_datetime,  # C: 面談日時
                "",  # D: 所要時間
                "",  # E: 事前キャンセル
                "",  # F: 初回/実施後ステータス
                "",  # G: 文字起こし
                "",  # H: 面談動画
                "",  # I: FB
                error_text  # J: エラー
            ]

            worksheet.update(values=[row_data], range_name=f"A{next_row}:J{next_row}")
            print(f"   → エラー行を新規追加（行{next_row}）: {short_error[:50]}...")
            return True

    except Exception as e:
        print(f"エラー記録失敗: {e}")
        return False


@retry_on_quota_error(max_retries=5, initial_delay=2.0)
def clear_error_in_zoom_sheet(
    spreadsheet_id: str,
    customer_name: str,
    assignee: str,
    sheet_name: str = None
) -> bool:
    """
    Zoom相談一覧シートのエラー情報をクリア（処理成功時）

    Args:
        spreadsheet_id: スプレッドシートID
        customer_name: 顧客名
        assignee: 担当者名
        sheet_name: シート名

    Returns:
        成功したかどうか
    """
    try:
        client = get_sheets_client()
        spreadsheet = client.open_by_key(spreadsheet_id)

        target_sheet = sheet_name or DEFAULT_SHEET_NAME
        try:
            worksheet = spreadsheet.worksheet(target_sheet)
        except:
            worksheet = spreadsheet.sheet1

        existing_row = find_existing_row_in_zoom_sheet(worksheet, customer_name, assignee)

        if existing_row:
            # J列をクリア
            worksheet.update(f"J{existing_row}", [[""]])
            return True

        return False

    except Exception as e:
        print(f"エラークリア失敗: {e}")
        return False


@retry_on_quota_error(max_retries=5, initial_delay=2.0)
def get_error_rows_from_zoom_sheet(
    spreadsheet_id: str,
    sheet_name: str = None
) -> list[dict]:
    """
    Zoom相談一覧シートからエラーがある行を取得

    Returns:
        [{"row_num": int, "customer_name": str, "assignee": str, "meeting_datetime": str, "error": str}]
    """
    try:
        client = get_sheets_client()
        spreadsheet = client.open_by_key(spreadsheet_id)

        target_sheet = sheet_name or DEFAULT_SHEET_NAME
        try:
            worksheet = spreadsheet.worksheet(target_sheet)
        except:
            worksheet = spreadsheet.sheet1

        all_values = worksheet.get_all_values()
        error_rows = []

        for i, row in enumerate(all_values[1:], start=2):  # ヘッダーをスキップ
            # J列（index 9）にエラーがあるか確認
            if len(row) > 9 and row[9].strip():
                error_rows.append({
                    "row_num": i,
                    "customer_name": row[0] if len(row) > 0 else "",
                    "assignee": row[1] if len(row) > 1 else "",
                    "meeting_datetime": row[2] if len(row) > 2 else "",
                    "error": row[9]
                })

        return error_rows

    except Exception as e:
        print(f"エラー行取得失敗: {e}")
        return []


@retry_on_quota_error(max_retries=5, initial_delay=2.0)
def get_rows_with_zoom_link_only(
    spreadsheet_id: str,
    sheet_name: str = None
) -> list[dict]:
    """
    Zoom相談一覧シートから、H列がZoomリンク（Drive未アップロード）の行を取得

    Returns:
        [{"row_num": int, "customer_name": str, "assignee": str, "meeting_datetime": str, "video_url": str}]
    """
    try:
        client = get_sheets_client()
        spreadsheet = client.open_by_key(spreadsheet_id)

        target_sheet = sheet_name or DEFAULT_SHEET_NAME
        try:
            worksheet = spreadsheet.worksheet(target_sheet)
        except:
            worksheet = spreadsheet.sheet1

        all_values = worksheet.get_all_values()
        zoom_only_rows = []

        for i, row in enumerate(all_values[1:], start=2):  # ヘッダーをスキップ
            # H列（動画）がZoomリンクで、Driveリンクでない行を検索
            has_video = len(row) > 7 and row[7].strip()
            is_zoom_link = has_video and "zoom.us" in row[7]
            is_drive_link = has_video and "drive.google.com" in row[7]

            if is_zoom_link and not is_drive_link:
                zoom_only_rows.append({
                    "row_num": i,
                    "customer_name": row[0] if len(row) > 0 else "",
                    "assignee": row[1] if len(row) > 1 else "",
                    "meeting_datetime": row[2] if len(row) > 2 else "",
                    "video_url": row[7] if len(row) > 7 else ""
                })

        return zoom_only_rows

    except Exception as e:
        print(f"Zoomリンク行の取得エラー: {e}")
        return []


@retry_on_quota_error(max_retries=5, initial_delay=2.0)
def update_video_url_in_zoom_sheet(
    spreadsheet_id: str,
    row_num: int,
    video_url: str,
    sheet_name: str = None
) -> bool:
    """
    Zoom相談一覧シートの指定行のH列（動画）を更新

    Args:
        spreadsheet_id: スプレッドシートID
        row_num: 行番号
        video_url: 動画のURL
        sheet_name: シート名

    Returns:
        成功したかどうか
    """
    try:
        client = get_sheets_client()
        spreadsheet = client.open_by_key(spreadsheet_id)

        target_sheet = sheet_name or DEFAULT_SHEET_NAME
        try:
            worksheet = spreadsheet.worksheet(target_sheet)
        except:
            worksheet = spreadsheet.sheet1

        # H列を更新
        worksheet.update(f"H{row_num}", [[video_url]])

        # K列に更新日時を記録
        update_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        worksheet.update(f"K{row_num}", [[update_timestamp]])

        print(f"   → 行{row_num} の動画URLを更新")
        return True

    except Exception as e:
        print(f"動画URL更新エラー: {e}")
        return False


@retry_on_quota_error(max_retries=5, initial_delay=2.0)
def get_rows_missing_transcript(
    spreadsheet_id: str,
    sheet_name: str = None
) -> list[dict]:
    """
    Zoom相談一覧シートから、動画はあるが文字起こしがない行を取得

    Returns:
        [{"row_num": int, "customer_name": str, "assignee": str, "meeting_datetime": str, "video_url": str}]
    """
    try:
        client = get_sheets_client()
        spreadsheet = client.open_by_key(spreadsheet_id)

        target_sheet = sheet_name or DEFAULT_SHEET_NAME
        try:
            worksheet = spreadsheet.worksheet(target_sheet)
        except:
            worksheet = spreadsheet.sheet1

        all_values = worksheet.get_all_values()
        missing_rows = []

        for i, row in enumerate(all_values[1:], start=2):  # ヘッダーをスキップ
            # H列（動画URL）があり、G列（文字起こし）がない行を検索
            h_val = row[7].strip() if len(row) > 7 else ""
            has_video = "drive.google.com" in h_val or "zoom.us" in h_val
            has_transcript = len(row) > 6 and row[6].strip() and "docs.google.com" in row[6]

            if has_video and not has_transcript:
                missing_rows.append({
                    "row_num": i,
                    "customer_name": row[0] if len(row) > 0 else "",
                    "assignee": row[1] if len(row) > 1 else "",
                    "meeting_datetime": row[2] if len(row) > 2 else "",
                    "video_url": row[7] if len(row) > 7 else ""
                })

        return missing_rows

    except Exception as e:
        print(f"文字起こし未作成行の取得エラー: {e}")
        return []


@retry_on_quota_error(max_retries=5, initial_delay=2.0)
def update_transcript_url_in_zoom_sheet(
    spreadsheet_id: str,
    row_num: int,
    transcript_url: str,
    sheet_name: str = None
) -> bool:
    """
    Zoom相談一覧シートの指定行のG列（文字起こし）を更新

    Args:
        spreadsheet_id: スプレッドシートID
        row_num: 行番号
        transcript_url: 文字起こしドキュメントのURL
        sheet_name: シート名

    Returns:
        成功したかどうか
    """
    try:
        client = get_sheets_client()
        spreadsheet = client.open_by_key(spreadsheet_id)

        target_sheet = sheet_name or DEFAULT_SHEET_NAME
        try:
            worksheet = spreadsheet.worksheet(target_sheet)
        except:
            worksheet = spreadsheet.sheet1

        # G列を更新
        worksheet.update(f"G{row_num}", [[transcript_url]])

        # K列に更新日時を記録
        update_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        worksheet.update(f"K{row_num}", [[update_timestamp]])

        print(f"   → 行{row_num} の文字起こしURLを更新")
        return True

    except Exception as e:
        print(f"文字起こしURL更新エラー: {e}")
        return False


@retry_on_quota_error(max_retries=5, initial_delay=2.0)
def write_to_data_storage_sheet(
    spreadsheet_id: str,
    customer_name: str,
    assignee: str,
    meeting_datetime: str,
    duration_minutes: int,
    cancel_status: str,
    result_status: str,
    transcript_doc_url: str,
    video_drive_url: Optional[str],
    feedback: str,
    sheet_name: str = "Zoom相談一覧 データ格納"
) -> bool:
    """
    データ格納シートに書き込む（常に新規行追加、更新なし）
    全履歴を蓄積するためのシート

    列構成:
    A: 顧客名
    B: 担当者
    C: 面談日時
    D: 所要時間
    E: 事前キャンセル（顧客管理シートG列: 着座/飛び/リスケ等）
    F: 初回/実施後ステータス（顧客管理シートH列: 成約/失注/保留等）
    G: 文字起こし（Google Docリンク）
    H: 面談動画（Google Driveリンク）
    I: FB

    Args:
        spreadsheet_id: スプレッドシートID
        customer_name: 顧客名
        assignee: 担当者名
        meeting_datetime: 面談日時
        duration_minutes: 所要時間（分）
        cancel_status: 事前キャンセルステータス（顧客管理シートG列）
        result_status: 初回/実施後ステータス（顧客管理シートH列）
        transcript_doc_url: 文字起こしGoogle DocsのURL
        video_drive_url: 動画Google DriveのURL
        feedback: フィードバック
        sheet_name: シート名

    Returns:
        成功したかどうか
    """
    try:
        client = get_sheets_client()
        spreadsheet = client.open_by_key(spreadsheet_id)

        # シートを取得
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
        except:
            print(f"   シート '{sheet_name}' が見つかりません")
            return False

        # 重複チェック（面談日時＋担当者で判定）
        all_values = worksheet.get_all_values()

        # 既存データから重複をチェック（B列:担当者, C列:面談日時）
        for row_idx, row in enumerate(all_values[1:], start=2):  # ヘッダー行をスキップ
            if len(row) >= 3:
                existing_assignee = row[1] if len(row) > 1 else ""
                existing_datetime = row[2] if len(row) > 2 else ""
                if existing_assignee == assignee and existing_datetime == meeting_datetime:
                    print(f"   → データ格納シート 重複スキップ: {customer_name} / {assignee} / {meeting_datetime}")
                    return True  # 既に存在するのでスキップ（成功扱い）

        next_row = len(all_values) + 1

        # 行データを作成
        row_data = [
            customer_name,  # A: 顧客名
            assignee,  # B: 担当者
            meeting_datetime,  # C: 面談日時
            f"{duration_minutes}分",  # D: 所要時間
            cancel_status,  # E: 事前キャンセル
            result_status,  # F: 初回/実施後ステータス
            transcript_doc_url,  # G: 文字起こし
            video_drive_url or "",  # H: 面談動画
            feedback  # I: FB
        ]

        worksheet.update(values=[row_data], range_name=f"A{next_row}:I{next_row}")

        print(f"   → データ格納シート 行 {next_row} に追加: {customer_name} / {assignee}")
        return True

    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "Quota exceeded" in error_str:
            raise
        print(f"データ格納シート書き込みエラー: {e}")
        import traceback
        traceback.print_exc()
        return False


@retry_on_quota_error(max_retries=5, initial_delay=2.0)
def reconcile_zoom_sheet_with_customer_sheet(
    zoom_spreadsheet_id: str,
    customer_spreadsheet_id: str,
    zoom_sheet_name: str = "Zoom相談一覧"
) -> int:
    """
    Zoom相談一覧シートのE列・F列が空の行を、顧客管理シートと再照合して更新

    処理内容:
    1. 顧客管理シートの全データを一括読み込み（API呼び出し削減）
    2. Zoom相談一覧シートの全行をチェック
    3. E列（事前キャンセル）またはF列（初回/実施後ステータス）が空の行を抽出
    4. B列（担当者）+ C列（面談日時）でメモリ内検索
    5. マッチすれば、A列（顧客名）、E列、F列を更新

    Args:
        zoom_spreadsheet_id: Zoom相談一覧のスプレッドシートID
        customer_spreadsheet_id: 顧客管理シートのスプレッドシートID
        zoom_sheet_name: Zoom相談一覧のシート名

    Returns:
        更新した行数
    """
    from datetime import timedelta

    try:
        client = get_sheets_client()

        # 顧客管理シートの全データを一括読み込み（API呼び出し削減のため）
        print("   顧客管理シートを一括読み込み中...")
        all_customer_data = load_all_customer_sheets_data(customer_spreadsheet_id)

        if not all_customer_data:
            print("   顧客管理シートのデータが取得できませんでした")
            return 0

        # Zoom相談一覧シートを取得
        zoom_spreadsheet = client.open_by_key(zoom_spreadsheet_id)
        try:
            zoom_worksheet = zoom_spreadsheet.worksheet(zoom_sheet_name)
        except:
            print(f"シート '{zoom_sheet_name}' が見つかりません")
            return 0

        zoom_values = zoom_worksheet.get_all_values()

        if len(zoom_values) <= 1:
            print("Zoom相談一覧にデータがありません")
            return 0

        updated_count = 0

        # ヘッダー行をスキップして各行をチェック
        for i, row in enumerate(zoom_values[1:], start=2):
            if len(row) < 6:
                continue

            customer_name = row[0] if len(row) > 0 else ""
            assignee = row[1] if len(row) > 1 else ""
            meeting_datetime = row[2] if len(row) > 2 else ""
            cancel_status = row[4] if len(row) > 4 else ""
            result_status = row[5] if len(row) > 5 else ""

            # E列またはF列が空の行を対象
            if cancel_status and result_status:
                continue  # 両方埋まっている場合はスキップ

            if not assignee or not meeting_datetime:
                continue  # 担当者または日時がない場合はスキップ

            # 日時をパース
            meeting_dt = parse_datetime_flexible(meeting_datetime)
            if not meeting_dt:
                continue

            # メモリ内で顧客管理シートと照合（API呼び出しなし）
            matched_row = find_matching_row_in_memory(
                all_customer_data=all_customer_data,
                assignee=assignee,
                zoom_start_time=meeting_dt - timedelta(hours=9),  # JSTからUTCに変換
                tolerance_minutes=45
            )

            if matched_row:
                new_customer_name = matched_row.get('customer_name', '')
                new_cancel_status = matched_row.get('status', '')
                new_result_status = matched_row.get('result_status', '')

                # 更新が必要かチェック
                needs_update = False
                if new_customer_name and new_customer_name != customer_name:
                    needs_update = True
                if new_cancel_status and new_cancel_status != cancel_status:
                    needs_update = True
                if new_result_status and new_result_status != result_status:
                    needs_update = True

                if needs_update:
                    # A列、E列、F列を更新
                    if new_customer_name:
                        zoom_worksheet.update(f"A{i}", [[new_customer_name]])
                    if new_cancel_status:
                        zoom_worksheet.update(f"E{i}", [[new_cancel_status]])
                    if new_result_status:
                        zoom_worksheet.update(f"F{i}", [[new_result_status]])

                    print(f"   → 行 {i} を更新: {customer_name} → {new_customer_name or customer_name}")
                    print(f"      E列: {cancel_status} → {new_cancel_status}")
                    print(f"      F列: {result_status} → {new_result_status}")
                    updated_count += 1

        return updated_count

    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "Quota exceeded" in error_str:
            raise
        print(f"再照合処理エラー: {e}")
        import traceback
        traceback.print_exc()
        return 0


@retry_on_quota_error(max_retries=5, initial_delay=2.0)
def get_zoom_credentials_from_sheet(
    spreadsheet_id: str,
    assignee: str,
    sheet_name: str = "Zoomキー"
) -> Optional[dict]:
    """
    スプレッドシートからZoom認証情報を取得（フォールバック用）

    シート構造（Zoomキーシート）:
    - A列: 担当者名
    - B列: Account ID
    - C列: Client ID
    - D列: Client Secret

    Args:
        spreadsheet_id: スプレッドシートID
        assignee: 担当者名
        sheet_name: シート名

    Returns:
        認証情報の辞書 {"account_id", "client_id", "client_secret"}
        見つからない場合はNone
    """
    try:
        client = get_sheets_client()
        spreadsheet = client.open_by_key(spreadsheet_id)

        try:
            worksheet = spreadsheet.worksheet(sheet_name)
        except:
            print(f"   シート '{sheet_name}' が見つかりません")
            return None

        all_values = worksheet.get_all_values()

        # ヘッダー行を探す（「担当者」または「名前」を含む行）
        header_row_idx = 0
        for i, row in enumerate(all_values[:5]):
            row_lower = [str(c).lower() for c in row]
            if any('担当' in c or '名前' in c or 'name' in c.lower() for c in row):
                header_row_idx = i
                break

        # データ行を検索
        for i, row in enumerate(all_values[header_row_idx + 1:], start=header_row_idx + 2):
            if len(row) < 4:
                continue

            row_assignee = row[0].strip() if row[0] else ""

            # 担当者名でマッチング（部分一致も許容）
            if row_assignee == assignee or assignee in row_assignee or row_assignee in assignee:
                account_id = row[1].strip() if len(row) > 1 and row[1] else ""
                client_id = row[2].strip() if len(row) > 2 and row[2] else ""
                client_secret = row[3].strip() if len(row) > 3 and row[3] else ""

                if account_id and client_id and client_secret:
                    return {
                        "account_id": account_id,
                        "client_id": client_id,
                        "client_secret": client_secret
                    }

        return None

    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "Quota exceeded" in error_str:
            raise
        print(f"   スプレッドシートから認証情報取得エラー: {e}")
        return None


@retry_on_quota_error(max_retries=5, initial_delay=2.0)
def write_analysis_to_sheet(
    spreadsheet_id: str,
    assignee: str,
    customer_name: str,
    meeting_datetime: str,
    duration_minutes: int,
    transcript: str,
    video_path: Optional[str],
    analysis: dict,
    feedback: str,
    sheet_name: str = None,
    drive_folder_id: Optional[str] = None
) -> bool:
    """
    分析結果をスプレッドシートに書き込む（統合版）
    - Google Docsに文字起こしを保存
    - Google Driveに動画をアップロード
    - シートにリンクとFBを書き込み

    Args:
        spreadsheet_id: スプレッドシートID
        assignee: 担当者名
        customer_name: 顧客名
        meeting_datetime: 面談日時
        duration_minutes: 所要時間（分）
        transcript: 文字起こしテキスト
        video_path: 動画ファイルパス（オプション）
        analysis: 分析結果
        feedback: フィードバック
        sheet_name: シート名（デフォルトは最初のシート）
        drive_folder_id: Google Driveフォルダ ID（オプション）

    Returns:
        成功したかどうか
    """
    from services.google_drive_client import create_transcript_doc, upload_video_to_drive

    try:
        # 1. 文字起こしをGoogle Docsに保存
        print("→ 文字起こしをGoogle Docsに保存中...")
        meeting_date = meeting_datetime[:10] if len(meeting_datetime) >= 10 else meeting_datetime
        transcript_doc_url = create_transcript_doc(
            transcript=transcript,
            assignee=assignee,
            customer_name=customer_name,
            meeting_date=meeting_date,
            folder_id=drive_folder_id
        )

        # 2. 動画をGoogle Driveにアップロード（あれば）
        video_drive_url = None
        if video_path and os.path.exists(video_path):
            print("→ 動画をGoogle Driveにアップロード中...")
            video_drive_url = upload_video_to_drive(
                video_path=video_path,
                assignee=assignee,
                customer_name=customer_name,
                meeting_date=meeting_date,
                folder_id=drive_folder_id
            )

        # 3. シートに書き込み
        print("→ スプレッドシートに書き込み中...")
        success = write_meeting_data(
            spreadsheet_id=spreadsheet_id,
            sheet_name=sheet_name or "シート1",
            customer_name=customer_name,
            assignee=assignee,
            meeting_datetime=meeting_datetime,
            duration_minutes=duration_minutes,
            transcript_doc_url=transcript_doc_url,
            video_drive_url=video_drive_url,
            feedback=feedback
        )

        return success

    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "Quota exceeded" in error_str:
            raise
        print(f"分析結果書き込みエラー: {e}")
        import traceback
        traceback.print_exc()
        return False


@retry_on_quota_error(max_retries=5, initial_delay=2.0)
def reconcile_zoom_sheet_with_customer_list(
    spreadsheet_id: str,
    zoom_sheet_name: str = "Zoom相談一覧",
    customer_list_sheet_name: str = "顧客一覧"
) -> int:
    """
    Zoom相談一覧シートのE列・F列が空の行を、顧客一覧シートと再照合して更新
    （同一スプレッドシート内の2つのシートを照合）

    処理内容:
    1. 顧客一覧シートの全データを一括読み込み
    2. Zoom相談一覧シートの全行をチェック
    3. E列（事前キャンセル）またはF列（初回/実施後ステータス）が空の行を抽出
    4. B列（担当者）+ C列（面談日時）でメモリ内検索
    5. マッチすれば、A列（顧客名）、E列、F列を更新

    Args:
        spreadsheet_id: スプレッドシートID
        zoom_sheet_name: Zoom相談一覧のシート名
        customer_list_sheet_name: 顧客一覧のシート名

    Returns:
        更新した行数
    """
    from datetime import timedelta

    try:
        client = get_sheets_client()
        spreadsheet = client.open_by_key(spreadsheet_id)

        # 顧客一覧シートを取得
        print(f"   顧客管理シートを一括読み込み中...")
        try:
            customer_worksheet = spreadsheet.worksheet(customer_list_sheet_name)
        except:
            print(f"   シート '{customer_list_sheet_name}' が見つかりません")
            return 0

        customer_values = customer_worksheet.get_all_values()
        if len(customer_values) < 2:
            print("   顧客一覧にデータがありません")
            return 0

        # 顧客データをメモリに読み込み（担当者+日時でインデックス）
        customer_data = []
        for row in customer_values[1:]:  # ヘッダーをスキップ
            if len(row) < 8:
                continue
            customer_name = row[0] if len(row) > 0 else ""
            assignee = row[1] if len(row) > 1 else ""
            scheduled_time_str = row[4] if len(row) > 4 else ""  # E列: 初回実施日
            status = row[6] if len(row) > 6 else ""  # G列: 事前キャンセル
            result_status = row[7] if len(row) > 7 else ""  # H列: 初回/実施後ステータス

            if assignee and scheduled_time_str:
                scheduled_time = parse_datetime_flexible(scheduled_time_str)
                if scheduled_time:
                    customer_data.append({
                        "customer_name": customer_name,
                        "assignee": assignee,  # 元の名前を保持（マッチングで柔軟に比較）
                        "scheduled_time": scheduled_time,
                        "status": status.strip(),
                        "result_status": result_status.strip()
                    })

        print(f"   顧客管理シート読み込み完了: {len(customer_data)}件")

        # Zoom相談一覧シートを取得
        try:
            zoom_worksheet = spreadsheet.worksheet(zoom_sheet_name)
        except:
            print(f"   シート '{zoom_sheet_name}' が見つかりません")
            return 0

        zoom_values = zoom_worksheet.get_all_values()

        if len(zoom_values) <= 1:
            print("   Zoom相談一覧にデータがありません")
            return 0

        updated_count = 0
        tolerance = timedelta(minutes=45)

        # ヘッダー行をスキップして各行をチェック
        for i, row in enumerate(zoom_values[1:], start=2):
            if len(row) < 6:
                continue

            customer_name = row[0] if len(row) > 0 else ""
            assignee = row[1] if len(row) > 1 else ""
            meeting_datetime = row[2] if len(row) > 2 else ""
            cancel_status = row[4] if len(row) > 4 else ""
            result_status = row[5] if len(row) > 5 else ""

            # E列またはF列が空の行を対象
            if cancel_status and result_status:
                continue  # 両方埋まっている場合はスキップ

            if not assignee or not meeting_datetime:
                continue  # 担当者または日時がない場合はスキップ

            # 日時をパース
            meeting_dt = parse_datetime_flexible(meeting_datetime)
            if not meeting_dt:
                continue

            # メモリ内で顧客一覧と照合（柔軟なマッチング）
            matched = None

            for cust in customer_data:
                # 担当者名の柔軟なマッチング
                if not match_assignee_name(assignee, cust["assignee"]):
                    continue

                # 時間の照合
                time_diff = abs((meeting_dt - cust["scheduled_time"]).total_seconds())
                if time_diff <= tolerance.total_seconds():
                    matched = cust
                    break

            if matched:
                new_customer_name = matched.get('customer_name', '')
                new_cancel_status = matched.get('status', '')
                new_result_status = matched.get('result_status', '')

                # 更新が必要かチェック
                needs_update = False
                if new_customer_name and new_customer_name != customer_name:
                    needs_update = True
                if new_cancel_status and new_cancel_status != cancel_status:
                    needs_update = True
                if new_result_status and new_result_status != result_status:
                    needs_update = True

                if needs_update:
                    # 更新実行
                    update_values = [
                        new_customer_name or customer_name,
                        new_cancel_status or cancel_status,
                        new_result_status or result_status
                    ]
                    zoom_worksheet.update(f'A{i}', [[update_values[0]]])
                    zoom_worksheet.update(f'E{i}:F{i}', [[update_values[1], update_values[2]]])
                    print(f"   → 行 {i} を更新: {customer_name} → {new_customer_name}")
                    print(f"      E列: {cancel_status} → {new_cancel_status}")
                    print(f"      F列: {result_status} → {new_result_status}")
                    updated_count += 1
                    time.sleep(0.5)  # API制限対策

        return updated_count

    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "Quota exceeded" in error_str:
            raise
        print(f"   再照合エラー: {e}")
        import traceback
        traceback.print_exc()
        return 0
