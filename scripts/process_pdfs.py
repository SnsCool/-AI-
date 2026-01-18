#!/usr/bin/env python3
"""
PDF テキスト抽出スクリプト (Feature C)
- notion_docs/ 内のMarkdownファイルからPDF URLを抽出
- PDFをダウンロードして元ファイルと同じ場所に保存
- テキスト抽出して元ファイルと同じ場所に保存
"""

import os
import re
import json
import hashlib
import ssl
import urllib.request
from pathlib import Path
from urllib.parse import urlparse, unquote
from datetime import datetime

ssl._create_default_https_context = ssl._create_unverified_context

BASE_DIR = Path(__file__).parent.parent
NOTION_DOCS_DIR = BASE_DIR / "notion_docs"

stats = {
    "files_scanned": 0,
    "pdfs_found": 0,
    "pdfs_downloaded": 0,
    "texts_extracted": 0,
    "errors": []
}


def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}", flush=True)


def get_url_hash(url):
    return hashlib.md5(url.encode()).hexdigest()[:12]


def extract_pdf_urls_from_markdown(content):
    pdf_urls = []
    # パターン1: [PDF: URL](URL) 形式
    pattern1 = r"\[PDF:\s*(https?://[^\]]+)\]"
    matches1 = re.findall(pattern1, content)
    pdf_urls.extend(matches1)
    # パターン2: .pdf で終わるURL
    pattern2 = r"(https?://[^\s\)\]]+\.pdf[^\s\)\]]*)"
    matches2 = re.findall(pattern2, content, re.IGNORECASE)
    pdf_urls.extend(matches2)
    # パターン3: Markdown形式のリンク
    pattern3 = r"\[[^\]]*\]\((https?://[^\)]+\.pdf[^\)]*)\)"
    matches3 = re.findall(pattern3, content, re.IGNORECASE)
    pdf_urls.extend(matches3)
    # 重複除去
    seen = set()
    unique_urls = []
    for url in pdf_urls:
        base_url = url.split("?")[0] if "?" in url else url
        if base_url not in seen:
            seen.add(base_url)
            unique_urls.append(url)
    return unique_urls


def download_pdf(url, save_dir):
    """PDFをダウンロードして元ファイルと同じ場所に保存"""
    try:
        url_hash = get_url_hash(url)
        filename = f"pdf_{url_hash}.pdf"
        filepath = save_dir / filename
        if filepath.exists() and filepath.stat().st_size > 0:
            log(f"  既存: {filename}")
            return str(filepath), filename, False
        log(f"  ダウンロード中: {url[:80]}...")
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0")
        with urllib.request.urlopen(req, timeout=120) as response:
            with open(filepath, "wb") as f:
                f.write(response.read())
        log(f"  完了: {filename} ({filepath.stat().st_size / 1024:.1f} KB)")
        return str(filepath), filename, True
    except Exception as e:
        stats["errors"].append(f"Download error: {e}")
        log(f"  ダウンロード失敗: {e}", "ERROR")
        return None, None, False


def extract_text_pypdf2(filepath):
    """PyPDF2でテキスト抽出"""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(filepath)
        text = ""
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text += f"\n--- Page {i+1} ---\n"
                text += page_text
        return text.strip() if text.strip() else None
    except ImportError:
        return None
    except Exception as e:
        log(f"  PyPDF2 error: {e}", "WARN")
        return None


def extract_text_pdfplumber(filepath):
    """pdfplumberでテキスト抽出"""
    try:
        import pdfplumber
        text = ""
        with pdfplumber.open(filepath) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n--- Page {i+1} ---\n"
                    text += page_text
        return text.strip() if text.strip() else None
    except ImportError:
        return None
    except Exception as e:
        log(f"  pdfplumber error: {e}", "WARN")
        return None


def extract_pdf_text(filepath):
    """PDFからテキスト抽出（複数ライブラリ対応）"""
    text = extract_text_pypdf2(filepath)
    if text:
        return text
    text = extract_text_pdfplumber(filepath)
    if text:
        return text
    return None


def save_pdf_text(text, pdf_filename, save_dir, source_md_file):
    """抽出テキストを元ファイルと同じ場所に保存"""
    base_name = Path(pdf_filename).stem
    text_path = save_dir / f"{base_name}_text.txt"
    header = f"""# PDF抽出テキスト

**PDFファイル**: {pdf_filename}
**参照元**: {source_md_file}
**抽出日時**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

"""
    with open(text_path, "w", encoding="utf-8") as f:
        f.write(header + text)
    log(f"  テキスト保存: {text_path.name}")
    return text_path


def process_markdown_file(md_path):
    """Markdownファイルを処理"""
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
        pdf_urls = extract_pdf_urls_from_markdown(content)
        if not pdf_urls:
            return 0

        # 元ファイルと同じディレクトリに保存
        save_dir = md_path.parent
        relative_path = md_path.relative_to(NOTION_DOCS_DIR)
        log(f"PDF {len(pdf_urls)}件: {relative_path}")

        processed = 0
        for url in pdf_urls:
            stats["pdfs_found"] += 1
            filepath, filename, is_new = download_pdf(url, save_dir)
            if filepath:
                if is_new:
                    stats["pdfs_downloaded"] += 1
                base_name = Path(filename).stem
                text_path = save_dir / f"{base_name}_text.txt"
                if text_path.exists():
                    log(f"  テキスト既存: {base_name}_text.txt")
                else:
                    text = extract_pdf_text(filepath)
                    if text:
                        save_pdf_text(text, filename, save_dir, str(relative_path))
                        stats["texts_extracted"] += 1
                    else:
                        log(f"  テキスト抽出失敗（ライブラリ未インストール?）", "WARN")
                processed += 1
        return processed
    except Exception as e:
        stats["errors"].append(f"Error processing {md_path}: {e}")
        return 0


def main():
    print("=" * 60)
    print("PDFテキスト抽出スクリプト (Feature C)")
    print("=" * 60)
    log(f"スキャン: {NOTION_DOCS_DIR}")
    md_files = list(NOTION_DOCS_DIR.rglob("*.md"))
    log(f"Markdownファイル: {len(md_files)}件")
    for md_file in md_files:
        stats["files_scanned"] += 1
        process_markdown_file(md_file)
    print("=" * 60)
    print("処理完了")
    print(f"  スキャンファイル: {stats['files_scanned']}")
    print(f"  発見PDF: {stats['pdfs_found']}")
    print(f"  ダウンロード: {stats['pdfs_downloaded']}")
    print(f"  テキスト抽出: {stats['texts_extracted']}")
    if stats["errors"]:
        print(f"  エラー: {len(stats['errors'])}")
    print("=" * 60)


if __name__ == "__main__":
    main()
