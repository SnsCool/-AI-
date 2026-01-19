#!/usr/bin/env python3
"""
大きなYouTube動画を分割して文字起こしするスクリプト
20MB上限を超えるファイルを10分ごとに分割して処理
"""

import os
import re
import json
import subprocess
import tempfile
import base64
import urllib.request
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
BASE_DIR = Path(__file__).parent.parent
KNOWLEDGE_BASE = BASE_DIR / 'knowledge_base'
TRANSCRIPTS_DIR = KNOWLEDGE_BASE / 'transcripts'

# 処理対象のサイズ超過動画
LARGE_VIDEOS = [
    '-kMHhrHfx5k',  # 63.6 MB
    'WGGfZ-5xUTo',  # 20.7 MB
    'bUcsCSXNHNM',  # 36.5 MB
]

def download_audio(video_id, output_path):
    """YouTube動画の音声をダウンロード"""
    url = f"https://www.youtube.com/watch?v={video_id}"
    cmd = [
        'yt-dlp',
        '-x',
        '--audio-format', 'mp3',
        '--audio-quality', '9',
        '--postprocessor-args', 'ffmpeg:-ac 1 -ar 16000',
        '-o', str(output_path),
        '--no-playlist',
        '--extractor-args', 'youtube:player_client=android',
        url
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    return result.returncode == 0

def split_audio(input_path, output_dir, segment_seconds=600):
    """音声ファイルを分割（デフォルト10分）"""
    segments = []

    # 音声の長さを取得
    cmd = ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
           '-of', 'default=noprint_wrappers=1:nokey=1', str(input_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    duration = float(result.stdout.strip())

    print(f"  音声長: {duration/60:.1f}分")

    # 分割
    segment_num = 0
    start = 0
    while start < duration:
        output_path = output_dir / f"segment_{segment_num:03d}.mp3"
        cmd = [
            'ffmpeg', '-y', '-i', str(input_path),
            '-ss', str(start),
            '-t', str(segment_seconds),
            '-ac', '1', '-ar', '16000', '-b:a', '32k',
            str(output_path)
        ]
        subprocess.run(cmd, capture_output=True, timeout=120)

        if output_path.exists() and output_path.stat().st_size > 0:
            segments.append(output_path)

        start += segment_seconds
        segment_num += 1

    print(f"  分割数: {len(segments)}セグメント")
    return segments

def transcribe_with_gemini(audio_path):
    """Geminiで文字起こし"""
    if not GEMINI_API_KEY:
        return None

    with open(audio_path, 'rb') as f:
        audio_data = base64.standard_b64encode(f.read()).decode('utf-8')

    file_size = audio_path.stat().st_size
    if file_size > 20 * 1024 * 1024:
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

    payload = {
        "contents": [{
            "parts": [
                {"inline_data": {"mime_type": "audio/mp3", "data": audio_data}},
                {"text": "この音声を日本語で文字起こししてください。"}
            ]
        }],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 8192}
    }

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})

    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"    Geminiエラー: {e}")
        return None

def process_large_video(video_id):
    """大きな動画を分割して文字起こし"""
    print(f"\n処理中: {video_id}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        audio_file = tmppath / f"{video_id}.mp3"

        # ダウンロード
        print("  ダウンロード中...")
        if not download_audio(video_id, audio_file):
            print("  → ダウンロード失敗")
            return None

        file_size = audio_file.stat().st_size / 1024 / 1024
        print(f"  → ダウンロード成功 ({file_size:.1f} MB)")

        # 分割
        print("  分割中...")
        segments = split_audio(audio_file, tmppath)

        if not segments:
            print("  → 分割失敗")
            return None

        # 各セグメントを文字起こし
        transcripts = []
        for i, segment in enumerate(segments):
            print(f"  セグメント {i+1}/{len(segments)} 処理中...")
            seg_size = segment.stat().st_size / 1024 / 1024
            print(f"    サイズ: {seg_size:.1f} MB")

            text = transcribe_with_gemini(segment)
            if text:
                transcripts.append(text)
                print(f"    → 成功 ({len(text)}文字)")
            else:
                print(f"    → 失敗")

            time.sleep(2)  # API制限対策

        if transcripts:
            return "\n\n".join(transcripts)
        return None

def main():
    print("=" * 60)
    print("大きなYouTube動画の分割文字起こし")
    print("=" * 60)

    for video_id in LARGE_VIDEOS:
        json_file = TRANSCRIPTS_DIR / f"youtube_{video_id}.json"

        if not json_file.exists():
            print(f"\n{video_id}: JSONファイルなし、スキップ")
            continue

        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if data.get('transcript'):
            print(f"\n{video_id}: 既に文字起こし済み、スキップ")
            continue

        transcript = process_large_video(video_id)

        if transcript:
            data['transcript'] = transcript
            data['transcribed_at'] = datetime.now().isoformat()
            data['transcription_method'] = 'gemini_split'

            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"  → 保存完了 (合計 {len(transcript)}文字)")
        else:
            print(f"  → 文字起こし失敗")

    print("\n" + "=" * 60)
    print("処理完了")
    print("=" * 60)

if __name__ == '__main__':
    main()
