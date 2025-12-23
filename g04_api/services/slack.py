"""
Slackサービス - Slack API連携
"""

import os
from typing import Optional
from datetime import datetime

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False


class SlackService:
    """Slack API サービス"""

    def __init__(self):
        self.client = None
        if SLACK_AVAILABLE:
            token = os.getenv("SLACK_BOT_TOKEN")
            if token:
                self.client = WebClient(token=token)

    async def search_messages(
        self,
        query: str,
        limit: int = 10,
        channel: str = None
    ) -> list[dict]:
        """メッセージを検索"""
        if not self.client:
            return []

        try:
            # チャンネル指定がある場合
            search_query = query
            if channel:
                search_query = f"in:{channel} {query}"

            response = self.client.search_messages(
                query=search_query,
                count=limit
            )

            messages = []
            for match in response.get("messages", {}).get("matches", []):
                msg = self._parse_message(match)
                if msg:
                    messages.append(msg)

            return messages

        except SlackApiError as e:
            print(f"Slack検索エラー: {e.response['error']}")
            return []
        except Exception as e:
            print(f"Slack検索エラー: {e}")
            return []

    def _parse_message(self, match: dict) -> Optional[dict]:
        """メッセージデータをパース"""
        try:
            channel_info = match.get("channel", {})
            channel_name = channel_info.get("name", "unknown")

            # タイムスタンプから日付を取得
            ts = match.get("ts", "")
            date_str = ""
            if ts:
                try:
                    dt = datetime.fromtimestamp(float(ts))
                    date_str = dt.strftime("%Y/%m/%d")
                except:
                    pass

            # パーマリンク
            permalink = match.get("permalink", "")

            return {
                "id": match.get("iid", ts),
                "source_type": "slack",
                "title": f"#{channel_name} {date_str}",
                "url": permalink,
                "content": match.get("text", ""),
                "snippet": match.get("text", "")[:200],
                "channel": channel_name,
                "user": match.get("user", ""),
                "created_at": date_str
            }

        except Exception as e:
            print(f"メッセージパースエラー: {e}")
            return None

    async def get_channel_history(
        self,
        channel_id: str,
        limit: int = 100
    ) -> list[dict]:
        """チャンネルの履歴を取得"""
        if not self.client:
            return []

        try:
            response = self.client.conversations_history(
                channel=channel_id,
                limit=limit
            )

            messages = []
            for msg in response.get("messages", []):
                ts = msg.get("ts", "")
                date_str = ""
                if ts:
                    try:
                        dt = datetime.fromtimestamp(float(ts))
                        date_str = dt.strftime("%Y/%m/%d %H:%M")
                    except:
                        pass

                messages.append({
                    "id": ts,
                    "source_type": "slack",
                    "content": msg.get("text", ""),
                    "user": msg.get("user", ""),
                    "created_at": date_str
                })

            return messages

        except SlackApiError as e:
            print(f"チャンネル履歴取得エラー: {e.response['error']}")
            return []
        except Exception as e:
            print(f"チャンネル履歴取得エラー: {e}")
            return []

    async def list_channels(self) -> list[dict]:
        """チャンネル一覧を取得"""
        if not self.client:
            return []

        try:
            response = self.client.conversations_list(
                types="public_channel,private_channel"
            )

            return [
                {
                    "id": ch.get("id"),
                    "name": ch.get("name"),
                    "is_private": ch.get("is_private", False)
                }
                for ch in response.get("channels", [])
            ]

        except SlackApiError as e:
            print(f"チャンネル一覧取得エラー: {e.response['error']}")
            return []
        except Exception as e:
            print(f"チャンネル一覧取得エラー: {e}")
            return []
