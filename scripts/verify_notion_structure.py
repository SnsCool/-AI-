#!/usr/bin/env python3
"""
Notion階層構造の検証スクリプト
Levela Portalの直接の子要素を取得し、既存データと比較する
"""

import urllib.request
import json
import os
import sys

TOKEN = os.environ.get('NOTION_API_TOKEN')
if not TOKEN:
    print("Error: NOTION_API_TOKEN environment variable is required")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Notion-Version": "2022-06-28"
}

ROOT_PAGE_ID = "7f19ff35-7ffc-4c78-8c71-92cb99d5204a"

def get_block_children(block_id, max_pages=100):
    """ブロックの子要素を取得"""
    all_results = []
    has_more = True
    start_cursor = None

    while has_more and len(all_results) < max_pages:
        url = f"https://api.notion.com/v1/blocks/{block_id}/children?page_size=100"
        if start_cursor:
            url += f"&start_cursor={start_cursor}"

        req = urllib.request.Request(url, headers=HEADERS, method='GET')

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
                all_results.extend(data.get('results', []))
                has_more = data.get('has_more', False)
                start_cursor = data.get('next_cursor')
        except Exception as e:
            print(f"Error fetching children: {e}")
            break

    return all_results

def extract_page_info(blocks):
    """ブロックからページとデータベース情報を抽出"""
    items = []

    for block in blocks:
        block_type = block.get('type', '')

        if block_type == 'child_page':
            title = block.get('child_page', {}).get('title', 'Untitled')
            items.append({
                'name': title,
                'type': 'page',
                'id': block['id']
            })
        elif block_type == 'child_database':
            title = block.get('child_database', {}).get('title', 'Untitled')
            items.append({
                'name': title,
                'type': 'database',
                'id': block['id']
            })

    return items

def main():
    print("=" * 60)
    print("Notion構造検証 - Levela Portal")
    print("=" * 60)
    print()

    # Levela Portalの直接の子要素を取得
    print("Levela Portalの子要素を取得中...")
    blocks = get_block_children(ROOT_PAGE_ID)
    print(f"取得したブロック数: {len(blocks)}")
    print()

    # ページとDBを抽出
    items = extract_page_info(blocks)
    print(f"子ページ/DB数: {len(items)}")
    print()

    print("-" * 60)
    print("Levela Portalの直接の子要素:")
    print("-" * 60)

    for i, item in enumerate(items, 1):
        icon = "📄" if item['type'] == 'page' else "📊"
        print(f"{i:2}. {icon} {item['name']}")

    print()
    print("=" * 60)

    # 結果をJSONで保存
    output = {
        'root': 'Levela Portal',
        'root_id': ROOT_PAGE_ID,
        'children_count': len(items),
        'children': items
    }

    output_path = '/Users/hatakiyoto/-AI-egent-libvela/notion_data/pages/verified_structure.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"検証結果を保存: {output_path}")

    return items

if __name__ == "__main__":
    main()
