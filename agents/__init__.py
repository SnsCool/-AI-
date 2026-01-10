"""
統合AIエージェントシステム

構造:
├── main_agent.py    - メインエージェント（振り分け・制御・CLI）
├── x_agent.py       - Xサブエージェント（X投稿処理）
└── zoom_agent.py    - Zoomサブエージェント（Zoom分析処理）

使用方法:
    python -m agents.main_agent "X投稿を作成して"
    python -m agents.main_agent --interactive
"""

from .base import BaseAgent, AgentResult, AgentStatus, AgentContext
from .main_agent import MainAgent

__all__ = [
    "BaseAgent",
    "AgentResult",
    "AgentStatus",
    "AgentContext",
    "MainAgent",
]
