"""
Zoomサブエージェント (Zoom Sub Agent)

役割:
- Zoom面談の文字起こし分析
- フィードバック生成
- 成功ナレッジ蓄積
- 類似事例検索

zoom/services/ のクライアントを呼び出して処理を実行する。
"""

import sys
from pathlib import Path

# zoom/ をインポートするためにパスを追加
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from .base import BaseAgent, AgentResult, AgentContext


class ZoomAgent(BaseAgent):
    """
    Zoomサブエージェント

    Zoom面談の分析・フィードバック生成を実行する。
    """

    def __init__(self):
        super().__init__()
        self._gemini_client = None
        self._supabase_client = None
        self._zoom_client = None
        self._sheets_client = None
        self._load_zoom_services()

    def _load_zoom_services(self):
        """zoom/services のクライアントを動的にロード"""
        try:
            from zoom.services import gemini_client, supabase_client, zoom_client, sheets_client
            self._gemini_client = gemini_client
            self._supabase_client = supabase_client
            self._zoom_client = zoom_client
            self._sheets_client = sheets_client
            self.log("Zoom services loaded successfully")
        except ImportError as e:
            self.log(f"Warning: Could not load zoom services: {e}", level="WARN")

    @property
    def name(self) -> str:
        return "zoom_agent"

    @property
    def description(self) -> str:
        return "Zoomサブエージェント - 面談分析・フィードバック生成・ナレッジ蓄積"

    @property
    def agent_type(self) -> str:
        return "sub"

    def get_capabilities(self) -> list[str]:
        return [
            "analyze_meeting",       # 面談分析
            "generate_feedback",     # フィードバック生成
            "save_knowledge",        # ナレッジ蓄積
            "search_similar",        # 類似事例検索
            "fetch_recordings"       # 録画取得
        ]

    def can_handle(self, request: str) -> bool:
        """Zoom関連のリクエストを処理できるか判定"""
        keywords = [
            "zoom", "面談", "録画", "文字起こし",
            "分析", "フィードバック", "ナレッジ",
            "商談", "ミーティング", "会議"
        ]
        request_lower = request.lower()
        return any(kw in request_lower for kw in keywords)

    def think(self, context: AgentContext) -> dict:
        """
        思考プロセス

        リクエストを分析し、どのアクションを実行するかを決定する。
        """
        request = context.original_request.lower()
        shared_data = context.shared_data

        # メインエージェントから渡されたパラメータを確認
        action = shared_data.get("action", "analyze")
        transcript = shared_data.get("transcript")
        meeting_date = shared_data.get("meeting_date")
        assignee = shared_data.get("assignee")
        customer_name = shared_data.get("customer_name")

        # リクエスト内容からアクションを判定
        if "録画" in request and "取得" in request:
            action = "fetch_recordings"
        elif "分析" in request or "フィードバック" in request:
            action = "analyze"
        elif "ナレッジ" in request or "検索" in request:
            action = "search_similar"
        elif "バッチ" in request or "一括" in request:
            action = "batch_process"

        return {
            "action": action,
            "transcript": transcript,
            "meeting_date": meeting_date,
            "assignee": assignee,
            "customer_name": customer_name,
            "reasoning": f"Action: {action}"
        }

    def execute(self, context: AgentContext, thought: dict) -> AgentResult:
        """
        実行プロセス

        思考結果に基づいて実際のZoom分析処理を実行する。
        """
        action = thought.get("action", "analyze")

        self.log(f"Executing action: {action}")

        if not self._gemini_client:
            return AgentResult(
                success=False,
                message="Zoomサービスが読み込めません",
                error="Zoom services not loaded"
            )

        try:
            if action == "analyze":
                return self._execute_analyze(thought)

            elif action == "fetch_recordings":
                return self._execute_fetch_recordings()

            elif action == "search_similar":
                return self._execute_search_similar(thought)

            elif action == "batch_process":
                return self._execute_batch_process()

            else:
                return AgentResult(
                    success=False,
                    message=f"Unknown action: {action}",
                    error=f"Unknown action: {action}"
                )

        except Exception as e:
            return AgentResult(
                success=False,
                message=f"実行エラー: {str(e)}",
                error=str(e)
            )

    def _execute_analyze(self, thought: dict) -> AgentResult:
        """面談分析を実行"""
        transcript = thought.get("transcript")

        if not transcript:
            return AgentResult(
                success=False,
                message="文字起こしデータが指定されていません",
                error="No transcript provided"
            )

        self.log("Analyzing meeting transcript...")

        try:
            # Gemini APIで分析
            analysis = self._gemini_client.analyze_meeting(transcript)

            # Embedding生成
            summary = analysis.get("summary", "")
            embedding = None
            if summary:
                embedding = self._gemini_client.generate_embedding(summary)

            # 類似成功事例を検索
            similar_cases = []
            if embedding and self._supabase_client:
                similar_cases = self._supabase_client.search_similar_knowledge(
                    query_embedding=embedding,
                    limit=3,
                    closing_result_filter="成約"
                )

            # フィードバック生成
            feedback = self._gemini_client.generate_feedback(
                current_analysis=analysis,
                similar_successes=similar_cases
            )

            # 成約の場合はナレッジ保存
            if analysis.get("closing_result") == "成約" and self._supabase_client:
                self._supabase_client.save_knowledge(
                    meeting_date=thought.get("meeting_date"),
                    assignee=thought.get("assignee"),
                    customer_name=thought.get("customer_name"),
                    closing_result=analysis.get("closing_result"),
                    talk_ratio_sales=analysis.get("talk_ratio", {}).get("sales"),
                    talk_ratio_customer=analysis.get("talk_ratio", {}).get("customer"),
                    issues_heard=analysis.get("issues_heard", []),
                    proposal=analysis.get("proposal", []),
                    good_points=analysis.get("good_points", []),
                    improvement_points=analysis.get("improvement_points", []),
                    success_keywords=analysis.get("success_keywords", []),
                    summary=summary,
                    embedding=embedding
                )
                self.log("Knowledge saved to Supabase")

            return AgentResult(
                success=True,
                message="面談分析が完了しました",
                data={
                    "analysis": analysis,
                    "feedback": feedback,
                    "similar_cases_count": len(similar_cases)
                }
            )

        except Exception as e:
            return AgentResult(
                success=False,
                message=f"分析失敗: {str(e)}",
                error=str(e)
            )

    def _execute_fetch_recordings(self) -> AgentResult:
        """Zoom録画を取得"""
        self.log("Fetching Zoom recordings...")

        try:
            if not self._zoom_client:
                return AgentResult(
                    success=False,
                    message="Zoomクライアントが読み込めません",
                    error="Zoom client not loaded"
                )

            # 全アカウントの録画を取得
            recordings = self._zoom_client.get_all_accounts_recordings(
                self._supabase_client
            )

            return AgentResult(
                success=True,
                message=f"{len(recordings)}件の録画を取得しました",
                data={
                    "recording_count": len(recordings),
                    "recordings": recordings[:10]  # 最初の10件のみ
                }
            )

        except Exception as e:
            return AgentResult(
                success=False,
                message=f"録画取得失敗: {str(e)}",
                error=str(e)
            )

    def _execute_search_similar(self, thought: dict) -> AgentResult:
        """類似事例を検索"""
        self.log("Searching similar cases...")

        try:
            if not self._supabase_client:
                return AgentResult(
                    success=False,
                    message="Supabaseクライアントが読み込めません",
                    error="Supabase client not loaded"
                )

            transcript = thought.get("transcript", "")
            if not transcript:
                return AgentResult(
                    success=False,
                    message="検索用のテキストが指定されていません",
                    error="No search text provided"
                )

            # Embedding生成
            embedding = self._gemini_client.generate_embedding(transcript)

            # 類似検索
            similar_cases = self._supabase_client.search_similar_knowledge(
                query_embedding=embedding,
                limit=5
            )

            return AgentResult(
                success=True,
                message=f"{len(similar_cases)}件の類似事例が見つかりました",
                data={
                    "similar_cases": similar_cases
                }
            )

        except Exception as e:
            return AgentResult(
                success=False,
                message=f"検索失敗: {str(e)}",
                error=str(e)
            )

    def _execute_batch_process(self) -> AgentResult:
        """バッチ処理を実行"""
        self.log("Running batch process...")

        try:
            # zoom/batch_zoom.py の処理を呼び出す
            from zoom import batch_zoom
            batch_zoom.main()

            return AgentResult(
                success=True,
                message="バッチ処理が完了しました",
                data={}
            )

        except Exception as e:
            return AgentResult(
                success=False,
                message=f"バッチ処理失敗: {str(e)}",
                error=str(e)
            )
