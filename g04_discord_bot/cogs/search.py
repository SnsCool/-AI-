"""
検索コマンド Cog
"""

import re
import discord
from discord.ext import commands
from discord import app_commands

from utils.api_client import G04APIClient
from utils.embed_builder import EmbedBuilder


class Search(commands.Cog):
    """ナレッジ検索コマンド"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.api = G04APIClient()
        self.embed_builder = EmbedBuilder()

    def parse_filters(self, query: str) -> tuple[str, dict]:
        """
        クエリからフィルターを抽出

        例: "!search --source=notion --after=2024-01-01 経費精算"
        """
        filters = {}

        # --source=xxx
        source_match = re.search(r"--source=(\w+)", query)
        if source_match:
            filters["source"] = source_match.group(1)
            query = query.replace(source_match.group(0), "")

        # --after=YYYY-MM-DD
        after_match = re.search(r"--after=(\d{4}-\d{2}-\d{2})", query)
        if after_match:
            filters["after"] = after_match.group(1)
            query = query.replace(after_match.group(0), "")

        # --before=YYYY-MM-DD
        before_match = re.search(r"--before=(\d{4}-\d{2}-\d{2})", query)
        if before_match:
            filters["before"] = before_match.group(1)
            query = query.replace(before_match.group(0), "")

        return query.strip(), filters

    async def do_search(self, ctx: commands.Context, query: str):
        """検索を実行"""
        # フィルター解析
        clean_query, filters = self.parse_filters(query)

        # クエリチェック
        if len(clean_query) < 5:
            await ctx.send(
                embed=self.embed_builder.build_error(
                    "QUERY_TOO_SHORT",
                    "検索クエリが短すぎます",
                    "最低5文字以上の質問を入力してください。\n\n例:\n✅ 経費精算のルールは?\n❌ 経費"
                )
            )
            return

        # 検索中メッセージ
        loading_msg = await ctx.send(
            embed=discord.Embed(
                title="🔍 検索中...",
                description=f"「{clean_query}」を検索しています...",
                color=discord.Color.blue()
            )
        )

        try:
            # API呼び出し
            result = await self.api.search(
                query=clean_query,
                source=filters.get("source"),
                after=filters.get("after"),
                before=filters.get("before"),
                user_id=str(ctx.author.id)
            )

            # 結果Embed作成
            embed = self.embed_builder.build_search_result(
                query=clean_query,
                answer=result["answer"],
                confidence=result["confidence"],
                sources=result["sources"],
                search_time=result["search_time"]
            )

            # 検索中メッセージを更新
            await loading_msg.edit(embed=embed)

            # リアクション追加
            await loading_msg.add_reaction("✅")  # 役に立った
            await loading_msg.add_reaction("❌")  # 役に立たなかった
            await loading_msg.add_reaction("🔖")  # 保存

        except Exception as e:
            await loading_msg.edit(
                embed=self.embed_builder.build_error(
                    "API_ERROR",
                    "検索APIに接続できません",
                    str(e)
                )
            )

    @commands.command(name="search", aliases=["検索", "ナレッジ"])
    async def search_command(self, ctx: commands.Context, *, query: str):
        """
        ナレッジ検索

        使用例:
          !search 経費精算のルールは?
          !検索 有給申請の方法
          !ナレッジ --source=notion 新機能リリース
        """
        await self.do_search(ctx, query)

    @app_commands.command(name="ナレッジ検索", description="社内ドキュメントを横断検索します")
    @app_commands.describe(
        question="検索したい質問（5文字以上）",
        source="検索対象を限定（notion/drive/slack）"
    )
    async def slash_search(
        self,
        interaction: discord.Interaction,
        question: str,
        source: str = None
    ):
        """スラッシュコマンドで検索"""
        await interaction.response.defer()

        # フィルター設定
        filters = {}
        if source:
            filters["source"] = source

        # クエリチェック
        if len(question) < 5:
            await interaction.followup.send(
                embed=self.embed_builder.build_error(
                    "QUERY_TOO_SHORT",
                    "検索クエリが短すぎます",
                    "最低5文字以上の質問を入力してください。"
                )
            )
            return

        try:
            # API呼び出し
            result = await self.api.search(
                query=question,
                source=filters.get("source"),
                user_id=str(interaction.user.id)
            )

            # 結果Embed作成
            embed = self.embed_builder.build_search_result(
                query=question,
                answer=result["answer"],
                confidence=result["confidence"],
                sources=result["sources"],
                search_time=result["search_time"]
            )

            message = await interaction.followup.send(embed=embed)

            # リアクション追加
            await message.add_reaction("✅")
            await message.add_reaction("❌")
            await message.add_reaction("🔖")

        except Exception as e:
            await interaction.followup.send(
                embed=self.embed_builder.build_error(
                    "API_ERROR",
                    "検索APIに接続できません",
                    str(e)
                )
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Search(bot))
