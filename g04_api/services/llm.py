"""
LLMサービス - Google Gemini連携
"""

import os
from typing import Tuple

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class LLMService:
    """Google Gemini サービス"""

    SYSTEM_PROMPT_KNOWLEDGE = """あなたは社内ナレッジ検索アシスタントです。
与えられたコンテキスト情報を使用して、ユーザーの質問に回答してください。

回答のルール:
1. コンテキストに基づいて正確に回答する
2. 出典を[出典N]の形式で明記する
3. 簡潔かつ分かりやすく回答する

回答形式:
- 箇条書きを活用する
- 手順がある場合は番号付きリストを使用
- 重要な情報は強調する"""

    SYSTEM_PROMPT_GENERAL = """あなたは親切なアシスタントです。
ユーザーの質問に対して、正確で役立つ回答を提供してください。

回答のルール:
1. 簡潔かつ分かりやすく回答する
2. 不確かな情報は「確実ではありませんが」と前置きする
3. 必要に応じて追加の質問を促す

回答形式:
- 箇条書きを活用する
- 手順がある場合は番号付きリストを使用"""

    def __init__(self):
        self.model = None
        self.general_model = None
        if GEMINI_AVAILABLE:
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel(
                    model_name="gemini-2.0-flash",
                    system_instruction=self.SYSTEM_PROMPT_KNOWLEDGE
                )
                self.general_model = genai.GenerativeModel(
                    model_name="gemini-2.0-flash",
                    system_instruction=self.SYSTEM_PROMPT_GENERAL
                )

    async def generate_answer(
        self,
        query: str,
        context: str
    ) -> Tuple[str, float]:
        """
        ナレッジベースで質問に回答

        Args:
            query: ユーザーの質問
            context: 検索で取得したドキュメントのコンテキスト

        Returns:
            Tuple[str, float]: (回答, 信頼度スコア)
        """
        if self.model:
            return await self._generate_with_gemini(query, context)

        return self._generate_mock(query, context)

    async def generate_general_answer(
        self,
        query: str
    ) -> Tuple[str, float]:
        """
        一般知識で質問に回答（ナレッジが見つからない場合）

        Args:
            query: ユーザーの質問

        Returns:
            Tuple[str, float]: (回答, 信頼度スコア)
        """
        if self.general_model:
            try:
                prompt = f"""
質問: {query}

上記の質問に対して、簡潔に回答してください。
社内ナレッジには該当する情報がなかったため、一般的な知識で回答しています。
"""
                response = self.general_model.generate_content(prompt)
                answer = "📌 **社内ナレッジには該当情報がありませんでした。一般的な回答です：**\n\n" + response.text
                return answer, 0.6

            except Exception as e:
                print(f"Gemini API エラー: {e}")

        return (
            "申し訳ありませんが、ご質問に回答できませんでした。\n"
            "別の質問をお試しください。",
            0.3
        )

    async def _generate_with_gemini(
        self,
        query: str,
        context: str
    ) -> Tuple[str, float]:
        """Google Geminiでナレッジベースの回答を生成"""
        try:
            prompt = f"""
コンテキスト情報:
{context}

質問: {query}

上記のコンテキスト情報を使用して回答してください。
"""
            response = self.model.generate_content(prompt)
            answer = response.text

            confidence = self._estimate_confidence(answer, context)

            return answer, confidence

        except Exception as e:
            print(f"Gemini API エラー: {e}")
            return self._generate_mock(query, context)

    def _generate_mock(
        self,
        query: str,
        context: str
    ) -> Tuple[str, float]:
        """モック回答を生成（デモ用）"""
        if "[出典1]" in context:
            lines = context.split("\n")
            content_start = False
            answer_parts = []

            for line in lines[:10]:
                if "[出典1]" in line:
                    content_start = True
                    continue
                if content_start and line.strip():
                    if "[出典2]" in line:
                        break
                    answer_parts.append(line)

            if answer_parts:
                answer = "\n".join(answer_parts[:5])
                answer += "\n\n詳細は出典をご確認ください。[出典1][出典2]"
                return answer, 0.85

        return (
            "申し訳ありませんが、ご質問に対する明確な情報が見つかりませんでした。\n"
            "検索キーワードを変更するか、担当部署に直接お問い合わせください。",
            0.3
        )

    def _estimate_confidence(self, answer: str, context: str) -> float:
        """回答の信頼度を推定"""
        confidence = 0.7

        if "[出典" in answer:
            confidence += 0.15

        uncertain_phrases = [
            "わかりません", "見つかりません", "不明", "情報がありません",
            "確認できません", "記載されていません"
        ]
        for phrase in uncertain_phrases:
            if phrase in answer:
                confidence -= 0.2
                break

        if len(answer) < 50:
            confidence -= 0.1

        return max(0.0, min(1.0, round(confidence, 2)))
