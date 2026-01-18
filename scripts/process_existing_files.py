#!/usr/bin/env python3
"""
既存のダウンロード済みファイルを処理するスクリプト
- 動画: Gemini APIで文字起こし
- PDF: PyPDF2でテキスト抽出
"""

import os
import re
import time
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
NOTION_DOCS_DIR = BASE_DIR / "notion_docs"


def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}", flush=True)


def transcribe_video(video_path):
    """動画をGemini APIで文字起こし"""
    try:
        import google.generativeai as genai
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            log("  GEMINI_API_KEY未設定", "WARN")
            return None

        genai.configure(api_key=api_key)
        log(f"  Geminiにアップロード中...")
        uploaded_file = genai.upload_file(str(video_path))

        while uploaded_file.state.name == "PROCESSING":
            time.sleep(2)
            uploaded_file = genai.get_file(uploaded_file.name)

        if uploaded_file.state.name == "FAILED":
            log("  アップロード失敗", "ERROR")
            return None

        log(f"  文字起こし中...")
        model = genai.GenerativeModel("gemini-2.0-flash")
        prompt = """この動画の内容を文字起こししてください。
以下の形式でタイムスタンプ付きで出力してください：
[MM:SS] 発言内容
例：
[00:00] こんにちは、今日は...
[00:15] それでは始めましょう
日本語で出力してください。"""

        response = model.generate_content([prompt, uploaded_file])

        try:
            genai.delete_file(uploaded_file.name)
        except:
            pass

        return response.text
    except Exception as e:
        log(f"  文字起こしエラー: {e}", "ERROR")
        return None


def extract_pdf_text(pdf_path):
    """PDFからテキスト抽出"""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(str(pdf_path))
        text = ""
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text += f"\n--- Page {i+1} ---\n"
                text += page_text
        return text.strip() if text.strip() else None
    except Exception as e:
        log(f"  PDF抽出エラー: {e}", "ERROR")
        return None


def process_videos():
    """ダウンロード済み動画を処理"""
    log("=" * 60)
    log("動画文字起こし処理")
    log("=" * 60)

    video_files = list(NOTION_DOCS_DIR.rglob("video_*.mp4")) + list(NOTION_DOCS_DIR.rglob("video_*.mov"))
    log(f"動画ファイル数: {len(video_files)}")

    processed = 0
    for video_path in video_files:
        transcript_path = video_path.parent / f"{video_path.stem}_transcript.txt"

        if transcript_path.exists():
            log(f"スキップ（既存）: {video_path.name}")
            continue

        log(f"処理中: {video_path.relative_to(NOTION_DOCS_DIR)}")

        # ファイルサイズ確認
        size_mb = video_path.stat().st_size / 1024 / 1024
        if size_mb < 0.01:
            log(f"  スキップ（ファイルが小さすぎる: {size_mb:.2f}MB）", "WARN")
            continue

        transcript = transcribe_video(video_path)

        if transcript:
            header = f"""# 動画文字起こし

**動画ファイル**: {video_path.name}
**参照元**: {video_path.parent.relative_to(NOTION_DOCS_DIR)}
**作成日時**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

"""
            with open(transcript_path, "w", encoding="utf-8") as f:
                f.write(header + transcript)
            log(f"  保存完了: {transcript_path.name}")
            processed += 1

    log(f"文字起こし完了: {processed}件")
    return processed


def process_pdfs():
    """ダウンロード済みPDFを処理"""
    log("=" * 60)
    log("PDFテキスト抽出処理")
    log("=" * 60)

    pdf_files = list(NOTION_DOCS_DIR.rglob("pdf_*.pdf"))
    log(f"PDFファイル数: {len(pdf_files)}")

    processed = 0
    for pdf_path in pdf_files:
        text_path = pdf_path.parent / f"{pdf_path.stem}_text.txt"

        if text_path.exists():
            log(f"スキップ（既存）: {pdf_path.name}")
            continue

        log(f"処理中: {pdf_path.relative_to(NOTION_DOCS_DIR)}")

        text = extract_pdf_text(pdf_path)

        if text:
            header = f"""# PDF抽出テキスト

**PDFファイル**: {pdf_path.name}
**参照元**: {pdf_path.parent.relative_to(NOTION_DOCS_DIR)}
**抽出日時**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

"""
            with open(text_path, "w", encoding="utf-8") as f:
                f.write(header + text)
            log(f"  保存完了: {text_path.name}")
            processed += 1
        else:
            log(f"  テキスト抽出失敗", "WARN")

    log(f"テキスト抽出完了: {processed}件")
    return processed


def main():
    print("=" * 60)
    print("既存ファイル処理スクリプト")
    print("=" * 60)

    # PDF処理（Gemini不要なので先に実行）
    pdf_count = process_pdfs()

    # 動画処理（Gemini APIが必要）
    video_count = process_videos()

    print("=" * 60)
    print("処理完了")
    print(f"  動画文字起こし: {video_count}件")
    print(f"  PDFテキスト抽出: {pdf_count}件")
    print("=" * 60)


if __name__ == "__main__":
    main()
