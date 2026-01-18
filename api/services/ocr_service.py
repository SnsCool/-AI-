"""
PDF OCR サービス
- PyMuPDFでPDFを画像化
- Gemini APIでOCR
"""

import os
import time
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple

# PDF処理
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

# Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class OCRService:
    def __init__(self):
        self.gemini_api_key = os.environ.get("GEMINI_API_KEY")
        if self.gemini_api_key and GEMINI_AVAILABLE:
            genai.configure(api_key=self.gemini_api_key)

    def ocr_pdf(self, pdf_path: str, output_path: Optional[str] = None) -> dict:
        """PDFをOCRでテキスト化"""
        if not PYMUPDF_AVAILABLE:
            return {"success": False, "error": "PyMuPDF がインストールされていません"}

        if not GEMINI_AVAILABLE:
            return {"success": False, "error": "google-generativeai がインストールされていません"}

        if not self.gemini_api_key:
            return {"success": False, "error": "GEMINI_API_KEY が設定されていません"}

        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            return {"success": False, "error": f"ファイルが見つかりません: {pdf_path}"}

        try:
            # PDFを画像に変換
            images = self._pdf_to_images(pdf_path)

            if not images:
                return {"success": False, "error": "PDFから画像を抽出できませんでした"}

            # 各ページをOCR
            model = genai.GenerativeModel("gemini-2.0-flash")
            all_text = []

            for page_num, img_path in images:
                try:
                    # 画像をアップロード
                    uploaded_file = genai.upload_file(img_path)

                    # 処理完了を待つ
                    while uploaded_file.state.name == "PROCESSING":
                        time.sleep(2)
                        uploaded_file = genai.get_file(uploaded_file.name)

                    if uploaded_file.state.name == "FAILED":
                        all_text.append(f"\n--- ページ {page_num} ---\n(OCR失敗)\n")
                        continue

                    # OCR実行
                    prompt = """この画像のテキストを読み取ってください。
レイアウトをできるだけ保持し、日本語で出力してください。
表がある場合は、Markdown形式の表として出力してください。"""

                    response = model.generate_content([prompt, uploaded_file])
                    page_text = response.text

                    all_text.append(f"\n--- ページ {page_num} ---\n{page_text}\n")

                    # クリーンアップ
                    try:
                        genai.delete_file(uploaded_file.name)
                        os.unlink(img_path)
                    except:
                        pass

                except Exception as e:
                    all_text.append(f"\n--- ページ {page_num} ---\n(エラー: {e})\n")

            full_text = "".join(all_text)

            # 保存
            if output_path:
                output_path = Path(output_path)
            else:
                output_path = pdf_path.parent / f"{pdf_path.stem}_text.txt"

            header = f"""# PDF テキスト抽出

**PDFファイル**: {pdf_path.name}
**ファイルサイズ**: {pdf_path.stat().st_size / 1024 / 1024:.2f} MB
**ページ数**: {len(images)}
**抽出日時**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**処理方法**: Gemini API OCR

---

"""
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(header + full_text)

            return {
                "success": True,
                "text": full_text,
                "output_path": str(output_path),
                "pages": len(images),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def extract_pdf_text(self, pdf_path: str) -> dict:
        """PDFからテキストを直接抽出（OCRなし）"""
        if not PYMUPDF_AVAILABLE:
            return {"success": False, "error": "PyMuPDF がインストールされていません"}

        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            return {"success": False, "error": f"ファイルが見つかりません: {pdf_path}"}

        try:
            doc = fitz.open(str(pdf_path))
            all_text = []

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                if text.strip():
                    all_text.append(f"\n--- ページ {page_num + 1} ---\n{text}\n")

            doc.close()

            if not all_text:
                return {
                    "success": False,
                    "error": "テキストが抽出できませんでした（画像ベースPDFの可能性があります）",
                    "needs_ocr": True,
                }

            return {
                "success": True,
                "text": "".join(all_text),
                "pages": len(all_text),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _pdf_to_images(self, pdf_path: Path) -> List[Tuple[int, str]]:
        """PDFを画像に変換"""
        doc = fitz.open(str(pdf_path))
        images = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            # 2倍の解像度で描画
            mat = fitz.Matrix(2, 2)
            pix = page.get_pixmap(matrix=mat)

            img_path = tempfile.mktemp(suffix=f"_page_{page_num + 1}.png")
            pix.save(img_path)
            images.append((page_num + 1, img_path))

        doc.close()
        return images
