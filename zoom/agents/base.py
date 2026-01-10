"""
ベースエージェントクラス（Zoom用）

全てのエージェントが継承する基底クラス。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
import json


class AgentStatus(Enum):
    """エージェントの状態"""
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentResult:
    """エージェントの実行結果"""
    success: bool
    message: str
    data: Optional[dict] = None
    next_agent: Optional[str] = None
    requires_approval: bool = False
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
    max_steps: int = 10

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
    """全エージェントの基底クラス"""

    def __init__(self):
        self.status = AgentStatus.IDLE
        self._log_enabled = True

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    def agent_type(self) -> str:
        return "base"

    def log(self, message: str, level: str = "INFO"):
        if self._log_enabled:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] [{self.name}] [{level}] {message}", flush=True)

    @abstractmethod
    def think(self, context: AgentContext) -> dict:
        pass

    @abstractmethod
    def execute(self, context: AgentContext, thought: dict) -> AgentResult:
        pass

    def run(self, context: AgentContext) -> AgentResult:
        self.log(f"Starting agent run...")
        self.status = AgentStatus.THINKING

        try:
            self.log("Thinking...")
            thought = self.think(context)
            self.log(f"Thought: {thought.get('action', 'unknown')}")

            self.status = AgentStatus.EXECUTING
            self.log("Executing...")
            result = self.execute(context, thought)

            if result.success:
                self.status = AgentStatus.COMPLETED
                self.log(f"Completed: {result.message}")
            else:
                self.status = AgentStatus.FAILED
                self.log(f"Failed: {result.error}", level="ERROR")

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
        return False

    def get_capabilities(self) -> list[str]:
        return []
