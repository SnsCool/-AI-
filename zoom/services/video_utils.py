"""
動画ユーティリティ
長い動画を分割して文字起こしする機能（Groq Whisper API）
"""

import os
import subprocess
import tempfile
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from services.groq_transcribe import transcribe_video as groq_transcribe

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

    duration = get_video_duration(video_path)
    print(f"動画の長さ: {duration/60:.1f}分")

    num_chunks = int(duration / chunk_duration_seconds) + 1
    print(f"分割数: {num_chunks}チャンク")

    chunk_paths = []

    for i in range(num_chunks):
        start_time = i * chunk_duration_seconds
        if start_time >= duration:
            break

        output_path = os.path.join(output_dir, f"chunk_{i:03d}.mp4")

        cmd = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-ss", str(start_time),
            "-t", str(chunk_duration_seconds),
            "-c", "copy",
            output_path
        ]

        print(f"  チャンク {i+1}/{num_chunks}: {start_time/60:.1f}分〜")
        subprocess.run(cmd, capture_output=True)

        if os.path.exists(output_path):
            chunk_paths.append(output_path)

    return chunk_paths


def transcribe_video_chunk(video_path: str, chunk_index: int = 0) -> dict:
    """
    動画チャンクをGroq Whisperで文字起こし

    Args:
        video_path: 動画ファイルのパス
        chunk_index: チャンク番号

    Returns:
        {"transcript": "文字起こしテキスト"}
    """
    print(f"  → チャンク {chunk_index + 1} をGroq Whisperで文字起こし中...")
    transcript = ""
    try:
        result = groq_transcribe(video_path)
        transcript = result or ""
    except Exception as e:
        print(f"    Groq文字起こしエラー: {e}")

    return {"transcript": transcript}


def transcribe_long_video(
    video_path: str,
    chunk_duration_minutes: int = 15
) -> dict:
    """
    長い動画を分割して文字起こし

    Args:
        video_path: 動画ファイルのパス
        chunk_duration_minutes: チャンクの長さ（分）

    Returns:
        {"full_transcript": "全体の文字起こし"}
    """
    print("=" * 60)
    print("動画文字起こし（Groq Whisper）")
    print("=" * 60)

    duration = get_video_duration(video_path)
    duration_minutes = duration / 60
    print(f"動画の長さ: {duration_minutes:.1f}分")

    # groq_transcribe が内部でチャンキングを処理するため、直接呼び出し
    print("Groq Whisperで文字起こし中...")
    try:
        transcript = groq_transcribe(video_path)
        return {"full_transcript": transcript or ""}
    except Exception as e:
        print(f"文字起こしエラー: {e}")
        return {"full_transcript": ""}
