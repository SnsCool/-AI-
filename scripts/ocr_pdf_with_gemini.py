#!/usr/bin/env python3
"""
画像ベースのPDFをGemini APIでOCR処理するスクリプト
- PDFを画像に変換
- Gemini APIで各ページのテキストを抽出
"""

import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime

# PDF処理
try:
    import fitz  # PyMuPDF
except ImportError:
    print("PyMuPDFが必要です: pip install PyMuPDF")
    sys.exit(1)

# Gemini API
try:
    import google.generativeai as genai
except ImportError:
    print("google-generativeaiが必要です: pip install google-generativeai")
    sys.exit(1)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")


def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}", flush=True)


def pdf_to_images(pdf_path):
    """PDFを画像に変換"""
    doc = fitz.open(pdf_path)
    images = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        # 高解像度で画像化
        mat = fitz.Matrix(2, 2)  # 2倍の解像度
        pix = page.get_pixmap(matrix=mat)

        # 一時ファイルに保存
        img_path = tempfile.mktemp(suffix=f"_page_{page_num + 1}.png")
        pix.save(img_path)
        images.append((page_num + 1, img_path))
        log(f"  ページ {page_num + 1}/{len(doc)} を画像化")

    doc.close()
    return images


def ocr_image_with_gemini(image_path, page_num):
    """Gemini APIで画像からテキストを抽出"""
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")

        # 画像をアップロード
        uploaded_file = genai.upload_file(image_path)

        prompt = """この画像に含まれるテキストを全て抽出してください。
- 日本語と英語の両方を正確に読み取ってください
- レイアウトをできるだけ保持してください
- 表がある場合は表形式で出力してください
- 図やグラフの説明も含めてください"""

        response = model.generate_content([prompt, uploaded_file])

        # アップロードしたファイルを削除
        try:
            genai.delete_file(uploaded_file.name)
        except:
            pass

        return response.text
    except Exception as e:
        log(f"  ページ {page_num} OCRエラー: {e}", "ERROR")
        return None


def process_pdf(pdf_path, output_path=None):
    """PDFをOCR処理"""
    pdf_path = Path(pdf_path)

    if output_path is None:
        output_path = pdf_path.parent / f"{pdf_path.stem}_text.txt"

    log(f"処理開始: {pdf_path.name}")
    log(f"出力先: {output_path}")

    # PDFを画像に変換
    log("PDFを画像に変換中...")
    images = pdf_to_images(pdf_path)
    log(f"  {len(images)}ページを画像化完了")

    # 各ページをOCR処理
    log("OCR処理中...")
    all_text = []

    for page_num, img_path in images:
        log(f"  ページ {page_num}/{len(images)} をOCR処理中...")
        text = ocr_image_with_gemini(img_path, page_num)

        if text:
            all_text.append(f"\n--- Page {page_num} ---\n")
            all_text.append(text)

        # 一時ファイルを削除
        try:
            os.remove(img_path)
        except:
            pass

    # 結果を保存
    if all_text:
        header = f"""# PDF OCR抽出テキスト

**PDFファイル**: {pdf_path.name}
**ページ数**: {len(images)}
**抽出日時**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**処理方法**: Gemini API OCR

---
"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(header + "\n".join(all_text))

        log(f"保存完了: {output_path}")
        return True
    else:
        log("テキスト抽出失敗", "ERROR")
        return False


def main():
    if not GEMINI_API_KEY:
        log("GEMINI_API_KEY が設定されていません", "ERROR")
        log("export GEMINI_API_KEY=your-api-key を実行してください")
        return

    genai.configure(api_key=GEMINI_API_KEY)

    # 処理対象のPDF
    pdf_path = "/Users/hatakiyoto/-AI-egent-libvela/notion_docs/ダイエット事業/その他メモ/ポータル構築/pdf_87feaffa3e2a.pdf"

    print("=" * 60)
    print("画像PDF OCR処理スクリプト")
    print("=" * 60)

    process_pdf(pdf_path)

    print("=" * 60)
    print("処理完了")
    print("=" * 60)


if __name__ == "__main__":
    main()
