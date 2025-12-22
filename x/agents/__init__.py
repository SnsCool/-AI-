"""
AIエージェントシステム - マルチエージェントアーキテクチャ

構造:
├── commander/     - 司令塔エージェント（振り分け・制御）
├── judgment/      - 判断エージェント（分類・ルール判断）
├── execution/     - 実行エージェント（DB・通知・更新）
└── generation/    - 生成エージェント（文章・資料作成）

設計原則:
1. 「判断」と「作業」を分ける
2. 司令塔が必ず最初に起動
3. 各エージェントは独立して動作可能
4. 人の承認トリガーを組み込む（安全装置）
"""

from .base import BaseAgent, AgentResult, AgentStatus
from .registry import AgentRegistry

__all__ = ["BaseAgent", "AgentResult", "AgentStatus", "AgentRegistry"]
