# AIエージェントシステム

## アーキテクチャ概要

```
┌─────────────────────────────────────────────────────┐
│                   Orchestrator                       │
│  ┌─────────────────────────────────────────────┐    │
│  │         Commander（司令塔エージェント）       │    │
│  │  - 全リクエストの入口                         │    │
│  │  - 適切なエージェントへ振り分け              │    │
│  │  - Gemini APIで思考・判断                    │    │
│  └─────────────────────────────────────────────┘    │
│                        │                             │
│         ┌──────────────┼──────────────┐             │
│         ▼              ▼              ▼             │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐        │
│  │ Judgment │   │Execution │   │Generation│        │
│  │  判断系  │   │  実行系  │   │  生成系  │        │
│  └──────────┘   └──────────┘   └──────────┘        │
└─────────────────────────────────────────────────────┘
```

## フォルダ構成

```
agents/
├── __init__.py          # パッケージ初期化
├── base.py              # BaseAgent, AgentResult, AgentContext
├── registry.py          # AgentRegistry（エージェント管理）
├── AGENT_TEMPLATE.py    # 新規エージェント作成テンプレート
├── README.md            # このファイル
│
├── commander/           # 司令塔エージェント
│   ├── __init__.py
│   └── commander.py     # CommanderAgent
│
├── execution/           # 実行系エージェント
│   ├── __init__.py
│   └── x_posting.py     # XPostingAgent
│
├── judgment/            # 判断系エージェント
│   └── __init__.py
│
└── generation/          # 生成系エージェント
    └── __init__.py
```

## 新しいエージェントの追加方法

### 1. テンプレートをコピー

```bash
cp agents/AGENT_TEMPLATE.py agents/execution/my_agent.py
```

### 2. エージェントを実装

```python
from ..base import BaseAgent, AgentResult, AgentContext
from ..registry import AgentRegistry

class MyAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "my_agent"  # 一意の名前

    @property
    def description(self) -> str:
        return "マイエージェント - 〇〇を実行"

    @property
    def agent_type(self) -> str:
        return "execution"  # execution/judgment/generation

    def get_capabilities(self) -> list[str]:
        return ["capability_1", "capability_2"]

    def can_handle(self, request: str) -> bool:
        keywords = ["キーワード1", "キーワード2"]
        return any(kw in request.lower() for kw in keywords)

    def think(self, context: AgentContext) -> dict:
        # リクエストを分析して何をするか決定
        return {"action": "do_something"}

    def execute(self, context: AgentContext, thought: dict) -> AgentResult:
        # 実際の処理を実行
        return AgentResult(success=True, message="完了")
```

### 3. `__init__.py` にインポート追加

```python
# agents/execution/__init__.py
from .my_agent import MyAgent
__all__ = ["XPostingAgent", "MyAgent"]
```

### 4. `orchestrator.py` に登録追加

```python
from agents.execution import XPostingAgent, MyAgent

def initialize_agents():
    AgentRegistry.register(CommanderAgent())
    AgentRegistry.register(XPostingAgent())
    AgentRegistry.register(MyAgent())  # 追加
```

## 振り分けの仕組み

1. **ユーザーがリクエスト**
   ```
   python orchestrator.py "X投稿を作成して"
   ```

2. **司令塔がGeminiで分析**
   - 登録済みエージェント一覧を参照
   - リクエスト内容と各エージェントの能力をマッチング

3. **適切なエージェントを選択**
   ```json
   {
     "action": "next_agent",
     "next_agent": "x_posting",
     "parameters": {"action": "full_workflow"},
     "reasoning": "X投稿に関するリクエストのため"
   }
   ```

4. **サブエージェントが実行**
   - `think()` で何をするか決定
   - `execute()` で実際に実行

5. **結果を司令塔に返却**

## エージェント間の連携

複数エージェントが連携する場合、`next_agent` を指定：

```python
def execute(self, context: AgentContext, thought: dict) -> AgentResult:
    # 自分の処理が終わったら次のエージェントを指定
    return AgentResult(
        success=True,
        message="判断完了、次は生成へ",
        data={"format": "共感型"},
        next_agent="text_generator"  # 次のエージェント
    )
```

## 承認フロー

重要な操作の前に人の承認を求める：

```python
def execute(self, context: AgentContext, thought: dict) -> AgentResult:
    return AgentResult(
        success=True,
        message="投稿内容を確認してください",
        data={"content": "投稿文..."},
        requires_approval=True  # 承認待ち
    )
```

## 使用例

```bash
# エージェント一覧
python orchestrator.py --list-agents

# 対話モード
python orchestrator.py --interactive

# 直接リクエスト
python orchestrator.py "X投稿のトレンドを取得して"
python orchestrator.py "投稿用のテキストを生成して"
```
