"""
X投稿エージェント (X Posting Agent)

役割:
- @ManusAI_JP からトレンド動画を取得
- 動画をダウンロード
- 模倣テキストを生成
- Google Driveにアップロード
- X (Twitter) に投稿

実行エージェントとして、具体的な作業を担当する。
"""

import os
import sys
from pathlib import Path

# main.pyの関数をインポートするためにパスを追加
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from ..base import BaseAgent, AgentResult, AgentContext
from ..registry import AgentRegistry


class XPostingAgent(BaseAgent):
    """
    X投稿エージェント

    動画トレンドを取得し、模倣投稿を作成・投稿する。
    """

    def __init__(self):
        super().__init__()
        self._main_module = None
        self._load_main_module()

    def _load_main_module(self):
        """main.pyモジュールを動的にロード"""
        try:
            import main as main_module
            self._main_module = main_module
            self.log("Main module loaded successfully")
        except ImportError as e:
            self.log(f"Warning: Could not load main module: {e}", level="WARN")

    @property
    def name(self) -> str:
        return "x_posting"

    @property
    def description(self) -> str:
        return "X投稿エージェント - 動画トレンド取得・模倣投稿作成・X投稿"

    @property
    def agent_type(self) -> str:
        return "execution"

    def get_capabilities(self) -> list[str]:
        return [
            "fetch_video_trends",    # 動画トレンド取得
            "generate_mimic_text",   # 模倣テキスト生成
            "upload_to_drive",       # Google Driveアップロード
            "post_to_x",             # X投稿
            "download_video"         # 動画ダウンロード
        ]

    def can_handle(self, request: str) -> bool:
        """X投稿関連のリクエストを処理できるか判定"""
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

        # 司令塔から渡されたパラメータを確認
        action = shared_data.get("action", "full_workflow")
        format_name = shared_data.get("format_name")
        post_to_x = shared_data.get("post_to_x", False)

        # リクエスト内容から追加のパラメータを抽出
        if "テスト" in request or "test" in request:
            action = "test"
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

        if not self._main_module:
            return AgentResult(
                success=False,
                message="main.pyモジュールが読み込めません",
                error="Main module not loaded"
            )

        try:
            if action == "test":
                # テストモード
                return self._execute_test()

            elif action == "fetch_only":
                # 取得のみ
                return self._execute_fetch_only()

            elif action == "full_workflow":
                # 完全なワークフロー実行
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
            formats = self._main_module.list_available_formats()

            # Brain データを読み込み
            brain_data = self._main_module.load_brain_data()

            return AgentResult(
                success=True,
                message="テスト完了",
                data={
                    "available_formats": formats,
                    "brain_data_loaded": bool(brain_data),
                    "target_account": self._main_module.TARGET_X_USERNAME
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
            tweets = self._main_module.fetch_tweets_with_video(
                self._main_module.SEARCH_QUERY,
                self._main_module.MAX_TWEETS
            )

            if tweets:
                save_path = self._main_module.save_tweets_to_analysis(tweets)
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
            self._main_module.process_tweets(
                format_name=format_name,
                skip_x_post=skip_x_post
            )

            return AgentResult(
                success=True,
                message="ワークフローが完了しました",
                data={
                    "format_used": format_name or self._main_module.DEFAULT_FORMAT,
                    "x_posting": not skip_x_post
                }
            )

        except Exception as e:
            return AgentResult(
                success=False,
                message=f"ワークフロー失敗: {str(e)}",
                error=str(e)
            )


# モジュール読み込み時に自動登録
def register():
    """X投稿エージェントを登録"""
    AgentRegistry.register(XPostingAgent())
