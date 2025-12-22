#!/usr/bin/env python3
"""
AIエージェントオーケストレーター

マルチエージェントシステムのメインエントリーポイント。

使用方法:
    # リクエストを処理
    python orchestrator.py "X投稿を作成して"

    # エージェント一覧を表示
    python orchestrator.py --list-agents

    # テストモード
    python orchestrator.py --test

アーキテクチャ:
┌─────────────────────────────────────────────────────┐
│                   Orchestrator                       │
│  ┌─────────────────────────────────────────────┐    │
│  │            Commander (司令塔)                │    │
│  │  - リクエスト理解                            │    │
│  │  - エージェント振り分け                      │    │
│  │  - 例外対応・制御                            │    │
│  └─────────────────────────────────────────────┘    │
│         │              │              │              │
│         ▼              ▼              ▼              │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐         │
│  │ Judgment │   │Execution │   │Generation│         │
│  │ 判断系   │   │ 実行系   │   │ 生成系   │         │
│  └──────────┘   └──────────┘   └──────────┘         │
│                      │                               │
│                      ▼                               │
│               ┌──────────────┐                       │
│               │  X Posting   │                       │
│               │  Agent       │                       │
│               └──────────────┘                       │
└─────────────────────────────────────────────────────┘
"""

import argparse
import sys
from datetime import datetime

# エージェントシステムをインポート
from agents import AgentRegistry
from agents.commander import CommanderAgent
from agents.execution import XPostingAgent


def initialize_agents():
    """全エージェントを初期化・登録"""
    print("=" * 60)
    print("AIエージェントシステム 初期化中...")
    print("=" * 60)
    print()

    # エージェントを登録
    AgentRegistry.register(CommanderAgent())
    AgentRegistry.register(XPostingAgent())

    print()
    print("登録済みエージェント:")
    for agent_info in AgentRegistry.list_all():
        print(f"  - {agent_info['name']} ({agent_info['type']})")
        print(f"    {agent_info['description']}")
    print()


def list_agents():
    """登録済みエージェントを表示"""
    print("\n登録済みエージェント一覧:")
    print("-" * 40)

    agents = AgentRegistry.list_all()
    if not agents:
        print("  (なし)")
        return

    for agent in agents:
        print(f"\n【{agent['name']}】 ({agent['type']})")
        print(f"  説明: {agent['description']}")
        print(f"  能力: {', '.join(agent['capabilities'])}")


def run_test():
    """テストモードを実行"""
    print("\nテストモードを実行中...")
    print("-" * 40)

    # 司令塔エージェントを取得
    commander = AgentRegistry.get_commander()
    if not commander:
        print("Error: Commander agent not found")
        return False

    # テストリクエストを実行
    test_requests = [
        "現在のエージェント状態を確認して",
        "X投稿のテストを実行して",
    ]

    for request in test_requests:
        print(f"\n>>> テストリクエスト: {request}")
        result = commander.orchestrate(request, max_iterations=3)
        print(f"結果: {result.message}")
        if result.data:
            print(f"データ: {result.data}")

    return True


def process_request(request: str):
    """リクエストを処理"""
    print(f"\nリクエスト受付: {request}")
    print("-" * 40)

    # 司令塔エージェントを取得
    commander = AgentRegistry.get_commander()
    if not commander:
        print("Error: Commander agent not found")
        sys.exit(1)

    # オーケストレーションを実行
    result = commander.orchestrate(request)

    print("\n" + "=" * 60)
    print("実行結果")
    print("=" * 60)
    print(f"成功: {'はい' if result.success else 'いいえ'}")
    print(f"メッセージ: {result.message}")

    if result.data:
        print(f"データ: {result.data}")

    if result.error:
        print(f"エラー: {result.error}")

    if result.requires_approval:
        print("\n⚠ 承認が必要です")

    return result.success


def main():
    """メインエントリーポイント"""
    parser = argparse.ArgumentParser(
        description="AIエージェントオーケストレーター"
    )
    parser.add_argument(
        "request",
        nargs="?",
        help="処理するリクエスト"
    )
    parser.add_argument(
        "--list-agents",
        action="store_true",
        help="登録済みエージェント一覧を表示"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="テストモードを実行"
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="対話モードを起動"
    )

    args = parser.parse_args()

    # エージェントを初期化
    initialize_agents()

    if args.list_agents:
        list_agents()
        sys.exit(0)

    if args.test:
        success = run_test()
        sys.exit(0 if success else 1)

    if args.interactive:
        # 対話モード
        print("\n対話モード開始 (終了するには 'exit' または 'quit' を入力)")
        print("-" * 40)

        while True:
            try:
                request = input("\n>>> ").strip()

                if not request:
                    continue

                if request.lower() in ["exit", "quit", "q"]:
                    print("終了します")
                    break

                process_request(request)

            except KeyboardInterrupt:
                print("\n中断されました")
                break

        sys.exit(0)

    if args.request:
        success = process_request(args.request)
        sys.exit(0 if success else 1)

    # 引数なしの場合はヘルプを表示
    parser.print_help()


if __name__ == "__main__":
    main()
