"""
Gemini API クライアント
商談分析、動画分析、Embedding生成を行う
"""

import os
import json
import time
from typing import Optional
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Gemini設定
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# モデル
ANALYSIS_MODEL = "gemini-2.0-flash-exp"
EMBEDDING_MODEL = "text-embedding-004"


def analyze_video(video_path: str) -> dict:
    """
    商談動画を分析（表情、態度、話し方）

    Args:
        video_path: 動画ファイルのパス

    Returns:
        {
            "presenter_analysis": {
                "confidence_level": "高/中/低",
                "eye_contact": "良好/普通/改善が必要",
                "speaking_pace": "適切/早すぎ/遅すぎ",
                "gestures": "効果的/普通/少ない"
            },
            "audience_reaction": {
                "engagement_level": "高/中/低",
                "interest_signals": ["うなずき", "メモを取る", ...]
            },
            "improvement_suggestions": ["改善点1", "改善点2", ...],
            "strengths": ["強み1", "強み2", ...]
        }
    """
    print(f"動画をアップロード中: {video_path}")

    # 動画ファイルをアップロード
    video_file = genai.upload_file(path=video_path)

    # 処理完了を待つ
    print("動画処理中...")
    while video_file.state.name == "PROCESSING":
        time.sleep(10)
        video_file = genai.get_file(video_file.name)

    if video_file.state.name == "FAILED":
        raise ValueError(f"動画処理に失敗しました: {video_file.state.name}")

    print("動画分析中...")
    model = genai.GenerativeModel(ANALYSIS_MODEL)

    prompt = """この商談・面談の動画を分析してください。

【分析項目】
1. プレゼンター（営業）の分析:
   - 自信レベル（高/中/低）
   - アイコンタクト（良好/普通/改善が必要）
   - 話すスピード（適切/早すぎ/遅すぎ）
   - ジェスチャー（効果的/普通/少ない）
   - 声のトーン（明るい/普通/暗い）

2. 相手（顧客）の反応:
   - 興味・関心レベル（高/中/低）
   - 興味を示すサイン（うなずき、前のめり、メモを取る等）
   - ネガティブサイン（腕組み、視線をそらす等）

3. 改善提案:
   - 具体的な改善点を3つ

4. 強み:
   - 良かった点を3つ

【出力形式】
必ず以下のJSON形式で出力してください:

{
  "presenter_analysis": {
    "confidence_level": "高 or 中 or 低",
    "eye_contact": "良好 or 普通 or 改善が必要",
    "speaking_pace": "適切 or 早すぎ or 遅すぎ",
    "gestures": "効果的 or 普通 or 少ない",
    "voice_tone": "明るい or 普通 or 暗い"
  },
  "audience_reaction": {
    "engagement_level": "高 or 中 or 低",
    "positive_signals": ["サイン1", "サイン2"],
    "negative_signals": ["サイン1", "サイン2"]
  },
  "improvement_suggestions": ["改善点1", "改善点2", "改善点3"],
  "strengths": ["強み1", "強み2", "強み3"]
}
"""

    response = model.generate_content([video_file, prompt])

    # JSONをパース
    try:
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        return json.loads(text.strip())
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Raw response: {response.text}")
        return {}
    finally:
        # アップロードしたファイルを削除
        try:
            genai.delete_file(video_file.name)
        except:
            pass


def analyze_meeting(transcript: str) -> dict:
    """
    商談の文字起こしを分析

    Returns:
        {
            "closing_result": "成約" | "未成約" | "継続",
            "talk_ratio": {"sales": 40, "customer": 60},
            "issues_heard": ["課題1", "課題2"],
            "proposal": ["提案1", "提案2"],
            "good_points": ["良かった点1", "良かった点2", "良かった点3"],
            "improvement_points": ["改善点1", "改善点2", "改善点3"],
            "success_keywords": ["キーワード1", "キーワード2"],
            "summary": "商談の要約..."
        }
    """

    model = genai.GenerativeModel(ANALYSIS_MODEL)

    prompt = f"""あなたは営業コーチです。以下の商談の文字起こしを分析してください。

【分析項目】
1. クロージング判定: 契約・申込みがあれば「成約」、明確に断られたら「未成約」、次回アポや検討中なら「継続」
2. 話す割合: 営業と顧客それぞれが話した割合を推定（%）
3. ヒアリングした課題: 顧客から引き出した具体的な困りごと・課題（箇条書き）
4. 提案内容: 営業が行った提案（箇条書き）
5. 良かった点: この商談で営業がうまくできた点（3つ）
6. 改善点: 次回改善すべき点（3つ、具体的な改善案付き）
7. 成功キーワード: この商談の成功要因となったキーワード（成約・継続の場合のみ）
8. 要約: 商談内容を3-5文で要約

【出力形式】
必ず以下のJSON形式で出力してください。他の文章は不要です。

{{
  "closing_result": "成約 or 未成約 or 継続",
  "talk_ratio": {{"sales": 数値, "customer": 数値}},
  "issues_heard": ["課題1", "課題2", ...],
  "proposal": ["提案1", "提案2", ...],
  "good_points": ["良かった点1", "良かった点2", "良かった点3"],
  "improvement_points": ["改善点1", "改善点2", "改善点3"],
  "success_keywords": ["キーワード1", "キーワード2", ...],
  "summary": "要約文..."
}}

【文字起こし】
{transcript}
"""

    # リトライ付きでAPI呼び出し
    response = None
    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            break
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                print(f"レート制限、60秒待機中... (attempt {attempt + 1}/3)")
                time.sleep(60)
            else:
                raise e

    # JSONをパース
    try:
        # ```json ... ``` を除去
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        return json.loads(text.strip())
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Raw response: {response.text}")
        return {}


def generate_embedding(text: str) -> list[float]:
    """テキストからEmbeddingベクトルを生成（768次元）"""

    result = genai.embed_content(
        model=f"models/{EMBEDDING_MODEL}",
        content=text,
        task_type="retrieval_document",
    )

    return result["embedding"]


def generate_detailed_feedback(transcript: str) -> str:
    """
    文字起こしから詳細なフィードバックを生成

    Args:
        transcript: 文字起こしテキスト

    Returns:
        詳細フィードバックテキスト
    """
    model = genai.GenerativeModel(ANALYSIS_MODEL)

    prompt = f"""# Zoom文字起こし分析・詳細フィードバック生成プロンプト

あなたは「会話分析とフィードバックを専門とするプロのコーチ」です。
以下は Zoom で文字起こしされた会話ログです。

---

## 🎯 目的
この会話内容をもとに、以下を **実務で使えるレベル** で分析・フィードバックしてください。

- 良い点
- 悪い点
- 改善点

---

## 🔍 分析観点
以下の観点を必ず含めて分析してください。

- 話し手の構成力
- 相手への配慮・理解度
- 論理の一貫性
- 説明のわかりやすさ
- 会話の主導権・流れ
- ゴール設定と着地点の明確さ
- 無駄・冗長・分かりにくい表現
- 相手目線が欠けているポイント

---

## 🧾 出力ルール
以下の構成を **必ず守って**、具体例を交えて出力してください。

### ① 全体総評（要約）
- この会話の目的は何か
- その目的はどこまで達成できているか
- 全体の完成度（5段階評価）

---

### ② 良い点（具体）
- なぜ良いのか
- どの発言・流れが評価できるか
- 今後も継続すべきポイント

---

### ③ 悪い点・課題点
- 相手にとって分かりにくい箇所
- 時間や理解のロスが発生している部分
- 誤解を生みやすい表現
- 放置した場合に起こりうるリスク

---

### ④ 改善ポイント（超具体）
- どう言い換えると良いか
- どの順番で話すと理解されやすいか
- 次回の会話で最初に入れるべき一言
- 削るべき表現／追加すべき説明

---

### ⑤ 次回に向けた改善テンプレ
- 次回、同様の内容を話す場合の
  **理想的な話し方構成（箇条書き）**

---

## 🎙 トーン指定
- 上から目線にならない
- 実務で成長につながるフィードバック
- 抽象論ではなく具体ベース

---

## 📝 Zoom文字起こし内容
{transcript}
"""

    # リトライ付きでAPI呼び出し
    response = None
    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            break
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                print(f"レート制限、60秒待機中... (attempt {attempt + 1}/3)")
                time.sleep(60)
            else:
                raise e

    return response.text


def generate_feedback(
    current_analysis: dict,
    similar_successes: list[dict],
) -> str:
    """
    現在の商談分析と類似成功事例を元にフィードバックを生成（旧版）
    """

    model = genai.GenerativeModel(ANALYSIS_MODEL)

    # 類似成功事例を整形
    success_examples = ""
    for i, success in enumerate(similar_successes, 1):
        success_examples += f"""
【成功事例{i}】
- 成功キーワード: {', '.join(success.get('success_keywords', []))}
- 良かった点: {', '.join(success.get('good_points', []))}
- 要約: {success.get('summary', '')}
"""

    prompt = f"""あなたは営業コーチです。以下の商談分析結果に対して、具体的なフィードバックを提供してください。

【今回の商談分析】
- クロージング結果: {current_analysis.get('closing_result', '不明')}
- 話す割合: 営業{current_analysis.get('talk_ratio', {}).get('sales', '?')}% / 顧客{current_analysis.get('talk_ratio', {}).get('customer', '?')}%
- ヒアリングした課題: {', '.join(current_analysis.get('issues_heard', []))}
- 良かった点: {', '.join(current_analysis.get('good_points', []))}
- 改善点: {', '.join(current_analysis.get('improvement_points', []))}

【参考: 類似の成功事例】
{success_examples if success_examples else "（まだ成功事例がありません）"}

【出力形式】
以下の形式でフィードバックを出力してください:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 商談分析フィードバック

✅ 良かった点:
- （具体的に3つ）

⚠️ 改善点:
- （具体的に3つ、成功事例を参考にした改善案を含める）

💡 成功事例からのアドバイス:
- （類似成功事例から学べるポイント）

📈 次回のアクションプラン:
- （具体的な行動提案）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    response = model.generate_content(prompt)
    return response.text


def generate_integrated_feedback(
    transcript_analysis: dict,
    video_analysis: Optional[dict] = None,
    similar_successes: list[dict] = None,
) -> str:
    """
    文字起こし分析と動画分析を統合したフィードバックを生成

    Args:
        transcript_analysis: 文字起こし分析結果
        video_analysis: 動画分析結果（オプション）
        similar_successes: 類似成功事例

    Returns:
        統合フィードバックテキスト
    """
    model = genai.GenerativeModel(ANALYSIS_MODEL)

    # 類似成功事例を整形
    success_examples = ""
    if similar_successes:
        for i, success in enumerate(similar_successes, 1):
            success_examples += f"""
【成功事例{i}】
- 成功キーワード: {', '.join(success.get('success_keywords', []))}
- 良かった点: {', '.join(success.get('good_points', []))}
"""

    # 動画分析部分
    video_section = ""
    if video_analysis:
        presenter = video_analysis.get("presenter_analysis", {})
        audience = video_analysis.get("audience_reaction", {})
        video_section = f"""
【動画分析結果】
- 自信レベル: {presenter.get('confidence_level', '不明')}
- アイコンタクト: {presenter.get('eye_contact', '不明')}
- 話すスピード: {presenter.get('speaking_pace', '不明')}
- ジェスチャー: {presenter.get('gestures', '不明')}
- 声のトーン: {presenter.get('voice_tone', '不明')}
- 顧客の関心度: {audience.get('engagement_level', '不明')}
- ポジティブサイン: {', '.join(audience.get('positive_signals', []))}
- ネガティブサイン: {', '.join(audience.get('negative_signals', []))}
- 動画からの改善点: {', '.join(video_analysis.get('improvement_suggestions', []))}
- 動画からの強み: {', '.join(video_analysis.get('strengths', []))}
"""

    prompt = f"""あなたは営業コーチです。以下の商談分析結果に対して、包括的なフィードバックを提供してください。

【文字起こし分析結果】
- クロージング結果: {transcript_analysis.get('closing_result', '不明')}
- 話す割合: 営業{transcript_analysis.get('talk_ratio', {}).get('sales', '?')}% / 顧客{transcript_analysis.get('talk_ratio', {}).get('customer', '?')}%
- ヒアリングした課題: {', '.join(transcript_analysis.get('issues_heard', []))}
- 提案内容: {', '.join(transcript_analysis.get('proposal', []))}
- 良かった点: {', '.join(transcript_analysis.get('good_points', []))}
- 改善点: {', '.join(transcript_analysis.get('improvement_points', []))}
{video_section}
【参考: 類似の成功事例】
{success_examples if success_examples else "（まだ成功事例がありません）"}

【出力形式】
以下の形式で統合フィードバックを出力してください。#で区切って1つのテキストとして出力:

# 総合評価
評価: [A/B/C/D]（A:素晴らしい B:良好 C:改善の余地あり D:要改善）
クロージング結果: {transcript_analysis.get('closing_result', '不明')}

# トークスクリプト分析
## 良かった点
- （具体的に3つ）

## 改善点
- （具体的に3つ）

## ヒアリング評価
- 引き出した課題の数と質についてコメント

## 提案評価
- 課題と提案の紐付けについてコメント

# 表情&態度分析
## 自信・態度
- 自信レベル、アイコンタクト、姿勢についてコメント

## 話し方
- 話すスピード、声のトーン、間の取り方についてコメント

## 顧客の反応
- 顧客の関心度、ポジティブ/ネガティブサインについてコメント

## 改善ポイント
- （動画から見える具体的な改善点を3つ）

# 成功事例からのアドバイス
- （類似成功事例から学べるポイント）

# 次回アクションプラン
1. （最優先で取り組むべきこと）
2. （次に取り組むこと）
3. （継続して意識すること）
"""

    response = model.generate_content(prompt)
    return response.text
