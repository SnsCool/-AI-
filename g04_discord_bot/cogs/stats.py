"""
統計・履歴コマンド Cog
"""

import discord
from discord.ext import commands

from utils.api_client import G04APIClient
from utils.embed_builder import EmbedBuilder


class Stats(commands.Cog):
    """統計・履歴コマンド"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.api = G04APIClient()
        self.embed_builder = EmbedBuilder()

    @commands.command(name="stats", aliases=["統計"])
    async def stats_command(self, ctx: commands.Context):
        """
        統計情報を表示

        使用例:
          !stats
          !統計
        """
        try:
            result = await self.api.get_stats(user_id=str(ctx.author.id))

            # 人気キーワードを整形
            keywords_text = ""
            for i, kw in enumerate(result.get("popular_keywords", [])[:5], 1):
                keywords_text += f"{i}. {kw['keyword']} ({kw['count']}回)\n"

            if not keywords_text:
                keywords_text = "データなし"

            embed = discord.Embed(
                title="📊 ナレッジ検索 統計情報",
                color=discord.Color.blue()
            )

            embed.add_field(
                name="総検索回数",
                value=f"{result.get('total_searches', 0):,}回",
                inline=True
            )
            embed.add_field(
                name="今日の検索",
                value=f"{result.get('today_searches', 0):,}回",
                inline=True
            )
            embed.add_field(
                name="平均応答時間",
                value=f"{result.get('avg_response_time', 0):.1f}秒",
                inline=True
            )
            embed.add_field(
                name="平均信頼度",
                value=f"{int(result.get('avg_confidence', 0) * 100)}%",
                inline=True
            )

            if result.get("user_search_count") is not None:
                embed.add_field(
                    name="あなたの検索回数",
                    value=f"{result['user_search_count']:,}回",
                    inline=True
                )

            embed.add_field(
                name="人気の検索キーワード",
                value=keywords_text,
                inline=False
            )

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(
                embed=self.embed_builder.build_error(
                    "STATS_ERROR",
                    "統計情報の取得に失敗しました",
                    str(e)
                )
            )

    @commands.command(name="history", aliases=["履歴"])
    async def history_command(self, ctx: commands.Context):
        """
        検索履歴を表示（DMに送信）

        使用例:
          !history
          !履歴
        """
        try:
            result = await self.api.get_history(
                user_id=str(ctx.author.id),
                limit=10
            )

            if not result:
                await ctx.author.send(
                    embed=discord.Embed(
                        title="📜 検索履歴",
                        description="検索履歴がありません。",
                        color=discord.Color.blue()
                    )
                )
                await ctx.send("📩 DMに検索履歴を送信しました。")
                return

            # 履歴を整形
            history_text = ""
            for i, log in enumerate(result, 1):
                timestamp = log.get("timestamp", "")[:16].replace("T", " ")
                query = log.get("query", "")[:30]
                history_text += f"{i}. {timestamp} - {query}\n"

            embed = discord.Embed(
                title="📜 あなたの検索履歴（最新10件）",
                description=history_text,
                color=discord.Color.blue()
            )
            embed.set_footer(text="履歴をクリア: !clear-history")

            await ctx.author.send(embed=embed)
            await ctx.send("📩 DMに検索履歴を送信しました。")

        except discord.Forbidden:
            await ctx.send(
                embed=discord.Embed(
                    title="❌ エラー",
                    description="DMの送信に失敗しました。DMを受け取れるように設定してください。",
                    color=discord.Color.red()
                )
            )
        except Exception as e:
            await ctx.send(
                embed=self.embed_builder.build_error(
                    "HISTORY_ERROR",
                    "検索履歴の取得に失敗しました",
                    str(e)
                )
            )

    @commands.command(name="clear-history", aliases=["履歴クリア"])
    async def clear_history_command(self, ctx: commands.Context):
        """
        検索履歴をクリア

        使用例:
          !clear-history
          !履歴クリア
        """
        try:
            await self.api.clear_history(user_id=str(ctx.author.id))

            await ctx.send(
                embed=discord.Embed(
                    title="✅ 完了",
                    description="検索履歴をクリアしました。",
                    color=discord.Color.green()
                )
            )

        except Exception as e:
            await ctx.send(
                embed=self.embed_builder.build_error(
                    "CLEAR_ERROR",
                    "履歴のクリアに失敗しました",
                    str(e)
                )
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Stats(bot))
