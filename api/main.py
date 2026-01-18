"""
FastAPI バックエンド
- 動画文字起こし
- PDF OCR
- ドキュメント管理
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from routers import transcribe, ocr, documents


@asynccontextmanager
async def lifespan(app: FastAPI):
    """起動時・終了時の処理"""
    print("🚀 API サーバー起動")
    yield
    print("👋 API サーバー終了")


app = FastAPI(
    title="ナレッジベース API",
    description="動画文字起こし、PDF OCR、ドキュメント管理を行うAPI",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS設定（Next.jsからアクセス可能にする）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーターを登録
app.include_router(transcribe.router, prefix="/api/transcribe", tags=["文字起こし"])
app.include_router(ocr.router, prefix="/api/ocr", tags=["PDF OCR"])
app.include_router(documents.router, prefix="/api/documents", tags=["ドキュメント"])


@app.get("/")
async def root():
    """ヘルスチェック"""
    return {
        "status": "ok",
        "message": "ナレッジベース API",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """ヘルスチェック"""
    return {"status": "healthy"}
