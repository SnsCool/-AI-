"""
Discord Embed ビルダー
"""

import discord


class EmbedBuilder:
    """検索結果のEmbed構築"""

    # ソースタイプごとの絵文字
    SOURCE_EMOJI = {
        "notion": "📝",
        "drive": "📁",
        "slack": "💬"
    }

    def build_search_result(
        self,
        query: str,
        answer: str,
        confidence: float,
        sources: list,
        search_time: float
    ) -> discord.Embed:
        """
        検索結果のEmbedを構築

        Args:
            query: 検索クエリ
            answer: AIの回答
            confidence: 信頼度（0.0-1.0）
            sources: 出典リスト
            search_time: 検索時間（秒）

        Returns:
            discord.Embed: 構築されたEmbed
        """
        # 信頼度に基づく色とインジケータ
        if confidence >= 0.8:
            color = discord.Color.green()
            confidence_emoji = "🟢"
        elif confidence >= 0.6:
            color = discord.Color.yellow()
            confidence_emoji = "🟡"
        else:
            color = discord.Color.red()
            confidence_emoji = "🔴"

        embed = discord.Embed(
            title=f"🔍 検索結果: {query[:50]}{'...' if len(query) > 50 else ''}",
            color=color
        )

        # 回答
        embed.add_field(
            name="💬 回答",
            value=answer[:1000] + ("..." if len(answer) > 1000 else ""),
            inline=False
        )

        # 低信頼度の場合の警告
        if confidence < 0.6:
            embed.add_field(
                name="⚠️ 注意",
                value="関連する情報が見つかりませんでした。\n検索キーワードを変更するか、担当部署に直接お問い合わせください。",
                inline=False
            )
        elif confidence < 0.8:
            embed.add_field(
                name="⚠️ 注意",
                value="信頼度がやや低いため、内容を確認することを推奨します。",
                inline=False
            )

        # メタ情報
        confidence_pct = int(confidence * 100)
        embed.add_field(
            name="📊 信頼度",
            value=f"{confidence_emoji} {confidence_pct}%",
            inline=True
        )
        embed.add_field(
            name="⏱️ 検索時間",
            value=f"{search_time:.2f}秒",
            inline=True
        )

        # 出典
        if sources:
            sources_text = ""
            for source in sources[:5]:
                emoji = self.SOURCE_EMOJI.get(source.get("source_type", ""), "📄")
                title = source.get("title", "不明")[:40]
                url = source.get("url", "")
                score = int(source.get("relevance_score", 0) * 100)

                if url:
                    sources_text += f"{emoji} [{title}]({url}) - {score}%\n"
                else:
                    sources_text += f"{emoji} {title} - {score}%\n"

            embed.add_field(
                name="📚 出典",
                value=sources_text,
                inline=False
            )

        embed.set_footer(text="✅役に立った ❌役に立たなかった 🔖保存")

        return embed

    def build_error(
        self,
        error_code: str,
        title: str,
        detail: str = None
    ) -> discord.Embed:
        """
        エラーEmbedを構築

        Args:
            error_code: エラーコード
            title: エラータイトル
            detail: 詳細説明

        Returns:
            discord.Embed: エラーEmbed
        """
        # エラーコードに応じたアイコン
        icons = {
            "QUERY_TOO_SHORT": "⚠️",
            "API_CONNECTION_ERROR": "❌",
            "TIMEOUT": "⏱️",
            "PERMISSION_DENIED": "🔒"
        }
        icon = icons.get(error_code, "❌")

        embed = discord.Embed(
            title=f"{icon} {title}",
            color=discord.Color.red()
        )

        if detail:
            embed.add_field(
                name="詳細",
                value=detail,
                inline=False
            )

        embed.set_footer(text=f"エラーコード: {error_code}")

        return embed

    def build_loading(self, query: str) -> discord.Embed:
        """検索中のEmbedを構築"""
        return discord.Embed(
            title="🔍 検索中...",
            description=f"「{query}」を検索しています...",
            color=discord.Color.blue()
        )
