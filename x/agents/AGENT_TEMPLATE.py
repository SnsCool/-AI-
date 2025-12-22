"""
新規エージェント作成テンプレート

使用方法:
1. このファイルをコピーして適切なフォルダに配置
   - 実行系 → agents/execution/
   - 判断系 → agents/judgment/
   - 生成系 → agents/generation/

2. クラス名と各プロパティを変更

3. think() と execute() を実装

4. __init__.py にインポートを追加

5. orchestrator.py でregisterを呼び出し
"""

# サブフォルダ（execution/, judgment/, generation/）に配置する場合のインポート
from ..base import BaseAgent, AgentResult, AgentContext
from ..registry import AgentRegistry


class NewAgent(BaseAgent):
    """
    新規エージェント

    ここにエージェントの説明を書く。
    何ができるエージェントなのかを明確に。
    """

    def __init__(self):
        super().__init__()
        # 初期化処理があればここに

    @property
    def name(self) -> str:
        """
        エージェント名（一意である必要がある）
        司令塔はこの名前でエージェントを呼び出す
        """
        return "new_agent"

    @property
    def description(self) -> str:
        """
        エージェントの説明
        司令塔がどのエージェントを呼ぶか判断する際に使用
        """
        return "新規エージェント - 〇〇を実行"

    @property
    def agent_type(self) -> str:
        """
        エージェントタイプ
        - "execution": 実行系
        - "judgment": 判断系
        - "generation": 生成系
        """
        return "execution"

    def get_capabilities(self) -> list[str]:
        """
        このエージェントの能力一覧
        司令塔が振り分けを判断する際に参照
        """
        return [
            "capability_1",  # 能力1
            "capability_2",  # 能力2
        ]

    def can_handle(self, request: str) -> bool:
        """
        このエージェントがリクエストを処理できるか判定

        司令塔が複数エージェントから選択する際の補助判定。
        キーワードマッチングなどで実装。
        """
        keywords = ["キーワード1", "キーワード2"]
        request_lower = request.lower()
        return any(kw in request_lower for kw in keywords)

    def think(self, context: AgentContext) -> dict:
        """
        思考プロセス

        リクエストとコンテキストを分析し、
        どのようなアクションを取るべきか決定する。

        Args:
            context: 共有コンテキスト
                - context.original_request: 元のリクエスト
                - context.shared_data: 司令塔から渡されたパラメータ
                - context.history: 過去の実行履歴

        Returns:
            dict: 思考結果
                - action: 実行するアクション名
                - その他のパラメータ
        """
        shared_data = context.shared_data
        action = shared_data.get("action", "default_action")

        return {
            "action": action,
            "reasoning": f"アクション {action} を実行"
        }

    def execute(self, context: AgentContext, thought: dict) -> AgentResult:
        """
        実行プロセス

        思考結果に基づいて実際の処理を実行する。

        Args:
            context: 共有コンテキスト
            thought: think()の戻り値

        Returns:
            AgentResult:
                - success: 成功/失敗
                - message: メッセージ
                - data: 結果データ
                - next_agent: 次に呼ぶエージェント（連携する場合）
                - requires_approval: 承認が必要な場合True
        """
        action = thought.get("action", "default_action")

        try:
            # ここに実際の処理を実装
            self.log(f"Executing: {action}")

            # 成功時
            return AgentResult(
                success=True,
                message="処理が完了しました",
                data={"action": action, "result": "success"}
            )

        except Exception as e:
            # 失敗時
            return AgentResult(
                success=False,
                message=f"処理に失敗しました: {str(e)}",
                error=str(e)
            )


# モジュール読み込み時に自動登録する場合
def register():
    """エージェントを登録"""
    AgentRegistry.register(NewAgent())
