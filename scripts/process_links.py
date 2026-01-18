#!/usr/bin/env python3
"""
リンク先コンテンツ取得スクリプト (Feature D)
- notion_docs/ 内のMarkdownファイルから外部リンク（http/https）を抽出
- Webページをスクレイピング
- テキストコンテンツを元ファイルと同じ場所に保存
"""

import os
import re
import json
import hashlib
import ssl
import urllib.request
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime
from html.parser import HTMLParser

ssl._create_default_https_context = ssl._create_unverified_context

BASE_DIR = Path(__file__).parent.parent
NOTION_DOCS_DIR = BASE_DIR / "notion_docs"

SKIP_DOMAINS = [
    "prod-files-secure.s3.us-west-2.amazonaws.com",
    "s3.us-west-2.amazonaws.com",
    "www.notion.so",
    "notion.so",
    "localhost",
    "127.0.0.1"
]

SKIP_EXTENSIONS = [
    ".pdf", ".mp4", ".mov", ".webm", ".avi", ".mkv", ".m4v",
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico",
    ".mp3", ".wav", ".ogg", ".flac",
    ".zip", ".tar", ".gz", ".rar", ".7z",
    ".exe", ".dmg", ".pkg", ".deb", ".rpm"
]

stats = {
    "files_scanned": 0,
    "links_found": 0,
    "links_scraped": 0,
    "contents_saved": 0,
    "errors": []
}


def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}", flush=True)


def get_url_hash(url):
    return hashlib.md5(url.encode()).hexdigest()[:12]


class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.skip_tags = {"script", "style", "noscript", "header", "footer", "nav", "aside"}
        self.current_skip = False
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.skip_tags:
            self.current_skip = True
            self.skip_depth += 1

    def handle_endtag(self, tag):
        if tag in self.skip_tags and self.skip_depth > 0:
            self.skip_depth -= 1
            if self.skip_depth == 0:
                self.current_skip = False

    def handle_data(self, data):
        if not self.current_skip:
            text = data.strip()
            if text:
                self.text_parts.append(text)

    def get_text(self):
        return "\n".join(self.text_parts)


def extract_links_from_markdown(content):
    links = []
    pattern1 = r'\[([^\]]*)\]\((https?://[^\)]+)\)'
    matches1 = re.findall(pattern1, content)
    for text, url in matches1:
        links.append({"text": text, "url": url})
    pattern2 = r'(?:^|\s)(https?://[^\s\)\]]+)'
    matches2 = re.findall(pattern2, content, re.MULTILINE)
    for url in matches2:
        if not any(l["url"] == url for l in links):
            links.append({"text": "", "url": url})
    filtered_links = []
    seen_urls = set()
    for link in links:
        url = link["url"]
        base_url = url.split("?")[0] if "?" in url else url
        if base_url in seen_urls:
            continue
        parsed = urlparse(url)
        if parsed.netloc in SKIP_DOMAINS:
            continue
        path_lower = parsed.path.lower()
        if any(path_lower.endswith(ext) for ext in SKIP_EXTENSIONS):
            continue
        seen_urls.add(base_url)
        filtered_links.append(link)
    return filtered_links


def scrape_webpage(url, timeout=30):
    """Webページをスクレイピング"""
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)")
        req.add_header("Accept", "text/html,*/*")
        with urllib.request.urlopen(req, timeout=timeout) as response:
            content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type and "text/plain" not in content_type:
                return None, f"Non-HTML content: {content_type}"
            html = response.read()
            encoding = "utf-8"
            match = re.search(r"charset=([^\s;]+)", content_type)
            if match:
                encoding = match.group(1)
            try:
                html_text = html.decode(encoding)
            except:
                html_text = html.decode("utf-8", errors="ignore")
            title_match = re.search(r"<title[^>]*>([^<]+)</title>", html_text, re.IGNORECASE)
            title = title_match.group(1).strip() if title_match else ""
            parser = HTMLTextExtractor()
            parser.feed(html_text)
            return {"title": title, "text": parser.get_text(), "url": url}, None
    except Exception as e:
        return None, str(e)


def save_link_content(content_data, link_text, save_dir, source_md_file):
    """スクレイピング結果を元ファイルと同じ場所に保存"""
    url_hash = get_url_hash(content_data["url"])
    filename = f"link_{url_hash}_content.txt"
    filepath = save_dir / filename

    text_content = content_data.get("text", "")
    if len(text_content) > 10000:
        text_content = text_content[:10000] + "\n\n[... 以下省略 ...]"

    output = f"""# リンク先コンテンツ

**URL**: {content_data["url"]}
**タイトル**: {content_data.get("title", "N/A")}
**リンクテキスト**: {link_text}
**参照元**: {source_md_file}
**取得日時**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## コンテンツ

{text_content}
"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(output)

    stats["contents_saved"] += 1
    log(f"  コンテンツ保存: {filename}")
    return filename


def process_markdown_file(md_file):
    """Markdownファイルを処理"""
    try:
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        stats["errors"].append(f"Read error {md_file}: {e}")
        return []

    links = extract_links_from_markdown(content)
    if not links:
        return []

    # 元ファイルと同じディレクトリに保存
    save_dir = md_file.parent
    relative_path = md_file.relative_to(NOTION_DOCS_DIR)
    stats["links_found"] += len(links)
    log(f"リンク {len(links)}件: {relative_path}")

    results = []
    for link in links:
        url = link["url"]
        url_hash = get_url_hash(url)
        output_file = save_dir / f"link_{url_hash}_content.txt"

        if output_file.exists():
            log(f"  既存: link_{url_hash}_content.txt")
            continue

        log(f"  スクレイピング: {url[:60]}...")
        content_data, error = scrape_webpage(url)

        if error:
            stats["errors"].append(f"Scrape error {url}: {error}")
            continue

        if content_data:
            stats["links_scraped"] += 1
            filename = save_link_content(content_data, link["text"], save_dir, str(relative_path))
            results.append({
                "url": url,
                "title": content_data.get("title", ""),
                "link_text": link["text"],
                "source_file": str(md_file),
                "output_file": filename
            })

    return results


def main():
    print("=" * 60)
    print("リンク先コンテンツ取得スクリプト (Feature D)")
    print("=" * 60)

    if not NOTION_DOCS_DIR.exists():
        log(f"エラー: {NOTION_DOCS_DIR} が存在しません", "ERROR")
        return

    md_files = list(NOTION_DOCS_DIR.rglob("*.md"))
    log(f"Markdownファイル: {len(md_files)}件")

    for md_file in md_files:
        stats["files_scanned"] += 1
        process_markdown_file(md_file)

    print("=" * 60)
    print("処理完了")
    print(f"  スキャンファイル: {stats['files_scanned']}")
    print(f"  発見リンク: {stats['links_found']}")
    print(f"  スクレイピング成功: {stats['links_scraped']}")
    print(f"  保存コンテンツ: {stats['contents_saved']}")
    if stats["errors"]:
        print(f"  エラー: {len(stats['errors'])}")
    print("=" * 60)


if __name__ == "__main__":
    main()
