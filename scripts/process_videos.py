#!/usr/bin/env python3
"""
動画文字起こしスクリプト (Feature B)
- notion_docs/ 内のMarkdownファイルから動画URL（mp4, mov, webm等）を抽出
- 動画をダウンロードして元ファイルと同じ場所に保存
- Gemini APIで文字起こし
- タイムスタンプ付きで元ファイルと同じ場所に保存
"""

import os
import re
import json
import hashlib
import time
import ssl
import urllib.request
from pathlib import Path
from urllib.parse import urlparse, unquote
from datetime import datetime

ssl._create_default_https_context = ssl._create_unverified_context

BASE_DIR = Path(__file__).parent.parent
NOTION_DOCS_DIR = BASE_DIR / "notion_docs"

VIDEO_EXTENSIONS = [".mp4", ".mov", ".webm", ".avi", ".mkv", ".m4v"]

stats = {
    "files_scanned": 0,
    "videos_found": 0,
    "videos_downloaded": 0,
    "transcripts_created": 0,
    "errors": []
}


def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}", flush=True)


def get_url_hash(url):
    return hashlib.md5(url.encode()).hexdigest()[:12]


def extract_video_urls_from_markdown(content):
    video_urls = []
    pattern1 = r"\[Video:\s*(https?://[^\]]+)\]"
    matches1 = re.findall(pattern1, content)
    video_urls.extend(matches1)
    pattern2 = r"(https?://[^\s\)\]]+\.(?:mp4|mov|webm|avi|mkv|m4v)[^\s\)\]]*)"
    matches2 = re.findall(pattern2, content, re.IGNORECASE)
    video_urls.extend(matches2)
    seen = set()
    unique_urls = []
    for url in video_urls:
        base_url = url.split("?")[0] if "?" in url else url
        if base_url not in seen:
            seen.add(base_url)
            unique_urls.append(url)
    return unique_urls


def download_video(url, save_dir):
    """動画をダウンロードして元ファイルと同じ場所に保存"""
    try:
        url_hash = get_url_hash(url)
        parsed = urlparse(url)
        decoded_path = unquote(parsed.path)
        ext = ".mp4"
        for video_ext in VIDEO_EXTENSIONS:
            if video_ext in decoded_path.lower():
                ext = video_ext
                break
        filename = f"video_{url_hash}{ext}"
        filepath = save_dir / filename
        if filepath.exists() and filepath.stat().st_size > 0:
            log(f"  既存: {filename}")
            return str(filepath), filename, False
        log(f"  ダウンロード中: {url[:80]}...")
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0")
        with urllib.request.urlopen(req, timeout=300) as response:
            with open(filepath, "wb") as f:
                f.write(response.read())
        log(f"  完了: {filename} ({filepath.stat().st_size / 1024 / 1024:.1f} MB)")
        return str(filepath), filename, True
    except Exception as e:
        stats["errors"].append(f"Download error: {e}")
        log(f"  ダウンロード失敗: {e}", "ERROR")
        return None, None, False


def transcribe_with_gemini(filepath, video_filename):
    """Gemini APIで文字起こし"""
    try:
        import google.generativeai as genai
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            log("  GEMINI_API_KEY未設定、スキップ", "WARN")
            return None
        genai.configure(api_key=api_key)
        log(f"  Geminiにアップロード中...")
        uploaded_file = genai.upload_file(filepath)
        while uploaded_file.state.name == "PROCESSING":
            time.sleep(2)
            uploaded_file = genai.get_file(uploaded_file.name)
        if uploaded_file.state.name == "FAILED":
            return None
        log(f"  文字起こし中...")
        model = genai.GenerativeModel("gemini-2.0-flash")
        prompt = """この動画の内容を文字起こししてください。
以下の形式でタイムスタンプ付きで出力してください：
[MM:SS] 発言内容
例：
[00:00] こんにちは、今日は...
[00:15] それでは始めましょう
日本語で出力してください。"""
        response = model.generate_content([prompt, uploaded_file])
        try:
            genai.delete_file(uploaded_file.name)
        except:
            pass
        return response.text
    except ImportError:
        log("  google-generativeai未インストール", "ERROR")
        return None
    except Exception as e:
        stats["errors"].append(f"Transcription error: {e}")
        return None


def save_transcript(transcript, video_filename, save_dir, source_md_file):
    """文字起こしを元ファイルと同じ場所に保存"""
    base_name = Path(video_filename).stem
    transcript_path = save_dir / f"{base_name}_transcript.txt"
    header = f"""# 動画文字起こし

**動画ファイル**: {video_filename}
**参照元**: {source_md_file}
**作成日時**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

"""
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(header + transcript)
    log(f"  文字起こし保存: {transcript_path.name}")
    return transcript_path


def process_markdown_file(md_path):
    """Markdownファイルを処理"""
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
        video_urls = extract_video_urls_from_markdown(content)
        if not video_urls:
            return 0

        # 元ファイルと同じディレクトリに保存
        save_dir = md_path.parent
        relative_path = md_path.relative_to(NOTION_DOCS_DIR)
        log(f"動画 {len(video_urls)}件: {relative_path}")

        processed = 0
        for url in video_urls:
            stats["videos_found"] += 1
            filepath, filename, is_new = download_video(url, save_dir)
            if filepath:
                if is_new:
                    stats["videos_downloaded"] += 1
                base_name = Path(filename).stem
                transcript_path = save_dir / f"{base_name}_transcript.txt"
                if transcript_path.exists():
                    log(f"  文字起こし既存: {base_name}_transcript.txt")
                else:
                    transcript = transcribe_with_gemini(filepath, filename)
                    if transcript:
                        save_transcript(transcript, filename, save_dir, str(relative_path))
                        stats["transcripts_created"] += 1
                processed += 1
        return processed
    except Exception as e:
        stats["errors"].append(f"Error processing {md_path}: {e}")
        return 0


def main():
    print("=" * 60)
    print("動画文字起こしスクリプト (Feature B)")
    print("=" * 60)
    log(f"スキャン: {NOTION_DOCS_DIR}")
    md_files = list(NOTION_DOCS_DIR.rglob("*.md"))
    log(f"Markdownファイル: {len(md_files)}件")
    for md_file in md_files:
        stats["files_scanned"] += 1
        process_markdown_file(md_file)
    print("=" * 60)
    print("処理完了")
    print(f"  スキャンファイル: {stats['files_scanned']}")
    print(f"  発見動画: {stats['videos_found']}")
    print(f"  ダウンロード: {stats['videos_downloaded']}")
    print(f"  文字起こし作成: {stats['transcripts_created']}")
    if stats["errors"]:
        print(f"  エラー: {len(stats['errors'])}")
    print("=" * 60)


if __name__ == "__main__":
    main()
