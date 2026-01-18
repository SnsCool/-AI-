#!/usr/bin/env python3
"""
Notionから全コンテンツを取得し、階層フォルダ構造でエクスポート
データベースのレコード、プロパティ、画像も含む完全版
"""

import urllib.request
import json
import os
import sys
import re
import time
import hashlib
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, urlparse

# 設定
TOKEN = os.environ.get('NOTION_API_TOKEN')
ROOT_PAGE_ID = "7f19ff35-7ffc-4c78-8c71-92cb99d5204a"
BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / 'notion_docs'
IMAGES_DIR = BASE_DIR / 'notion_images'

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
} if TOKEN else {}

# API呼び出し間隔（レート制限対策）
API_DELAY = 0.35

# 統計
stats = {
    'pages': 0,
    'databases': 0,
    'records': 0,
    'images': 0,
    'errors': []
}

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
        print(f"  HTTP Error {e.code}: {e.reason}")
        stats['errors'].append(f"HTTP {e.code}: {url}")
        return None
    except Exception as e:
        print(f"  Error: {e}")
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

def get_database_info(database_id):
    """データベースの情報（プロパティ含む）を取得"""
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

def download_image(url, save_dir):
    """画像をダウンロード"""
    try:
        # URLからファイル名を生成
        url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
        parsed = urlparse(url)
        ext = os.path.splitext(parsed.path)[1] or '.png'
        filename = f"{url_hash}{ext}"

        filepath = save_dir / filename

        if filepath.exists():
            return str(filepath)

        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0')

        with urllib.request.urlopen(req, timeout=30) as response:
            with open(filepath, 'wb') as f:
                f.write(response.read())

        stats['images'] += 1
        return str(filepath)
    except Exception as e:
        stats['errors'].append(f"Image download error: {e}")
        return url

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
        return prop.get('url', '')
    elif prop_type == 'email':
        return prop.get('email', '')
    elif prop_type == 'phone_number':
        return prop.get('phone_number', '')
    elif prop_type == 'formula':
        formula = prop.get('formula', {})
        return str(formula.get(formula.get('type', ''), ''))
    elif prop_type == 'relation':
        return f"[{len(prop.get('relation', []))} 件のリンク]"
    elif prop_type == 'rollup':
        rollup = prop.get('rollup', {})
        rollup_type = rollup.get('type', '')
        if rollup_type == 'array':
            return f"[{len(rollup.get('array', []))} 件]"
        return str(rollup.get(rollup_type, ''))
    elif prop_type == 'created_time':
        return prop.get('created_time', '')
    elif prop_type == 'created_by':
        return prop.get('created_by', {}).get('name', '')
    elif prop_type == 'last_edited_time':
        return prop.get('last_edited_time', '')
    elif prop_type == 'last_edited_by':
        return prop.get('last_edited_by', {}).get('name', '')
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

    # データベース情報を取得
    db_info = get_database_info(database_id)
    if not db_info:
        return f"\n### データベース: {title}\n\n(データベース情報を取得できませんでした)\n"

    # プロパティ（スキーマ）を取得
    properties = db_info.get('properties', {})
    if properties:
        md_parts.append("#### プロパティ（カラム）\n\n")
        md_parts.append("| プロパティ名 | タイプ |\n")
        md_parts.append("|------------|--------|\n")
        for prop_name, prop_info in properties.items():
            prop_type = prop_info.get('type', 'unknown')
            md_parts.append(f"| {prop_name} | {prop_type} |\n")
        md_parts.append("\n")

    # レコードを取得
    records = query_database(database_id)
    stats['records'] += len(records)

    if not records:
        md_parts.append("(レコードなし)\n")
        return ''.join(md_parts)

    md_parts.append(f"#### レコード（{len(records)}件）\n\n")

    # プロパティ名を取得（タイトル列を最初に）
    prop_names = list(properties.keys())
    title_prop = None
    for name, info in properties.items():
        if info.get('type') == 'title':
            title_prop = name
            break

    if title_prop:
        prop_names.remove(title_prop)
        prop_names.insert(0, title_prop)

    # テーブルヘッダー
    md_parts.append("| " + " | ".join(prop_names[:8]) + " |\n")  # 最大8列
    md_parts.append("|" + "---|" * min(len(prop_names), 8) + "\n")

    # レコードを出力
    for record in records[:100]:  # 最大100レコード
        record_props = record.get('properties', {})
        row = []
        for prop_name in prop_names[:8]:
            prop = record_props.get(prop_name, {})
            value = property_value_to_string(prop)
            # テーブルセル用にエスケープ (Noneの場合は空文字に)
            if value is None:
                value = ''
            value = str(value).replace('|', '\\|').replace('\n', ' ')[:50]
            row.append(value)
        md_parts.append("| " + " | ".join(row) + " |\n")

    if len(records) > 100:
        md_parts.append(f"\n*（他 {len(records) - 100} 件のレコード）*\n")

    return ''.join(md_parts)

def block_to_markdown(block, indent_level=0):
    """Notionブロックを Markdown に変換"""
    block_type = block.get('type', '')
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
        return f"{indent}[テーブル]\n"

    elif block_type == 'image':
        image = block.get('image', {})
        url = image.get('file', {}).get('url') or image.get('external', {}).get('url', '')
        caption = rich_text_to_markdown(image.get('caption', []))
        # 画像をダウンロード
        if url and 'amazonaws.com' in url:
            local_path = download_image(url, IMAGES_DIR)
            if local_path != url:
                url = f"../../../notion_images/{os.path.basename(local_path)}"
        return f"{indent}![{caption}]({url})\n"

    elif block_type == 'bookmark':
        url = block.get('bookmark', {}).get('url', '')
        return f"{indent}[Bookmark: {url}]({url})\n"

    elif block_type == 'link_preview':
        url = block.get('link_preview', {}).get('url', '')
        return f"{indent}[Link: {url}]({url})\n"

    elif block_type == 'child_page':
        title = block.get('child_page', {}).get('title', 'Untitled')
        return f"{indent}📄 **{title}** (子ページ)\n"

    elif block_type == 'child_database':
        title = block.get('child_database', {}).get('title', 'Untitled')
        # データベースの内容を取得
        db_content = database_to_markdown(block['id'], title)
        return f"{indent}📊 **{title}** (データベース)\n{db_content}\n"

    elif block_type == 'embed':
        url = block.get('embed', {}).get('url', '')
        return f"{indent}[Embed: {url}]({url})\n"

    elif block_type == 'video':
        video = block.get('video', {})
        url = video.get('external', {}).get('url') or video.get('file', {}).get('url', '')
        return f"{indent}[Video: {url}]({url})\n"

    elif block_type == 'pdf':
        pdf = block.get('pdf', {})
        url = pdf.get('file', {}).get('url') or pdf.get('external', {}).get('url', '')
        return f"{indent}[PDF: {url}]({url})\n"

    elif block_type == 'file':
        file_data = block.get('file', {})
        url = file_data.get('file', {}).get('url') or file_data.get('external', {}).get('url', '')
        return f"{indent}[File: {url}]({url})\n"

    elif block_type in ['column_list', 'column', 'synced_block']:
        return ""  # コンテナは子要素で処理

    else:
        return f"{indent}[{block_type}]\n"

def fetch_page_content(page_id, max_depth=5, current_depth=0):
    """ページの全コンテンツを取得してMarkdownに変換"""
    if current_depth > max_depth:
        return ""

    blocks = get_block_children(page_id)
    markdown_parts = []

    for block in blocks:
        # ブロックをMarkdownに変換
        md = block_to_markdown(block)
        if md:
            markdown_parts.append(md)

        # 子要素があれば再帰的に取得
        if block.get('has_children', False):
            block_type = block.get('type', '')
            # 子ページ/DBは別途処理するのでスキップ
            if block_type not in ['child_page', 'child_database']:
                child_content = fetch_page_content(block['id'], max_depth, current_depth + 1)
                if child_content:
                    markdown_parts.append(child_content)

    return ''.join(markdown_parts)

def sanitize_filename(name):
    """ファイル名として安全な文字列に変換"""
    # 危険な文字を置換
    unsafe_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '\n', '\r']
    result = name
    for char in unsafe_chars:
        result = result.replace(char, '_')
    # 先頭・末尾の空白とピリオドを削除
    result = result.strip('. ')
    # 長すぎる場合は切り詰め
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

            # ページコンテンツを取得
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

            # データベースの全情報を取得
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

        # コンテナブロックの子を探索
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

    # 全子孫を含める
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

        # index.md を作成
        descendants = get_all_descendants(node)
        index_content = generate_index_md(node, descendants)

        index_file = folder_path / 'index.md'
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(index_content)

        # 子ノードのフォルダを再帰的に作成
        if node['children']:
            create_folder_structure(node['children'], folder_path)

def main():
    print("=" * 60, flush=True)
    print("Notion完全エクスポートツール（レコード・画像含む）", flush=True)
    print("=" * 60, flush=True)
    print(flush=True)

    if not TOKEN:
        print("❌ NOTION_API_TOKEN が設定されていません")
        print("   export NOTION_API_TOKEN='your_token_here'")
        sys.exit(1)

    # 出力ディレクトリを準備
    if OUTPUT_DIR.exists():
        print(f"📁 既存のフォルダを削除: {OUTPUT_DIR}", flush=True)
        import shutil
        shutil.rmtree(OUTPUT_DIR)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 出力先: {OUTPUT_DIR}", flush=True)
    print(f"📁 画像保存先: {IMAGES_DIR}", flush=True)
    print(flush=True)

    # Notionから全データを取得
    print("🌐 Notionからデータを取得中...", flush=True)
    print("   (データベースのレコードも取得するため時間がかかります)", flush=True)
    print(flush=True)

    hierarchy = fetch_hierarchy_with_content(ROOT_PAGE_ID)

    print()
    print(f"✅ 取得完了!")
    print(f"   - ページ: {stats['pages']} 件")
    print(f"   - データベース: {stats['databases']} 件")
    print(f"   - レコード: {stats['records']} 件")
    print(f"   - 画像: {stats['images']} 件")
    if stats['errors']:
        print(f"   - エラー: {len(stats['errors'])} 件")
    print()

    # フォルダ構造を作成
    print("📝 フォルダ構造を作成中...")
    create_folder_structure(hierarchy, OUTPUT_DIR)

    # ルートのindex.mdを作成
    root_index = f"""# Levela Portal ドキュメント（完全版）

**最終更新**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 統計

- ページ数: {stats['pages']}
- データベース数: {stats['databases']}
- レコード数: {stats['records']}
- 画像数: {stats['images']}

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
2. 各`index.md`にはそのページの全コンテンツ、データベースのレコード、子孫情報が含まれています
3. データベースにはプロパティ（カラム）とレコード（行）が含まれています
4. 画像は`notion_images/`フォルダにダウンロードされています

---

*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""

    with open(OUTPUT_DIR / 'index.md', 'w', encoding='utf-8') as f:
        f.write(root_index)

    print()
    print("=" * 60)
    print("✅ エクスポート完了!")
    print(f"   出力先: {OUTPUT_DIR}")
    print(f"   画像: {IMAGES_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()
