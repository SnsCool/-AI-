#!/usr/bin/env python3
"""
Notion APIデータと既存ツリーデータの比較
"""

import json
import re

# Notion APIから取得したデータを読み込み
with open('/Users/hatakiyoto/-AI-egent-libvela/notion_data/pages/verified_detailed.json', 'r', encoding='utf-8') as f:
    api_data = json.load(f)

# ツリーファイルからトップレベル項目を抽出
with open('/Users/hatakiyoto/-AI-egent-libvela/notion_data/pages/notion_hierarchy_tree.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

tree_items = []
for line in lines:
    if '===' in line or '📁' in line or not line.strip():
        continue
    match = re.match(r'^(📄|📊)\s*(.+)', line)
    if match:
        icon, title = match.groups()
        item_type = 'database' if icon == '📊' else 'page'
        tree_items.append({'name': title.strip(), 'type': item_type})

# APIからのデータ
api_items = [
    {'name': item['name'], 'type': 'database' if item['type'] == 'child_database' else 'page'}
    for item in api_data['pages_and_databases']
    if item['name']  # 空の名前を除外
]

print("=" * 70)
print("データ整合性レポート")
print("=" * 70)
print()

print(f"Notion API から取得: {len(api_items)} 項目")
print(f"ツリーファイル: {len(tree_items)} 項目")
print()

# 名前でセットを作成
api_names = set(item['name'] for item in api_items)
tree_names = set(item['name'] for item in tree_items)

# 差分を確認
only_in_api = api_names - tree_names
only_in_tree = tree_names - api_names
common = api_names & tree_names

print("-" * 70)
print("共通項目:", len(common))
print("-" * 70)

print("\n✅ 一致している項目:")
for name in sorted(common):
    print(f"  - {name}")

if only_in_api:
    print(f"\n⚠️  APIにのみ存在 ({len(only_in_api)}項目):")
    for name in sorted(only_in_api):
        print(f"  - {name}")

if only_in_tree:
    print(f"\n⚠️  ツリーファイルにのみ存在 ({len(only_in_tree)}項目):")
    for name in sorted(only_in_tree):
        print(f"  - {name}")

# 類似名の検出
print("\n" + "-" * 70)
print("類似名の検出（名前が近い項目）:")
print("-" * 70)

for api_name in only_in_api:
    for tree_name in only_in_tree:
        # 類似度チェック（簡易）
        if api_name in tree_name or tree_name in api_name:
            print(f"  API: '{api_name}' ↔ Tree: '{tree_name}'")

# 結果サマリー
print("\n" + "=" * 70)
print("サマリー")
print("=" * 70)

match_rate = len(common) / max(len(api_names), len(tree_names)) * 100
print(f"一致率: {match_rate:.1f}%")
print(f"完全一致: {len(common)} 項目")
print(f"不一致: {len(only_in_api) + len(only_in_tree)} 項目")

if only_in_api or only_in_tree:
    print("\n⚠️  データに差分があります。ツリーファイルの更新が必要です。")
else:
    print("\n✅ データは完全に一致しています。")
