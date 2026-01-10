"""
Zoom API クライアント
録画データの取得を行う
"""

import os
import requests
import base64
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


def get_zoom_access_token(account_id: str, client_id: str, client_secret: str) -> str:
    """
    Zoom OAuth Server-to-Server でアクセストークンを取得
    """
    url = "https://zoom.us/oauth/token"

    # Basic認証ヘッダー
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "grant_type": "account_credentials",
        "account_id": account_id
    }

    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()

    return response.json()["access_token"]


def get_zoom_recordings_single_month(
    access_token: str,
    from_date: str,
    to_date: str
) -> list[dict]:
    """
    Zoom録画一覧を取得（1ヶ月分）

    Args:
        access_token: Zoomアクセストークン
        from_date: 開始日 (YYYY-MM-DD)
        to_date: 終了日 (YYYY-MM-DD)

    Returns:
        録画データのリスト
    """
    url = "https://api.zoom.us/v2/users/me/recordings"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    params = {
        "from": from_date,
        "to": to_date,
        "page_size": 300  # 最大300件/リクエスト
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    data = response.json()
    meetings = data.get("meetings", [])

    # 録画ファイル情報を整理
    recordings = []
    for meeting in meetings:
        recording_files = meeting.get("recording_files", [])

        # MP4とTRANSCRIPTを分離
        mp4_file = None
        transcript_file = None

        for file in recording_files:
            file_type = file.get("file_type", "")
            if file_type == "MP4":
                mp4_file = file
            elif file_type == "TRANSCRIPT":
                transcript_file = file

        recordings.append({
            "meeting_id": meeting.get("uuid"),
            "topic": meeting.get("topic"),
            "start_time": meeting.get("start_time"),
            "duration": meeting.get("duration"),
            "mp4_url": mp4_file.get("download_url") if mp4_file else None,
            "mp4_size": mp4_file.get("file_size") if mp4_file else None,
            "transcript_url": transcript_file.get("download_url") if transcript_file else None,
            "share_url": meeting.get("share_url"),  # 共有リンク（認証不要）
        })

    return recordings


def get_zoom_recordings(
    access_token: str,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    months: int = 6
) -> list[dict]:
    """
    Zoom録画一覧を取得（複数月対応）

    Zoom APIは1リクエストで最大1ヶ月分しか取得できないため、
    月ごとに分割してリクエストを行う。

    Args:
        access_token: Zoomアクセストークン
        from_date: 開始日 (YYYY-MM-DD) - 指定時はmonthsを無視
        to_date: 終了日 (YYYY-MM-DD)
        months: 取得する月数（デフォルト6ヶ月、最大6ヶ月）

    Returns:
        録画データのリスト
    """
    all_recordings = []

    # 日付が指定されている場合は従来通り（1ヶ月以内を想定）
    if from_date and to_date:
        return get_zoom_recordings_single_month(access_token, from_date, to_date)

    # デフォルト: 過去6ヶ月を月ごとに取得
    months = min(months, 6)  # 最大6ヶ月
    today = datetime.now()

    for i in range(months):
        # 各月の範囲を計算
        # 例: i=0 → 今月, i=1 → 先月, ...
        month_end = today - timedelta(days=30 * i)
        month_start = month_end - timedelta(days=30)

        from_str = month_start.strftime("%Y-%m-%d")
        to_str = month_end.strftime("%Y-%m-%d")

        try:
            month_recordings = get_zoom_recordings_single_month(
                access_token, from_str, to_str
            )
            all_recordings.extend(month_recordings)
        except Exception as e:
            # 1ヶ月分の取得に失敗しても続行
            print(f"   {from_str}〜{to_str} の取得エラー: {e}")
            continue

    # 重複を除去（meeting_idでユニーク化）
    seen_ids = set()
    unique_recordings = []
    for rec in all_recordings:
        if rec["meeting_id"] not in seen_ids:
            seen_ids.add(rec["meeting_id"])
            unique_recordings.append(rec)

    return unique_recordings


def download_file(url: str, access_token: str, save_path: str) -> str:
    """
    Zoomからファイルをダウンロード

    Args:
        url: ダウンロードURL
        access_token: Zoomアクセストークン
        save_path: 保存先パス

    Returns:
        保存したファイルパス
    """
    # アクセストークンをURLに付与
    download_url = f"{url}?access_token={access_token}"

    response = requests.get(download_url, stream=True)
    response.raise_for_status()

    with open(save_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    return save_path


def download_transcript(url: str, access_token: str) -> str:
    """
    文字起こしファイルをダウンロードしてテキストとして返す
    """
    download_url = f"{url}?access_token={access_token}"

    response = requests.get(download_url)
    response.raise_for_status()

    # VTT形式の場合、テキスト部分を抽出
    content = response.text

    # VTTのタイムスタンプを除去してテキストのみ抽出
    lines = content.split("\n")
    text_lines = []

    for line in lines:
        line = line.strip()
        # WEBVTTヘッダー、空行、タイムスタンプ行をスキップ
        if not line or line.startswith("WEBVTT") or "-->" in line or line.isdigit():
            continue
        text_lines.append(line)

    return "\n".join(text_lines)


def get_all_accounts_recordings(supabase_client) -> list[dict]:
    """
    全アカウントの録画を取得

    Args:
        supabase_client: Supabaseクライアント

    Returns:
        [{"assignee": "担当者名", "recordings": [...]}]
    """
    # zoom_accountsからアカウント情報を取得
    result = supabase_client.table("zoom_accounts").select("*").execute()
    accounts = result.data if result.data else []

    all_recordings = []

    for account in accounts:
        assignee = account["assignee"]
        account_id = account["account_id"]
        client_id = account["client_id"]
        client_secret = account["client_secret"]

        try:
            # アクセストークン取得
            access_token = get_zoom_access_token(account_id, client_id, client_secret)

            # 録画一覧取得
            recordings = get_zoom_recordings(access_token)

            all_recordings.append({
                "assignee": assignee,
                "access_token": access_token,
                "recordings": recordings
            })

        except Exception as e:
            print(f"Error fetching recordings for {assignee}: {e}")
            continue

    return all_recordings
