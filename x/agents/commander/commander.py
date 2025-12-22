"""
司令塔エージェント (Commander Agent)

役割:
- 依頼内容を理解
- どのエージェントに振るか判断
- 例外対応・止める判断
- ワークフロー全体の制御

設計原則:
- こいつがいないと崩壊する
- 全てのリクエストはまずこのエージェントを経由
"""

import os
import json
import re
from typing import Optional
from datetime import datetime

import google.generativeai as genai
from dotenv import load_dotenv

from ..base import BaseAgent, AgentResult, AgentContext, AgentStatus
from ..registry import AgentRegistry

load_dotenv()


class CommanderAgent(BaseAgent):
    """
    司令塔エージェント

    全エージェントを統括し、タスクの振り分けと制御を行う。
    Gemini APIを使用して思考・判断を行う。
    """

    def __init__(self):
        super().__init__()
        self._gemini_api_key = os.getenv("GEMINI_API_KEY")
        self._model = None
        self._initialize_gemini()

    def _initialize_gemini(self):
        """Geminiモデルを初期化"""
        if self._gemini_api_key:
            genai.configure(api_key=self._gemini_api_key)
            self._model = genai.GenerativeModel(
                model_name="gemini-2.0-flash-exp",
                system_instruction=self._get_system_prompt()
            )
            self.log("Gemini model initialized")
        else:
            self.log("Warning: GEMINI_API_KEY not found", level="WARN")

    def _get_system_prompt(self) -> str:
        """システムプロンプトを取得"""
        return """あなたは「司令塔エージェント」です。全てのタスクはあなたを経由して適切なサブエージェントに振り分けられます。

## あなたの役割
1. ユーザーからのリクエストを理解・分析する
2. 利用可能なエージェント一覧から最適なものを選択する
3. エージェントにパラメータを渡して実行を委譲する
4. 例外やエラーを検知して適切に対応する
5. 複数エージェントの連携が必要な場合は順番に呼び出す

## 振り分けルール
リクエスト内容を分析し、以下のルールで振り分けてください：

### execution（実行系）に振り分け
- データ取得、投稿、更新など「具体的な作業」
- API呼び出し、ファイル操作
- 例: 「X投稿して」「トレンド取得して」「データをアップロード」

### judgment（判断系）に振り分け
- 分類、ルール判断、承認チェック
- 「〜すべきか？」「どれが適切か？」
- 例: 「どのフォーマットを使うべき？」「この内容は投稿OK？」

### generation（生成系）に振り分け
- 文章作成、レポート生成
- 例: 「投稿文を作成して」「レポートを生成して」

## 応答形式（必ずJSON）
{
    "understanding": "リクエストの理解内容",
    "action": "next_agent | complete | need_clarification | abort",
    "next_agent": "呼び出すエージェント名（利用可能なエージェントから選択）",
    "parameters": {
        "action": "エージェント内のアクション（full_workflow, fetch_only, test など）",
        "その他のパラメータ": "値"
    },
    "reasoning": "なぜこのエージェントを選んだか",
    "message": "ユーザーへのメッセージ"
}

## 重要
- next_agentには「利用可能なエージェント一覧」に記載された名前のみ使用可能
- 該当するエージェントがない場合は need_clarification で確認
- エラーや危険な操作の場合は abort で中止
"""

    @property
    def name(self) -> str:
        return "commander"

    @property
    def description(self) -> str:
        return "司令塔エージェント - タスク振り分けと全体制御"

    @property
    def agent_type(self) -> str:
        return "commander"

    def get_capabilities(self) -> list[str]:
        return [
            "task_routing",      # タスク振り分け
            "workflow_control",  # ワークフロー制御
            "exception_handling", # 例外対応
            "agent_coordination" # エージェント間調整
        ]

    def can_handle(self, request: str) -> bool:
        """司令塔は全てのリクエストを処理できる"""
        return True

    def _get_available_agents_info(self) -> str:
        """登録済みエージェントの情報を取得"""
        agents = AgentRegistry.list_all()
        if not agents:
            return "現在登録されているエージェントはありません。"

        info_parts = []
        for agent in agents:
            if agent["name"] != "commander":  # 自分以外
                info_parts.append(
                    f"- {agent['name']} ({agent['type']}): {agent['description']}\n"
                    f"  能力: {', '.join(agent['capabilities'])}"
                )

        return "\n".join(info_parts) if info_parts else "サブエージェントが登録されていません。"

    def think(self, context: AgentContext) -> dict:
        """
        思考プロセス

        リクエストを分析し、どのエージェントに振るかを決定する。
        """
        if not self._model:
            return {
                "action": "abort",
                "reasoning": "Gemini API key not configured",
                "message": "AIモデルが設定されていません"
            }

        # 利用可能なエージェント情報を取得
        available_agents = self._get_available_agents_info()

        # コンテキスト情報を構築
        history_summary = ""
        if context.history:
            recent = context.history[-3:]  # 最新3件
            history_summary = "\n".join([
                f"Step {h['step']}: {h['agent']} - {h['result'].get('message', '')}"
                for h in recent
            ])

        # Geminiに問い合わせ
        prompt = f"""
ユーザーリクエスト: {context.original_request}

利用可能なエージェント:
{available_agents}

過去の履歴:
{history_summary if history_summary else "なし"}

共有データ:
{json.dumps(context.shared_data, ensure_ascii=False) if context.shared_data else "なし"}

現在のステップ: {context.current_step} / {context.max_steps}

上記を分析し、次のアクションをJSON形式で決定してください。
"""

        try:
            response = self._model.generate_content(prompt)
            response_text = response.text

            # JSONを抽出
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                thought = json.loads(json_match.group())
                return thought
            else:
                return {
                    "action": "abort",
                    "reasoning": "Failed to parse AI response",
                    "message": "AI応答の解析に失敗しました",
                    "raw_response": response_text
                }

        except Exception as e:
            return {
                "action": "abort",
                "reasoning": f"Gemini API error: {str(e)}",
                "message": "AI処理中にエラーが発生しました"
            }

    def execute(self, context: AgentContext, thought: dict) -> AgentResult:
        """
        実行プロセス

        思考結果に基づいてアクションを実行する。
        """
        action = thought.get("action", "abort")
        message = thought.get("message", "")
        reasoning = thought.get("reasoning", "")

        self.log(f"Action: {action}, Reasoning: {reasoning}")

        if action == "complete":
            # タスク完了
            return AgentResult(
                success=True,
                message=message or "タスクが完了しました",
                data=thought.get("parameters")
            )

        elif action == "need_clarification":
            # 確認が必要
            return AgentResult(
                success=True,
                message=message or "確認が必要です",
                requires_approval=True,
                data={"clarification_needed": thought.get("parameters")}
            )

        elif action == "next_agent":
            # 次のエージェントを呼び出し
            next_agent_name = thought.get("next_agent")
            if not next_agent_name:
                return AgentResult(
                    success=False,
                    message="次のエージェントが指定されていません",
                    error="next_agent not specified"
                )

            next_agent = AgentRegistry.get(next_agent_name)
            if not next_agent:
                return AgentResult(
                    success=False,
                    message=f"エージェント '{next_agent_name}' が見つかりません",
                    error=f"Agent not found: {next_agent_name}"
                )

            # パラメータを共有データに追加
            if thought.get("parameters"):
                context.shared_data.update(thought["parameters"])

            # サブエージェントを実行
            self.log(f"Delegating to: {next_agent_name}")
            sub_result = next_agent.run(context)

            # サブエージェントの結果に基づいて次のアクションを決定
            if sub_result.next_agent:
                return AgentResult(
                    success=sub_result.success,
                    message=sub_result.message,
                    data=sub_result.data,
                    next_agent=sub_result.next_agent
                )
            else:
                return sub_result

        elif action == "abort":
            # 中止
            return AgentResult(
                success=False,
                message=message or "タスクが中止されました",
                error=reasoning
            )

        else:
            return AgentResult(
                success=False,
                message=f"Unknown action: {action}",
                error=f"Unknown action type: {action}"
            )

    def orchestrate(self, request: str, max_iterations: int = 10) -> AgentResult:
        """
        完全なオーケストレーションを実行

        リクエストを受け取り、完了するまでエージェントを
        連鎖的に実行する。

        Args:
            request: ユーザーリクエスト
            max_iterations: 最大反復回数（無限ループ防止）

        Returns:
            AgentResult: 最終結果
        """
        self.log("=" * 50)
        self.log(f"Orchestration started: {request}")
        self.log("=" * 50)

        # コンテキストを作成
        context = AgentContext(
            task_id=f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            original_request=request,
            max_steps=max_iterations
        )

        iteration = 0
        current_result = None

        while iteration < max_iterations:
            iteration += 1
            self.log(f"\n--- Iteration {iteration} ---")

            # 司令塔が実行
            current_result = self.run(context)

            # 完了条件をチェック
            if not current_result.success:
                self.log(f"Failed at iteration {iteration}")
                break

            if current_result.requires_approval:
                self.log("Waiting for approval...")
                break

            if not current_result.next_agent:
                self.log("No next agent, completing...")
                break

            # 次のエージェントがある場合は継続
            # (next_agentの処理は execute() で既に行われている)

        self.log("=" * 50)
        self.log(f"Orchestration completed: {current_result.message if current_result else 'No result'}")
        self.log("=" * 50)

        return current_result


# モジュール読み込み時に自動登録
def register():
    """司令塔エージェントを登録"""
    AgentRegistry.register(CommanderAgent())
