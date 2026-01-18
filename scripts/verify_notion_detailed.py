#!/usr/bin/env python3
"""
Notion階層構造の詳細検証スクリプト
全ブロックタイプを調査し、ネストした構造も展開する
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

def get_block_children(block_id):
    """ブロックの子要素を取得"""
    all_results = []
    has_more = True
    start_cursor = None

    while has_more:
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

def explore_blocks(block_id, depth=0, max_depth=3):
    """ブロックを再帰的に探索"""
    if depth > max_depth:
        return []

    blocks = get_block_children(block_id)
    results = []

    for block in blocks:
        block_type = block.get('type', 'unknown')
        block_id = block['id']
        has_children = block.get('has_children', False)

        item = {
            'type': block_type,
            'id': block_id,
            'depth': depth,
            'has_children': has_children
        }

        # ページとデータベースの名前を取得
        if block_type == 'child_page':
            item['name'] = block.get('child_page', {}).get('title', 'Untitled')
        elif block_type == 'child_database':
            item['name'] = block.get('child_database', {}).get('title', 'Untitled')
        else:
            item['name'] = None

        results.append(item)

        # コンテナタイプのブロックは子を再帰的に取得
        container_types = ['column_list', 'column', 'toggle', 'synced_block', 'callout', 'bulleted_list_item', 'numbered_list_item']
        if has_children and block_type in container_types:
            children = explore_blocks(block_id, depth + 1, max_depth)
            results.extend(children)

    return results

def main():
    print("=" * 70)
    print("Notion詳細構造検証 - Levela Portal")
    print("=" * 70)
    print()

    # Levela Portalの全ブロックを取得
    print("Levela Portalの全ブロックを探索中...")
    all_blocks = explore_blocks(ROOT_PAGE_ID)

    # ブロックタイプの集計
    type_counts = {}
    for block in all_blocks:
        t = block['type']
        type_counts[t] = type_counts.get(t, 0) + 1

    print(f"\n総ブロック数: {len(all_blocks)}")
    print("\nブロックタイプ別集計:")
    for t, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {t}: {count}")

    # ページとデータベースを抽出
    pages_and_dbs = [b for b in all_blocks if b['type'] in ['child_page', 'child_database']]

    print(f"\n子ページ/DB数: {len(pages_and_dbs)}")
    print("-" * 70)
    print("Levela Portalの子ページ/データベース:")
    print("-" * 70)

    for i, item in enumerate(pages_and_dbs, 1):
        icon = "📄" if item['type'] == 'child_page' else "📊"
        indent = "  " * item['depth']
        print(f"{i:2}. {indent}{icon} {item['name']} (depth={item['depth']})")

    # 結果をJSON保存
    output = {
        'root': 'Levela Portal',
        'root_id': ROOT_PAGE_ID,
        'total_blocks': len(all_blocks),
        'type_counts': type_counts,
        'pages_and_databases': pages_and_dbs
    }

    output_path = '/Users/hatakiyoto/-AI-egent-libvela/notion_data/pages/verified_detailed.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n検証結果を保存: {output_path}")

    return pages_and_dbs

if __name__ == "__main__":
    main()
