"""
ベクトルストアサービス - Qdrant連携
"""

import os
from typing import Optional
from datetime import datetime

# Qdrantが利用可能な場合はインポート
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

# OpenAI Embeddingが利用可能な場合
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class VectorStoreService:
    """Qdrantベクトルストアサービス"""

    COLLECTION_NAME = "knowledge_base"
    EMBEDDING_DIM = 1536  # OpenAI text-embedding-3-small

    def __init__(self):
        self.client = None
        self.openai_client = None

        # Qdrant接続
        if QDRANT_AVAILABLE:
            qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
            qdrant_api_key = os.getenv("QDRANT_API_KEY")
            try:
                self.client = QdrantClient(
                    url=qdrant_url,
                    api_key=qdrant_api_key if qdrant_api_key else None
                )
                self._ensure_collection()
            except Exception as e:
                print(f"Qdrant接続エラー: {e}")
                self.client = None

        # OpenAI Embedding
        if OPENAI_AVAILABLE:
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                self.openai_client = openai.OpenAI(api_key=openai_key)

    def _ensure_collection(self):
        """コレクションが存在しない場合は作成"""
        if not self.client:
            return

        collections = self.client.get_collections().collections
        exists = any(c.name == self.COLLECTION_NAME for c in collections)

        if not exists:
            self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=self.EMBEDDING_DIM,
                    distance=Distance.COSINE
                )
            )
            print(f"コレクション '{self.COLLECTION_NAME}' を作成しました")

    async def get_embedding(self, text: str) -> list[float]:
        """テキストのEmbeddingを取得"""
        if self.openai_client:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding

        # フォールバック: ダミーベクトル
        import hashlib
        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
        return [(hash_val >> i & 0xFF) / 255.0 for i in range(self.EMBEDDING_DIM)]

    async def search(
        self,
        query: str,
        source: Optional[str] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
        top_k: int = 3
    ) -> list[dict]:
        """
        ベクトル検索を実行

        Returns:
            list[dict]: 検索結果のドキュメントリスト
        """
        # Qdrantが利用可能な場合
        if self.client:
            return await self._search_qdrant(query, source, after, before, top_k)

        # フォールバック: モックデータ
        return await self._search_mock(query, source, top_k)

    async def _search_qdrant(
        self,
        query: str,
        source: Optional[str],
        after: Optional[str],
        before: Optional[str],
        top_k: int
    ) -> list[dict]:
        """Qdrantでベクトル検索"""
        query_vector = await self.get_embedding(query)

        # フィルター構築
        filter_conditions = []
        if source:
            filter_conditions.append(
                FieldCondition(
                    key="source_type",
                    match=MatchValue(value=source)
                )
            )

        search_filter = None
        if filter_conditions:
            search_filter = Filter(must=filter_conditions)

        # 検索実行
        results = self.client.search(
            collection_name=self.COLLECTION_NAME,
            query_vector=query_vector,
            query_filter=search_filter,
            limit=top_k
        )

        # 結果を整形
        documents = []
        for hit in results:
            payload = hit.payload or {}
            documents.append({
                "id": hit.id,
                "source_type": payload.get("source_type", "unknown"),
                "title": payload.get("title", "不明"),
                "url": payload.get("url", ""),
                "content": payload.get("content", ""),
                "snippet": payload.get("snippet", ""),
                "score": round(hit.score, 2),
                "created_at": payload.get("created_at")
            })

        return documents

    async def _search_mock(
        self,
        query: str,
        source: Optional[str],
        top_k: int
    ) -> list[dict]:
        """モックデータで検索（デモ用）"""
        mock_data = [
            {
                "id": "1",
                "source_type": "notion",
                "title": "経費精算規定 2024",
                "url": "https://notion.so/expense-policy-2024",
                "content": "経費精算は以下の手順で行います。\n1. 領収書をスマホで撮影\n2. Slackの@経費精算AIに送信\n3. 自動で申請が完了します。\n\n対象となる経費：交通費、接待費、消耗品費など",
                "snippet": "経費精算は以下の手順で行います...",
                "score": 0.95,
                "created_at": "2024-01-15"
            },
            {
                "id": "2",
                "source_type": "drive",
                "title": "経費申請マニュアル.pdf",
                "url": "https://drive.google.com/file/d/xxx",
                "content": "経費申請の詳細マニュアルです。月末締め、翌月15日払いとなります。上限金額は1件あたり10万円です。",
                "snippet": "経費申請の詳細マニュアルです...",
                "score": 0.88,
                "created_at": "2024-02-01"
            },
            {
                "id": "3",
                "source_type": "slack",
                "title": "#総務チャンネル 2024/11/20",
                "url": "https://slack.com/archives/xxx/p123",
                "content": "【お知らせ】経費精算の承認フローが変更になりました。5万円以上の場合は部長承認が必要です。",
                "snippet": "経費精算の承認フローが変更になりました...",
                "score": 0.82,
                "created_at": "2024-11-20"
            },
            {
                "id": "4",
                "source_type": "notion",
                "title": "有給休暇申請ガイド",
                "url": "https://notion.so/vacation-guide",
                "content": "有給休暇の申請方法について説明します。申請は3営業日前までにSlackワークフローから行ってください。",
                "snippet": "有給休暇の申請方法について...",
                "score": 0.75,
                "created_at": "2024-03-01"
            },
            {
                "id": "5",
                "source_type": "notion",
                "title": "リモートワーク規定",
                "url": "https://notion.so/remote-work-policy",
                "content": "リモートワークの申請は上長承認が必要です。週3日まで在宅勤務可能。申請はHRシステムから。",
                "snippet": "リモートワークの申請は上長承認が必要...",
                "score": 0.70,
                "created_at": "2024-04-01"
            }
        ]

        # ソースフィルター
        if source:
            mock_data = [d for d in mock_data if d["source_type"] == source]

        # クエリに基づく簡易スコアリング
        query_lower = query.lower()
        for doc in mock_data:
            if any(kw in doc["content"].lower() for kw in query_lower.split()):
                doc["score"] = min(doc["score"] + 0.1, 1.0)

        # スコア順でソート
        mock_data.sort(key=lambda x: x["score"], reverse=True)

        return mock_data[:top_k]

    async def add_document(
        self,
        doc_id: str,
        content: str,
        metadata: dict
    ) -> bool:
        """ドキュメントを追加"""
        if not self.client:
            return False

        embedding = await self.get_embedding(content)

        self.client.upsert(
            collection_name=self.COLLECTION_NAME,
            points=[
                PointStruct(
                    id=doc_id,
                    vector=embedding,
                    payload={
                        "content": content,
                        **metadata
                    }
                )
            ]
        )
        return True
