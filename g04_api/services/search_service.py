"""
検索サービス - メインの検索ロジック
"""

import os
import uuid
from datetime import datetime
from typing import Optional

from models.schemas import (
    SearchResponse,
    SourceDocument,
    StatsResponse,
    FeedbackRequest,
)
from .llm import LLMService
from .notion import NotionService
from .drive import DriveService
from .slack import SlackService


class SearchService:
    """ナレッジ検索サービス"""

    def __init__(self):
        self.llm = LLMService()
        self.notion = NotionService()
        self.drive = DriveService()
        self.slack = SlackService()

        # インメモリストレージ（本番ではSupabase等を使用）
        self._search_logs = []
        self._feedbacks = []

    async def search(
        self,
        query: str,
        source: Optional[str] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
        top_k: int = 3,
        user_id: Optional[str] = None
    ) -> SearchResponse:
        """
        ナレッジ検索を実行

        1. Notion + Google Driveから関連ドキュメントを検索
        2. PDF/画像はGeminiで解析
        3. LLMで回答を生成
        4. ナレッジがない場合は一般知識で回答
        """
        search_id = str(uuid.uuid4())
        documents = []

        # ソースに応じて検索（並列で実行）
        if source is None or source == "notion":
            notion_docs = await self._search_notion(query, top_k)
            documents.extend(notion_docs)

        if source is None or source == "drive":
            drive_docs = await self._search_drive(query, top_k)
            documents.extend(drive_docs)

        # ドキュメントが見つかった場合：ナレッジベースで回答
        if documents:
            context = self._build_context(documents)
            answer, confidence = await self.llm.generate_answer(query, context)

            sources = [
                SourceDocument(
                    source_type=doc["source_type"],
                    title=doc["title"],
                    url=doc["url"],
                    relevance_score=doc.get("score", 0.8),
                    snippet=doc.get("snippet"),
                    created_at=doc.get("created_at")
                )
                for doc in documents
            ]
        else:
            # ドキュメントが見つからない場合：回答なし
            answer = "申し訳ございません。関連するナレッジが見つかりませんでした。\n\n検索対象：Notion、Google Drive\n\n別のキーワードでお試しください。"
            confidence = 0.0
            sources = []

        # 検索ログを保存
        self._save_search_log(
            search_id=search_id,
            user_id=user_id,
            query=query,
            result_count=len(documents),
            confidence=confidence
        )

        return SearchResponse(
            query=query,
            answer=answer,
            confidence=confidence,
            sources=sources,
            search_time=0.0  # 呼び出し元で設定
        )

    async def _search_notion(self, query: str, limit: int) -> list[dict]:
        """Notionからドキュメントを検索"""
        if not self.notion.client:
            print("Notion client not initialized")
            return []

        try:
            pages = await self.notion.search_pages(query, limit)

            documents = []
            for page in pages:
                content = await self.notion.get_page_content(page["id"])

                if content:
                    documents.append({
                        "id": page["id"],
                        "source_type": "notion",
                        "title": page["title"],
                        "url": page["url"],
                        "content": content,
                        "snippet": content[:200] + "..." if len(content) > 200 else content,
                        "score": 0.85,
                        "created_at": page.get("created_at")
                    })

            return documents

        except Exception as e:
            print(f"Notion検索エラー: {e}")
            return []

    async def _search_drive(self, query: str, limit: int) -> list[dict]:
        """Google Driveからドキュメントを検索（PDF/画像も解析）"""
        if not self.drive.service:
            print("Drive service not initialized")
            return []

        try:
            files = await self.drive.search_files(query, limit)

            documents = []
            for file in files:
                # ファイルコンテンツを取得（PDF/画像はGeminiで解析）
                content = await self.drive.get_file_content(
                    file["id"],
                    file.get("mime_type")
                )

                if content:
                    documents.append({
                        "id": file["id"],
                        "source_type": "drive",
                        "title": file["title"],
                        "url": file["url"],
                        "content": content,
                        "snippet": content[:200] + "..." if len(content) > 200 else content,
                        "score": 0.80,
                        "created_at": file.get("created_at")
                    })

            return documents

        except Exception as e:
            print(f"Drive検索エラー: {e}")
            return []

    def _build_context(self, documents: list) -> str:
        """ドキュメントからコンテキストを構築"""
        context_parts = []
        for i, doc in enumerate(documents, 1):
            context_parts.append(
                f"[出典{i}] {doc['title']} ({doc['source_type']})\n{doc['content']}"
            )
        return "\n\n".join(context_parts)

    def _save_search_log(
        self,
        search_id: str,
        user_id: Optional[str],
        query: str,
        result_count: int,
        confidence: float
    ):
        """検索ログを保存"""
        self._search_logs.append({
            "search_id": search_id,
            "user_id": user_id,
            "query": query,
            "result_count": result_count,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        })

    async def get_stats(self, user_id: Optional[str] = None) -> StatsResponse:
        """統計情報を取得"""
        total = len(self._search_logs)
        today = datetime.now().date()
        today_logs = [
            log for log in self._search_logs
            if datetime.fromisoformat(log["timestamp"]).date() == today
        ]

        avg_confidence = 0.0
        if total > 0:
            avg_confidence = sum(log["confidence"] for log in self._search_logs) / total

        keyword_counts = {}
        for log in self._search_logs:
            kw = log["query"][:20]
            keyword_counts[kw] = keyword_counts.get(kw, 0) + 1

        popular = sorted(
            keyword_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        user_count = None
        if user_id:
            user_count = len([
                log for log in self._search_logs
                if log.get("user_id") == user_id
            ])

        return StatsResponse(
            total_searches=total,
            today_searches=len(today_logs),
            avg_response_time=1.2,
            avg_confidence=round(avg_confidence, 2),
            popular_keywords=[
                {"keyword": kw, "count": count}
                for kw, count in popular
            ],
            user_search_count=user_count
        )

    async def save_feedback(self, request: FeedbackRequest):
        """フィードバックを保存"""
        self._feedbacks.append({
            "search_id": request.search_id,
            "user_id": request.user_id,
            "feedback_type": request.feedback_type,
            "comment": request.comment,
            "timestamp": datetime.now().isoformat()
        })

    async def get_history(self, user_id: str, limit: int = 10) -> list:
        """ユーザーの検索履歴を取得"""
        user_logs = [
            log for log in self._search_logs
            if log.get("user_id") == user_id
        ]
        return sorted(
            user_logs,
            key=lambda x: x["timestamp"],
            reverse=True
        )[:limit]

    async def clear_history(self, user_id: str):
        """ユーザーの検索履歴をクリア"""
        self._search_logs = [
            log for log in self._search_logs
            if log.get("user_id") != user_id
        ]
