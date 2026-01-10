"""
動画ユーティリティ
長い動画を分割して分析する機能
"""

import os
import subprocess
import tempfile
import time
import json
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

ANALYSIS_MODEL = "gemini-2.0-flash-exp"
CHUNK_DURATION_MINUTES = 15


def get_video_duration(video_path: str) -> float:
    """動画の長さを秒で取得"""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())


def split_video(video_path: str, chunk_duration_seconds: int = 900, output_dir: str = None) -> list[str]:
    """
    動画を指定秒数ごとに分割

    Args:
        video_path: 元動画のパス
        chunk_duration_seconds: チャンクの長さ（秒）、デフォルト15分
        output_dir: 出力ディレクトリ

    Returns:
        分割された動画ファイルのパスリスト
    """
    if output_dir is None:
        output_dir = tempfile.mkdtemp()

    # 動画の長さを取得
    duration = get_video_duration(video_path)
    print(f"動画の長さ: {duration/60:.1f}分")

    # チャンク数を計算
    num_chunks = int(duration / chunk_duration_seconds) + 1
    print(f"分割数: {num_chunks}チャンク")

    chunk_paths = []

    for i in range(num_chunks):
        start_time = i * chunk_duration_seconds

        # 残り時間がチャンク長より短い場合はスキップ（短すぎる断片を避ける）
        if start_time >= duration:
            break

        output_path = os.path.join(output_dir, f"chunk_{i:03d}.mp4")

        cmd = [
            "ffmpeg",
            "-y",  # 上書き
            "-i", video_path,
            "-ss", str(start_time),
            "-t", str(chunk_duration_seconds),
            "-c", "copy",  # 再エンコードなし（高速）
            output_path
        ]

        print(f"  チャンク {i+1}/{num_chunks}: {start_time/60:.1f}分〜")
        subprocess.run(cmd, capture_output=True)

        if os.path.exists(output_path):
            chunk_paths.append(output_path)

    return chunk_paths


def analyze_video_chunk(video_path: str, chunk_index: int = 0, retry_delay: int = 60) -> dict:
    """
    動画チャンクを分析（文字起こし + 表情分析）

    Args:
        video_path: 動画ファイルのパス
        chunk_index: チャンク番号
        retry_delay: レート制限時の待機秒数

    Returns:
        {
            "transcript": "文字起こしテキスト",
            "analysis": {...}  # 表情・態度分析
        }
    """
    print(f"  → チャンク {chunk_index + 1} をアップロード中...")

    # 動画をアップロード
    video_file = genai.upload_file(path=video_path)

    # 処理完了を待つ
    while video_file.state.name == "PROCESSING":
        time.sleep(5)
        video_file = genai.get_file(video_file.name)

    if video_file.state.name == "FAILED":
        raise ValueError(f"動画処理に失敗: {video_file.state.name}")

    model = genai.GenerativeModel(ANALYSIS_MODEL)

    # 1. 文字起こしを生成（リトライ付き）
    print(f"  → チャンク {chunk_index + 1} の文字起こし生成中...")
    transcript_prompt = """この動画の会話内容を文字起こししてください。
話者を区別して、できるだけ正確に書き起こしてください。

形式:
話者A: 〇〇〇
話者B: 〇〇〇
"""

    transcript = ""
    for attempt in range(3):
        try:
            transcript_response = model.generate_content([video_file, transcript_prompt])
            transcript = transcript_response.text
            break
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                print(f"    レート制限、{retry_delay}秒待機...")
                time.sleep(retry_delay)
            else:
                raise e

    # 2. 表情・態度分析（リトライ付き）
    print(f"  → チャンク {chunk_index + 1} の表情分析中...")
    analysis_prompt = """この動画の出演者の表情と態度を分析してください。

以下のJSON形式で出力してください:
{
  "presenter_analysis": {
    "confidence_level": "高/中/低",
    "eye_contact": "良好/普通/改善が必要",
    "speaking_pace": "適切/早すぎ/遅すぎ",
    "gestures": "効果的/普通/少ない",
    "voice_tone": "明るい/普通/暗い"
  },
  "audience_reaction": {
    "engagement_level": "高/中/低",
    "positive_signals": ["サイン1", "サイン2"],
    "negative_signals": ["サイン1", "サイン2"]
  },
  "observations": "このチャンクで観察された特記事項"
}
"""

    analysis_response = None
    for attempt in range(3):
        try:
            analysis_response = model.generate_content([video_file, analysis_prompt])
            break
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                print(f"    レート制限、{retry_delay}秒待機...")
                time.sleep(retry_delay)
            else:
                raise e

    # JSONをパース
    try:
        text = analysis_response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        analysis = json.loads(text.strip())
    except json.JSONDecodeError:
        analysis = {"raw_response": analysis_response.text}

    # アップロードしたファイルを削除
    try:
        genai.delete_file(video_file.name)
    except:
        pass

    return {
        "transcript": transcript,
        "analysis": analysis
    }


def analyze_long_video(
    video_path: str,
    chunk_duration_minutes: int = 15
) -> dict:
    """
    長い動画を分割して分析

    Args:
        video_path: 動画ファイルのパス
        chunk_duration_minutes: チャンクの長さ（分）

    Returns:
        {
            "full_transcript": "全体の文字起こし",
            "chunk_analyses": [...],  # 各チャンクの分析
            "overall_analysis": {...}  # 統合分析
        }
    """
    print("=" * 60)
    print("長時間動画分析")
    print("=" * 60)

    # 動画の長さを確認
    duration = get_video_duration(video_path)
    duration_minutes = duration / 60
    print(f"動画の長さ: {duration_minutes:.1f}分")

    chunk_duration_seconds = chunk_duration_minutes * 60

    # 15分以下なら分割不要
    if duration <= chunk_duration_seconds:
        print("→ 分割不要（15分以下）")
        result = analyze_video_chunk(video_path, 0)
        return {
            "full_transcript": result["transcript"],
            "chunk_analyses": [result["analysis"]],
            "overall_analysis": result["analysis"]
        }

    # 動画を分割
    print("\n動画を分割中...")
    with tempfile.TemporaryDirectory() as temp_dir:
        chunk_paths = split_video(video_path, chunk_duration_seconds, temp_dir)

        print(f"\n{len(chunk_paths)}チャンクを分析中...")

        all_transcripts = []
        all_analyses = []

        for i, chunk_path in enumerate(chunk_paths):
            print(f"\nチャンク {i+1}/{len(chunk_paths)} を分析中...")

            # チャンク間で待機（レート制限対策）
            if i > 0:
                print("  → レート制限対策: 60秒待機...")
                time.sleep(60)

            try:
                result = analyze_video_chunk(chunk_path, i)
                all_transcripts.append(f"[{i*chunk_duration_minutes}分〜{(i+1)*chunk_duration_minutes}分]\n{result['transcript']}")
                all_analyses.append(result["analysis"])
            except Exception as e:
                print(f"  エラー: {e}")
                all_transcripts.append(f"[{i*chunk_duration_minutes}分〜] (分析エラー)")

    # 全体の文字起こしを結合
    full_transcript = "\n\n".join(all_transcripts)

    # 全体の分析を統合
    overall_analysis = merge_analyses(all_analyses)

    return {
        "full_transcript": full_transcript,
        "chunk_analyses": all_analyses,
        "overall_analysis": overall_analysis
    }


def merge_analyses(analyses: list[dict]) -> dict:
    """複数チャンクの分析を統合"""
    if not analyses:
        return {}

    if len(analyses) == 1:
        return analyses[0]

    # 最も多い評価を採用
    def most_common(items):
        if not items:
            return "不明"
        return max(set(items), key=items.count)

    presenter_keys = ["confidence_level", "eye_contact", "speaking_pace", "gestures", "voice_tone"]
    presenter_analysis = {}

    for key in presenter_keys:
        values = [a.get("presenter_analysis", {}).get(key) for a in analyses if a.get("presenter_analysis", {}).get(key)]
        presenter_analysis[key] = most_common(values) if values else "不明"

    # 顧客反応
    engagement_levels = [a.get("audience_reaction", {}).get("engagement_level") for a in analyses if a.get("audience_reaction", {}).get("engagement_level")]

    positive_signals = []
    negative_signals = []
    for a in analyses:
        positive_signals.extend(a.get("audience_reaction", {}).get("positive_signals", []))
        negative_signals.extend(a.get("audience_reaction", {}).get("negative_signals", []))

    # 重複を除去
    positive_signals = list(set(positive_signals))[:5]
    negative_signals = list(set(negative_signals))[:5]

    return {
        "presenter_analysis": presenter_analysis,
        "audience_reaction": {
            "engagement_level": most_common(engagement_levels) if engagement_levels else "不明",
            "positive_signals": positive_signals,
            "negative_signals": negative_signals
        }
    }
