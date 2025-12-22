"""
エージェントレジストリ

全エージェントを登録・管理するシステム。
動的にエージェントを追加・削除できる。
"""

from typing import Optional, Type
from .base import BaseAgent


class AgentRegistry:
    """
    エージェントレジストリ

    全てのエージェントを登録し、名前やタイプで検索できる。
    """

    _instance = None
    _agents: dict[str, BaseAgent] = {}

    def __new__(cls):
        """シングルトンパターン"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._agents = {}
        return cls._instance

    @classmethod
    def register(cls, agent: BaseAgent) -> None:
        """エージェントを登録"""
        instance = cls()
        instance._agents[agent.name] = agent
        print(f"[Registry] Registered agent: {agent.name} ({agent.agent_type})")

    @classmethod
    def unregister(cls, agent_name: str) -> bool:
        """エージェントを登録解除"""
        instance = cls()
        if agent_name in instance._agents:
            del instance._agents[agent_name]
            print(f"[Registry] Unregistered agent: {agent_name}")
            return True
        return False

    @classmethod
    def get(cls, agent_name: str) -> Optional[BaseAgent]:
        """名前でエージェントを取得"""
        instance = cls()
        return instance._agents.get(agent_name)

    @classmethod
    def get_by_type(cls, agent_type: str) -> list[BaseAgent]:
        """タイプでエージェントを取得"""
        instance = cls()
        return [
            agent for agent in instance._agents.values()
            if agent.agent_type == agent_type
        ]

    @classmethod
    def list_all(cls) -> list[dict]:
        """全エージェント情報を取得"""
        instance = cls()
        return [
            {
                "name": agent.name,
                "type": agent.agent_type,
                "description": agent.description,
                "capabilities": agent.get_capabilities()
            }
            for agent in instance._agents.values()
        ]

    @classmethod
    def find_capable(cls, request: str) -> list[BaseAgent]:
        """リクエストを処理できるエージェントを検索"""
        instance = cls()
        return [
            agent for agent in instance._agents.values()
            if agent.can_handle(request)
        ]

    @classmethod
    def clear(cls) -> None:
        """全エージェントを削除"""
        instance = cls()
        instance._agents.clear()
        print("[Registry] Cleared all agents")

    @classmethod
    def get_commander(cls) -> Optional[BaseAgent]:
        """司令塔エージェントを取得"""
        commanders = cls.get_by_type("commander")
        return commanders[0] if commanders else None
