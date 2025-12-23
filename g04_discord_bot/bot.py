#!/usr/bin/env python3
"""
G04 ナレッジ検索 Discord Bot

社内ドキュメント（Notion/Drive/Slack）を横断検索するBot
"""

import os
import asyncio
import logging
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()

# ロギング設定
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("g04_bot")

# Bot設定
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(
    command_prefix=["!", "！"],
    intents=intents,
    help_command=None  # カスタムヘルプを使用
)


@bot.event
async def on_ready():
    """Bot起動時"""
    logger.info(f"Bot起動完了: {bot.user.name} ({bot.user.id})")
    logger.info(f"接続サーバー数: {len(bot.guilds)}")

    # ステータス設定
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name="!search で検索"
        )
    )

    # スラッシュコマンド同期
    try:
        synced = await bot.tree.sync()
        logger.info(f"スラッシュコマンド同期完了: {len(synced)}個")
    except Exception as e:
        logger.error(f"スラッシュコマンド同期エラー: {e}")


@bot.event
async def on_message(message: discord.Message):
    """メッセージ受信時"""
    # Bot自身のメッセージは無視
    if message.author.bot:
        return

    # メンション検索
    if bot.user in message.mentions:
        # メンションを除去してクエリを取得
        query = message.content.replace(f"<@{bot.user.id}>", "").strip()
        query = query.replace(f"<@!{bot.user.id}>", "").strip()

        if query:
            ctx = await bot.get_context(message)
            search_cog = bot.get_cog("Search")
            if search_cog:
                await search_cog.do_search(ctx, query)
            return

    # コマンド処理
    await bot.process_commands(message)


@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    """リアクション追加時"""
    if user.bot:
        return

    # Bot自身のメッセージへのリアクションのみ処理
    if reaction.message.author != bot.user:
        return

    emoji = str(reaction.emoji)

    # 保存リアクション
    if emoji == "🔖":
        try:
            await user.send(
                f"**保存した検索結果:**\n{reaction.message.embeds[0].description if reaction.message.embeds else reaction.message.content}"
            )
            logger.info(f"検索結果をDMに転送: {user.name}")
        except discord.Forbidden:
            logger.warning(f"DMの送信に失敗: {user.name}")

    # フィードバック記録
    elif emoji in ["✅", "❌"]:
        feedback_type = "helpful" if emoji == "✅" else "not_helpful"
        logger.info(f"フィードバック受信: {feedback_type} from {user.name}")


@bot.event
async def on_command_error(ctx: commands.Context, error):
    """コマンドエラー時"""
    if isinstance(error, commands.CommandNotFound):
        return  # 不明なコマンドは無視

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(
            embed=discord.Embed(
                title="⚠️ 引数エラー",
                description="検索クエリを入力してください。\n例: `!search 経費精算のルールは?`",
                color=discord.Color.yellow()
            )
        )
        return

    logger.error(f"コマンドエラー: {error}")
    await ctx.send(
        embed=discord.Embed(
            title="❌ エラー",
            description="予期しないエラーが発生しました。",
            color=discord.Color.red()
        )
    )


async def load_extensions():
    """Cogを読み込み"""
    cogs = ["cogs.search", "cogs.stats", "cogs.help"]
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            logger.info(f"Cog読み込み完了: {cog}")
        except Exception as e:
            logger.error(f"Cog読み込みエラー ({cog}): {e}")


async def main():
    """メインエントリーポイント"""
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        logger.error("DISCORD_BOT_TOKEN が設定されていません")
        return

    async with bot:
        await load_extensions()
        await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
