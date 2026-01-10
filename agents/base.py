"""
ベースエージェントクラス

全てのエージェントが継承する基底クラス。
共通のインターフェースと機能を提供。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
import json


class AgentStatus(Enum):
    """エージェントの状態"""
    IDLE = "idle"           # 待機中
    THINKING = "thinking"   # 思考中
    EXECUTING = "executing" # 実行中
    WAITING = "waiting"     # 承認待ち
    COMPLETED = "completed" # 完了
    FAILED = "failed"       # 失敗
    CANCELLED = "cancelled" # キャンセル


@dataclass
class AgentResult:
    """エージェントの実行結果"""
    success: bool
    message: str
    data: Optional[dict] = None
    next_agent: Optional[str] = None  # 次に呼び出すべきエージェント
    requires_approval: bool = False    # 人の承認が必要か
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "next_agent": self.next_agent,
            "requires_approval": self.requires_approval,
            "error": self.error,
            "timestamp": self.timestamp
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


@dataclass
class AgentContext:
    """エージェント間で共有されるコンテキスト"""
    task_id: str
    original_request: str
    history: list = field(default_factory=list)
    shared_data: dict = field(default_factory=dict)
    current_step: int = 0
    max_steps: int = 10  # 無限ループ防止

    def add_history(self, agent_name: str, result: AgentResult):
        """履歴を追加"""
        self.history.append({
            "step": self.current_step,
            "agent": agent_name,
            "result": result.to_dict(),
            "timestamp": datetime.now().isoformat()
        })
        self.current_step += 1

    def get_last_result(self) -> Optional[AgentResult]:
        """最後の結果を取得"""
        if not self.history:
            return None
        last = self.history[-1]
        return AgentResult(**last["result"])


class BaseAgent(ABC):
    """
    全エージェントの基底クラス

    継承クラスは以下を実装する必要がある:
    - name: エージェント名
    - description: エージェントの説明
    - think(): 思考プロセス
    - execute(): 実行プロセス
    """

    def __init__(self):
        self.status = AgentStatus.IDLE
        self._log_enabled = True

    @property
    @abstractmethod
    def name(self) -> str:
        """エージェント名"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """エージェントの説明"""
        pass

    @property
    def agent_type(self) -> str:
        """エージェントタイプ (main/sub)"""
        return "sub"

    def log(self, message: str, level: str = "INFO"):
        """ログ出力"""
        if self._log_enabled:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] [{self.name}] [{level}] {message}", flush=True)

    @abstractmethod
    def think(self, context: AgentContext) -> dict:
        """
        思考プロセス

        与えられたコンテキストを分析し、どのように行動するかを決定する。

        Returns:
            dict: 思考結果 (action, reasoning, parameters など)
        """
        pass

    @abstractmethod
    def execute(self, context: AgentContext, thought: dict) -> AgentResult:
        """
        実行プロセス

        思考結果に基づいて実際のアクションを実行する。

        Returns:
            AgentResult: 実行結果
        """
        pass

    def run(self, context: AgentContext) -> AgentResult:
        """
        エージェントのメイン実行フロー

        1. 思考 (think)
        2. 実行 (execute)
        3. 結果返却
        """
        self.log(f"Starting agent run...")
        self.status = AgentStatus.THINKING

        try:
            # Step 1: 思考
            self.log("Thinking...")
            thought = self.think(context)
            self.log(f"Thought: {thought.get('action', 'unknown')}")

            # Step 2: 実行
            self.status = AgentStatus.EXECUTING
            self.log("Executing...")
            result = self.execute(context, thought)

            # Step 3: 結果
            if result.success:
                self.status = AgentStatus.COMPLETED
                self.log(f"Completed: {result.message}")
            else:
                self.status = AgentStatus.FAILED
                self.log(f"Failed: {result.error}", level="ERROR")

            # 履歴に追加
            context.add_history(self.name, result)

            return result

        except Exception as e:
            self.status = AgentStatus.FAILED
            error_msg = str(e)
            self.log(f"Error: {error_msg}", level="ERROR")
            result = AgentResult(
                success=False,
                message="Agent execution failed",
                error=error_msg
            )
            context.add_history(self.name, result)
            return result

    def can_handle(self, request: str) -> bool:
        """
        このエージェントがリクエストを処理できるか判定

        サブクラスでオーバーライドして詳細なロジックを実装
        """
        return False

    def get_capabilities(self) -> list[str]:
        """
        このエージェントの能力一覧を返す

        サブクラスでオーバーライドして具体的な能力を返す
        """
        return []
