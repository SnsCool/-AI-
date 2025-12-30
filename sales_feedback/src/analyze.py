#!/usr/bin/env python3
"""
営業会議分析スクリプト

Gemini APIを使用して営業会議の議事録を分析し、
フィードバックを生成する。
"""

import argparse
import json
import os
import sys
from datetime import datetime

import google.generativeai as genai


# 評価プロンプト
EVALUATION_PROMPT = """あなたは経験豊富な営業マネージャーです。
以下の営業会議の議事録を分析し、営業担当者へのフィードバックを生成してください。

【商談情報】
- 担当者: {sales_rep}
- 顧客: {customer}
- 業種: {industry}
- 商材: {product}
- クロージング: {is_closed}

【評価項目】
1. ヒアリング力（1-5点）
   - 顧客の課題・ニーズを適切に引き出せているか
   - オープンクエスチョンを効果的に使えているか

2. 提案力（1-5点）
   - 課題に対する解決策を適切に提示できているか
   - 顧客のニーズに合った提案ができているか

3. 異議対応（1-5点）
   - 顧客の懸念・反論に適切に対応できているか
   - 反論を機会に変えられているか

4. クロージング（1-5点）
   - 次のアクションへ適切に導けているか
   - 明確なネクストステップを設定できているか

5. ラポール構築（1-5点）
   - 信頼関係を構築できているか
   - 顧客との会話がスムーズか

6. BANT確認（1-5点）
   - Budget（予算）を確認できているか
   - Authority（決裁者）を特定できているか
   - Need（ニーズ）を明確にできているか
   - Timeline（導入時期）を確認できているか

【議事録】
{transcript}

【出力形式】
以下のJSON形式で出力してください。JSON以外のテキストは含めないでください。

{{
  "overall_score": <1-5の小数点1桁>,
  "scores": {{
    "hearing": {{"score": <1-5>, "reason": "<評価理由>"}},
    "proposal": {{"score": <1-5>, "reason": "<評価理由>"}},
    "objection_handling": {{"score": <1-5>, "reason": "<評価理由>"}},
    "closing": {{"score": <1-5>, "reason": "<評価理由>"}},
    "rapport": {{"score": <1-5>, "reason": "<評価理由>"}},
    "bant": {{"score": <1-5>, "reason": "<評価理由>"}}
  }},
  "good_points": [
    "<良かった点1（具体的な発言や行動を引用）>",
    "<良かった点2>",
    "<良かった点3>"
  ],
  "improvements": [
    "<改善点1（具体的な代替案を提示）>",
    "<改善点2>",
    "<改善点3>"
  ],
  "key_phrases": [
    "<効果的だったフレーズ1>",
    "<効果的だったフレーズ2>"
  ],
  "advice": [
    "<次回へのアドバイス1>",
    "<次回へのアドバイス2>",
    "<次回へのアドバイス3>"
  ],
  "success_factors": "<成功/失敗の主要因の分析（クロージング成功の場合は特に詳しく）>"
}}
"""


def load_transcript(transcript_text: str = None, transcript_file: str = None, transcript_url: str = None) -> str:
    """議事録を読み込む"""
    if transcript_text:
        return transcript_text

    if transcript_file and os.path.exists(transcript_file):
        with open(transcript_file, 'r', encoding='utf-8') as f:
            return f.read()

    if transcript_url:
        # TODO: Google Drive/Notion からの取得を実装
        raise NotImplementedError("URL からの取得は未実装です")

    raise ValueError("議事録が指定されていません")


def analyze_meeting(
    transcript: str,
    sales_rep: str,
    customer: str,
    industry: str = "未分類",
    product: str = "未分類",
    is_closed: bool = False
) -> dict:
    """営業会議を分析してフィードバックを生成"""

    # Gemini APIの設定
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY が設定されていません")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")

    # プロンプトを構築
    prompt = EVALUATION_PROMPT.format(
        sales_rep=sales_rep,
        customer=customer,
        industry=industry,
        product=product,
        is_closed="成功" if is_closed else "未成約/進行中",
        transcript=transcript
    )

    # Gemini APIを呼び出し
    print(f"[INFO] Gemini API で分析中...", file=sys.stderr)
    response = model.generate_content(prompt)

    # レスポンスをパース
    response_text = response.text.strip()

    # JSON部分を抽出（```json ... ``` で囲まれている場合に対応）
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        json_lines = []
        in_json = False
        for line in lines:
            if line.startswith("```json"):
                in_json = True
                continue
            elif line.startswith("```"):
                in_json = False
                continue
            if in_json:
                json_lines.append(line)
        response_text = "\n".join(json_lines)

    try:
        feedback = json.loads(response_text)
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSONパースエラー: {e}", file=sys.stderr)
        print(f"[ERROR] レスポンス: {response_text[:500]}", file=sys.stderr)
        raise

    # メタデータを追加
    feedback["metadata"] = {
        "sales_rep": sales_rep,
        "customer": customer,
        "industry": industry,
        "product": product,
        "is_closed": is_closed,
        "analyzed_at": datetime.now().isoformat(),
    }

    return feedback


def main():
    parser = argparse.ArgumentParser(description="営業会議分析")
    parser.add_argument("--transcript-text", help="議事録テキスト")
    parser.add_argument("--transcript-file", help="議事録ファイルパス")
    parser.add_argument("--transcript-url", help="議事録URL")
    parser.add_argument("--sales-rep", required=True, help="営業担当者名")
    parser.add_argument("--customer", required=True, help="顧客名")
    parser.add_argument("--industry", default="未分類", help="業種")
    parser.add_argument("--product", default="未分類", help="商材")
    parser.add_argument("--is-closed", default="false", help="クロージング成功フラグ")
    parser.add_argument("--output", default="feedback.json", help="出力ファイル")

    args = parser.parse_args()

    # 議事録を読み込み
    transcript_text = os.getenv("TRANSCRIPT_TEXT") or args.transcript_text
    transcript_file = os.getenv("TRANSCRIPT_FILE") or args.transcript_file
    transcript_url = os.getenv("TRANSCRIPT_URL") or args.transcript_url

    transcript = load_transcript(
        transcript_text=transcript_text,
        transcript_file=transcript_file,
        transcript_url=transcript_url
    )

    print(f"[INFO] 議事録を読み込みました（{len(transcript)}文字）", file=sys.stderr)

    # 分析実行
    is_closed = args.is_closed.lower() in ["true", "1", "yes"]
    feedback = analyze_meeting(
        transcript=transcript,
        sales_rep=args.sales_rep,
        customer=args.customer,
        industry=args.industry,
        product=args.product,
        is_closed=is_closed
    )

    # 結果を出力
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(feedback, f, ensure_ascii=False, indent=2)

    print(f"[INFO] 分析完了: {args.output}", file=sys.stderr)
    print(f"[INFO] 総合スコア: {feedback['overall_score']}/5.0", file=sys.stderr)

    # 標準出力にも出力（GitHub Actions用）
    print(json.dumps(feedback, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
