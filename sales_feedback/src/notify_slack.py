#!/usr/bin/env python3
"""
Slack通知スクリプト

フィードバック結果をSlackチャンネルに通知する
"""

import argparse
import json
import os
import sys

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


def get_slack_client() -> WebClient:
    """Slackクライアントを取得"""
    token = os.getenv("SLACK_BOT_TOKEN")
    if not token:
        raise ValueError("SLACK_BOT_TOKEN が設定されていません")
    return WebClient(token=token)


def get_score_emoji(score: float) -> str:
    """スコアに応じた絵文字を返す"""
    if score >= 4.5:
        return ":star2:"
    elif score >= 4.0:
        return ":star:"
    elif score >= 3.0:
        return ":thumbsup:"
    elif score >= 2.0:
        return ":thinking_face:"
    else:
        return ":point_up:"


def format_slack_message(feedback: dict) -> list:
    """Slack用のBlocksを生成"""
    meta = feedback.get("metadata", {})
    scores = feedback.get("scores", {})
    overall_score = feedback.get("overall_score", 0)

    score_emoji = get_score_emoji(overall_score)

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"商談フィードバック {score_emoji}",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*担当者:*\n{meta.get('sales_rep', 'N/A')}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*顧客:*\n{meta.get('customer', 'N/A')}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*業種:*\n{meta.get('industry', 'N/A')}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*総合スコア:*\n*{overall_score}/5.0*"
                }
            ]
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*各項目スコア*"
            }
        }
    ]

    # スコア詳細
    score_names = {
        "hearing": "ヒアリング力",
        "proposal": "提案力",
        "objection_handling": "異議対応",
        "closing": "クロージング",
        "rapport": "ラポール構築",
        "bant": "BANT確認"
    }

    score_text = ""
    for key, name in score_names.items():
        score_data = scores.get(key, {})
        score = score_data.get("score", 0)
        bar = "█" * score + "░" * (5 - score)
        score_text += f"{name}: {bar} {score}/5\n"

    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"```{score_text}```"
        }
    })

    blocks.append({"type": "divider"})

    # 良かった点
    good_points = feedback.get("good_points", [])
    if good_points:
        good_text = "\n".join([f"• {p}" for p in good_points[:3]])
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*:white_check_mark: 良かった点*\n{good_text}"
            }
        })

    # 改善点
    improvements = feedback.get("improvements", [])
    if improvements:
        improve_text = "\n".join([f"• {p}" for p in improvements[:3]])
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*:chart_with_upwards_trend: 改善ポイント*\n{improve_text}"
            }
        })

    # アドバイス
    advice = feedback.get("advice", [])
    if advice:
        advice_text = "\n".join([f"{i+1}. {a}" for i, a in enumerate(advice[:3])])
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*:bulb: 次回へのアドバイス*\n{advice_text}"
            }
        })

    return blocks


def send_slack_notification(feedback: dict, channel_id: str) -> str:
    """Slackに通知を送信"""
    client = get_slack_client()
    blocks = format_slack_message(feedback)

    meta = feedback.get("metadata", {})
    fallback_text = f"商談フィードバック: {meta.get('customer', 'N/A')} - スコア: {feedback.get('overall_score', 'N/A')}/5.0"

    try:
        response = client.chat_postMessage(
            channel=channel_id,
            text=fallback_text,
            blocks=blocks
        )
        ts = response.get("ts", "")
        print(f"[INFO] Slack通知完了: {ts}", file=sys.stderr)
        return ts

    except SlackApiError as e:
        print(f"[ERROR] Slack通知エラー: {e.response['error']}", file=sys.stderr)
        raise


def main():
    parser = argparse.ArgumentParser(description="Slack通知")
    parser.add_argument("--feedback-file", required=True, help="フィードバックJSONファイル")
    parser.add_argument("--channel-id", required=True, help="SlackチャンネルID")

    args = parser.parse_args()

    # フィードバック読み込み
    with open(args.feedback_file, 'r', encoding='utf-8') as f:
        feedback = json.load(f)

    # 通知送信
    send_slack_notification(feedback, args.channel_id)


if __name__ == "__main__":
    main()
