"""
G04 ナレッジ検索 API

Notion、Google Drive、Slackを横断検索するFastAPI バックエンド
"""

import os
import time
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from routers import search
from services.vector_store import VectorStoreService

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    print("G04 API 起動中...")
    # 起動時の初期化処理
    yield
    # 終了時のクリーンアップ
    print("G04 API 終了")


app = FastAPI(
    title="G04 ナレッジ検索 API",
    description="社内ドキュメント横断検索API（Notion/Drive/Slack）",
    version="1.0.0",
    lifespan=lifespan
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(search.router, prefix="/api/v1", tags=["search"])


@app.get("/")
async def root():
    """ヘルスチェック"""
    return {
        "status": "ok",
        "service": "G04 Knowledge Search API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """詳細ヘルスチェック"""
    return {
        "status": "healthy",
        "timestamp": time.time()
    }
