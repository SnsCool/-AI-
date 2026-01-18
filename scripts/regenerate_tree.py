#!/usr/bin/env python3
"""
Notion APIからツリーファイルを再生成
"""

import urllib.request
import json
import os
import sys
from datetime import datetime

TOKEN = os.environ.get('NOTION_API_TOKEN')
if not TOKEN:
    print("Error: NOTION_API_TOKEN environment variable is required")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Notion-Version": "2022-06-28"
}

ROOT_PAGE_ID = "7f19ff35-7ffc-4c78-8c71-92cb99d5204a"

visited = set()
relationships = []
tree_lines = []

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
            print(f"  [Error: {str(e)[:30]}]", flush=True)
            break

    return all_results

def explore_page(page_id, page_title, depth=0, max_depth=5):
    """ページを再帰的に探索"""
    if page_id in visited or depth > max_depth:
        return
    visited.add(page_id)

    blocks = get_block_children(page_id)

    for block in blocks:
        block_type = block.get('type', '')
        block_id = block['id']
        has_children = block.get('has_children', False)

        if block_type == 'child_page':
            child_title = block.get('child_page', {}).get('title', 'Untitled')
            if not child_title.strip():
                continue

            indent = "  " * depth
            tree_lines.append(f"{indent}📄 {child_title}")
            relationships.append({
                'parent_id': page_id[:8],
                'parent_title': page_title,
                'child_id': block_id[:8],
                'child_title': child_title,
                'depth': depth,
                'type': 'page'
            })
            print(f"{'  ' * depth}📄 {child_title}", flush=True)

            # 子ページを再帰的に探索
            explore_page(block_id, child_title, depth + 1, max_depth)

        elif block_type == 'child_database':
            child_title = block.get('child_database', {}).get('title', 'Untitled')
            if not child_title.strip():
                continue

            indent = "  " * depth
            tree_lines.append(f"{indent}📊 {child_title}")
            relationships.append({
                'parent_id': page_id[:8],
                'parent_title': page_title,
                'child_id': block_id[:8],
                'child_title': child_title,
                'depth': depth,
                'type': 'database'
            })
            print(f"{'  ' * depth}📊 {child_title}", flush=True)

        # コンテナブロックは子を再帰的に探索
        elif block_type in ['column_list', 'column', 'toggle', 'synced_block', 'callout']:
            if has_children:
                explore_page(block_id, page_title, depth, max_depth)

def main():
    print("=" * 60)
    print("Notion階層構造再生成")
    print("=" * 60)
    print()
    print("📁 Levela Portal")
    print()

    tree_lines.append("=== Scanning Levela Portal Structure (Read-Only) ===")
    tree_lines.append("")
    tree_lines.append("📁 Levela Portal")
    tree_lines.append("")

    explore_page(ROOT_PAGE_ID, "Levela Portal", depth=0, max_depth=5)

    print()
    print(f"Total relationships: {len(relationships)}")

    # ツリーファイル保存
    tree_path = '/Users/hatakiyoto/-AI-egent-libvela/notion_data/pages/notion_hierarchy_tree.txt'
    with open(tree_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(tree_lines))
    print(f"Saved tree: {tree_path}")

    # マークダウン生成
    md = f"""# Notion 親子構造テーブル

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

- **Root Page**: Levela Portal
- **Total Parent-Child Relationships**: {len(relationships)}

---

## 親子関係テーブル

| # | 親ページ | 子ページ/DB | 種類 | 階層 |
|---|----------|-------------|------|------|
"""

    for i, rel in enumerate(relationships, 1):
        parent = rel['parent_title'].replace('|', '\\|')[:40]
        child = rel['child_title'].replace('|', '\\|')[:40]
        icon = "📄" if rel['type'] == 'page' else "📊"
        md += f"| {i} | {parent} | {icon} {child} | {rel['type']} | {rel['depth']} |\n"

    md_path = '/Users/hatakiyoto/-AI-egent-libvela/notion_data/pages/notion_hierarchy.md'
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md)
    print(f"Saved markdown: {md_path}")

if __name__ == "__main__":
    main()
