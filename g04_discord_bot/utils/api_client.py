"""
G04 API クライアント
"""

import os
import aiohttp
from typing import Optional


class G04APIClient:
    """G04 ナレッジ検索 API クライアント"""

    def __init__(self):
        self.base_url = os.getenv("G04_API_URL", "http://localhost:8004")
        self.timeout = int(os.getenv("SEARCH_TIMEOUT", "30"))

    async def _request(
        self,
        method: str,
        endpoint: str,
        json: dict = None,
        params: dict = None
    ) -> dict:
        """APIリクエストを実行"""
        url = f"{self.base_url}/api/v1{endpoint}"

        async with aiohttp.ClientSession() as session:
            async with session.request(
                method,
                url,
                json=json,
                params=params,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                if response.status >= 400:
                    error_data = await response.json()
                    raise APIError(
                        error_data.get("detail", {}).get("error_code", "UNKNOWN"),
                        error_data.get("detail", {}).get("message", "不明なエラー")
                    )
                return await response.json()

    async def search(
        self,
        query: str,
        source: Optional[str] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
        top_k: int = 3,
        user_id: Optional[str] = None
    ) -> dict:
        """
        ナレッジ検索

        Args:
            query: 検索クエリ
            source: ソース指定（notion/drive/slack）
            after: この日付以降
            before: この日付以前
            top_k: 取得件数
            user_id: Discord User ID

        Returns:
            dict: 検索結果
        """
        payload = {
            "query": query,
            "top_k": top_k
        }

        if source:
            payload["source"] = source
        if after:
            payload["after"] = after
        if before:
            payload["before"] = before
        if user_id:
            payload["user_id"] = user_id

        return await self._request("POST", "/search", json=payload)

    async def get_stats(self, user_id: Optional[str] = None) -> dict:
        """統計情報を取得"""
        params = {}
        if user_id:
            params["user_id"] = user_id

        return await self._request("GET", "/stats", params=params)

    async def get_history(
        self,
        user_id: str,
        limit: int = 10
    ) -> list:
        """検索履歴を取得"""
        return await self._request(
            "GET",
            "/history",
            params={"user_id": user_id, "limit": limit}
        )

    async def clear_history(self, user_id: str) -> dict:
        """検索履歴をクリア"""
        return await self._request(
            "DELETE",
            "/history",
            params={"user_id": user_id}
        )

    async def submit_feedback(
        self,
        search_id: str,
        user_id: str,
        feedback_type: str,
        comment: Optional[str] = None
    ) -> dict:
        """フィードバックを送信"""
        payload = {
            "search_id": search_id,
            "user_id": user_id,
            "feedback_type": feedback_type
        }
        if comment:
            payload["comment"] = comment

        return await self._request("POST", "/feedback", json=payload)


class APIError(Exception):
    """API エラー"""

    def __init__(self, error_code: str, message: str):
        self.error_code = error_code
        self.message = message
        super().__init__(f"[{error_code}] {message}")
