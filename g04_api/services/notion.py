"""
Notionサービス - Notion API連携
"""

import os
from typing import Optional
from datetime import datetime

try:
    from notion_client import Client
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False


class NotionService:
    """Notion API サービス"""

    def __init__(self):
        self.client = None
        if NOTION_AVAILABLE:
            token = os.getenv("NOTION_TOKEN")
            if token:
                self.client = Client(auth=token)

    async def search_pages(
        self,
        query: str,
        limit: int = 10
    ) -> list[dict]:
        """Notionページを検索"""
        if not self.client:
            return []

        try:
            response = self.client.search(
                query=query,
                filter={"property": "object", "value": "page"},
                page_size=limit
            )

            pages = []
            for result in response.get("results", []):
                page = self._parse_page(result)
                if page:
                    pages.append(page)

            return pages

        except Exception as e:
            print(f"Notion検索エラー: {e}")
            return []

    def _parse_page(self, page_data: dict) -> Optional[dict]:
        """ページデータをパース"""
        try:
            page_id = page_data.get("id", "")
            url = page_data.get("url", "")

            # タイトルを取得
            title = "無題"
            properties = page_data.get("properties", {})
            for prop in properties.values():
                if prop.get("type") == "title":
                    title_content = prop.get("title", [])
                    if title_content:
                        title = title_content[0].get("plain_text", "無題")
                    break

            # 作成日時
            created_time = page_data.get("created_time", "")

            return {
                "id": page_id,
                "source_type": "notion",
                "title": title,
                "url": url,
                "created_at": created_time[:10] if created_time else None
            }

        except Exception as e:
            print(f"ページパースエラー: {e}")
            return None

    async def get_page_content(self, page_id: str) -> str:
        """ページのコンテンツを取得"""
        if not self.client:
            return ""

        try:
            blocks = self.client.blocks.children.list(block_id=page_id)
            content_parts = []

            for block in blocks.get("results", []):
                text = self._extract_block_text(block)
                if text:
                    content_parts.append(text)

            return "\n".join(content_parts)

        except Exception as e:
            print(f"ページコンテンツ取得エラー: {e}")
            return ""

    def _extract_block_text(self, block: dict) -> str:
        """ブロックからテキストを抽出"""
        block_type = block.get("type", "")

        # テキストを含むブロックタイプ
        text_types = [
            "paragraph", "heading_1", "heading_2", "heading_3",
            "bulleted_list_item", "numbered_list_item", "quote", "callout"
        ]

        if block_type in text_types:
            content = block.get(block_type, {})
            rich_text = content.get("rich_text", [])
            return "".join(t.get("plain_text", "") for t in rich_text)

        return ""

    async def sync_database(self, database_id: str) -> list[dict]:
        """データベースの全ページを同期"""
        if not self.client:
            return []

        try:
            pages = []
            has_more = True
            start_cursor = None

            while has_more:
                response = self.client.databases.query(
                    database_id=database_id,
                    start_cursor=start_cursor
                )

                for result in response.get("results", []):
                    page = self._parse_page(result)
                    if page:
                        content = await self.get_page_content(page["id"])
                        page["content"] = content
                        pages.append(page)

                has_more = response.get("has_more", False)
                start_cursor = response.get("next_cursor")

            return pages

        except Exception as e:
            print(f"データベース同期エラー: {e}")
            return []
