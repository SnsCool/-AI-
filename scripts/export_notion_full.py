#!/usr/bin/env python3
"""
Notionから全コンテンツを取得し、階層フォルダ構造でエクスポート
各フォルダにindex.mdを作成し、ページの全内容と子孫情報を含める
"""

import urllib.request
import json
import os
import sys
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

# 設定
TOKEN = os.environ.get('NOTION_API_TOKEN')
ROOT_PAGE_ID = "7f19ff35-7ffc-4c78-8c71-92cb99d5204a"
BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / 'notion_docs'

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
} if TOKEN else {}

# API呼び出し間隔（レート制限対策）
API_DELAY = 0.35

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
        return None
    except Exception as e:
        print(f"  Error: {e}")
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

def get_page_info(page_id):
    """ページの情報を取得"""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    return api_request(url)

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

def database_entry_to_markdown(entry):
    """データベースエントリをMarkdownに変換"""
    props = entry.get('properties', {})
    md_parts = []

    # タイトルプロパティを探す
    title = ""
    for prop_name, prop_value in props.items():
        prop_type = prop_value.get('type', '')

        if prop_type == 'title':
            title_array = prop_value.get('title', [])
            title = rich_text_to_markdown(title_array) or "(無題)"
            break

    if title:
        md_parts.append(f"### {title}")

    # その他のプロパティ
    for prop_name, prop_value in props.items():
        prop_type = prop_value.get('type', '')
        value = ""

        if prop_type == 'title':
            continue  # 既に処理済み
        elif prop_type == 'rich_text':
            value = rich_text_to_markdown(prop_value.get('rich_text', []))
        elif prop_type == 'number':
            value = str(prop_value.get('number', ''))
        elif prop_type == 'select':
            select = prop_value.get('select')
            value = select.get('name', '') if select else ''
        elif prop_type == 'multi_select':
            values = [s.get('name', '') for s in prop_value.get('multi_select', [])]
            value = ', '.join(values)
        elif prop_type == 'date':
            date = prop_value.get('date')
            if date:
                value = date.get('start', '')
                if date.get('end'):
                    value += f" → {date.get('end')}"
        elif prop_type == 'checkbox':
            value = "✅" if prop_value.get('checkbox') else "☐"
        elif prop_type == 'url':
            url = prop_value.get('url', '')
            value = f"[リンク]({url})" if url else ''
        elif prop_type == 'email':
            value = prop_value.get('email', '')
        elif prop_type == 'phone_number':
            value = prop_value.get('phone_number', '')
        elif prop_type == 'status':
            status = prop_value.get('status')
            value = status.get('name', '') if status else ''
        elif prop_type == 'people':
            people = prop_value.get('people', [])
            names = [p.get('name', 'Unknown') for p in people]
            value = ', '.join(names)
        elif prop_type == 'files':
            files = prop_value.get('files', [])
            file_links = []
            for f in files:
                name = f.get('name', 'ファイル')
                url = f.get('file', {}).get('url') or f.get('external', {}).get('url', '')
                if url:
                    file_links.append(f"[{name}]({url})")
            value = ', '.join(file_links)
        elif prop_type == 'formula':
            formula = prop_value.get('formula', {})
            formula_type = formula.get('type', '')
            if formula_type == 'string':
                value = formula.get('string', '')
            elif formula_type == 'number':
                value = str(formula.get('number', ''))
            elif formula_type == 'boolean':
                value = "✅" if formula.get('boolean') else "☐"
        elif prop_type == 'relation':
            relations = prop_value.get('relation', [])
            value = f"({len(relations)}件の関連)"
        elif prop_type == 'rollup':
            rollup = prop_value.get('rollup', {})
            rollup_type = rollup.get('type', '')
            if rollup_type == 'array':
                value = f"({len(rollup.get('array', []))}件)"
            else:
                value = str(rollup.get(rollup_type, ''))

        if value:
            md_parts.append(f"- **{prop_name}**: {value}")

    return '\n'.join(md_parts) + '\n'

def fetch_database_content(database_id, title):
    """データベースの全内容をMarkdownで取得"""
    entries = query_database(database_id)

    if not entries:
        return f"[データベース: {title}]\n\n(レコードなし)"

    md_parts = [f"[データベース: {title}]\n"]
    md_parts.append(f"**レコード数**: {len(entries)}件\n")
    md_parts.append("---\n")

    for i, entry in enumerate(entries, 1):
        entry_md = database_entry_to_markdown(entry)
        if entry_md.strip():
            md_parts.append(entry_md)
            md_parts.append("")  # 空行

    return '\n'.join(md_parts)

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
        return f"{indent}📊 **{title}** (データベース)\n"

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

            # データベースの全レコードを取得
            db_content = fetch_database_content(block_id, title)

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
    print("Notion全コンテンツ エクスポートツール", flush=True)
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
    print(f"📁 出力先: {OUTPUT_DIR}", flush=True)
    print(flush=True)

    # Notionから全データを取得
    print("🌐 Notionからデータを取得中...", flush=True)
    print("   (これには数分かかる場合があります)", flush=True)
    print(flush=True)

    hierarchy = fetch_hierarchy_with_content(ROOT_PAGE_ID)

    print()
    print(f"✅ 取得完了: {sum(1 for _ in _flatten_nodes(hierarchy))} ノード")
    print()

    # フォルダ構造を作成
    print("📝 フォルダ構造を作成中...")
    create_folder_structure(hierarchy, OUTPUT_DIR)

    # ルートのindex.mdを作成
    root_index = f"""# Levela Portal ドキュメント

**最終更新**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

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
2. 各`index.md`にはそのページの全コンテンツと子孫情報が含まれています
3. AIに特定セクションのドキュメントを渡して質問できます

---

*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""

    with open(OUTPUT_DIR / 'index.md', 'w', encoding='utf-8') as f:
        f.write(root_index)

    print()
    print("=" * 60)
    print("✅ エクスポート完了!")
    print(f"   出力先: {OUTPUT_DIR}")
    print("=" * 60)

def _flatten_nodes(nodes):
    """ノードをフラット化（カウント用）"""
    for node in nodes:
        yield node
        yield from _flatten_nodes(node.get('children', []))

if __name__ == "__main__":
    main()
