#!/usr/bin/env python3
"""
階層構造をQ&A用ドキュメント形式でエクスポート
"""

import json
import re
from datetime import datetime
from pathlib import Path

def parse_hierarchy_tree(file_path):
    """階層ツリーファイルをパース"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    nodes = []
    stack = []

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

            while len(stack) > depth:
                stack.pop()

            parent = stack[-1] if stack else None
            path = [s['name'] for s in stack] + [name]

            node = {
                'name': name.strip(),
                'type': node_type,
                'depth': depth,
                'parent': parent['name'] if parent else None,
                'path': path
            }
            nodes.append(node)
            stack.append(node)

    return nodes

def generate_markdown_doc(nodes):
    """Q&A用Markdownドキュメントを生成"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M')

    # 統計情報
    total_nodes = len(nodes)
    pages = [n for n in nodes if n['type'] == 'page']
    databases = [n for n in nodes if n['type'] == 'database']
    max_depth = max(n['depth'] for n in nodes) if nodes else 0

    # 親ノード別の集計
    parents = {}
    for node in nodes:
        if node['parent']:
            if node['parent'] not in parents:
                parents[node['parent']] = []
            parents[node['parent']].append(node['name'])

    doc = f"""# Levela Portal 階層構造ドキュメント

**最終更新**: {now}
**総ノード数**: {total_nodes}
**ページ数**: {len(pages)}
**データベース数**: {len(databases)}
**最大階層深度**: {max_depth + 1} 段階

---

## 概要

このドキュメントはLevela PortalのNotion階層構造を記録したものです。
AIへの質問や情報検索の際にこのドキュメントを参照してください。

---

## セクション一覧

Levela Portalは以下の6つのメインセクションで構成されています：

| セクション | 説明 |
|-----------|------|
| Levela全体 | 全体会議、メンバー紹介、MVV、図書館 |
| 部署 | CS部、マーケティング部、営業ポータル等 |
| 事業 | 各事業部門（AI教育、コーチング、運用代行等） |
| マニュアル | 業務マニュアル、ナレッジ共有 |
| インテリジェンス | 教材、AI活用事例、開発ツール |
| その他 | その他の情報 |

---

## 階層構造詳細

"""

    # 深さごとにグループ化
    by_depth = {}
    for node in nodes:
        d = node['depth']
        if d not in by_depth:
            by_depth[d] = []
        by_depth[d].append(node)

    for depth in sorted(by_depth.keys()):
        level_nodes = by_depth[depth]
        doc += f"### 階層 {depth + 1}（{len(level_nodes)}件）\n\n"

        # 親でグループ化
        by_parent = {}
        for node in level_nodes:
            p = node['parent'] or 'ROOT'
            if p not in by_parent:
                by_parent[p] = []
            by_parent[p].append(node)

        for parent, children in sorted(by_parent.items()):
            if parent != 'ROOT':
                doc += f"**{parent}** の子:\n"
            for child in children:
                icon = '📊' if child['type'] == 'database' else '📄'
                doc += f"- {icon} {child['name']}\n"
            doc += "\n"

    doc += """---

## 全ノードリスト（パス付き）

以下は全ノードをパス形式で一覧化したものです：

| ノード名 | 種類 | 階層 | フルパス |
|---------|------|------|---------|
"""

    for node in nodes:
        path_str = ' → '.join(node['path'])
        doc += f"| {node['name'][:30]}{'...' if len(node['name']) > 30 else ''} | {node['type']} | {node['depth'] + 1} | {path_str} |\n"

    doc += f"""

---

## 使い方

このドキュメントをAIに渡して以下のような質問ができます：

1. 「CS部の下にはどんなページがありますか？」
2. 「マーケティング部の階層構造を教えてください」
3. 「AI教育事業に関連するページを探してください」
4. 「Weekly会議の子ページは何がありますか？」

---

*Generated: {now}*
"""

    return doc

def generate_json_export(nodes):
    """JSON形式でエクスポート"""
    return json.dumps({
        'generated_at': datetime.now().isoformat(),
        'total_nodes': len(nodes),
        'nodes': nodes
    }, ensure_ascii=False, indent=2)

def generate_tree_text(nodes):
    """ツリー形式のテキストを生成"""
    lines = ["Levela Portal 階層構造\n" + "=" * 40 + "\n"]

    for node in nodes:
        indent = "  " * node['depth']
        icon = '📊' if node['type'] == 'database' else '📄'
        lines.append(f"{indent}{icon} {node['name']}")

    return '\n'.join(lines)

def main():
    base_dir = Path(__file__).parent.parent
    tree_file = base_dir / 'notion_data' / 'pages' / 'notion_hierarchy_tree.txt'
    output_dir = base_dir / 'notion_data' / 'exports'

    output_dir.mkdir(exist_ok=True)

    print("Parsing hierarchy tree...")
    nodes = parse_hierarchy_tree(tree_file)
    print(f"Found {len(nodes)} nodes")

    # Markdown出力
    print("Generating Markdown document...")
    md_content = generate_markdown_doc(nodes)
    md_file = output_dir / 'levela_structure.md'
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"Saved: {md_file}")

    # JSON出力
    print("Generating JSON export...")
    json_content = generate_json_export(nodes)
    json_file = output_dir / 'levela_structure.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        f.write(json_content)
    print(f"Saved: {json_file}")

    # Tree text出力
    print("Generating tree text...")
    tree_content = generate_tree_text(nodes)
    tree_file_out = output_dir / 'levela_structure_tree.txt'
    with open(tree_file_out, 'w', encoding='utf-8') as f:
        f.write(tree_content)
    print(f"Saved: {tree_file_out}")

    print("\nExport complete!")
    print(f"Files saved to: {output_dir}")

if __name__ == "__main__":
    main()
