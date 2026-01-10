#!/usr/bin/env python3
"""
統合メインエージェント (Main Agent)

役割:
- リクエストを理解・分析
- 適切なサブエージェントに振り分け
- ワークフロー全体の制御
- エージェント管理（Registry機能内蔵）
- CLI エントリーポイント

使用方法:
    python -m agents.main_agent "X投稿を作成して"
    python -m agents.main_agent "Zoom面談を分析して"
    python -m agents.main_agent --interactive
    python -m agents.main_agent --list-agents
"""

import argparse
import os
import json
import re
import sys
from typing import Optional
from datetime import datetime, timedelta, timezone

import google.generativeai as genai
from dotenv import load_dotenv

from .base import BaseAgent, AgentResult, AgentContext, AgentStatus

load_dotenv()

# タスクスケジュール設定
TASK_SCHEDULE = {
    "x_posting": {
        "hours": [7, 9, 18, 20],  # JST: 実行する時間
        "min_interval_hours": 3,  # 最小間隔（時間）
    },
    "zoom_analysis": {
        "min_interval_minutes": 30,  # 最小間隔（分）
        "check_new_recordings": True,  # 新規録画チェック
    },
}


class MainAgent(BaseAgent):
    """
    統合メインエージェント

    サブエージェントを管理し、タスクの振り分けと制御を行う。
    Gemini APIを使用して思考・判断を行う。
    """

    # サブエージェント管理（クラス変数）
    _sub_agents: dict[str, BaseAgent] = {}

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
                model_name="gemini-2.0-flash",
                system_instruction=self._get_system_prompt()
            )
            self.log("Gemini model initialized")
        else:
            self.log("Warning: GEMINI_API_KEY not found", level="WARN")

    def _get_system_prompt(self) -> str:
        """システムプロンプトを取得"""
        return """あなたは「メインエージェント」です。全てのタスクはあなたを経由して適切なサブエージェントに振り分けられます。

## あなたの役割
1. ユーザーからのリクエストを理解・分析する
2. 利用可能なサブエージェント一覧から最適なものを選択する
3. サブエージェントにパラメータを渡して実行を委譲する
4. 例外やエラーを検知して適切に対応する

## 振り分けルール

### x_agent（X投稿エージェント）に振り分け
- X（Twitter）関連の操作
- ツイート投稿、トレンド取得
- 動画投稿、模倣投稿作成
- キーワード: X投稿, ツイート, Twitter, トレンド, 投稿作成

### zoom_agent（Zoom分析エージェント）に振り分け
- Zoom面談の分析
- 文字起こし処理
- フィードバック生成
- ナレッジ蓄積
- キーワード: Zoom, 面談, 録画, 文字起こし, 分析, フィードバック

## 応答形式（必ずJSON）
{
    "understanding": "リクエストの理解内容",
    "action": "next_agent | complete | need_clarification | abort",
    "next_agent": "呼び出すサブエージェント名（x_agent または zoom_agent）",
    "parameters": {
        "action": "サブエージェント内のアクション",
        "その他のパラメータ": "値"
    },
    "reasoning": "なぜこのエージェントを選んだか",
    "message": "ユーザーへのメッセージ"
}

## 重要
- next_agentには「利用可能なサブエージェント一覧」に記載された名前のみ使用可能
- 該当するエージェントがない場合は need_clarification で確認
- エラーや危険な操作の場合は abort で中止
"""

    @property
    def name(self) -> str:
        return "main_agent"

    @property
    def description(self) -> str:
        return "メインエージェント - タスク振り分けと全体制御"

    @property
    def agent_type(self) -> str:
        return "main"

    def get_capabilities(self) -> list[str]:
        return [
            "task_routing",      # タスク振り分け
            "workflow_control",  # ワークフロー制御
            "exception_handling", # 例外対応
            "agent_coordination" # エージェント間調整
        ]

    def can_handle(self, request: str) -> bool:
        """メインエージェントは全てのリクエストを処理できる"""
        return True

    # =========================================================================
    # サブエージェント管理（Registry機能）
    # =========================================================================

    @classmethod
    def register_sub_agent(cls, agent: BaseAgent) -> None:
        """サブエージェントを登録"""
        cls._sub_agents[agent.name] = agent
        print(f"[MainAgent] Registered: {agent.name} ({agent.agent_type})")

    @classmethod
    def get_sub_agent(cls, agent_name: str) -> Optional[BaseAgent]:
        """名前でサブエージェントを取得"""
        return cls._sub_agents.get(agent_name)

    @classmethod
    def list_sub_agents(cls) -> list[dict]:
        """サブエージェント一覧を取得"""
        return [
            {
                "name": agent.name,
                "type": agent.agent_type,
                "description": agent.description,
                "capabilities": agent.get_capabilities()
            }
            for agent in cls._sub_agents.values()
        ]

    @classmethod
    def clear_sub_agents(cls) -> None:
        """全サブエージェントを削除"""
        cls._sub_agents.clear()

    def _get_available_agents_info(self) -> str:
        """登録済みサブエージェントの情報を取得"""
        agents = self.list_sub_agents()
        if not agents:
            return "現在登録されているサブエージェントはありません。"

        info_parts = []
        for agent in agents:
            info_parts.append(
                f"- {agent['name']}: {agent['description']}\n"
                f"  能力: {', '.join(agent['capabilities'])}"
            )

        return "\n".join(info_parts)

    # =========================================================================
    # 思考・実行プロセス
    # =========================================================================

    def think(self, context: AgentContext) -> dict:
        """
        思考プロセス

        リクエストを分析し、どのサブエージェントに振るかを決定する。
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
            recent = context.history[-3:]
            history_summary = "\n".join([
                f"Step {h['step']}: {h['agent']} - {h['result'].get('message', '')}"
                for h in recent
            ])

        # Geminiに問い合わせ
        prompt = f"""
ユーザーリクエスト: {context.original_request}

利用可能なサブエージェント:
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
                    "message": "AI応答の解析に失敗しました"
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
            return AgentResult(
                success=True,
                message=message or "タスクが完了しました",
                data=thought.get("parameters")
            )

        elif action == "need_clarification":
            return AgentResult(
                success=True,
                message=message or "確認が必要です",
                requires_approval=True,
                data={"clarification_needed": thought.get("parameters")}
            )

        elif action == "next_agent":
            # サブエージェントを呼び出し
            next_agent_name = thought.get("next_agent")
            if not next_agent_name:
                return AgentResult(
                    success=False,
                    message="次のエージェントが指定されていません",
                    error="next_agent not specified"
                )

            next_agent = self.get_sub_agent(next_agent_name)
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

            return sub_result

        elif action == "abort":
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

        Args:
            request: ユーザーリクエスト
            max_iterations: 最大反復回数

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

            current_result = self.run(context)

            if not current_result.success:
                self.log(f"Failed at iteration {iteration}")
                break

            if current_result.requires_approval:
                self.log("Waiting for approval...")
                break

            if not current_result.next_agent:
                self.log("Completed")
                break

        self.log("=" * 50)
        self.log(f"Orchestration completed: {current_result.message if current_result else 'No result'}")
        self.log("=" * 50)

        return current_result

    # =========================================================================
    # スケジューラーモード（統一トリガー）
    # =========================================================================

    def _get_supabase_client(self):
        """Supabaseクライアントを取得"""
        try:
            from zoom.services.supabase_client import get_supabase_client
            return get_supabase_client()
        except ImportError:
            self.log("Warning: Could not import supabase_client", level="WARN")
            return None

    def _get_last_execution(self, task_type: str) -> Optional[datetime]:
        """タスクの最終実行時刻を取得"""
        client = self._get_supabase_client()
        if not client:
            return None

        try:
            result = client.table("task_execution_log").select("executed_at").eq(
                "task_type", task_type
            ).order("executed_at", desc=True).limit(1).execute()

            if result.data and len(result.data) > 0:
                executed_at = result.data[0]["executed_at"]
                return datetime.fromisoformat(executed_at.replace("Z", "+00:00"))
            return None
        except Exception as e:
            self.log(f"Error getting last execution: {e}", level="WARN")
            return None

    def _log_task_execution(self, task_type: str, status: str, details: dict = None):
        """タスク実行をログに記録"""
        client = self._get_supabase_client()
        if not client:
            return

        try:
            client.table("task_execution_log").insert({
                "task_type": task_type,
                "executed_at": datetime.now(timezone.utc).isoformat(),
                "status": status,
                "details": details or {}
            }).execute()
        except Exception as e:
            self.log(f"Error logging task execution: {e}", level="WARN")

    def _check_new_zoom_recordings(self) -> bool:
        """未処理のZoom録画があるかチェック"""
        try:
            from zoom.services.supabase_client import get_supabase_client
            from zoom.services.zoom_client import get_zoom_access_token, get_zoom_recordings

            client = get_supabase_client()

            # アカウント取得
            result = client.table("zoom_accounts").select("*").execute()
            accounts = result.data if result.data else []

            for account in accounts:
                try:
                    access_token = get_zoom_access_token(
                        account["account_id"],
                        account["client_id"],
                        account["client_secret"]
                    )
                    recordings = get_zoom_recordings(access_token)

                    # 未処理の録画があるかチェック
                    for rec in recordings:
                        meeting_id = rec.get("meeting_id")
                        check = client.table("processed_recordings").select("id").eq(
                            "recording_id", meeting_id
                        ).execute()
                        if not check.data or len(check.data) == 0:
                            return True  # 未処理の録画あり
                except Exception:
                    continue

            return False
        except Exception as e:
            self.log(f"Error checking new recordings: {e}", level="WARN")
            return False

    def decide_tasks(self) -> list[str]:
        """
        実行すべきタスクを決定

        Returns:
            list[str]: 実行すべきタスクのリスト
        """
        tasks = []
        now = datetime.now(timezone.utc)
        jst = timezone(timedelta(hours=9))
        now_jst = now.astimezone(jst)

        self.log(f"Current time (JST): {now_jst.strftime('%Y-%m-%d %H:%M')}")

        # X投稿チェック
        x_schedule = TASK_SCHEDULE["x_posting"]
        x_last = self._get_last_execution("x_posting")

        should_run_x = False
        if now_jst.hour in x_schedule["hours"]:
            # 指定時刻内
            if x_last is None:
                should_run_x = True
            else:
                hours_since = (now - x_last).total_seconds() / 3600
                if hours_since >= x_schedule["min_interval_hours"]:
                    should_run_x = True

        if should_run_x:
            tasks.append("x_posting")
            self.log("Task added: x_posting")

        # Zoom分析チェック
        zoom_schedule = TASK_SCHEDULE["zoom_analysis"]
        zoom_last = self._get_last_execution("zoom_analysis")

        should_run_zoom = False
        if zoom_last is None:
            should_run_zoom = True
        else:
            minutes_since = (now - zoom_last).total_seconds() / 60
            if minutes_since >= zoom_schedule["min_interval_minutes"]:
                should_run_zoom = True

        # 新しい録画があるかチェック
        if should_run_zoom and zoom_schedule.get("check_new_recordings"):
            if self._check_new_zoom_recordings():
                tasks.append("zoom_analysis")
                self.log("Task added: zoom_analysis (new recordings found)")
            else:
                self.log("Skipped: zoom_analysis (no new recordings)")
        elif should_run_zoom:
            tasks.append("zoom_analysis")
            self.log("Task added: zoom_analysis")

        return tasks

    def run_scheduled_tasks(self) -> dict:
        """
        スケジュールされたタスクを実行

        Returns:
            dict: 実行結果
        """
        self.log("=" * 60)
        self.log("Scheduler Mode Started")
        self.log("=" * 60)

        # 実行すべきタスクを決定
        tasks = self.decide_tasks()

        if not tasks:
            self.log("No tasks to run")
            return {"tasks": [], "results": []}

        self.log(f"Tasks to run: {tasks}")

        results = []

        for task_type in tasks:
            self.log(f"\n--- Running: {task_type} ---")

            try:
                if task_type == "x_posting":
                    agent = self.get_sub_agent("x_agent")
                    if agent:
                        context = AgentContext(
                            task_id=f"scheduled_{task_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                            original_request="スケジュールされたX投稿を実行",
                            shared_data={"action": "full_workflow", "post_to_x": True}
                        )
                        result = agent.run(context)
                        status = "success" if result.success else "failed"
                        self._log_task_execution(task_type, status, {"message": result.message})
                        results.append({"task": task_type, "success": result.success, "message": result.message})
                    else:
                        self._log_task_execution(task_type, "failed", {"error": "Agent not found"})
                        results.append({"task": task_type, "success": False, "message": "Agent not found"})

                elif task_type == "zoom_analysis":
                    agent = self.get_sub_agent("zoom_agent")
                    if agent:
                        context = AgentContext(
                            task_id=f"scheduled_{task_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                            original_request="スケジュールされたZoom分析を実行",
                            shared_data={"action": "batch_process"}
                        )
                        result = agent.run(context)
                        status = "success" if result.success else "failed"
                        self._log_task_execution(task_type, status, {"message": result.message})
                        results.append({"task": task_type, "success": result.success, "message": result.message})
                    else:
                        self._log_task_execution(task_type, "failed", {"error": "Agent not found"})
                        results.append({"task": task_type, "success": False, "message": "Agent not found"})

            except Exception as e:
                self.log(f"Error running {task_type}: {e}")
                self._log_task_execution(task_type, "failed", {"error": str(e)})
                results.append({"task": task_type, "success": False, "message": str(e)})

        self.log("\n" + "=" * 60)
        self.log("Scheduler Mode Completed")
        self.log("=" * 60)

        return {"tasks": tasks, "results": results}


# =============================================================================
# CLI エントリーポイント
# =============================================================================

def initialize_agents() -> MainAgent:
    """全エージェントを初期化・登録"""
    from .x_agent import XAgent
    from .zoom_agent import ZoomAgent

    print("=" * 60)
    print("統合AIエージェントシステム")
    print("=" * 60)
    print()

    # メインエージェント作成
    main_agent = MainAgent()

    # サブエージェントを登録
    main_agent.register_sub_agent(XAgent())
    main_agent.register_sub_agent(ZoomAgent())

    print()
    return main_agent


def list_agents(main_agent: MainAgent):
    """登録済みエージェントを表示"""
    print("\n登録済みサブエージェント:")
    print("-" * 40)

    agents = main_agent.list_sub_agents()
    if not agents:
        print("  (なし)")
        return

    for agent in agents:
        print(f"\n【{agent['name']}】")
        print(f"  説明: {agent['description']}")
        print(f"  能力: {', '.join(agent['capabilities'])}")


def process_request(main_agent: MainAgent, request: str) -> bool:
    """リクエストを処理"""
    print(f"\nリクエスト: {request}")
    print("-" * 40)

    result = main_agent.orchestrate(request)

    print("\n" + "=" * 60)
    print("実行結果")
    print("=" * 60)
    print(f"成功: {'はい' if result.success else 'いいえ'}")
    print(f"メッセージ: {result.message}")

    if result.data:
        print(f"データ: {result.data}")

    if result.error:
        print(f"エラー: {result.error}")

    return result.success


def interactive_mode(main_agent: MainAgent):
    """対話モード"""
    print("\n対話モード開始")
    print("終了: exit | ヘルプ: help | エージェント一覧: list")
    print("-" * 40)

    while True:
        try:
            request = input("\n>>> ").strip()

            if not request:
                continue

            if request.lower() in ["exit", "quit", "q"]:
                print("終了します")
                break

            if request.lower() == "help":
                print("\n使用例:")
                print("  X投稿を作成して")
                print("  Zoom面談を分析して")
                continue

            if request.lower() == "list":
                list_agents(main_agent)
                continue

            process_request(main_agent, request)

        except KeyboardInterrupt:
            print("\n終了します")
            break


def main():
    """メインエントリーポイント"""
    parser = argparse.ArgumentParser(
        description="統合AIエージェントシステム"
    )
    parser.add_argument(
        "request",
        nargs="?",
        help="処理するリクエスト"
    )
    parser.add_argument(
        "--list-agents",
        action="store_true",
        help="登録済みエージェント一覧"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="対話モード"
    )
    parser.add_argument(
        "--scheduler",
        action="store_true",
        help="スケジューラーモード（自動タスク実行）"
    )

    args = parser.parse_args()

    # エージェント初期化
    main_agent = initialize_agents()

    if args.list_agents:
        list_agents(main_agent)
        sys.exit(0)

    if args.scheduler:
        # スケジューラーモード
        result = main_agent.run_scheduled_tasks()
        print(f"\n実行タスク: {result['tasks']}")
        for r in result['results']:
            status = "成功" if r['success'] else "失敗"
            print(f"  {r['task']}: {status} - {r['message']}")
        sys.exit(0 if all(r['success'] for r in result['results']) else 1)

    if args.interactive:
        interactive_mode(main_agent)
        sys.exit(0)

    if args.request:
        success = process_request(main_agent, args.request)
        sys.exit(0 if success else 1)

    # 引数なしは対話モード
    interactive_mode(main_agent)


if __name__ == "__main__":
    main()
