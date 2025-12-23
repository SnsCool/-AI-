"""
検索API ルーター
"""

import time
from fastapi import APIRouter, HTTPException

from models.schemas import (
    SearchRequest,
    SearchResponse,
    StatsResponse,
    FeedbackRequest,
    ErrorResponse,
)
from services.search_service import SearchService

router = APIRouter()
search_service = SearchService()


@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    ナレッジ検索

    Notion、Google Drive、Slackを横断検索し、
    AIが質問に対する回答を生成します。
    """
    start_time = time.time()

    try:
        # クエリの長さチェック
        if len(request.query.strip()) < 5:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "QUERY_TOO_SHORT",
                    "message": "検索クエリが短すぎます。5文字以上入力してください。"
                }
            )

        # 検索実行
        result = await search_service.search(
            query=request.query,
            source=request.source,
            after=request.after,
            before=request.before,
            top_k=request.top_k,
            user_id=request.user_id
        )

        search_time = time.time() - start_time
        result.search_time = round(search_time, 2)

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "SEARCH_ERROR",
                "message": "検索中にエラーが発生しました",
                "details": str(e)
            }
        )


@router.get("/stats", response_model=StatsResponse)
async def get_stats(user_id: str = None):
    """統計情報を取得"""
    try:
        return await search_service.get_stats(user_id)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "STATS_ERROR",
                "message": "統計情報の取得に失敗しました",
                "details": str(e)
            }
        )


@router.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """フィードバックを送信"""
    try:
        await search_service.save_feedback(request)
        return {"status": "ok", "message": "フィードバックを記録しました"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "FEEDBACK_ERROR",
                "message": "フィードバックの保存に失敗しました",
                "details": str(e)
            }
        )


@router.get("/history")
async def get_history(user_id: str, limit: int = 10):
    """ユーザーの検索履歴を取得"""
    try:
        return await search_service.get_history(user_id, limit)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "HISTORY_ERROR",
                "message": "検索履歴の取得に失敗しました",
                "details": str(e)
            }
        )


@router.delete("/history")
async def clear_history(user_id: str):
    """ユーザーの検索履歴をクリア"""
    try:
        await search_service.clear_history(user_id)
        return {"status": "ok", "message": "検索履歴をクリアしました"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "CLEAR_HISTORY_ERROR",
                "message": "検索履歴のクリアに失敗しました",
                "details": str(e)
            }
        )
