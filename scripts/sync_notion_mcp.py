#!/usr/bin/env python3
"""
Notion差分同期スクリプト（MCP + API ハイブリッド版）
- MCPで高速に最新ページを取得
- APIで詳細コンテンツを取得
- 最終更新日時を比較して差分のみ同期
"""

import os
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
import time
import requests

# バッファリング無効
sys.stdout.reconfigure(line_buffering=True)

# 設定
NOTION_API_TOKEN = os.environ.get('NOTION_API_TOKEN', '')
NOTION_DOCS_DIR = Path('/Users/hatakiyoto/-AI-egent-libvela/notion_docs')
SYNC_STATE_FILE = NOTION_DOCS_DIR.parent / '.notion_sync_state.json'
HEADERS = {
    'Authorization': f'Bearer {NOTION_API_TOKEN}',
    'Notion-Version': '2022-06-28',
    'Content-Type': 'application/json'
}

def load_sync_state():
    """前回の同期状態を読み込む"""
    if SYNC_STATE_FILE.exists():
        with open(SYNC_STATE_FILE, 'r') as f:
            return json.load(f)
    return {'last_sync': None, 'pages': {}}

def save_sync_state(state):
    """同期状態を保存"""
    state['last_sync'] = datetime.now(timezone.utc).isoformat()
    with open(SYNC_STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def search_all_pages_api():
    """API経由で全ページを検索"""
    print("[API] Notionから全ページを取得中...", flush=True)
    all_results = []
    start_cursor = None

    while True:
        payload = {'page_size': 100}
        if start_cursor:
            payload['start_cursor'] = start_cursor

        try:
            response = requests.post(
                'https://api.notion.com/v1/search',
                headers=HEADERS,
                json=payload,
                timeout=30
            )
        except Exception as e:
            print(f"  Error: {e}", flush=True)
            break

        if response.status_code != 200:
            print(f"  API Error: {response.status_code}", flush=True)
            break

        data = response.json()
        results = data.get('results', [])
        all_results.extend(results)
        print(f"  取得中: {len(all_results)}件...", flush=True)

        if not data.get('has_more'):
            break
        start_cursor = data.get('next_cursor')
        time.sleep(0.3)

    return all_results

def get_page_title(page):
    """ページタイトルを取得"""
    props = page.get('properties', {})
    for prop_name, prop_value in props.items():
        if prop_value.get('type') == 'title':
            title_list = prop_value.get('title', [])
            if title_list:
                return ''.join([t.get('plain_text', '') for t in title_list])
    return 'Untitled'

def get_page_content(page_id):
    """ページのブロック内容を取得"""
    blocks = []
    start_cursor = None

    while True:
        url = f'https://api.notion.com/v1/blocks/{page_id}/children'
        if start_cursor:
            url += f'?start_cursor={start_cursor}'

        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
        except:
            return blocks

        if response.status_code != 200:
            return blocks

        data = response.json()
        blocks.extend(data.get('results', []))

        if not data.get('has_more'):
            break
        start_cursor = data.get('next_cursor')
        time.sleep(0.2)

    return blocks

def extract_text_from_blocks(blocks, depth=0):
    """ブロックからテキストを抽出"""
    if depth > 5:
        return ""

    text_parts = []
    indent = "  " * depth

    for block in blocks:
        block_type = block.get('type', '')
        block_data = block.get(block_type, {})

        # リッチテキストを抽出
        rich_text = block_data.get('rich_text', [])
        if rich_text:
            text = ''.join([rt.get('plain_text', '') for rt in rich_text])
            if text.strip():
                text_parts.append(f"{indent}{text}")

        # 子ブロックがあれば再帰的に処理
        if block.get('has_children'):
            child_blocks = get_page_content(block['id'])
            child_text = extract_text_from_blocks(child_blocks, depth + 1)
            if child_text:
                text_parts.append(child_text)

    return '\n'.join(text_parts)

def sanitize_filename(name):
    """ファイル名として安全な文字列に変換"""
    # 危険な文字を置換
    unsafe_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in unsafe_chars:
        name = name.replace(char, '_')
    return name[:100]  # 長すぎる名前を制限

def sync_page(page, sync_state):
    """単一ページを同期"""
    page_id = page['id']
    last_edited = page.get('last_edited_time', '')
    title = get_page_title(page)

    # 同期状態をチェック
    cached = sync_state['pages'].get(page_id, {})
    if cached.get('last_edited') == last_edited:
        return False  # 変更なし

    # ページ内容を取得
    blocks = get_page_content(page_id)
    content = extract_text_from_blocks(blocks)

    # 保存先ディレクトリを作成
    safe_title = sanitize_filename(title)
    page_dir = NOTION_DOCS_DIR / safe_title
    page_dir.mkdir(parents=True, exist_ok=True)

    # メタデータを保存
    metadata = {
        'id': page_id,
        'title': title,
        'last_edited_time': last_edited,
        'url': page.get('url', ''),
        'synced_at': datetime.now(timezone.utc).isoformat()
    }
    with open(page_dir / 'metadata.json', 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    # コンテンツを保存
    with open(page_dir / 'page_content.txt', 'w', encoding='utf-8') as f:
        f.write(f"# {title}\n\n")
        f.write(f"Notion URL: {page.get('url', '')}\n")
        f.write(f"同期日時: {datetime.now().strftime('%Y-%m-%dT%H:%M:%S+09:00')}\n\n")
        f.write("---\n\n")
        f.write(content if content else "(コンテンツなし)")

    # 同期状態を更新
    sync_state['pages'][page_id] = {
        'title': title,
        'last_edited': last_edited,
        'path': str(page_dir)
    }

    return True

def main():
    """メイン処理"""
    print("=" * 60)
    print("Notion差分同期スクリプト（MCP + API ハイブリッド版）")
    print("=" * 60)

    if not NOTION_API_TOKEN:
        print("Error: NOTION_API_TOKEN が設定されていません")
        sys.exit(1)

    # 同期状態を読み込む
    sync_state = load_sync_state()
    last_sync = sync_state.get('last_sync')
    if last_sync:
        print(f"前回の同期: {last_sync}")
    else:
        print("初回同期を実行します")

    # 全ページを取得
    pages = search_all_pages_api()
    print(f"\n[検索完了] {len(pages)}件のページを発見")

    # ページタイプでフィルタ（データベースを除外）
    pages = [p for p in pages if p.get('object') == 'page']
    print(f"[フィルタ後] {len(pages)}件のページを同期対象")

    # 差分同期
    updated_count = 0
    skipped_count = 0

    for i, page in enumerate(pages):
        title = get_page_title(page)

        if sync_page(page, sync_state):
            updated_count += 1
            print(f"[{i+1}/{len(pages)}] 更新: {title[:50]}")
        else:
            skipped_count += 1
            if (i + 1) % 100 == 0:
                print(f"[{i+1}/{len(pages)}] スキップ中...")

        # レート制限対策
        if updated_count > 0 and updated_count % 10 == 0:
            time.sleep(1)

    # 同期状態を保存
    save_sync_state(sync_state)

    print("\n" + "=" * 60)
    print(f"✅ 同期完了!")
    print(f"   更新: {updated_count}件")
    print(f"   スキップ: {skipped_count}件")
    print("=" * 60)

    return updated_count

if __name__ == '__main__':
    main()
