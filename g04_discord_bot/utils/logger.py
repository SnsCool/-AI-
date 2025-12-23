"""
ロギングユーティリティ
"""

import os
import logging
from datetime import datetime


def setup_logger(name: str) -> logging.Logger:
    """
    ロガーをセットアップ

    Args:
        name: ロガー名

    Returns:
        logging.Logger: 設定済みロガー
    """
    logger = logging.getLogger(name)

    # 既に設定済みの場合はスキップ
    if logger.handlers:
        return logger

    level = getattr(logging, os.getenv("LOG_LEVEL", "INFO"))
    logger.setLevel(level)

    # コンソールハンドラ
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    # フォーマット
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    return logger


class SearchLogger:
    """検索ログ専用ロガー"""

    def __init__(self):
        self.logger = setup_logger("search_log")

    def log_search(
        self,
        user_id: str,
        query: str,
        result_count: int,
        confidence: float,
        search_time: float,
        channel_id: str = None,
        guild_id: str = None
    ):
        """検索ログを記録"""
        self.logger.info(
            f"SEARCH | "
            f"user={user_id} | "
            f"query=\"{query[:50]}\" | "
            f"results={result_count} | "
            f"confidence={confidence:.2f} | "
            f"time={search_time:.2f}s | "
            f"channel={channel_id} | "
            f"guild={guild_id}"
        )

    def log_feedback(
        self,
        user_id: str,
        search_id: str,
        feedback_type: str
    ):
        """フィードバックログを記録"""
        self.logger.info(
            f"FEEDBACK | "
            f"user={user_id} | "
            f"search_id={search_id} | "
            f"type={feedback_type}"
        )

    def log_error(
        self,
        error_code: str,
        message: str,
        user_id: str = None
    ):
        """エラーログを記録"""
        self.logger.error(
            f"ERROR | "
            f"code={error_code} | "
            f"message=\"{message}\" | "
            f"user={user_id}"
        )
