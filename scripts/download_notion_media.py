#!/usr/bin/env python3
"""
Notion API経由で動画・PDFをダウンロードするスクリプト
- Notion APIからブロックを再帰的に取得
- video, file, pdfタイプのブロックから署名付きURLを取得
- ダウンロードしてnotion_docs/の対応するフォルダに保存
- 動画はGeminiで文字起こし、PDFはテキスト抽出
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

NOTION_TOKEN = os.environ.get("NOTION_API_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

ROOT_PAGE_ID = "7f19ff35-7ffc-4c78-8c71-92cb99d5204a"

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
} if NOTION_TOKEN else {}

API_DELAY = 0.35

stats = {
    "pages_scanned": 0,
    "videos_found": 0,
    "videos_downloaded": 0,
    "transcripts_created": 0,
    "pdfs_found": 0,
    "pdfs_downloaded": 0,
    "pdfs_extracted": 0,
    "errors": []
}

# 処理済みブロックIDを追跡
processed_blocks = set()


def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}", flush=True)


def get_url_hash(url):
    return hashlib.md5(url.encode()).hexdigest()[:12]


def api_request(url, method='GET', data=None):
    """Notion API リクエスト"""
    req = urllib.request.Request(url, headers=HEADERS, method=method)
    if data:
        req.data = json.dumps(data).encode('utf-8')
    try:
        time.sleep(API_DELAY)
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        if e.code == 429:
            log("  Rate limited, waiting 30s...", "WARN")
            time.sleep(30)
            return api_request(url, method, data)
        return None
    except Exception as e:
        return None


def get_block_children(block_id):
    """ブロックの子要素を取得"""
    all_results = []
    has_more = True
    start_cursor = None
    while has_more:
        url = f"https://api.notion.com/v1/blocks/{block_id}/children?page_size=100"
        if start_cursor:
            url += f"&start_cursor={start_cursor}"
        data = api_request(url)
        if not data:
            break
        all_results.extend(data.get('results', []))
        has_more = data.get('has_more', False)
        start_cursor = data.get('next_cursor')
    return all_results


def download_file(url, save_dir, prefix):
    """ファイルをダウンロード"""
    try:
        url_hash = get_url_hash(url)
        parsed = urlparse(url)
        decoded_path = unquote(parsed.path)

        # 拡張子を取得
        ext = os.path.splitext(decoded_path)[1].split('?')[0]
        if not ext or len(ext) > 10:
            if 'video' in prefix:
                ext = '.mp4'
            elif 'pdf' in prefix:
                ext = '.pdf'
            else:
                ext = '.bin'

        filename = f"{prefix}_{url_hash}{ext}"
        filepath = save_dir / filename

        if filepath.exists() and filepath.stat().st_size > 1000:
            log(f"    既存: {filename}")
            return str(filepath), filename, False

        log(f"    ダウンロード中...")
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0")

        with urllib.request.urlopen(req, timeout=300) as response:
            content = response.read()

            # HTMLでないか確認
            if content[:15].startswith(b'<!DOCTYPE html>') or content[:6].startswith(b'<html>'):
                log(f"    スキップ（HTMLページ）", "WARN")
                return None, None, False

            save_dir.mkdir(parents=True, exist_ok=True)
            with open(filepath, "wb") as f:
                f.write(content)

        size_mb = filepath.stat().st_size / 1024 / 1024
        log(f"    完了: {filename} ({size_mb:.2f}MB)")
        return str(filepath), filename, True
    except Exception as e:
        log(f"    ダウンロード失敗: {e}", "ERROR")
        stats["errors"].append(str(e))
        return None, None, False


def transcribe_video(filepath):
    """動画をGemini APIで文字起こし"""
    if not GEMINI_API_KEY:
        log("    GEMINI_API_KEY未設定", "WARN")
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)

        log(f"    Geminiにアップロード中...")
        uploaded_file = genai.upload_file(filepath)

        while uploaded_file.state.name == "PROCESSING":
            time.sleep(2)
            uploaded_file = genai.get_file(uploaded_file.name)

        if uploaded_file.state.name == "FAILED":
            log("    アップロード失敗", "ERROR")
            return None

        log(f"    文字起こし中...")
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
    except Exception as e:
        log(f"    文字起こし失敗: {e}", "ERROR")
        return None


def extract_pdf_text(filepath):
    """PDFからテキスト抽出"""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(filepath)
        text = ""
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text += f"\n--- Page {i+1} ---\n"
                text += page_text
        return text.strip() if text.strip() else None
    except Exception as e:
        log(f"    PDF抽出失敗: {e}", "ERROR")
        return None


def get_page_title(page_id):
    """ページタイトルを取得"""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    data = api_request(url)
    if data:
        props = data.get('properties', {})
        title_prop = props.get('title') or props.get('Name') or props.get('名前')
        if title_prop:
            title_items = title_prop.get('title', [])
            if title_items:
                return title_items[0].get('plain_text', 'Untitled')
    return 'Untitled'


def sanitize_filename(name):
    """ファイル名として使える形式に変換"""
    # 特殊文字を置換
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = name.strip()
    return name[:100] if len(name) > 100 else name


def process_block(block, save_dir, page_path):
    """ブロックを処理して動画/PDFをダウンロード"""
    block_id = block.get('id')
    if block_id in processed_blocks:
        return
    processed_blocks.add(block_id)

    block_type = block.get('type')

    # 動画ブロック
    if block_type == 'video':
        video_data = block.get('video', {})
        file_type = video_data.get('type')

        if file_type == 'file':
            url = video_data.get('file', {}).get('url')
        elif file_type == 'external':
            url = video_data.get('external', {}).get('url')
        else:
            url = None

        if url:
            stats["videos_found"] += 1
            log(f"  動画発見: {page_path}")
            filepath, filename, is_new = download_file(url, save_dir, "video")

            if filepath and is_new:
                stats["videos_downloaded"] += 1

                # 文字起こし
                transcript_path = save_dir / f"{Path(filename).stem}_transcript.txt"
                if not transcript_path.exists():
                    transcript = transcribe_video(filepath)
                    if transcript:
                        header = f"""# 動画文字起こし

**動画ファイル**: {filename}
**参照元**: {page_path}
**作成日時**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

"""
                        with open(transcript_path, "w", encoding="utf-8") as f:
                            f.write(header + transcript)
                        stats["transcripts_created"] += 1
                        log(f"    文字起こし保存: {transcript_path.name}")

    # ファイルブロック
    elif block_type == 'file':
        file_data = block.get('file', {})
        file_type = file_data.get('type')

        if file_type == 'file':
            url = file_data.get('file', {}).get('url')
        elif file_type == 'external':
            url = file_data.get('external', {}).get('url')
        else:
            url = None

        if url and '.pdf' in url.lower():
            stats["pdfs_found"] += 1
            log(f"  PDF発見: {page_path}")
            filepath, filename, is_new = download_file(url, save_dir, "pdf")

            if filepath and is_new:
                stats["pdfs_downloaded"] += 1
                process_pdf(filepath, filename, save_dir, page_path)

    # PDFブロック
    elif block_type == 'pdf':
        pdf_data = block.get('pdf', {})
        file_type = pdf_data.get('type')

        if file_type == 'file':
            url = pdf_data.get('file', {}).get('url')
        elif file_type == 'external':
            url = pdf_data.get('external', {}).get('url')
        else:
            url = None

        if url:
            stats["pdfs_found"] += 1
            log(f"  PDF発見: {page_path}")
            filepath, filename, is_new = download_file(url, save_dir, "pdf")

            if filepath and is_new:
                stats["pdfs_downloaded"] += 1
                process_pdf(filepath, filename, save_dir, page_path)


def process_pdf(filepath, filename, save_dir, page_path):
    """PDFを処理してテキスト抽出"""
    text_path = save_dir / f"{Path(filename).stem}_text.txt"
    if not text_path.exists():
        text = extract_pdf_text(filepath)
        if text:
            header = f"""# PDF抽出テキスト

**PDFファイル**: {filename}
**参照元**: {page_path}
**抽出日時**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

"""
            with open(text_path, "w", encoding="utf-8") as f:
                f.write(header + text)
            stats["pdfs_extracted"] += 1
            log(f"    テキスト保存: {text_path.name}")


def process_page_recursive(page_id, path_parts, depth=0):
    """ページを再帰的に処理"""
    if depth > 10:  # 深さ制限
        return

    stats["pages_scanned"] += 1

    # 現在のパスに対応するディレクトリ
    if path_parts:
        save_dir = NOTION_DOCS_DIR / "/".join([sanitize_filename(p) for p in path_parts])
    else:
        save_dir = NOTION_DOCS_DIR

    page_path = "/".join(path_parts) if path_parts else "root"
    log(f"[{stats['pages_scanned']}] {page_path}")

    # ブロックを取得
    blocks = get_block_children(page_id)

    for block in blocks:
        block_type = block.get('type')

        # 動画/PDFブロックを処理
        process_block(block, save_dir, page_path)

        # 子ページを再帰処理
        if block_type == 'child_page':
            child_title = block.get('child_page', {}).get('title', 'Untitled')
            new_path = path_parts + [child_title]
            process_page_recursive(block['id'], new_path, depth + 1)

        # 子データベースも処理
        elif block_type == 'child_database':
            db_title = block.get('child_database', {}).get('title', 'Database')
            new_path = path_parts + [db_title]
            # データベース内のページも処理可能（省略）

        # 子ブロックがある場合は再帰
        elif block.get('has_children'):
            child_blocks = get_block_children(block['id'])
            for child_block in child_blocks:
                process_block(child_block, save_dir, page_path)


def main():
    print("=" * 60)
    print("Notion API経由 動画/PDFダウンロードスクリプト")
    print("=" * 60)

    if not NOTION_TOKEN:
        log("NOTION_API_TOKEN未設定", "ERROR")
        log("export NOTION_API_TOKEN=xxx を実行してください")
        return

    log(f"ルートページID: {ROOT_PAGE_ID}")
    log(f"出力先: {NOTION_DOCS_DIR}")

    # ルートページから再帰的に処理
    process_page_recursive(ROOT_PAGE_ID, [])

    print("=" * 60)
    print("処理完了")
    print(f"  スキャンページ: {stats['pages_scanned']}")
    print(f"  発見動画: {stats['videos_found']}")
    print(f"  ダウンロード動画: {stats['videos_downloaded']}")
    print(f"  文字起こし: {stats['transcripts_created']}")
    print(f"  発見PDF: {stats['pdfs_found']}")
    print(f"  ダウンロードPDF: {stats['pdfs_downloaded']}")
    print(f"  PDF抽出: {stats['pdfs_extracted']}")
    if stats["errors"]:
        print(f"  エラー: {len(stats['errors'])}")
    print("=" * 60)


if __name__ == "__main__":
    main()
