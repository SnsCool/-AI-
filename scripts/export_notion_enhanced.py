#!/usr/bin/env python3
"""
Notion完全エクスポート - 拡張版
- テーブル（シンプルテーブル）の中身を取得
- リンク先のWebページをスクレイピング
- 動画・音声ファイルをダウンロード + 文字起こし
- PDFをダウンロード + テキスト抽出
"""

import urllib.request
import json
import os
import sys
import re
import time
import hashlib
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, urlparse, urljoin
from html.parser import HTMLParser
import ssl

# SSL証明書検証を無効化（一部サイト対応）
ssl._create_default_https_context = ssl._create_unverified_context

# 設定
TOKEN = os.environ.get('NOTION_API_TOKEN')
ROOT_PAGE_ID = "7f19ff35-7ffc-4c78-8c71-92cb99d5204a"
BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / 'notion_docs'
MEDIA_DIR = BASE_DIR / 'notion_media'
IMAGES_DIR = BASE_DIR / 'notion_images'
TRANSCRIPTS_DIR = BASE_DIR / 'notion_transcripts'

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
} if TOKEN else {}

# API呼び出し間隔
API_DELAY = 0.35

# 統計
stats = {
    'pages': 0,
    'databases': 0,
    'records': 0,
    'images': 0,
    'tables': 0,
    'links_scraped': 0,
    'media_downloaded': 0,
    'transcripts': 0,
    'pdfs': 0,
    'errors': []
}

# HTMLからテキスト抽出用
class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.skip_tags = {'script', 'style', 'nav', 'header', 'footer', 'aside'}
        self.current_tag = None

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag

    def handle_endtag(self, tag):
        if tag in ['p', 'div', 'br', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            self.text.append('\n')
        self.current_tag = None

    def handle_data(self, data):
        if self.current_tag not in self.skip_tags:
            text = data.strip()
            if text:
                self.text.append(text + ' ')

    def get_text(self):
        return ''.join(self.text).strip()

def api_request(url, method='GET', data=None):
    """API リクエストを実行"""
    req = urllib.request.Request(url, headers=HEADERS, method=method)
    if data:
        req.data = json.dumps(data).encode('utf-8')
    try:
        time.sleep(API_DELAY)
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        if e.code == 429:
            print("  Rate limited, waiting 30s...")
            time.sleep(30)
            return api_request(url, method, data)
        stats['errors'].append(f"HTTP {e.code}: {url}")
        return None
    except Exception as e:
        stats['errors'].append(f"Error: {e}")
        return None

def get_block_children(block_id):
    """ブロックの子要素をすべて取得"""
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

def download_file(url, save_dir, prefix=""):
    """ファイルをダウンロード"""
    try:
        url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
        parsed = urlparse(url)
        path = parsed.path
        # URLエンコードされたファイル名をデコード
        from urllib.parse import unquote
        decoded_path = unquote(path)
        ext = os.path.splitext(decoded_path)[1] or '.bin'
        # 拡張子をクリーンアップ
        ext = ext.split('?')[0]
        filename = f"{prefix}{url_hash}{ext}"
        filepath = save_dir / filename

        if filepath.exists():
            return str(filepath), filename

        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0')

        with urllib.request.urlopen(req, timeout=120) as response:
            with open(filepath, 'wb') as f:
                f.write(response.read())

        return str(filepath), filename
    except Exception as e:
        stats['errors'].append(f"Download error: {e}")
        return None, None

def scrape_webpage(url):
    """Webページをスクレイピングしてテキスト抽出"""
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)')

        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8', errors='ignore')

        # HTMLからテキスト抽出
        extractor = HTMLTextExtractor()
        extractor.feed(html)
        text = extractor.get_text()

        # 長すぎる場合は切り詰め
        if len(text) > 5000:
            text = text[:5000] + "\n\n[... 以下省略 ...]"

        stats['links_scraped'] += 1
        return text
    except Exception as e:
        return f"[スクレイピング失敗: {e}]"

def transcribe_audio(filepath):
    """音声ファイルを文字起こし（Gemini 2.0 Flash優先）"""
    # Gemini APIを優先使用
    return transcribe_with_gemini(filepath)

def transcribe_with_gemini(filepath):
    """Gemini 2.0 Flashで文字起こし（タイムスタンプ付き）"""
    try:
        import google.generativeai as genai

        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return "[文字起こしスキップ: GEMINI_API_KEY未設定]"

        genai.configure(api_key=api_key)

        # ファイルをアップロード
        print(f"      📤 Geminiにファイルをアップロード中...")
        uploaded_file = genai.upload_file(filepath)

        # アップロード完了を待つ
        import time
        while uploaded_file.state.name == "PROCESSING":
            time.sleep(2)
            uploaded_file = genai.get_file(uploaded_file.name)

        if uploaded_file.state.name == "FAILED":
            return f"[文字起こし失敗: ファイルアップロード失敗]"

        # Gemini 2.0 Flashで文字起こし
        model = genai.GenerativeModel('gemini-2.0-flash')

        prompt = """この音声/動画ファイルの内容を文字起こししてください。
以下の形式でタイムスタンプ付きで出力してください：

[MM:SS] 発言内容

例：
[00:00] こんにちは、今日は...
[00:15] それでは始めましょう

日本語で出力してください。"""

        response = model.generate_content([prompt, uploaded_file])

        # アップロードしたファイルを削除
        try:
            genai.delete_file(uploaded_file.name)
        except:
            pass

        stats['transcripts'] += 1
        return response.text

    except Exception as e:
        return f"[文字起こし失敗: {e}]"

def transcribe_with_openai(filepath):
    """OpenAI Whisper APIで文字起こし（フォールバック）"""
    try:
        import openai

        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            # Geminiを試す
            return transcribe_with_gemini(filepath)

        client = openai.OpenAI(api_key=api_key)

        with open(filepath, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="ja",
                response_format="text"
            )

        stats['transcripts'] += 1
        return transcript
    except Exception as e:
        return f"[文字起こし失敗: {e}]"

def extract_pdf_text(filepath):
    """PDFからテキスト抽出"""
    try:
        # PyPDF2を試す
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(filepath)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            if text.strip():
                stats['pdfs'] += 1
                return text
        except ImportError:
            pass

        # pdfplumberを試す
        try:
            import pdfplumber
            with pdfplumber.open(filepath) as pdf:
                text = ""
                for page in pdf.pages:
                    text += (page.extract_text() or "") + "\n"
            if text.strip():
                stats['pdfs'] += 1
                return text
        except ImportError:
            pass

        return "[PDFテキスト抽出: ライブラリ未インストール (pip install PyPDF2)]"

    except Exception as e:
        return f"[PDFテキスト抽出失敗: {e}]"

def table_to_markdown(block_id):
    """テーブルブロックをMarkdownに変換"""
    try:
        rows = get_block_children(block_id)
        if not rows:
            return "[テーブル: データなし]\n"

        md_lines = []
        for i, row in enumerate(rows):
            if row.get('type') != 'table_row':
                continue
            cells = row.get('table_row', {}).get('cells', [])
            row_text = []
            for cell in cells:
                cell_text = ''.join([t.get('plain_text', '') for t in cell])
                cell_text = cell_text.replace('|', '\\|').replace('\n', ' ')
                row_text.append(cell_text)
            md_lines.append("| " + " | ".join(row_text) + " |")

            # ヘッダー行の後にセパレータ
            if i == 0:
                md_lines.append("|" + "---|" * len(row_text))

        stats['tables'] += 1
        return "\n".join(md_lines) + "\n"
    except Exception as e:
        return f"[テーブル取得失敗: {e}]\n"

def rich_text_to_markdown(rich_text_array):
    """Notion rich_text を Markdown に変換"""
    if not rich_text_array:
        return ""
    result = []
    for rt in rich_text_array:
        text = rt.get('plain_text', '')
        annotations = rt.get('annotations', {})
        if annotations.get('bold'):
            text = f"**{text}**"
        if annotations.get('italic'):
            text = f"*{text}*"
        if annotations.get('strikethrough'):
            text = f"~~{text}~~"
        if annotations.get('code'):
            text = f"`{text}`"
        href = rt.get('href')
        if href:
            text = f"[{text}]({href})"
        result.append(text)
    return ''.join(result)

def get_database_info(database_id):
    """データベースの情報を取得"""
    url = f"https://api.notion.com/v1/databases/{database_id}"
    return api_request(url)

def query_database(database_id):
    """データベースの全レコードを取得"""
    all_results = []
    has_more = True
    start_cursor = None
    while has_more:
        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        data = {"page_size": 100}
        if start_cursor:
            data["start_cursor"] = start_cursor
        result = api_request(url, method='POST', data=data)
        if not result:
            break
        all_results.extend(result.get('results', []))
        has_more = result.get('has_more', False)
        start_cursor = result.get('next_cursor')
    return all_results

def property_value_to_string(prop):
    """Notionプロパティ値を文字列に変換"""
    prop_type = prop.get('type', '')
    if prop_type == 'title':
        return rich_text_to_markdown(prop.get('title', []))
    elif prop_type == 'rich_text':
        return rich_text_to_markdown(prop.get('rich_text', []))
    elif prop_type == 'number':
        val = prop.get('number')
        return str(val) if val is not None else ''
    elif prop_type == 'select':
        select = prop.get('select')
        return select.get('name', '') if select else ''
    elif prop_type == 'multi_select':
        return ', '.join([s.get('name', '') for s in prop.get('multi_select', [])])
    elif prop_type == 'date':
        date = prop.get('date')
        if date:
            start = date.get('start', '')
            end = date.get('end', '')
            return f"{start} → {end}" if end else start
        return ''
    elif prop_type == 'people':
        return ', '.join([p.get('name', '') for p in prop.get('people', [])])
    elif prop_type == 'files':
        files = prop.get('files', [])
        return ', '.join([f.get('name', '') or f.get('file', {}).get('url', '') for f in files])
    elif prop_type == 'checkbox':
        return '✓' if prop.get('checkbox') else '✗'
    elif prop_type == 'url':
        return prop.get('url', '') or ''
    elif prop_type == 'email':
        return prop.get('email', '') or ''
    elif prop_type == 'phone_number':
        return prop.get('phone_number', '') or ''
    elif prop_type == 'status':
        status = prop.get('status')
        return status.get('name', '') if status else ''
    elif not prop_type:
        return ''
    else:
        return f"[{prop_type}]"

def database_to_markdown(database_id, title):
    """データベースの全情報をMarkdownに変換"""
    md_parts = [f"\n### データベース: {title}\n\n"]
    db_info = get_database_info(database_id)
    if not db_info:
        return f"\n### データベース: {title}\n\n(データベース情報を取得できませんでした)\n"

    properties = db_info.get('properties', {})
    if properties:
        md_parts.append("#### プロパティ（カラム）\n\n")
        md_parts.append("| プロパティ名 | タイプ |\n")
        md_parts.append("|------------|--------|\n")
        for prop_name, prop_info in properties.items():
            prop_type = prop_info.get('type', 'unknown')
            md_parts.append(f"| {prop_name} | {prop_type} |\n")
        md_parts.append("\n")

    records = query_database(database_id)
    stats['records'] += len(records)

    if not records:
        md_parts.append("(レコードなし)\n")
        return ''.join(md_parts)

    md_parts.append(f"#### レコード（{len(records)}件）\n\n")

    prop_names = list(properties.keys())
    title_prop = None
    for name, info in properties.items():
        if info.get('type') == 'title':
            title_prop = name
            break
    if title_prop:
        prop_names.remove(title_prop)
        prop_names.insert(0, title_prop)

    md_parts.append("| " + " | ".join(prop_names[:8]) + " |\n")
    md_parts.append("|" + "---|" * min(len(prop_names), 8) + "\n")

    for record in records[:100]:
        record_props = record.get('properties', {})
        row = []
        for prop_name in prop_names[:8]:
            prop = record_props.get(prop_name, {})
            value = property_value_to_string(prop)
            if value is None:
                value = ''
            value = str(value).replace('|', '\\|').replace('\n', ' ')[:50]
            row.append(value)
        md_parts.append("| " + " | ".join(row) + " |\n")

    if len(records) > 100:
        md_parts.append(f"\n*（他 {len(records) - 100} 件のレコード）*\n")

    return ''.join(md_parts)

def block_to_markdown(block, indent_level=0):
    """Notionブロックを Markdown に変換（拡張版）"""
    block_type = block.get('type', '')
    block_id = block.get('id', '')
    indent = "  " * indent_level

    if block_type == 'paragraph':
        text = rich_text_to_markdown(block.get('paragraph', {}).get('rich_text', []))
        return f"{indent}{text}\n" if text else "\n"

    elif block_type == 'heading_1':
        text = rich_text_to_markdown(block.get('heading_1', {}).get('rich_text', []))
        return f"{indent}# {text}\n"

    elif block_type == 'heading_2':
        text = rich_text_to_markdown(block.get('heading_2', {}).get('rich_text', []))
        return f"{indent}## {text}\n"

    elif block_type == 'heading_3':
        text = rich_text_to_markdown(block.get('heading_3', {}).get('rich_text', []))
        return f"{indent}### {text}\n"

    elif block_type == 'bulleted_list_item':
        text = rich_text_to_markdown(block.get('bulleted_list_item', {}).get('rich_text', []))
        return f"{indent}- {text}\n"

    elif block_type == 'numbered_list_item':
        text = rich_text_to_markdown(block.get('numbered_list_item', {}).get('rich_text', []))
        return f"{indent}1. {text}\n"

    elif block_type == 'to_do':
        todo = block.get('to_do', {})
        text = rich_text_to_markdown(todo.get('rich_text', []))
        checked = "x" if todo.get('checked') else " "
        return f"{indent}- [{checked}] {text}\n"

    elif block_type == 'toggle':
        text = rich_text_to_markdown(block.get('toggle', {}).get('rich_text', []))
        return f"{indent}<details>\n{indent}<summary>{text}</summary>\n"

    elif block_type == 'code':
        code = block.get('code', {})
        text = rich_text_to_markdown(code.get('rich_text', []))
        lang = code.get('language', '')
        return f"{indent}```{lang}\n{text}\n{indent}```\n"

    elif block_type == 'quote':
        text = rich_text_to_markdown(block.get('quote', {}).get('rich_text', []))
        return f"{indent}> {text}\n"

    elif block_type == 'callout':
        callout = block.get('callout', {})
        text = rich_text_to_markdown(callout.get('rich_text', []))
        icon_data = callout.get('icon') or {}
        icon = icon_data.get('emoji', '💡') if isinstance(icon_data, dict) else '💡'
        return f"{indent}> {icon} {text}\n"

    elif block_type == 'divider':
        return f"{indent}---\n"

    elif block_type == 'table':
        # テーブルの中身を取得
        return f"{indent}{table_to_markdown(block_id)}\n"

    elif block_type == 'image':
        image = block.get('image', {})
        url = image.get('file', {}).get('url') or image.get('external', {}).get('url', '')
        caption = rich_text_to_markdown(image.get('caption', []))
        if url and 'amazonaws.com' in url:
            filepath, filename = download_file(url, IMAGES_DIR, "img_")
            if filepath:
                stats['images'] += 1
                url = f"../../../notion_images/{filename}"
        return f"{indent}![{caption}]({url})\n"

    elif block_type == 'bookmark':
        url = block.get('bookmark', {}).get('url', '')
        # リンク先をスクレイピング
        content = ""
        if url and not any(x in url for x in ['youtube.com', 'youtu.be', 'twitter.com', 'x.com']):
            print(f"    🔗 スクレイピング: {url[:50]}...")
            scraped = scrape_webpage(url)
            if scraped and not scraped.startswith('['):
                content = f"\n\n<details>\n<summary>リンク先の内容</summary>\n\n{scraped}\n\n</details>\n"
        return f"{indent}[Bookmark: {url}]({url}){content}\n"

    elif block_type == 'link_preview':
        url = block.get('link_preview', {}).get('url', '')
        return f"{indent}[Link: {url}]({url})\n"

    elif block_type == 'child_page':
        title = block.get('child_page', {}).get('title', 'Untitled')
        return f"{indent}📄 **{title}** (子ページ)\n"

    elif block_type == 'child_database':
        title = block.get('child_database', {}).get('title', 'Untitled')
        db_content = database_to_markdown(block_id, title)
        return f"{indent}📊 **{title}** (データベース)\n{db_content}\n"

    elif block_type == 'embed':
        url = block.get('embed', {}).get('url', '')
        return f"{indent}[Embed: {url}]({url})\n"

    elif block_type == 'video':
        video = block.get('video', {})
        url = video.get('file', {}).get('url') or video.get('external', {}).get('url', '')

        result = f"{indent}[Video: {url}]({url})\n"

        # 動画をダウンロード + 文字起こし
        if url and 'amazonaws.com' in url:
            print(f"    🎬 動画ダウンロード中...")
            filepath, filename = download_file(url, MEDIA_DIR, "video_")
            if filepath:
                stats['media_downloaded'] += 1
                result = f"{indent}[Video: notion_media/{filename}](../../../notion_media/{filename})\n"

                # 文字起こし
                print(f"    📝 文字起こし中...")
                transcript = transcribe_audio(filepath)
                if transcript and not transcript.startswith('['):
                    result += f"\n<details>\n<summary>📝 文字起こし</summary>\n\n{transcript}\n\n</details>\n"

        return result

    elif block_type == 'audio':
        audio = block.get('audio', {})
        url = audio.get('file', {}).get('url') or audio.get('external', {}).get('url', '')

        result = f"{indent}[Audio: {url}]({url})\n"

        if url and 'amazonaws.com' in url:
            print(f"    🎵 音声ダウンロード中...")
            filepath, filename = download_file(url, MEDIA_DIR, "audio_")
            if filepath:
                stats['media_downloaded'] += 1
                result = f"{indent}[Audio: notion_media/{filename}](../../../notion_media/{filename})\n"

                print(f"    📝 文字起こし中...")
                transcript = transcribe_audio(filepath)
                if transcript and not transcript.startswith('['):
                    result += f"\n<details>\n<summary>📝 文字起こし</summary>\n\n{transcript}\n\n</details>\n"

        return result

    elif block_type == 'pdf':
        pdf = block.get('pdf', {})
        url = pdf.get('file', {}).get('url') or pdf.get('external', {}).get('url', '')

        result = f"{indent}[PDF: {url}]({url})\n"

        if url and 'amazonaws.com' in url:
            print(f"    📄 PDFダウンロード中...")
            filepath, filename = download_file(url, MEDIA_DIR, "pdf_")
            if filepath:
                stats['media_downloaded'] += 1
                result = f"{indent}[PDF: notion_media/{filename}](../../../notion_media/{filename})\n"

                print(f"    📝 テキスト抽出中...")
                text = extract_pdf_text(filepath)
                if text and not text.startswith('['):
                    result += f"\n<details>\n<summary>📝 PDFテキスト</summary>\n\n{text[:3000]}\n\n</details>\n"

        return result

    elif block_type == 'file':
        file_data = block.get('file', {})
        url = file_data.get('file', {}).get('url') or file_data.get('external', {}).get('url', '')

        if url and 'amazonaws.com' in url:
            print(f"    📁 ファイルダウンロード中...")
            filepath, filename = download_file(url, MEDIA_DIR, "file_")
            if filepath:
                stats['media_downloaded'] += 1
                return f"{indent}[File: notion_media/{filename}](../../../notion_media/{filename})\n"

        return f"{indent}[File: {url}]({url})\n"

    elif block_type in ['column_list', 'column', 'synced_block']:
        return ""

    else:
        return ""

def fetch_page_content(page_id, max_depth=5, current_depth=0):
    """ページの全コンテンツを取得してMarkdownに変換"""
    if current_depth > max_depth:
        return ""
    blocks = get_block_children(page_id)
    markdown_parts = []
    for block in blocks:
        md = block_to_markdown(block)
        if md:
            markdown_parts.append(md)
        if block.get('has_children', False):
            block_type = block.get('type', '')
            if block_type not in ['child_page', 'child_database']:
                child_content = fetch_page_content(block['id'], max_depth, current_depth + 1)
                if child_content:
                    markdown_parts.append(child_content)
    return ''.join(markdown_parts)

def sanitize_filename(name):
    """ファイル名として安全な文字列に変換"""
    unsafe_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '\n', '\r']
    result = name
    for char in unsafe_chars:
        result = result.replace(char, '_')
    result = result.strip('. ')
    if len(result) > 100:
        result = result[:100]
    return result or 'unnamed'

def fetch_hierarchy_with_content(page_id, depth=0, max_depth=7, visited=None, parent_path=""):
    """階層構造とコンテンツを再帰的に取得"""
    if visited is None:
        visited = set()
    if depth > max_depth or page_id in visited:
        return []
    visited.add(page_id)
    blocks = get_block_children(page_id)
    results = []

    for block in blocks:
        block_type = block.get('type', '')
        block_id = block['id']
        has_children = block.get('has_children', False)
        node = None

        if block_type == 'child_page':
            title = block.get('child_page', {}).get('title', 'Untitled')
            print(f"{'  ' * depth}📄 {title}", flush=True)
            stats['pages'] += 1
            content = fetch_page_content(block_id)
            node = {
                'id': block_id,
                'name': title.strip(),
                'type': 'page',
                'depth': depth,
                'content': content,
                'path': f"{parent_path}/{sanitize_filename(title)}" if parent_path else sanitize_filename(title),
                'children': []
            }
            if has_children:
                child_path = node['path']
                children = fetch_hierarchy_with_content(block_id, depth + 1, max_depth, visited.copy(), child_path)
                node['children'] = children

        elif block_type == 'child_database':
            title = block.get('child_database', {}).get('title', 'Untitled')
            print(f"{'  ' * depth}📊 {title}", flush=True)
            stats['databases'] += 1
            db_content = database_to_markdown(block_id, title)
            node = {
                'id': block_id,
                'name': title.strip(),
                'type': 'database',
                'depth': depth,
                'content': db_content,
                'path': f"{parent_path}/{sanitize_filename(title)}" if parent_path else sanitize_filename(title),
                'children': []
            }

        elif block_type in ['column_list', 'column', 'toggle', 'synced_block', 'callout'] and has_children:
            children = fetch_hierarchy_with_content(block_id, depth, max_depth, visited.copy(), parent_path)
            results.extend(children)
            continue

        if node:
            results.append(node)
    return results

def generate_index_md(node, all_descendants=None):
    """ノードのindex.mdを生成"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    md = f"""# {node['name']}

**種類**: {'📄 ページ' if node['type'] == 'page' else '📊 データベース'}
**階層**: {node['depth'] + 1}
**更新日時**: {now}

---

## コンテンツ

{node.get('content', '(コンテンツなし)')}

---

## 子要素一覧

"""
    if node['children']:
        for child in node['children']:
            icon = '📊' if child['type'] == 'database' else '📄'
            md += f"- {icon} [{child['name']}](./{sanitize_filename(child['name'])}/index.md)\n"
    else:
        md += "(子要素なし)\n"

    if all_descendants:
        md += f"""
---

## 全子孫構造

このセクション配下の全ページ/データベース（{len(all_descendants)}件）:

"""
        for desc in all_descendants:
            indent = "  " * desc['depth']
            icon = '📊' if desc['type'] == 'database' else '📄'
            md += f"{indent}- {icon} {desc['name']}\n"
    md += f"\n---\n*Generated: {now}*\n"
    return md

def get_all_descendants(node):
    """ノードの全子孫をフラットなリストで取得"""
    descendants = []
    for child in node.get('children', []):
        descendants.append({
            'name': child['name'],
            'type': child['type'],
            'depth': child['depth'] - node['depth']
        })
        descendants.extend([
            {**d, 'depth': d['depth'] + 1}
            for d in get_all_descendants(child)
        ])
    return descendants

def create_folder_structure(nodes, base_path):
    """フォルダ構造を作成"""
    for node in nodes:
        folder_path = base_path / sanitize_filename(node['name'])
        folder_path.mkdir(parents=True, exist_ok=True)
        descendants = get_all_descendants(node)
        index_content = generate_index_md(node, descendants)
        index_file = folder_path / 'index.md'
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(index_content)
        if node['children']:
            create_folder_structure(node['children'], folder_path)

def main():
    print("=" * 60, flush=True)
    print("Notion完全エクスポート - 拡張版", flush=True)
    print("テーブル・リンク・動画・音声・PDF対応", flush=True)
    print("=" * 60, flush=True)
    print(flush=True)

    if not TOKEN:
        print("❌ NOTION_API_TOKEN が設定されていません")
        sys.exit(1)

    # 出力ディレクトリを準備
    if OUTPUT_DIR.exists():
        print(f"📁 既存のフォルダを削除: {OUTPUT_DIR}", flush=True)
        import shutil
        shutil.rmtree(OUTPUT_DIR)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"📁 出力先: {OUTPUT_DIR}", flush=True)
    print(f"📁 メディア保存先: {MEDIA_DIR}", flush=True)
    print(f"📁 画像保存先: {IMAGES_DIR}", flush=True)
    print(flush=True)

    print("🌐 Notionからデータを取得中...", flush=True)
    print("   (テーブル・リンク・動画も処理するため時間がかかります)", flush=True)
    print(flush=True)

    hierarchy = fetch_hierarchy_with_content(ROOT_PAGE_ID)

    print()
    print(f"✅ 取得完了!")
    print(f"   - ページ: {stats['pages']} 件")
    print(f"   - データベース: {stats['databases']} 件")
    print(f"   - レコード: {stats['records']} 件")
    print(f"   - テーブル: {stats['tables']} 件")
    print(f"   - 画像: {stats['images']} 件")
    print(f"   - リンクスクレイピング: {stats['links_scraped']} 件")
    print(f"   - メディアDL: {stats['media_downloaded']} 件")
    print(f"   - 文字起こし: {stats['transcripts']} 件")
    print(f"   - PDFテキスト: {stats['pdfs']} 件")
    if stats['errors']:
        print(f"   - エラー: {len(stats['errors'])} 件")
    print()

    print("📝 フォルダ構造を作成中...")
    create_folder_structure(hierarchy, OUTPUT_DIR)

    # ルートのindex.mdを作成
    root_index = f"""# Levela Portal ドキュメント（完全版・拡張）

**最終更新**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 統計

- ページ数: {stats['pages']}
- データベース数: {stats['databases']}
- レコード数: {stats['records']}
- テーブル数: {stats['tables']}
- 画像数: {stats['images']}
- リンクスクレイピング: {stats['links_scraped']}
- メディアダウンロード: {stats['media_downloaded']}
- 文字起こし: {stats['transcripts']}
- PDFテキスト抽出: {stats['pdfs']}

---

## セクション一覧

"""
    for node in hierarchy:
        icon = '📊' if node['type'] == 'database' else '📄'
        root_index += f"- {icon} [{node['name']}](./{sanitize_filename(node['name'])}/index.md)\n"

    root_index += f"""
---

## 使い方

1. 各フォルダはNotionの階層構造に対応しています
2. データベースにはプロパティ（カラム）とレコード（行）が含まれています
3. テーブルの中身もMarkdownテーブルとして出力されています
4. リンク先のWebページ内容が <details> タグ内に格納されています
5. 動画・音声ファイルは notion_media/ にダウンロードされ、文字起こしが含まれています
6. PDFファイルはテキスト抽出されています

---

*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""

    with open(OUTPUT_DIR / 'index.md', 'w', encoding='utf-8') as f:
        f.write(root_index)

    print()
    print("=" * 60)
    print("✅ エクスポート完了!")
    print(f"   出力先: {OUTPUT_DIR}")
    print(f"   メディア: {MEDIA_DIR}")
    print(f"   画像: {IMAGES_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()
