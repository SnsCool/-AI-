"""
Xサブエージェント (X Sub Agent)

役割:
- X（Twitter）関連の操作を実行
- 動画トレンド取得
- 模倣テキスト生成
- Google Driveアップロード
- X投稿

x/main.py の関数を呼び出して処理を実行する。
"""

import sys
from pathlib import Path

# x/main.py をインポートするためにパスを追加
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from .base import BaseAgent, AgentResult, AgentContext


class XAgent(BaseAgent):
    """
    Xサブエージェント

    X（Twitter）関連の操作を実行する。
    """

    def __init__(self):
        super().__init__()
        self._x_module = None
        self._load_x_module()

    def _load_x_module(self):
        """x/main.py モジュールを動的にロード"""
        try:
            from x import main as x_main
            self._x_module = x_main
            self.log("X module loaded successfully")
        except ImportError as e:
            self.log(f"Warning: Could not load x module: {e}", level="WARN")

    @property
    def name(self) -> str:
        return "x_agent"

    @property
    def description(self) -> str:
        return "Xサブエージェント - X投稿・トレンド取得・模倣投稿作成"

    @property
    def agent_type(self) -> str:
        return "sub"

    def get_capabilities(self) -> list[str]:
        return [
            "fetch_video_trends",    # 動画トレンド取得
            "generate_mimic_text",   # 模倣テキスト生成
            "upload_to_drive",       # Google Driveアップロード
            "post_to_x",             # X投稿
            "download_video"         # 動画ダウンロード
        ]

    def can_handle(self, request: str) -> bool:
        """X関連のリクエストを処理できるか判定"""
        keywords = [
            "x投稿", "twitter投稿", "ツイート",
            "動画トレンド", "video trend",
            "manusai", "投稿作成", "模倣",
            "トレンド取得", "自動投稿"
        ]
        request_lower = request.lower()
        return any(kw in request_lower for kw in keywords)

    def think(self, context: AgentContext) -> dict:
        """
        思考プロセス

        リクエストを分析し、どのアクションを実行するかを決定する。
        """
        request = context.original_request.lower()
        shared_data = context.shared_data

        # メインエージェントから渡されたパラメータを確認
        action = shared_data.get("action", "full_workflow")
        format_name = shared_data.get("format_name")
        post_to_x = shared_data.get("post_to_x", False)

        # リクエスト内容から追加のパラメータを抽出
        if "テスト" in request or "test" in request:
            action = "test"
        elif "取得" in request and "投稿" not in request:
            action = "fetch_only"
        elif "投稿" in request and ("する" in request or "して" in request):
            post_to_x = True

        return {
            "action": action,
            "format_name": format_name,
            "post_to_x": post_to_x,
            "reasoning": f"Action: {action}, Format: {format_name}, Post: {post_to_x}"
        }

    def execute(self, context: AgentContext, thought: dict) -> AgentResult:
        """
        実行プロセス

        思考結果に基づいて実際のX投稿ワークフローを実行する。
        """
        action = thought.get("action", "full_workflow")
        format_name = thought.get("format_name")
        post_to_x = thought.get("post_to_x", False)

        self.log(f"Executing action: {action}")

        if not self._x_module:
            return AgentResult(
                success=False,
                message="x/main.py モジュールが読み込めません",
                error="X module not loaded"
            )

        try:
            if action == "test":
                return self._execute_test()

            elif action == "fetch_only":
                return self._execute_fetch_only()

            elif action == "full_workflow":
                return self._execute_full_workflow(
                    format_name=format_name,
                    skip_x_post=not post_to_x
                )

            else:
                return AgentResult(
                    success=False,
                    message=f"Unknown action: {action}",
                    error=f"Unknown action: {action}"
                )

        except Exception as e:
            return AgentResult(
                success=False,
                message=f"実行エラー: {str(e)}",
                error=str(e)
            )

    def _execute_test(self) -> AgentResult:
        """テストモードを実行"""
        self.log("Running test mode...")

        try:
            # フォーマット一覧を取得
            formats = self._x_module.list_available_formats()

            # Brain データを読み込み
            brain_data = self._x_module.load_brain_data()

            return AgentResult(
                success=True,
                message="テスト完了",
                data={
                    "available_formats": formats,
                    "brain_data_loaded": bool(brain_data),
                    "target_account": getattr(self._x_module, 'TARGET_X_USERNAME', 'unknown')
                }
            )

        except Exception as e:
            return AgentResult(
                success=False,
                message=f"テスト失敗: {str(e)}",
                error=str(e)
            )

    def _execute_fetch_only(self) -> AgentResult:
        """取得のみを実行"""
        self.log("Fetching tweets only...")

        try:
            tweets = self._x_module.fetch_tweets_with_video(
                self._x_module.SEARCH_QUERY,
                self._x_module.MAX_TWEETS
            )

            if tweets:
                save_path = self._x_module.save_tweets_to_analysis(tweets)
                return AgentResult(
                    success=True,
                    message=f"{len(tweets)}件のツイートを取得しました",
                    data={
                        "tweet_count": len(tweets),
                        "save_path": save_path
                    }
                )
            else:
                return AgentResult(
                    success=False,
                    message="ツイートが見つかりませんでした",
                    error="No tweets found"
                )

        except Exception as e:
            return AgentResult(
                success=False,
                message=f"取得失敗: {str(e)}",
                error=str(e)
            )

    def _execute_full_workflow(
        self,
        format_name: str = None,
        skip_x_post: bool = True
    ) -> AgentResult:
        """完全なワークフローを実行"""
        self.log(f"Running full workflow (format={format_name}, skip_x_post={skip_x_post})...")

        try:
            # process_tweets関数を呼び出し
            self._x_module.process_tweets(
                format_name=format_name,
                skip_x_post=skip_x_post
            )

            return AgentResult(
                success=True,
                message="X投稿ワークフローが完了しました",
                data={
                    "format_used": format_name or getattr(self._x_module, 'DEFAULT_FORMAT', 'default'),
                    "x_posting": not skip_x_post
                }
            )

        except Exception as e:
            return AgentResult(
                success=False,
                message=f"ワークフロー失敗: {str(e)}",
                error=str(e)
            )
