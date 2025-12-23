"""
LLMサービス - OpenAI GPT-4o連携
"""

import os
from typing import Tuple

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class LLMService:
    """OpenAI GPT-4o サービス"""

    SYSTEM_PROMPT = """あなたは社内ナレッジ検索アシスタントです。
与えられたコンテキスト情報のみを使用して、ユーザーの質問に回答してください。

回答のルール:
1. コンテキストに基づいて正確に回答する
2. 出典を[出典N]の形式で明記する
3. 不明な場合は「情報が見つかりませんでした」と回答する
4. 推測や創作は絶対にしない
5. 簡潔かつ分かりやすく回答する

回答形式:
- 箇条書きを活用する
- 手順がある場合は番号付きリストを使用
- 重要な情報は強調する"""

    def __init__(self):
        self.client = None
        if OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.client = openai.OpenAI(api_key=api_key)

    async def generate_answer(
        self,
        query: str,
        context: str
    ) -> Tuple[str, float]:
        """
        質問に対する回答を生成

        Args:
            query: ユーザーの質問
            context: 検索で取得したドキュメントのコンテキスト

        Returns:
            Tuple[str, float]: (回答, 信頼度スコア)
        """
        if self.client:
            return await self._generate_with_openai(query, context)

        # フォールバック: モック回答
        return self._generate_mock(query, context)

    async def _generate_with_openai(
        self,
        query: str,
        context: str
    ) -> Tuple[str, float]:
        """OpenAI GPT-4oで回答を生成"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": f"""
コンテキスト情報:
{context}

質問: {query}

上記のコンテキスト情報のみを使用して回答してください。
"""}
                ],
                temperature=0.3,
                max_tokens=1000
            )

            answer = response.choices[0].message.content

            # 信頼度を推定（簡易版）
            confidence = self._estimate_confidence(answer, context)

            return answer, confidence

        except Exception as e:
            print(f"OpenAI API エラー: {e}")
            return self._generate_mock(query, context)

    def _generate_mock(
        self,
        query: str,
        context: str
    ) -> Tuple[str, float]:
        """モック回答を生成（デモ用）"""
        # コンテキストから最初のドキュメントの内容を抜粋
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

        # デフォルト回答
        return (
            "申し訳ありませんが、ご質問に対する明確な情報が見つかりませんでした。\n"
            "検索キーワードを変更するか、担当部署に直接お問い合わせください。",
            0.3
        )

    def _estimate_confidence(self, answer: str, context: str) -> float:
        """
        回答の信頼度を推定

        - 出典が含まれているか
        - 「わかりません」等のフレーズがないか
        - 回答の長さ
        """
        confidence = 0.7  # ベースライン

        # 出典参照があれば加点
        if "[出典" in answer:
            confidence += 0.15

        # 不確実フレーズがあれば減点
        uncertain_phrases = [
            "わかりません", "見つかりません", "不明", "情報がありません",
            "確認できません", "記載されていません"
        ]
        for phrase in uncertain_phrases:
            if phrase in answer:
                confidence -= 0.2
                break

        # 回答が短すぎる場合は減点
        if len(answer) < 50:
            confidence -= 0.1

        # 0.0 - 1.0 の範囲に収める
        return max(0.0, min(1.0, round(confidence, 2)))
