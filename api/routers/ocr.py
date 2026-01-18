"""
PDF OCR API
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import tempfile
import os

from services.ocr_service import OCRService

router = APIRouter()
service = OCRService()


class OCRResponse(BaseModel):
    success: bool
    text: Optional[str] = None
    output_path: Optional[str] = None
    pages: Optional[int] = None
    needs_ocr: Optional[bool] = None
    error: Optional[str] = None


@router.post("/pdf", response_model=OCRResponse)
async def ocr_pdf(file: UploadFile = File(...)):
    """
    PDFをOCRでテキスト化

    - **file**: PDFファイル
    - 画像ベースのPDFにも対応（Gemini API使用）
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="PDFファイルを指定してください")

    # 一時ファイルに保存
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # まずテキスト抽出を試みる
        result = service.extract_pdf_text(tmp_path)

        if result.get("success"):
            return OCRResponse(**result)

        # テキストが抽出できない場合はOCR
        if result.get("needs_ocr"):
            result = service.ocr_pdf(tmp_path)

        return OCRResponse(**result)

    finally:
        # 一時ファイルを削除
        try:
            os.unlink(tmp_path)
        except:
            pass


@router.post("/pdf/force-ocr", response_model=OCRResponse)
async def force_ocr_pdf(file: UploadFile = File(...)):
    """
    PDFを強制的にOCR（画像として処理）

    - **file**: PDFファイル
    - テキスト抽出可能なPDFでも画像としてOCR処理
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="PDFファイルを指定してください")

    # 一時ファイルに保存
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = service.ocr_pdf(tmp_path)
        return OCRResponse(**result)

    finally:
        # 一時ファイルを削除
        try:
            os.unlink(tmp_path)
        except:
            pass
