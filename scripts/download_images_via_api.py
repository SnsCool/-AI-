#!/usr/bin/env python3
"""
Notion API経由で画像をダウンロード
- APIから新しい署名付きURLを取得
- notion_images/ フォルダに保存
- markdownのリンクを更新
"""

import os
import re
import json
import requests
import hashlib
import time
from pathlib import Path
from urllib.parse import urlparse, unquote
from collections import defaultdict
from dotenv import load_dotenv

# 設定
load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_API_TOKEN")
NOTION_DOCS_DIR = Path("/Users/hatakiyoto/-AI-egent-libvela/notion_docs")
NOTION_IMAGES_DIR = Path("/Users/hatakiyoto/-AI-egent-libvela/notion_images")
STRUCTURE_FILE = Path("/Users/hatakiyoto/-AI-egent-libvela/notion_data/pages/verified_structure.json")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

REQUEST_DELAY = 0.35  # レート制限対策

# 統計
stats = {
    "total_pages": 0,
    "pages_with_images": 0,
    "total_images": 0,
    "downloaded": 0,
    "failed": 0,
    "total_bytes": 0,
    "by_folder": defaultdict(lambda: {"count": 0, "bytes": 0})
}

def get_file_extension(url, content_type=None):
    """URLまたはContent-Typeから拡張子を取得"""
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
        response = requests.get(url, timeout=60)
        response.raise_for_status()

        content_type = response.headers.get('Content-Type', '')
        expected_ext = get_file_extension(url, content_type)

        if save_path.suffix.lower() != expected_ext:
            save_path = save_path.with_suffix(expected_ext)

        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, 'wb') as f:
            f.write(response.content)

        return save_path, len(response.content)

    except Exception as e:
        print(f"    ❌ ダウンロード失敗: {str(e)[:100]}")
        return None, 0

def get_page_blocks(page_id):
    """ページのブロックを取得（画像を含む）"""
    blocks = []
    url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100"

    while url:
        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            data = response.json()

            for block in data.get("results", []):
                blocks.append(block)
                # 子ブロックがある場合は再帰的に取得
                if block.get("has_children") and block["type"] not in ["child_page", "child_database"]:
                    child_blocks = get_page_blocks(block["id"])
                    blocks.extend(child_blocks)

            if data.get("has_more"):
                url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100&start_cursor={data['next_cursor']}"
            else:
                url = None

            time.sleep(REQUEST_DELAY)

        except Exception as e:
            print(f"    ⚠️ ブロック取得エラー: {str(e)[:50]}")
            break

    return blocks

def extract_image_urls(blocks):
    """ブロックから画像URLを抽出"""
    images = []

    for block in blocks:
        block_type = block.get("type")

        if block_type == "image":
            image_data = block.get("image", {})
            image_type = image_data.get("type")

            if image_type == "file":
                url = image_data.get("file", {}).get("url")
                if url:
                    images.append({
                        "url": url,
                        "type": "notion_file",
                        "block_id": block["id"]
                    })
            elif image_type == "external":
                url = image_data.get("external", {}).get("url")
                if url:
                    images.append({
                        "url": url,
                        "type": "external",
                        "block_id": block["id"]
                    })

        # calloutブロックのアイコン画像
        elif block_type == "callout":
            icon = block.get("callout", {}).get("icon", {})
            if icon and icon.get("type") == "file":
                url = icon.get("file", {}).get("url")
                if url:
                    images.append({
                        "url": url,
                        "type": "notion_file",
                        "block_id": block["id"]
                    })

    return images

def sanitize_folder_name(name):
    """フォルダ名をサニタイズ"""
    # 無効な文字を置換
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    return name.strip()

def get_relative_path(image_path, md_path):
    """markdownファイルからの相対パスを計算"""
    try:
        return os.path.relpath(image_path, md_path.parent)
    except ValueError:
        return str(image_path)

def update_markdown_links(md_path, old_urls, new_paths):
    """markdownファイル内のURLを相対パスに更新"""
    if not old_urls or not new_paths:
        return

    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        modified = False
        for old_url, new_path in zip(old_urls, new_paths):
            if new_path and old_url in content:
                # S3 URLの基本部分でマッチ（パラメータ部分は変わる可能性がある）
                # URLの基本部分を抽出
                base_url_match = re.search(r'(https://prod-files-secure\.s3\.us-west-2\.amazonaws\.com/[^?]+)', old_url)
                if base_url_match:
                    base_url = base_url_match.group(1)
                    # 同じ基本URLを持つすべてのURLを置換
                    pattern = re.escape(base_url) + r'[^)\s\]"]*'
                    relative_path = get_relative_path(new_path, md_path)
                    content = re.sub(pattern, relative_path, content)
                    modified = True

        if modified:
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
    except Exception as e:
        print(f"    ⚠️ Markdown更新エラー: {e}")

    return False

def process_page(page_info, folder_path_map):
    """1ページを処理"""
    page_id = page_info["id"]
    page_title = page_info.get("title", "untitled")
    page_path = page_info.get("path", [])

    # フォルダパスを構築
    if page_path:
        folder_name = "/".join([sanitize_folder_name(p) for p in page_path])
    else:
        folder_name = sanitize_folder_name(page_title)

    # ブロックを取得
    blocks = get_page_blocks(page_id)
    images = extract_image_urls(blocks)

    if not images:
        return 0

    stats["pages_with_images"] += 1
    print(f"\n📄 {page_title} ({len(images)}画像)")

    # 画像保存先フォルダ
    image_folder = NOTION_IMAGES_DIR / folder_name

    # 対応するmarkdownファイルを探す
    md_path = None
    for candidate_path in [
        NOTION_DOCS_DIR / folder_name / "index.md",
        NOTION_DOCS_DIR / sanitize_folder_name(page_title) / "index.md"
    ]:
        if candidate_path.exists():
            md_path = candidate_path
            break

    downloaded_count = 0
    old_urls = []
    new_paths = []

    for i, img in enumerate(images):
        stats["total_images"] += 1
        url = img["url"]

        # ファイル名生成
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        ext = get_file_extension(url)
        filename = f"image_{i+1:03d}_{url_hash}{ext}"
        save_path = image_folder / filename

        print(f"  📥 {i+1}/{len(images)}: {filename}")

        actual_path, size = download_image(url, save_path)

        if actual_path:
            downloaded_count += 1
            stats["downloaded"] += 1
            stats["total_bytes"] += size
            stats["by_folder"][folder_name]["count"] += 1
            stats["by_folder"][folder_name]["bytes"] += size

            old_urls.append(url)
            new_paths.append(actual_path)

            print(f"    ✅ {size/1024:.1f} KB")
        else:
            stats["failed"] += 1
            new_paths.append(None)
            old_urls.append(url)

        time.sleep(REQUEST_DELAY)

    # Markdownリンクを更新
    if md_path and any(new_paths):
        update_markdown_links(md_path, old_urls, new_paths)

    return downloaded_count

def format_size(bytes_size):
    """バイト数を読みやすい形式に変換"""
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
    print("Notion API 画像ダウンロードスクリプト")
    print(f"保存先: {NOTION_IMAGES_DIR}")
    print("=" * 60)

    if not NOTION_TOKEN:
        print("❌ NOTION_API_TOKEN が設定されていません")
        return

    # 構造ファイルを読み込み
    if not STRUCTURE_FILE.exists():
        print(f"❌ 構造ファイルが見つかりません: {STRUCTURE_FILE}")
        return

    with open(STRUCTURE_FILE, 'r', encoding='utf-8') as f:
        structure = json.load(f)

    # ページ一覧を取得（データベースは除く）
    pages = [node for node in structure.get("nodes", []) if node.get("type") == "page"]
    stats["total_pages"] = len(pages)

    print(f"\n📁 処理対象: {len(pages)} ページ")
    print("=" * 60)

    # 画像フォルダ作成
    NOTION_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    # フォルダパスマップを構築
    folder_path_map = {}
    for page in pages:
        page_id = page["id"]
        path = page.get("path", [])
        folder_path_map[page_id] = path

    # 各ページを処理
    for i, page in enumerate(pages):
        print(f"\n[{i+1}/{len(pages)}] 処理中...", end="", flush=True)
        try:
            process_page(page, folder_path_map)
        except Exception as e:
            print(f"\n  ❌ エラー: {str(e)[:100]}")

        # 進捗表示（100ページごと）
        if (i + 1) % 100 == 0:
            print(f"\n--- 進捗: {i+1}/{len(pages)} ページ完了, {stats['downloaded']}画像, {format_size(stats['total_bytes'])} ---")

    # レポート
    print("\n" + "=" * 60)
    print("📊 ダウンロード結果レポート")
    print("=" * 60)
    print(f"\n処理ページ数: {stats['total_pages']}")
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
    report_path = NOTION_IMAGES_DIR.parent / "image_download_report.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("Notion画像ダウンロードレポート\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"保存先: {NOTION_IMAGES_DIR}\n")
        f.write(f"処理ページ数: {stats['total_pages']}\n")
        f.write(f"画像を含むページ: {stats['pages_with_images']}\n")
        f.write(f"合計画像数: {stats['total_images']}\n")
        f.write(f"ダウンロード成功: {stats['downloaded']}\n")
        f.write(f"ダウンロード失敗: {stats['failed']}\n")
        f.write(f"合計サイズ: {format_size(stats['total_bytes'])}\n\n")
        f.write("フォルダ別サイズ:\n")
        for folder, data in sorted(stats["by_folder"].items(), key=lambda x: x[1]["bytes"], reverse=True):
            f.write(f"  {folder}: {data['count']}画像, {format_size(data['bytes'])}\n")

    print(f"\n📄 レポート保存: {report_path}")
    print("\n完了!")

if __name__ == "__main__":
    main()
