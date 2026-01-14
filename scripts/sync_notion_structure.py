#!/usr/bin/env python3
"""
Notion階層構造の同期スクリプト
- Notion APIから最新データを取得
- ローカルデータとの差分を検出
- 変更があれば更新を実行
"""

import urllib.request
import json
import os
import sys
import re
from datetime import datetime
from pathlib import Path

# 設定
TOKEN = os.environ.get('NOTION_API_TOKEN')
ROOT_PAGE_ID = "7f19ff35-7ffc-4c78-8c71-92cb99d5204a"
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'notion_data'

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Notion-Version": "2022-06-28"
} if TOKEN else {}

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
            print(f"  Error: {e}")
            break

    return all_results

def fetch_notion_structure(block_id, depth=0, max_depth=10, visited=None):
    """Notion構造を再帰的に取得"""
    if visited is None:
        visited = set()

    if depth > max_depth or block_id in visited:
        return []

    visited.add(block_id)
    blocks = get_block_children(block_id)
    results = []

    for block in blocks:
        block_type = block.get('type', 'unknown')
        bid = block['id']
        has_children = block.get('has_children', False)

        name = None
        node_type = 'page'

        if block_type == 'child_page':
            name = block.get('child_page', {}).get('title', 'Untitled')
            node_type = 'page'
        elif block_type == 'child_database':
            name = block.get('child_database', {}).get('title', 'Untitled')
            node_type = 'database'

        if name:
            results.append({
                'id': bid,
                'name': name.strip(),
                'type': node_type,
                'depth': depth,
                'has_children': has_children
            })

            if has_children:
                children = fetch_notion_structure(bid, depth + 1, max_depth, visited.copy())
                results.extend(children)

        # コンテナブロックの子を探索
        container_types = ['column_list', 'column', 'toggle', 'synced_block', 'callout']
        if block_type in container_types and has_children:
            children = fetch_notion_structure(bid, depth, max_depth, visited.copy())
            results.extend(children)

    return results

def load_local_structure():
    """ローカルの階層ツリーファイルをパース"""
    tree_file = DATA_DIR / 'pages' / 'notion_hierarchy_tree.txt'
    if not tree_file.exists():
        return []

    with open(tree_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    nodes = []
    for line in lines:
        if not line.strip() or line.startswith('==='):
            continue

        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        depth = indent // 2

        match = re.match(r'([📁📄📊])\s*(.+)', stripped.strip())
        if match:
            icon, name = match.groups()
            node_type = 'database' if icon == '📊' else 'page'
            nodes.append({
                'name': name.strip(),
                'type': node_type,
                'depth': depth
            })

    return nodes

def compare_structures(notion_nodes, local_nodes):
    """Notionとローカルの構造を比較"""
    notion_names = {n['name'] for n in notion_nodes}
    local_names = {n['name'] for n in local_nodes}

    added = notion_names - local_names
    removed = local_names - notion_names

    # 名前変更の検出（同じ深さで近い位置にある）
    renamed = []

    return {
        'added': list(added),
        'removed': list(removed),
        'renamed': renamed,
        'notion_count': len(notion_nodes),
        'local_count': len(local_nodes)
    }

def generate_diff_report(diff):
    """差分レポートを生成"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    report = f"""# Notion階層構造 同期レポート

**実行日時**: {now}

---

## 概要

| 項目 | 数値 |
|------|------|
| Notionノード数 | {diff['notion_count']} |
| ローカルノード数 | {diff['local_count']} |
| 追加されたノード | {len(diff['added'])} |
| 削除されたノード | {len(diff['removed'])} |

"""

    if diff['added']:
        report += "## 追加されたノード\n\n"
        for name in sorted(diff['added'])[:50]:
            report += f"- ➕ {name}\n"
        if len(diff['added']) > 50:
            report += f"\n... 他 {len(diff['added']) - 50} 件\n"
        report += "\n"

    if diff['removed']:
        report += "## 削除されたノード\n\n"
        for name in sorted(diff['removed'])[:50]:
            report += f"- ➖ {name}\n"
        if len(diff['removed']) > 50:
            report += f"\n... 他 {len(diff['removed']) - 50} 件\n"
        report += "\n"

    if not diff['added'] and not diff['removed']:
        report += "## 結果\n\n✅ **変更なし** - ローカルデータは最新です。\n"

    report += f"\n---\n*Generated: {now}*\n"

    return report

def update_local_structure(notion_nodes):
    """ローカルの階層構造を更新"""
    # ツリーテキスト形式で保存
    lines = ["=== Scanning Levela Portal Structure (Read-Only) ===\n", "\n📁 Levela Portal\n"]

    for node in notion_nodes:
        indent = "  " * node['depth']
        icon = '📊' if node['type'] == 'database' else '📄'
        lines.append(f"{indent}{icon} {node['name']}\n")

    tree_file = DATA_DIR / 'pages' / 'notion_hierarchy_tree.txt'
    with open(tree_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    return tree_file

def main():
    print("=" * 60)
    print("Notion階層構造 同期ツール")
    print("=" * 60)
    print()

    if not TOKEN:
        print("⚠️  NOTION_API_TOKEN が設定されていません")
        print("   環境変数を設定してください:")
        print("   export NOTION_API_TOKEN='your_token_here'")
        print()
        print("ローカルデータのみで動作します...")
        local_nodes = load_local_structure()
        print(f"ローカルノード数: {len(local_nodes)}")
        return

    # 1. ローカルデータを読み込み
    print("📂 ローカルデータを読み込み中...")
    local_nodes = load_local_structure()
    print(f"   ローカルノード数: {len(local_nodes)}")

    # 2. Notionから最新データを取得
    print("\n🌐 Notionから最新データを取得中...")
    notion_nodes = fetch_notion_structure(ROOT_PAGE_ID)
    print(f"   Notionノード数: {len(notion_nodes)}")

    # 3. 差分を比較
    print("\n🔍 差分を検出中...")
    diff = compare_structures(notion_nodes, local_nodes)

    print(f"   追加: {len(diff['added'])} 件")
    print(f"   削除: {len(diff['removed'])} 件")

    # 4. レポート生成
    report = generate_diff_report(diff)
    report_file = DATA_DIR / 'sync_reports' / f"sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    report_file.parent.mkdir(exist_ok=True)

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n📋 レポート保存: {report_file}")

    # 5. 変更があれば更新
    if diff['added'] or diff['removed']:
        print("\n⚠️  変更が検出されました")
        response = input("ローカルデータを更新しますか？ (y/N): ")

        if response.lower() == 'y':
            print("\n📝 ローカルデータを更新中...")
            updated_file = update_local_structure(notion_nodes)
            print(f"   更新完了: {updated_file}")

            # ビューアも再生成
            print("\n🔄 ビューアを再生成中...")
            import subprocess
            subprocess.run([
                '/Library/Developer/CommandLineTools/usr/bin/python3',
                str(BASE_DIR / 'scripts' / 'generate_tree_viewer.py')
            ])
            print("   完了!")
        else:
            print("   更新をスキップしました")
    else:
        print("\n✅ 変更なし - ローカルデータは最新です")

    print("\n" + "=" * 60)
    print("同期完了")
    print("=" * 60)

if __name__ == "__main__":
    main()
