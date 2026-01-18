#!/usr/bin/env python3
"""
Notion API経由で全画像をダウンロード
- 全ページを再帰的にスキャン（column_list/column対応）
- 画像ブロックから新しいURLを取得
- notion_images/ フォルダに保存
- markdownのリンクを更新
"""

import urllib.request
import json
import os
import sys
import re
import time
import hashlib
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, urlparse, unquote
from collections import defaultdict

# 設定
TOKEN = os.environ.get('NOTION_API_TOKEN')
ROOT_PAGE_ID = "7f19ff35-7ffc-4c78-8c71-92cb99d5204a"
BASE_DIR = Path(__file__).parent.parent
NOTION_DOCS_DIR = BASE_DIR / 'notion_docs'
NOTION_IMAGES_DIR = BASE_DIR / 'notion_images'

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
} if TOKEN else {}

API_DELAY = 0.35

# 統計
stats = {
    "pages_scanned": 0,
    "pages_with_images": 0,
    "total_images": 0,
    "downloaded": 0,
    "failed": 0,
    "total_bytes": 0,
    "by_folder": defaultdict(lambda: {"count": 0, "bytes": 0})
}

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
        return None
    except Exception as e:
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

def get_all_blocks_recursive(block_id, depth=0):
    """ブロックとその子孫をすべて再帰的に取得（column_list/column対応）"""
    all_blocks = []
    blocks = get_block_children(block_id)

    for block in blocks:
        all_blocks.append(block)
        block_type = block.get("type")

        # これらのブロックタイプは再帰的に子を取得（child_page, child_databaseは除く）
        if block.get("has_children") and block_type not in ["child_page", "child_database"]:
            child_blocks = get_all_blocks_recursive(block["id"], depth + 1)
            all_blocks.extend(child_blocks)

    return all_blocks

def find_child_pages(blocks):
    """ブロックリストからchild_pageを抽出"""
    child_pages = []
    for block in blocks:
        if block.get("type") == "child_page":
            child_pages.append({
                "id": block.get("id"),
                "title": block.get("child_page", {}).get("title", "untitled")
            })
    return child_pages

def sanitize_name(name):
    """ファイル名をサニタイズ"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    return name.strip() or "unnamed"

def get_file_extension(url, content_type=None):
    """拡張子を取得"""
    parsed = urlparse(url)
    path = unquote(parsed.path)

    ext_match = re.search(r'\.([a-zA-Z0-9]+)(?:\?|$)', path)
    if ext_match:
        ext = ext_match.group(1).lower()
        if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp', 'ico']:
            return f".{ext}"

    if content_type:
        type_map = {
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp',
            'image/svg+xml': '.svg',
        }
        for mime, extension in type_map.items():
            if mime in content_type:
                return extension

    return '.jpg'

def download_image(url, save_path):
    """画像をダウンロード"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as response:
            content = response.read()
            content_type = response.headers.get('Content-Type', '')

            expected_ext = get_file_extension(url, content_type)
            if save_path.suffix.lower() != expected_ext:
                save_path = save_path.with_suffix(expected_ext)

            save_path.parent.mkdir(parents=True, exist_ok=True)

            with open(save_path, 'wb') as f:
                f.write(content)

            return save_path, len(content)

    except Exception as e:
        print(f"    ❌ {str(e)[:60]}")
        return None, 0

def extract_images_from_blocks(blocks):
    """ブロックから画像情報を抽出"""
    images = []

    for block in blocks:
        block_type = block.get("type")

        if block_type == "image":
            image_data = block.get("image", {})
            image_type = image_data.get("type")

            if image_type == "file":
                url = image_data.get("file", {}).get("url")
                if url:
                    images.append({"url": url, "type": "file"})
            elif image_type == "external":
                url = image_data.get("external", {}).get("url")
                if url:
                    images.append({"url": url, "type": "external"})

        # ファイルブロック（画像のみ）
        elif block_type == "file":
            file_data = block.get("file", {})
            file_type = file_data.get("type")
            if file_type == "file":
                url = file_data.get("file", {}).get("url")
                if url and any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                    images.append({"url": url, "type": "file"})

    return images

def get_relative_path(image_path, md_path):
    """相対パスを計算"""
    try:
        return os.path.relpath(image_path, md_path.parent)
    except ValueError:
        return str(image_path)

def update_markdown(md_path, url_mapping):
    """Markdownファイルのリンクを更新"""
    if not url_mapping or not md_path.exists():
        return False

    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        modified = False
        for base_url, new_path in url_mapping.items():
            if new_path:
                # S3 URLパターンをマッチ（パラメータ部分は除く）
                pattern = re.escape(base_url) + r'[^)\s\]"]*'
                relative_path = get_relative_path(new_path, md_path)
                if re.search(pattern, content):
                    content = re.sub(pattern, relative_path, content)
                    modified = True

        if modified:
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
    except Exception as e:
        print(f"    ⚠️ MD更新エラー: {e}")

    return False

def process_page(page_id, page_title, folder_path):
    """1ページの画像を処理"""
    stats["pages_scanned"] += 1
    print(f"\n[{stats['pages_scanned']}] 📄 {folder_path}")

    # このページのすべてのブロックを取得（子孫含む）
    all_blocks = get_all_blocks_recursive(page_id)

    # 画像を抽出
    images = extract_images_from_blocks(all_blocks)

    if images:
        stats["pages_with_images"] += 1
        print(f"  📷 {len(images)}画像")

        # 画像保存先
        image_folder = NOTION_IMAGES_DIR / folder_path

        # 対応するMarkdownファイル
        md_path = NOTION_DOCS_DIR / folder_path / "index.md"

        url_mapping = {}

        for i, img in enumerate(images):
            stats["total_images"] += 1
            url = img["url"]

            # URLの基本部分を抽出（パラメータ除く）
            base_url_match = re.search(r'(https://[^?]+)', url)
            base_url = base_url_match.group(1) if base_url_match else url

            # ファイル名生成
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            ext = get_file_extension(url)
            filename = f"image_{i+1:03d}_{url_hash}{ext}"
            save_path = image_folder / filename

            print(f"    [{i+1}/{len(images)}] {filename}", end=" ", flush=True)

            actual_path, size = download_image(url, save_path)

            if actual_path:
                stats["downloaded"] += 1
                stats["total_bytes"] += size
                stats["by_folder"][str(folder_path)]["count"] += 1
                stats["by_folder"][str(folder_path)]["bytes"] += size

                url_mapping[base_url] = actual_path
                print(f"✅ {size/1024:.1f}KB")
            else:
                stats["failed"] += 1

        # Markdownリンクを更新
        if url_mapping:
            update_markdown(md_path, url_mapping)

    # 子ページを取得して再帰処理
    child_pages = find_child_pages(all_blocks)
    for child in child_pages:
        child_title = sanitize_name(child["title"])
        child_path = folder_path / child_title
        process_page(child["id"], child_title, child_path)

def format_size(bytes_size):
    """サイズをフォーマット"""
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size/1024:.1f} KB"
    elif bytes_size < 1024 * 1024 * 1024:
        return f"{bytes_size/(1024*1024):.1f} MB"
    else:
        return f"{bytes_size/(1024*1024*1024):.2f} GB"

def main():
    print("=" * 60)
    print("Notion 画像ダウンロードスクリプト（全ページスキャン）")
    print(f"保存先: {NOTION_IMAGES_DIR}")
    print("=" * 60)

    if not TOKEN:
        print("❌ NOTION_API_TOKEN が設定されていません")
        sys.exit(1)

    # 画像フォルダ作成
    NOTION_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    # ルートページから開始
    print(f"\n🚀 ルートページから開始: {ROOT_PAGE_ID}")

    # ルートページのすべてのブロックを取得（column_list/column含む）
    all_root_blocks = get_all_blocks_recursive(ROOT_PAGE_ID)

    # トップレベルの子ページを取得
    child_pages = find_child_pages(all_root_blocks)
    print(f"\n📁 トップレベルページ数: {len(child_pages)}")

    for child in child_pages:
        child_title = sanitize_name(child["title"])
        process_page(child["id"], child_title, Path(child_title))

        # 100ページごとに進捗表示
        if stats["pages_scanned"] % 100 == 0:
            print(f"\n--- 進捗: {stats['pages_scanned']}ページ, {stats['downloaded']}画像, {format_size(stats['total_bytes'])} ---")

    # レポート
    print("\n" + "=" * 60)
    print("📊 結果レポート")
    print("=" * 60)
    print(f"\nスキャンページ数: {stats['pages_scanned']}")
    print(f"画像を含むページ: {stats['pages_with_images']}")
    print(f"合計画像数: {stats['total_images']}")
    print(f"ダウンロード成功: {stats['downloaded']}")
    print(f"ダウンロード失敗: {stats['failed']}")
    print(f"\n💾 合計サイズ: {format_size(stats['total_bytes'])}")

    if stats["by_folder"]:
        print("\n📁 フォルダ別サイズ（上位20件）:")
        sorted_folders = sorted(
            stats["by_folder"].items(),
            key=lambda x: x[1]["bytes"],
            reverse=True
        )[:20]
        for folder, data in sorted_folders:
            print(f"  {folder}: {data['count']}画像, {format_size(data['bytes'])}")

    # レポートファイル保存
    report_path = BASE_DIR / "image_download_report.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("Notion画像ダウンロードレポート\n")
        f.write(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"保存先: {NOTION_IMAGES_DIR}\n")
        f.write(f"スキャンページ数: {stats['pages_scanned']}\n")
        f.write(f"画像を含むページ: {stats['pages_with_images']}\n")
        f.write(f"合計画像数: {stats['total_images']}\n")
        f.write(f"ダウンロード成功: {stats['downloaded']}\n")
        f.write(f"ダウンロード失敗: {stats['failed']}\n")
        f.write(f"合計サイズ: {format_size(stats['total_bytes'])}\n\n")
        f.write("フォルダ別サイズ:\n")
        for folder, data in sorted(stats["by_folder"].items(), key=lambda x: x[1]["bytes"], reverse=True):
            f.write(f"  {folder}: {data['count']}画像, {format_size(data['bytes'])}\n")

    print(f"\n📄 レポート: {report_path}")
    print("\n✅ 完了!")

if __name__ == "__main__":
    main()
