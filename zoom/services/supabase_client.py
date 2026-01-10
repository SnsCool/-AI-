"""
Supabase クライアント
ナレッジの保存・検索を行う
"""

import os
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


def get_supabase_client() -> Client:
    """Supabaseクライアントを取得"""
    url = os.getenv("SUPABASE_URL")
    # SERVICE_ROLE_KEYがあれば使用、なければANON_KEYを使用
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")

    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY (or SUPABASE_SERVICE_ROLE_KEY) must be set")

    return create_client(url, key)


def save_knowledge(
    client: Client,
    meeting_date: str,
    assignee: str,
    customer_name: Optional[str],
    closing_result: str,
    talk_ratio_sales: int,
    talk_ratio_customer: int,
    issues_heard: list[str],
    proposal: list[str],
    good_points: list[str],
    improvement_points: list[str],
    success_keywords: list[str],
    summary: str,
    embedding: list[float],
    transcript_file_path: Optional[str] = None,
    video_file_path: Optional[str] = None,
    sheet_row_id: Optional[str] = None,
) -> dict:
    """ナレッジを保存"""

    data = {
        "meeting_date": meeting_date,
        "assignee": assignee,
        "customer_name": customer_name,
        "closing_result": closing_result,
        "talk_ratio_sales": talk_ratio_sales,
        "talk_ratio_customer": talk_ratio_customer,
        "issues_heard": issues_heard,
        "proposal": proposal,
        "good_points": good_points,
        "improvement_points": improvement_points,
        "success_keywords": success_keywords,
        "summary": summary,
        "embedding": embedding,
        "transcript_file_path": transcript_file_path,
        "video_file_path": video_file_path,
        "sheet_row_id": sheet_row_id,
    }

    result = client.table("success_knowledge").insert(data).execute()
    return result.data[0] if result.data else {}


def search_similar_knowledge(
    client: Client,
    query_embedding: list[float],
    limit: int = 5,
    closing_result_filter: Optional[str] = "成約",
) -> list[dict]:
    """類似ナレッジを検索（ベクトル検索）"""

    # Supabase RPC で cosine similarity 検索
    result = client.rpc(
        "match_success_knowledge",
        {
            "query_embedding": query_embedding,
            "match_count": limit,
            "filter_closing_result": closing_result_filter,
        }
    ).execute()

    return result.data if result.data else []


def get_knowledge_by_assignee(
    client: Client,
    assignee: str,
    limit: int = 10,
) -> list[dict]:
    """担当者別のナレッジを取得"""

    result = (
        client.table("success_knowledge")
        .select("*")
        .eq("assignee", assignee)
        .order("meeting_date", desc=True)
        .limit(limit)
        .execute()
    )

    return result.data if result.data else []
