"""
Zoom面談分析エージェント

商談の文字起こしを分析し、フィードバックと成功ナレッジを蓄積する。
"""

import sys
import os
from typing import Optional
import json

# zoom/をパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents.base import BaseAgent, AgentContext, AgentResult, AgentStatus
from services.gemini_client import analyze_meeting, generate_embedding, generate_feedback
from services.supabase_client import get_supabase_client, save_knowledge, search_similar_knowledge


class MeetingAnalysisAgent(BaseAgent):
    """
    Zoom面談分析エージェント

    機能:
    - 商談の文字起こしを分析
    - クロージング判定（成約/未成約/継続）
    - 成功ナレッジの蓄積（Supabase）
    - 類似成功事例に基づくフィードバック生成
    """

    def __init__(self):
        super().__init__()
        self._supabase_client = None

    @property
    def name(self) -> str:
        return "MeetingAnalysisAgent"

    @property
    def description(self) -> str:
        return "Zoom面談の文字起こしを分析し、営業フィードバックと成功ナレッジを蓄積するエージェント"

    @property
    def agent_type(self) -> str:
        return "execution"

    def get_capabilities(self) -> list[str]:
        return [
            "商談分析",
            "クロージング判定",
            "フィードバック生成",
            "成功ナレッジ蓄積",
            "類似事例検索"
        ]

    def can_handle(self, request: str) -> bool:
        """Zoom面談関連のリクエストを処理できるか"""
        keywords = ["面談", "商談", "zoom", "分析", "フィードバック", "ナレッジ"]
        return any(kw in request.lower() for kw in keywords)

    @property
    def supabase_client(self):
        """Supabaseクライアントを遅延初期化"""
        if self._supabase_client is None:
            self._supabase_client = get_supabase_client()
        return self._supabase_client

    def think(self, context: AgentContext) -> dict:
        """
        思考プロセス: 何を分析するか決定
        """
        request = context.original_request
        shared_data = context.shared_data

        # 文字起こしデータがあるか確認
        transcript = shared_data.get("transcript")
        meeting_date = shared_data.get("meeting_date")
        assignee = shared_data.get("assignee")
        customer_name = shared_data.get("customer_name")

        if not transcript:
            return {
                "action": "error",
                "reasoning": "文字起こしデータが提供されていません",
                "parameters": {}
            }

        return {
            "action": "analyze_meeting",
            "reasoning": "文字起こしデータを分析してフィードバックを生成します",
            "parameters": {
                "transcript": transcript,
                "meeting_date": meeting_date,
                "assignee": assignee,
                "customer_name": customer_name
            }
        }

    def execute(self, context: AgentContext, thought: dict) -> AgentResult:
        """
        実行プロセス: 商談分析を実行
        """
        action = thought.get("action")
        params = thought.get("parameters", {})

        if action == "error":
            return AgentResult(
                success=False,
                message=thought.get("reasoning", "エラーが発生しました"),
                error=thought.get("reasoning")
            )

        if action == "analyze_meeting":
            return self._analyze_and_store(
                transcript=params.get("transcript"),
                meeting_date=params.get("meeting_date"),
                assignee=params.get("assignee"),
                customer_name=params.get("customer_name")
            )

        return AgentResult(
            success=False,
            message=f"Unknown action: {action}",
            error=f"Unknown action: {action}"
        )

    def _analyze_and_store(
        self,
        transcript: str,
        meeting_date: Optional[str] = None,
        assignee: Optional[str] = None,
        customer_name: Optional[str] = None
    ) -> AgentResult:
        """
        商談を分析し、結果を保存
        """
        try:
            self.log("商談分析を開始...")

            # Step 1: Geminiで分析
            self.log("Gemini APIで分析中...")
            analysis = analyze_meeting(transcript)

            if not analysis:
                return AgentResult(
                    success=False,
                    message="分析に失敗しました",
                    error="Gemini APIからの応答が空です"
                )

            self.log(f"クロージング結果: {analysis.get('closing_result', '不明')}")

            # Step 2: 要約のEmbeddingを生成
            self.log("Embeddingを生成中...")
            summary = analysis.get("summary", "")
            embedding = generate_embedding(summary) if summary else None

            # Step 3: 類似成功事例を検索
            self.log("類似成功事例を検索中...")
            similar_successes = []
            if embedding:
                similar_successes = search_similar_knowledge(
                    self.supabase_client,
                    embedding,
                    limit=3,
                    closing_result_filter="成約"
                )

            # Step 4: フィードバック生成
            self.log("フィードバックを生成中...")
            feedback = generate_feedback(analysis, similar_successes)

            # Step 5: ナレッジを保存（成約の場合）
            saved_id = None
            if analysis.get("closing_result") == "成約" and embedding:
                self.log("成功ナレッジを保存中...")
                talk_ratio = analysis.get("talk_ratio", {})
                saved = save_knowledge(
                    client=self.supabase_client,
                    meeting_date=meeting_date or "1970-01-01",
                    assignee=assignee or "不明",
                    customer_name=customer_name,
                    closing_result=analysis.get("closing_result", "不明"),
                    talk_ratio_sales=talk_ratio.get("sales", 0),
                    talk_ratio_customer=talk_ratio.get("customer", 0),
                    issues_heard=analysis.get("issues_heard", []),
                    proposal=analysis.get("proposal", []),
                    good_points=analysis.get("good_points", []),
                    improvement_points=analysis.get("improvement_points", []),
                    success_keywords=analysis.get("success_keywords", []),
                    summary=summary,
                    embedding=embedding
                )
                saved_id = saved.get("id")
                self.log(f"ナレッジ保存完了: {saved_id}")

            return AgentResult(
                success=True,
                message="商談分析が完了しました",
                data={
                    "analysis": analysis,
                    "feedback": feedback,
                    "similar_successes_count": len(similar_successes),
                    "knowledge_saved": saved_id is not None,
                    "knowledge_id": saved_id
                }
            )

        except Exception as e:
            self.log(f"エラー: {str(e)}", level="ERROR")
            return AgentResult(
                success=False,
                message="商談分析中にエラーが発生しました",
                error=str(e)
            )

    def analyze_transcript(self, transcript: str, **kwargs) -> dict:
        """
        外部から直接呼び出し可能な分析メソッド

        Args:
            transcript: 文字起こしテキスト
            **kwargs: meeting_date, assignee, customer_name など

        Returns:
            分析結果とフィードバック
        """
        from datetime import datetime
        import uuid

        # コンテキストを作成
        context = AgentContext(
            task_id=str(uuid.uuid4()),
            original_request="商談を分析してフィードバックを生成",
            shared_data={
                "transcript": transcript,
                "meeting_date": kwargs.get("meeting_date"),
                "assignee": kwargs.get("assignee"),
                "customer_name": kwargs.get("customer_name")
            }
        )

        # 実行
        result = self.run(context)

        return {
            "success": result.success,
            "analysis": result.data.get("analysis") if result.data else None,
            "feedback": result.data.get("feedback") if result.data else None,
            "error": result.error
        }
