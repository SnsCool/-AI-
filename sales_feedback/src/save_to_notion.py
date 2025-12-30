#!/usr/bin/env python3
"""
Notionナレッジ保存スクリプト

成功事例をNotionデータベースに保存する
"""

import argparse
import json
import os
import sys
from datetime import datetime

from notion_client import Client


def get_notion_client() -> Client:
    """Notionクライアントを取得"""
    token = os.getenv("NOTION_TOKEN")
    if not token:
        raise ValueError("NOTION_TOKEN が設定されていません")
    return Client(auth=token)


def save_to_notion(feedback: dict, database_id: str) -> str:
    """Notionデータベースに保存"""
    client = get_notion_client()
    meta = feedback.get("metadata", {})
    scores = feedback.get("scores", {})

    # 良かった点を文字列に
    good_points = "\n".join([f"• {p}" for p in feedback.get("good_points", [])])

    # 効果的フレーズを文字列に
    key_phrases = "\n".join([f"「{p}」" for p in feedback.get("key_phrases", [])])

    # 成功要因
    success_factors = feedback.get("success_factors", "")

    # ページを作成
    new_page = client.pages.create(
        parent={"database_id": database_id},
        properties={
            "名前": {
                "title": [
                    {
                        "text": {
                            "content": f"{meta.get('customer', 'N/A')} - {datetime.now().strftime('%Y/%m/%d')}"
                        }
                    }
                ]
            },
            "日付": {
                "date": {
                    "start": datetime.now().strftime("%Y-%m-%d")
                }
            },
            "担当者": {
                "rich_text": [
                    {
                        "text": {
                            "content": meta.get("sales_rep", "")
                        }
                    }
                ]
            },
            "顧客名": {
                "rich_text": [
                    {
                        "text": {
                            "content": meta.get("customer", "")
                        }
                    }
                ]
            },
            "業種": {
                "select": {
                    "name": meta.get("industry", "未分類")
                }
            },
            "商材": {
                "select": {
                    "name": meta.get("product", "未分類")
                }
            },
            "総合スコア": {
                "number": feedback.get("overall_score", 0)
            },
            "ヒアリング力": {
                "number": scores.get("hearing", {}).get("score", 0)
            },
            "提案力": {
                "number": scores.get("proposal", {}).get("score", 0)
            },
            "クロージング": {
                "number": scores.get("closing", {}).get("score", 0)
            },
            "クロージング成功": {
                "checkbox": meta.get("is_closed", False)
            }
        },
        children=[
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "成功要因"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": success_factors}}]
                }
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "良かった点"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": good_points}}]
                }
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "効果的だったフレーズ"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": key_phrases}}]
                }
            }
        ]
    )

    page_url = new_page.get("url", "")
    print(f"[INFO] Notion保存完了: {page_url}", file=sys.stderr)
    return page_url


def main():
    parser = argparse.ArgumentParser(description="Notionナレッジ保存")
    parser.add_argument("--feedback-file", required=True, help="フィードバックJSONファイル")
    parser.add_argument("--database-id", required=True, help="NotionデータベースID")

    args = parser.parse_args()

    # フィードバック読み込み
    with open(args.feedback_file, 'r', encoding='utf-8') as f:
        feedback = json.load(f)

    # 保存
    url = save_to_notion(feedback, args.database_id)
    print(url)


if __name__ == "__main__":
    main()
