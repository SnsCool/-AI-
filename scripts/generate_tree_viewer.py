#!/usr/bin/env python3
"""
階層構造ツリーファイルからツリービューアHTMLを生成
"""

import re
import json

def parse_tree_txt(txt_path):
    """ツリー形式のテキストファイルから階層構造を解析"""
    with open(txt_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Levela Portalの直接の子とその子孫を構築
    root_children = []
    stack = [(root_children, -1)]  # (current_children_list, depth)

    for line in lines:
        # スキップ: ヘッダー行や空行
        if '===' in line or '📁' in line or not line.strip():
            continue

        # インデントレベルを計算（2スペースごとに1レベル）
        stripped = line.rstrip()
        leading_spaces = len(line) - len(line.lstrip())
        depth = leading_spaces // 2

        # アイコンとタイトルを抽出
        match = re.match(r'\s*(📄|📊)\s*(.+)', stripped)
        if not match:
            continue

        icon, title = match.groups()
        node_type = 'database' if icon == '📊' else 'page'
        title = title.strip()

        if not title:
            continue

        node = {'name': title, 'type': node_type, 'children': []}

        # スタックを適切なレベルまで戻す
        while len(stack) > 1 and stack[-1][1] >= depth:
            stack.pop()

        # 現在のリストに追加
        stack[-1][0].append(node)

        # このノードの子リストをスタックに追加
        stack.append((node['children'], depth))

    # 空のchildren配列を削除
    def clean_empty_children(node):
        if not node.get('children'):
            if 'children' in node:
                del node['children']
        else:
            for child in node['children']:
                clean_empty_children(child)

    for node in root_children:
        clean_empty_children(node)

    return root_children


# Notionの画面構成に基づいてセクション分け（スクリーンショットの構造と一致）
SECTIONS = {
    'Levela全体': [
        '全体会議議事録',
        'Levelaメンバー紹介',
        'LevelaのMVV',
        'Levelaオンライン図書館'
    ],
    '部署': [
        'CS部',
        'マーケティング部',
        '工事中🚧マーケティング部',
        '営業ポータル',
        '社長室ポータル',
        'クリエイティ部',
        '知足ポータル',
        'TikTok Shopマネタイズ講座ローンチ',
        'AI Brain 知識ベース'
    ],
    '事業': [
        '新規事業_Monthly会議',
        '運用代行',
        'AI教育事業',
        'Mrs.PROTEIN',
        'ダイエット事業',
        'アイレポート',
        '営業代行事業',
        'コーチングスクール事業',  # APIから確認した正式名称
        'TikTokライブスクール',
        '各事業計画',
        'UGC'
    ],
    'マニュアル': [
        '採用決定後のフロー (New)',
        '業務対応マニュアル',
        'ナレッジ共有',
        '週次/月次入力フォーマット',
        'SnsClub講師紹介制度について'
    ],
    'インテリジェンス': [
        '教材格納庫',
        'AIスクール用動画',
        'AI活用事例ナレッジDB',
        '開発ツール'
    ],
    'その他': [
        'クライアントワークの報酬設定',
        'カウンセリングメンバー募集'
    ]
}

# 順序を保持するためにOrderedDictのように扱う
SECTION_ORDER = ['Levela全体', '部署', '事業', 'マニュアル', 'インテリジェンス', 'その他']


def organize_by_sections(root_children):
    """Notionの画面構成に基づいてセクションに分類"""
    # ノード名でインデックスを作成
    node_index = {node['name']: node for node in root_children}

    organized = []

    for section_name, items in SECTIONS.items():
        section_node = {
            'name': section_name,
            'type': 'section',
            'children': []
        }

        for item_name in items:
            if item_name in node_index:
                section_node['children'].append(node_index[item_name])

        if section_node['children']:
            organized.append(section_node)

    # セクションに含まれないノードを「その他」に追加
    categorized = set()
    for items in SECTIONS.values():
        categorized.update(items)

    other_items = [node for node in root_children if node['name'] not in categorized]
    if other_items:
        # 既存の「その他」セクションを探す
        other_section = next((s for s in organized if s['name'] == 'その他'), None)
        if other_section:
            other_section['children'].extend(other_items)
        else:
            organized.append({
                'name': 'その他',
                'type': 'section',
                'children': other_items
            })

    return organized


def generate_html(tree_data, template_path, output_path):
    """ツリーデータをHTMLに埋め込み"""
    with open(template_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # JSON形式でデータを埋め込み
    json_data = json.dumps(tree_data, ensure_ascii=False, indent=2)
    html = html.replace('TREE_DATA_PLACEHOLDER', json_data)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    return output_path


if __name__ == "__main__":
    txt_path = "/Users/hatakiyoto/-AI-egent-libvela/notion_data/pages/notion_hierarchy_tree.txt"
    template_path = "/Users/hatakiyoto/-AI-egent-libvela/notion_data/viewer/family-tree.html"
    output_path = "/Users/hatakiyoto/-AI-egent-libvela/notion_data/viewer/family-tree-view.html"

    print("Parsing hierarchy tree...")
    root_children = parse_tree_txt(txt_path)
    print(f"Found {len(root_children)} top-level items")

    print("Organizing by sections...")
    organized = organize_by_sections(root_children)
    print(f"Created {len(organized)} sections")

    for section in organized:
        children_count = len(section.get('children', []))
        print(f"  - {section['name']}: {children_count} items")

    print("Generating HTML...")
    output = generate_html(organized, template_path, output_path)
    print(f"Saved to: {output}")
