#!/usr/bin/env python3
"""
Notion画像ダウンロードスクリプト
- notion_docs内のmarkdownファイルからS3画像URLを抽出
- 画像をローカルにダウンロード
- markdownのリンクを相対パスに書き換え
"""

import os
import re
import requests
import hashlib
import time
from pathlib import Path
from urllib.parse import urlparse, unquote
from collections import defaultdict

# 設定
NOTION_DOCS_DIR = "/Users/hatakiyoto/-AI-egent-libvela/notion_docs"
S3_PATTERN = r'https://prod-files-secure\.s3\.us-west-2\.amazonaws\.com/[^)\s\]"]+'
REQUEST_DELAY = 0.2  # レート制限対策

# 統計
stats = {
    "total_images": 0,
    "downloaded": 0,
    "failed": 0,
    "skipped": 0,
    "total_bytes": 0,
    "by_folder": defaultdict(lambda: {"count": 0, "bytes": 0})
}

def get_file_extension(url, content_type=None):
    """URLまたはContent-Typeから拡張子を取得"""
    # URLのパスから拡張子を抽出
    parsed = urlparse(url)
    path = unquote(parsed.path)

    # パスから拡張子を取得
    ext_match = re.search(r'\.([a-zA-Z0-9]+)(?:\?|$)', path)
    if ext_match:
        ext = ext_match.group(1).lower()
        if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp', 'ico']:
            return f".{ext}"

    # Content-Typeから判断
    if content_type:
        type_map = {
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp',
            'image/svg+xml': '.svg',
            'image/bmp': '.bmp',
            'image/x-icon': '.ico',
        }
        for mime, extension in type_map.items():
            if mime in content_type:
                return extension

    return '.jpg'  # デフォルト

def download_image(url, save_path):
    """画像をダウンロード"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # 拡張子を確認・修正
        content_type = response.headers.get('Content-Type', '')
        expected_ext = get_file_extension(url, content_type)

        # 保存パスの拡張子を修正
        current_ext = save_path.suffix.lower()
        if current_ext != expected_ext:
            save_path = save_path.with_suffix(expected_ext)

        # ディレクトリ作成
        save_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存
        with open(save_path, 'wb') as f:
            f.write(response.content)

        return save_path, len(response.content)

    except Exception as e:
        print(f"  ❌ ダウンロード失敗: {e}")
        return None, 0

def process_markdown_file(md_path):
    """Markdownファイル内の画像URLを処理"""
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # S3 URLを検索
    urls = re.findall(S3_PATTERN, content)

    if not urls:
        return 0

    folder_path = md_path.parent
    assets_dir = folder_path / "assets"
    folder_name = folder_path.name

    modified = False
    image_count = 0

    for i, url in enumerate(urls):
        stats["total_images"] += 1

        # ファイル名生成（URLのハッシュを使用）
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        ext = get_file_extension(url)
        filename = f"image_{i+1:03d}_{url_hash}{ext}"
        save_path = assets_dir / filename

        print(f"  📥 画像 {i+1}/{len(urls)}: {filename}")

        # ダウンロード
        actual_path, size = download_image(url, save_path)

        if actual_path:
            # markdownのURLを相対パスに置換
            relative_path = f"./assets/{actual_path.name}"
            content = content.replace(url, relative_path)
            modified = True
            image_count += 1

            stats["downloaded"] += 1
            stats["total_bytes"] += size
            stats["by_folder"][folder_name]["count"] += 1
            stats["by_folder"][folder_name]["bytes"] += size

            print(f"    ✅ 保存完了 ({size/1024:.1f} KB)")
        else:
            stats["failed"] += 1

        time.sleep(REQUEST_DELAY)

    # 変更があればファイルを保存
    if modified:
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(content)

    return image_count

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
    print("Notion画像ダウンロードスクリプト")
    print("=" * 60)

    # 全markdownファイルを検索
    md_files = list(Path(NOTION_DOCS_DIR).rglob("index.md"))
    print(f"\n📁 処理対象: {len(md_files)} ファイル\n")

    for i, md_path in enumerate(md_files):
        relative_path = md_path.relative_to(NOTION_DOCS_DIR)

        # S3 URLが含まれているかチェック
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if 'prod-files-secure.s3.us-west-2.amazonaws.com' in content:
            print(f"\n[{i+1}/{len(md_files)}] 📄 {relative_path.parent}")
            count = process_markdown_file(md_path)
            if count > 0:
                print(f"  → {count} 画像を処理")

    # レポート出力
    print("\n" + "=" * 60)
    print("📊 ダウンロード結果レポート")
    print("=" * 60)
    print(f"\n合計画像数: {stats['total_images']}")
    print(f"ダウンロード成功: {stats['downloaded']}")
    print(f"ダウンロード失敗: {stats['failed']}")
    print(f"\n💾 合計サイズ: {format_size(stats['total_bytes'])}")

    # フォルダ別サイズ（大きい順）
    if stats["by_folder"]:
        print("\n📁 フォルダ別サイズ（上位20件）:")
        sorted_folders = sorted(
            stats["by_folder"].items(),
            key=lambda x: x[1]["bytes"],
            reverse=True
        )[:20]

        for folder, data in sorted_folders:
            print(f"  {folder}: {data['count']}画像, {format_size(data['bytes'])}")

    # 結果をファイルに保存
    report_path = Path(NOTION_DOCS_DIR).parent / "image_download_report.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("Notion画像ダウンロードレポート\n")
        f.write("=" * 50 + "\n\n")
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
