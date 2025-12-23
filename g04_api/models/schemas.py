"""
Pydantic スキーマ定義
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """検索リクエスト"""
    query: str = Field(..., min_length=5, description="検索クエリ（5文字以上）")
    source: Optional[str] = Field(None, description="ソース指定: notion, drive, slack")
    after: Optional[str] = Field(None, description="この日付以降 (YYYY-MM-DD)")
    before: Optional[str] = Field(None, description="この日付以前 (YYYY-MM-DD)")
    top_k: int = Field(3, ge=1, le=10, description="取得件数")
    user_id: Optional[str] = Field(None, description="Discord User ID（権限チェック用）")


class SourceDocument(BaseModel):
    """出典ドキュメント"""
    source_type: str  # notion, drive, slack
    title: str
    url: str
    relevance_score: float  # 0.0 - 1.0
    snippet: Optional[str] = None
    created_at: Optional[str] = None


class SearchResponse(BaseModel):
    """検索レスポンス"""
    query: str
    answer: str
    confidence: float  # 0.0 - 1.0 (信頼度)
    sources: list[SourceDocument]
    search_time: float  # 検索時間（秒）
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class ErrorResponse(BaseModel):
    """エラーレスポンス"""
    error_code: str
    message: str
    details: Optional[str] = None


class StatsResponse(BaseModel):
    """統計情報レスポンス"""
    total_searches: int
    today_searches: int
    avg_response_time: float
    avg_confidence: float
    popular_keywords: list[dict]
    user_search_count: Optional[int] = None


class FeedbackRequest(BaseModel):
    """フィードバックリクエスト"""
    search_id: str
    user_id: str
    feedback_type: str  # helpful, not_helpful, saved
    comment: Optional[str] = None
