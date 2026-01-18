#!/usr/bin/env python3
"""
Loom動画の字幕（文字起こし）を抽出するスクリプト
- HTMLファイルからLoomのcaptions_source_urlを抽出
- VTTファイルをダウンロードしてテキストに変換
"""

import os
import re
import json
import ssl
import urllib.request
from pathlib import Path
from datetime import datetime

ssl._create_default_https_context = ssl._create_unverified_context

BASE_DIR = Path(__file__).parent.parent
NOTION_DOCS_DIR = BASE_DIR / "notion_docs"


def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}", flush=True)


def extract_loom_captions_url(html_content):
    """HTMLからLoomの字幕URLを抽出"""
    # captions_source_urlを探す
    match = re.search(r'"captions_source_url":"([^"]+)"', html_content)
    if match:
        url = match.group(1).replace('\\u0026', '&').replace('\\/', '/')
        return url
    return None


def extract_loom_transcript_url(html_content):
    """HTMLからLoomのtranscript URLを抽出"""
    match = re.search(r'"source_url":"([^"]+)"', html_content)
    if match:
        url = match.group(1).replace('\\u0026', '&').replace('\\/', '/')
        return url
    return None


def extract_video_info(html_content):
    """HTMLから動画情報を抽出"""
    title_match = re.search(r'"name":"([^"]+)"', html_content)
    duration_match = re.search(r'"duration":(\d+)', html_content)

    return {
        "title": title_match.group(1) if title_match else "Unknown",
        "duration_seconds": int(duration_match.group(1)) if duration_match else 0
    }


def fetch_loom_page(video_id):
    """Loomのページを直接取得して新鮮なURLを得る"""
    url = f"https://www.loom.com/share/{video_id}"
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)")
        req.add_header("Accept", "text/html,application/xhtml+xml")
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        log(f"  Loomページ取得失敗: {e}", "ERROR")
        return None


def download_vtt(url):
    """VTTファイルをダウンロード"""
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0")
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        log(f"  VTTダウンロード失敗: {e}", "ERROR")
        return None


def download_transcript_json(url):
    """Loom transcript JSONをダウンロード"""
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0")
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        log(f"  Transcriptダウンロード失敗: {e}", "ERROR")
        return None


def vtt_to_text(vtt_content):
    """VTT形式を読みやすいテキストに変換"""
    lines = vtt_content.split('\n')
    result = []
    current_time = None

    for line in lines:
        line = line.strip()
        # 空行やWEBVTTヘッダーをスキップ
        if not line or line == "WEBVTT" or line.startswith("NOTE"):
            continue
        # 番号行をスキップ
        if line.isdigit():
            continue
        # タイムスタンプ行
        if '-->' in line:
            # 開始時刻を抽出
            time_match = re.match(r'(\d+):(\d+):(\d+)', line)
            if time_match:
                hours = int(time_match.group(1))
                mins = int(time_match.group(2))
                secs = int(time_match.group(3))
                total_mins = hours * 60 + mins
                current_time = f"[{total_mins:02d}:{secs:02d}]"
            else:
                time_match = re.match(r'(\d+):(\d+)', line)
                if time_match:
                    mins = int(time_match.group(1))
                    secs = int(time_match.group(2))
                    current_time = f"[{mins:02d}:{secs:02d}]"
            continue
        # テキスト行（HTMLタグを除去）
        text = re.sub(r'<[^>]+>', '', line)
        if text and current_time:
            result.append(f"{current_time} {text}")
            current_time = None
        elif text:
            result.append(text)

    return '\n'.join(result)


def transcript_json_to_text(transcript_data):
    """Loom transcript JSONを読みやすいテキストに変換"""
    if not transcript_data:
        return None

    result = []

    # データ構造を確認
    if isinstance(transcript_data, dict):
        segments = transcript_data.get('segments', []) or transcript_data.get('results', [])
    elif isinstance(transcript_data, list):
        segments = transcript_data
    else:
        return None

    for segment in segments:
        if isinstance(segment, dict):
            start = segment.get('start', segment.get('start_time', 0))
            text = segment.get('text', segment.get('transcript', ''))

            if isinstance(start, (int, float)):
                mins = int(start) // 60
                secs = int(start) % 60
                result.append(f"[{mins:02d}:{secs:02d}] {text}")
            else:
                result.append(text)

    return '\n'.join(result) if result else None


def extract_loom_video_id(html_content):
    """HTMLからLoomの動画IDを抽出"""
    # s3_idやidフィールドから抽出
    match = re.search(r'"s3_id":"([a-z0-9]{32})"', html_content)
    if match:
        return match.group(1)
    match = re.search(r'loom\.com/share/([a-z0-9]{32})', html_content)
    if match:
        return match.group(1)
    return None


def process_loom_html_file(html_path):
    """LoomのHTMLファイルを処理して文字起こしを取得"""
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Loomページか確認
        if 'loom.com' not in html_content:
            return False

        # 動画IDを抽出
        video_id = extract_loom_video_id(html_content)
        if not video_id:
            log(f"  動画ID抽出失敗", "WARN")
            return False

        log(f"  Loom動画ID: {video_id}")

        # Loomから新鮮なページを取得
        fresh_html = fetch_loom_page(video_id)
        if fresh_html:
            html_content = fresh_html
            log(f"  新鮮なLoomページを取得")

        video_info = extract_video_info(html_content)
        log(f"  動画タイトル: {video_info['title']}")

        # 字幕URLを取得
        captions_url = extract_loom_captions_url(html_content)
        transcript_url = extract_loom_transcript_url(html_content)

        transcript_text = None

        # まずVTT（字幕）を試す
        if captions_url:
            log(f"  字幕URL取得成功")
            vtt_content = download_vtt(captions_url)
            if vtt_content:
                transcript_text = vtt_to_text(vtt_content)

        # VTTがなければtranscript JSONを試す
        if not transcript_text and transcript_url:
            log(f"  Transcript URL取得成功")
            transcript_data = download_transcript_json(transcript_url)
            if transcript_data:
                transcript_text = transcript_json_to_text(transcript_data)

        if transcript_text:
            # 保存先
            transcript_path = html_path.parent / f"{html_path.stem}_transcript.txt"

            header = f"""# Loom動画 文字起こし

**動画タイトル**: {video_info['title']}
**動画時間**: {video_info['duration_seconds'] // 60}分{video_info['duration_seconds'] % 60}秒
**元ファイル**: {html_path.name}
**抽出日時**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

"""
            with open(transcript_path, 'w', encoding='utf-8') as f:
                f.write(header + transcript_text)

            log(f"  保存完了: {transcript_path.name}")
            return True
        else:
            log(f"  字幕取得失敗", "WARN")
            return False

    except Exception as e:
        log(f"  処理エラー: {e}", "ERROR")
        return False


def main():
    print("=" * 60)
    print("Loom動画 字幕抽出スクリプト")
    print("=" * 60)

    # video_*.mp4ファイルを探す（実際にはHTMLファイル）
    video_files = list(NOTION_DOCS_DIR.rglob("video_*.mp4"))
    log(f"動画ファイル数: {len(video_files)}")

    processed = 0
    skipped = 0

    for video_path in video_files:
        # 既に文字起こしがあればスキップ
        transcript_path = video_path.parent / f"{video_path.stem}_transcript.txt"
        if transcript_path.exists():
            log(f"スキップ（既存）: {video_path.name}")
            skipped += 1
            continue

        log(f"処理中: {video_path.relative_to(NOTION_DOCS_DIR)}")

        # ファイルがHTMLか確認
        try:
            with open(video_path, 'rb') as f:
                first_bytes = f.read(100)

            if b'<!doctype html' in first_bytes.lower() or b'<html' in first_bytes.lower():
                if process_loom_html_file(video_path):
                    processed += 1
            else:
                log(f"  実際の動画ファイル - Gemini処理が必要", "INFO")
        except Exception as e:
            log(f"  ファイル読み込みエラー: {e}", "ERROR")

    print("=" * 60)
    print("処理完了")
    print(f"  処理済み: {processed}件")
    print(f"  スキップ: {skipped}件")
    print("=" * 60)


if __name__ == "__main__":
    main()
