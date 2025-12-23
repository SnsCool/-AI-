"""
ヘルプコマンド Cog
"""

import discord
from discord.ext import commands


class Help(commands.Cog):
    """ヘルプコマンド"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="help", aliases=["ヘルプ"])
    async def help_command(self, ctx: commands.Context):
        """
        ヘルプを表示

        使用例:
          !help
          !ヘルプ
        """
        embed = discord.Embed(
            title="📖 ナレッジ検索Bot ヘルプ",
            description="社内ドキュメント（Notion/Drive/Slack）を横断検索します。",
            color=discord.Color.blue()
        )

        # 基本コマンド
        embed.add_field(
            name="🔍 基本コマンド",
            value=(
                "`!search [質問]` - ナレッジ検索\n"
                "`!検索 [質問]` - ナレッジ検索（日本語）\n"
                "`/ナレッジ検索` - スラッシュコマンド\n"
                "`@Bot [質問]` - メンションで検索"
            ),
            inline=False
        )

        # フィルター
        embed.add_field(
            name="🎯 フィルター",
            value=(
                "`--source=notion` - Notionのみ検索\n"
                "`--source=drive` - Google Driveのみ検索\n"
                "`--source=slack` - Slackのみ検索\n"
                "`--after=YYYY-MM-DD` - 指定日以降\n"
                "`--before=YYYY-MM-DD` - 指定日以前"
            ),
            inline=False
        )

        # その他のコマンド
        embed.add_field(
            name="📊 その他",
            value=(
                "`!stats` - 統計情報\n"
                "`!history` - 検索履歴（DMに送信）\n"
                "`!clear-history` - 履歴をクリア"
            ),
            inline=False
        )

        # 使用例
        embed.add_field(
            name="💡 使用例",
            value=(
                "```\n"
                "!search 経費精算のルールは?\n"
                "!search --source=notion 新機能リリース\n"
                "!検索 --after=2024-01-01 有給申請\n"
                "```"
            ),
            inline=False
        )

        # リアクション説明
        embed.add_field(
            name="👍 リアクション",
            value=(
                "✅ 役に立った\n"
                "❌ 役に立たなかった\n"
                "🔖 DMに保存"
            ),
            inline=False
        )

        embed.set_footer(text="問題が発生した場合は #tech-support までご連絡ください")

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))
