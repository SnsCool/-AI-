#!/usr/bin/env python3
"""
Notion階層構造スキャナー（読み取り専用）
Levela Portalから親子構造を再帰的に取得し、マークダウンファイルを生成
"""

import urllib.request
import json
from datetime import datetime
import sys
import os

TOKEN = os.environ.get('NOTION_API_TOKEN')
if not TOKEN:
    print("Error: NOTION_API_TOKEN environment variable is required")
    print("Set it with: export NOTION_API_TOKEN=your_token")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Notion-Version": "2022-06-28"
}

relationships = []
visited = set()

def get_page_children(page_id, page_title, depth=0, max_depth=5):
    """ページの子要素を再帰的に取得（読み取り専用）"""
    if page_id in visited or depth > max_depth:
        return
    visited.add(page_id)

    url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100"
    req = urllib.request.Request(url, headers=HEADERS, method='GET')

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))

            for block in data.get('results', []):
                block_type = block.get('type', '')

                if block_type == 'child_page':
                    child_title = block.get('child_page', {}).get('title', 'Untitled')
                    child_id = block['id']

                    relationships.append({
                        'parent_id': page_id[:8],
                        'parent_title': page_title,
                        'child_id': child_id[:8],
                        'child_title': child_title,
                        'child_full_id': child_id,
                        'depth': depth,
                        'type': 'page'
                    })

                    print(f"{'  ' * depth}📄 {child_title}", flush=True)
                    get_page_children(child_id, child_title, depth + 1, max_depth)

                elif block_type == 'child_database':
                    child_title = block.get('child_database', {}).get('title', 'Untitled')
                    child_id = block['id']

                    relationships.append({
                        'parent_id': page_id[:8],
                        'parent_title': page_title,
                        'child_id': child_id[:8],
                        'child_title': child_title,
                        'child_full_id': child_id,
                        'depth': depth,
                        'type': 'database'
                    })

                    print(f"{'  ' * depth}📊 {child_title}", flush=True)

                elif block_type in ['column_list', 'column', 'toggle', 'synced_block', 'callout']:
                    if block.get('has_children'):
                        get_page_children(block['id'], page_title, depth, max_depth)

    except urllib.error.HTTPError as e:
        print(f"{'  ' * depth}[Error {e.code}]", flush=True)
    except Exception as e:
        print(f"{'  ' * depth}[Error: {str(e)[:30]}]", flush=True)


def generate_markdown():
    """マークダウンファイルを生成"""
    md = f"""# Notion 親子構造テーブル

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

- **Root Page**: Levela Portal
- **Total Parent-Child Relationships**: {len(relationships)}

---

## 階層構造ツリー

```
Levela Portal
"""

    for rel in relationships:
        indent = "│   " * rel['depth'] + "├── "
        icon = "📄" if rel['type'] == 'page' else "📊"
        md += f"{indent}{icon} {rel['child_title']}\n"

    md += """```

---

## 親子関係テーブル

| # | 親ページ | 子ページ/DB | 種類 | 階層 | 親ID | 子ID |
|---|----------|-------------|------|------|------|------|
"""

    for i, rel in enumerate(relationships, 1):
        parent = rel['parent_title'].replace('|', '\\|')[:40]
        child = rel['child_title'].replace('|', '\\|')[:40]
        rel_type = "📄 Page" if rel['type'] == 'page' else "📊 DB"
        md += f"| {i} | {parent} | {child} | {rel_type} | {rel['depth']} | `{rel['parent_id']}` | `{rel['child_id']}` |\n"

    md += """

---

## 親ページ別 子要素一覧

"""

    parent_groups = {}
    for rel in relationships:
        parent = rel['parent_title']
        if parent not in parent_groups:
            parent_groups[parent] = []
        parent_groups[parent].append(rel)

    for parent, children in parent_groups.items():
        md += f"### {parent}\n\n"
        md += "| 子ページ/DB | 種類 | ID |\n"
        md += "|-------------|------|----|\\n"
        for child in children:
            icon = "📄" if child['type'] == 'page' else "📊"
            name = child['child_title'].replace('|', '\\|')
            md += f"| {icon} {name} | {child['type']} | `{child['child_id']}` |\n"
        md += "\n"

    return md


if __name__ == "__main__":
    root_id = "7f19ff35-7ffc-4c78-8c71-92cb99d5204a"
    root_title = "Levela Portal"

    print("=== Scanning Levela Portal Structure (Read-Only) ===\n", flush=True)
    print(f"📁 {root_title}\n", flush=True)

    get_page_children(root_id, root_title)

    print(f"\n\nTotal relationships found: {len(relationships)}", flush=True)

    md_content = generate_markdown()

    output_path = "/Users/hatakiyoto/-AI-egent-libvela/notion_data/pages/notion_hierarchy.md"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md_content)

    print(f"\nSaved to: {output_path}", flush=True)
