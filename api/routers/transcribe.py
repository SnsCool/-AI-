"""
文字起こし API
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import tempfile
import os

from services.transcribe_service import TranscribeService

router = APIRouter()
service = TranscribeService()


class YouTubeRequest(BaseModel):
    video_id: str


class LoomRequest(BaseModel):
    url: str


class TranscribeResponse(BaseModel):
    success: bool
    transcript: Optional[str] = None
    video_id: Optional[str] = None
    source: Optional[str] = None
    output_path: Optional[str] = None
    error: Optional[str] = None


@router.post("/youtube", response_model=TranscribeResponse)
async def transcribe_youtube(request: YouTubeRequest):
    """
    YouTube動画の字幕を取得

    - **video_id**: YouTubeの動画ID (例: dQw4w9WgXcQ)
    """
    result = service.transcribe_youtube(request.video_id)
    return TranscribeResponse(**result)


@router.post("/loom", response_model=TranscribeResponse)
async def transcribe_loom(request: LoomRequest):
    """
    Loom動画の字幕を取得

    - **url**: LoomのシェアURL (例: https://www.loom.com/share/xxxxx)
    """
    result = service.transcribe_loom(request.url)
    return TranscribeResponse(**result)


@router.post("/video", response_model=TranscribeResponse)
async def transcribe_video(file: UploadFile = File(...)):
    """
    動画ファイルをGemini APIで文字起こし

    - **file**: 動画ファイル (mp4, webm, mov など)
    """
    # 一時ファイルに保存
    suffix = os.path.splitext(file.filename)[1] if file.filename else ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = service.transcribe_video_with_gemini(tmp_path)
        return TranscribeResponse(**result)
    finally:
        # 一時ファイルを削除
        try:
            os.unlink(tmp_path)
        except:
            pass
