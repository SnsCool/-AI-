"""
Groq Whisper 文字起こしサービス
動画/音声ファイルをGroq Whisper APIで文字起こしする
"""

import os
import shutil
import subprocess
import tempfile
import time
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv(override=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ffmpeg/ffprobe の存在チェック
if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
    print("WARNING: ffmpeg/ffprobe が見つかりません。音声抽出が失敗します。")
GROQ_API_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
WHISPER_MODEL = "whisper-large-v3-turbo"

# Groq Whisper の制限: 25MB
MAX_AUDIO_SIZE_MB = 25
# 音声チャンク長（秒）: 25MBに収まるよう15分
AUDIO_CHUNK_SECONDS = 900


def _extract_audio(video_path: str, output_path: str) -> bool:
    """動画から音声を抽出（mp3形式、ビットレート制御で25MB制限に対応）"""
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn",
        "-acodec", "libmp3lame",
        "-b:a", "48k",  # 低ビットレートで25MB制限内に収める
        "-loglevel", "error",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        print(f"   ffmpeg error: {result.stderr[:200]}")
        return False
    return os.path.exists(output_path)


def _get_audio_duration(audio_path: str) -> float:
    """音声ファイルの長さを秒で取得"""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        print(f"   ffprobe error: {result.stderr[:200]}")
        return 0.0
    try:
        return float(result.stdout.strip())
    except (ValueError, AttributeError):
        return 0.0


def _split_audio(audio_path: str, chunk_seconds: int, output_dir: str) -> list[str]:
    """音声ファイルをチャンクに分割"""
    duration = _get_audio_duration(audio_path)
    if duration <= 0:
        return []

    num_chunks = int(duration / chunk_seconds) + 1
    chunk_paths = []

    for i in range(num_chunks):
        start = i * chunk_seconds
        if start >= duration:
            break
        output_path = os.path.join(output_dir, f"chunk_{i:03d}.mp3")
        cmd = [
            "ffmpeg", "-y",
            "-i", audio_path,
            "-ss", str(start),
            "-t", str(chunk_seconds),
            "-acodec", "libmp3lame",
            "-b:a", "48k",
            "-loglevel", "error",
            output_path,
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            print(f"   チャンク{i}分割エラー: {r.stderr[:100]}")
            continue
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            chunk_paths.append(output_path)

    return chunk_paths


def _call_groq_whisper(audio_path: str, api_key: str = None, language: str = "ja") -> Optional[str]:
    """Groq Whisper APIを呼び出して文字起こし"""
    key = api_key or GROQ_API_KEY
    if not key:
        raise ValueError("GROQ_API_KEY is not set")

    headers = {"Authorization": f"Bearer {key}"}

    for attempt in range(3):
        try:
            with open(audio_path, "rb") as f:
                files = {"file": (os.path.basename(audio_path), f, "audio/mpeg")}
                data = {
                    "model": WHISPER_MODEL,
                    "language": language,
                    "response_format": "verbose_json",
                }
                resp = requests.post(
                    GROQ_API_URL,
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=300,
                )

            if resp.status_code == 429:
                retry_after = int(resp.headers.get("retry-after", 30))
                print(f"   Groq API レート制限、{retry_after}秒待機... ({attempt+1}/3)")
                time.sleep(retry_after)
                continue

            resp.raise_for_status()
            result = resp.json()
            return result.get("text", "")

        except requests.exceptions.HTTPError as e:
            print(f"   Groq API HTTPエラー ({attempt+1}/3): {e}")
            if attempt < 2 and "429" in str(e):
                time.sleep(30)
                continue
            raise
        except Exception as e:
            print(f"   Groq APIエラー ({attempt+1}/3): {e}")
            if attempt < 2:
                time.sleep(5 * (attempt + 1))
                continue
            raise

    return None


def transcribe_video(video_path: str, api_key: str = None, language: str = "ja") -> Optional[str]:
    """
    動画ファイルをGroq Whisperで文字起こし

    Args:
        video_path: 動画ファイルのパス
        api_key: Groq APIキー（省略時は環境変数から取得）
        language: 言語コード（デフォルト: ja）

    Returns:
        文字起こしテキスト、失敗時はNone
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        # 1. 音声を抽出
        audio_path = os.path.join(temp_dir, "audio.mp3")
        print("   音声を抽出中...")
        if not _extract_audio(video_path, audio_path):
            print("   音声抽出に失敗しました")
            return None

        audio_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
        duration = _get_audio_duration(audio_path)
        print(f"   音声: {audio_size_mb:.1f}MB, {duration/60:.1f}分")

        # 2. サイズが25MB以下ならそのまま送信
        if audio_size_mb <= MAX_AUDIO_SIZE_MB:
            print("   Groq Whisperで文字起こし中...")
            return _call_groq_whisper(audio_path, api_key, language)

        # 3. 大きい場合はチャンク分割
        print(f"   音声が{MAX_AUDIO_SIZE_MB}MBを超えるため分割...")
        chunks = _split_audio(audio_path, AUDIO_CHUNK_SECONDS, temp_dir)
        print(f"   {len(chunks)}チャンクに分割")

        all_texts = []
        for i, chunk_path in enumerate(chunks):
            print(f"   チャンク {i+1}/{len(chunks)} を文字起こし中...")
            if i > 0:
                time.sleep(2)  # レート制限対策

            text = _call_groq_whisper(chunk_path, api_key, language)
            start_min = i * (AUDIO_CHUNK_SECONDS // 60)
            end_min = (i + 1) * (AUDIO_CHUNK_SECONDS // 60)

            if text:
                all_texts.append(f"[{start_min}分〜{end_min}分]\n{text}")
            else:
                all_texts.append(f"[{start_min}分〜{end_min}分] (文字起こし失敗)")

        return "\n\n".join(all_texts) if all_texts else None


def transcribe_audio(audio_path: str, api_key: str = None, language: str = "ja") -> Optional[str]:
    """
    音声ファイルを直接Groq Whisperで文字起こし

    Args:
        audio_path: 音声ファイルのパス
        api_key: Groq APIキー
        language: 言語コード

    Returns:
        文字起こしテキスト
    """
    audio_size_mb = os.path.getsize(audio_path) / (1024 * 1024)

    if audio_size_mb <= MAX_AUDIO_SIZE_MB:
        return _call_groq_whisper(audio_path, api_key, language)

    # 大きい場合はチャンク分割
    with tempfile.TemporaryDirectory() as temp_dir:
        chunks = _split_audio(audio_path, AUDIO_CHUNK_SECONDS, temp_dir)
        all_texts = []
        for i, chunk_path in enumerate(chunks):
            if i > 0:
                time.sleep(2)
            text = _call_groq_whisper(chunk_path, api_key, language)
            if text:
                all_texts.append(text)
        return "\n\n".join(all_texts) if all_texts else None
