#!/usr/bin/env python3
"""
Loom動画の既存文字起こしを取得するスクリプト
LoomはWhisperで自動文字起こしを生成しているため、それを取得する
"""

import os
import re
import json
import urllib.request
import time
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
KNOWLEDGE_BASE = BASE_DIR / 'knowledge_base'
TRANSCRIPTS_DIR = KNOWLEDGE_BASE / 'transcripts'

def get_loom_transcript(video_id):
    """Loom動画の文字起こしを取得"""
    url = f"https://www.loom.com/share/{video_id}"

    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode('utf-8')

        # Apollo Stateからtranscript URLを抽出
        match = re.search(r'"source_url":\s*"([^"]+transcription[^"]+)"', html)
        if not match:
            print(f"  文字起こしURLが見つかりません")
            return None

        transcript_url = match.group(1).replace('\\u0026', '&')

        # 文字起こしJSONを取得
        req = urllib.request.Request(transcript_url, headers={
            'User-Agent': 'Mozilla/5.0'
        })
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))

        # phrasesからテキストを抽出
        if 'phrases' in data:
            texts = []
            for phrase in data['phrases']:
                if 'value' in phrase:
                    texts.append(phrase['value'])
                elif 'text' in phrase:
                    texts.append(phrase['text'])

            full_text = ' '.join(texts)
            return full_text

        return None

    except Exception as e:
        print(f"  エラー: {e}")
        return None

def get_loom_info(video_id):
    """Loom動画の情報を取得"""
    url = f"https://www.loom.com/v1/oembed?url=https://www.loom.com/share/{video_id}"

    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0'
        })
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except:
        return {}

def process_all_loom_videos():
    """全Loom動画の文字起こしを取得"""
    print("=" * 60)
    print("Loom動画の文字起こし取得")
    print("=" * 60)

    # 既存のLoom JSONファイルを読み込み
    loom_files = list(TRANSCRIPTS_DIR.glob('loom_*.json'))
    print(f"\n対象動画: {len(loom_files)}件")

    success_count = 0
    skip_count = 0
    fail_count = 0

    for json_file in loom_files:
        video_id = json_file.stem.replace('loom_', '')

        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 既に文字起こしがあればスキップ
        if data.get('transcript'):
            skip_count += 1
            continue

        print(f"\n処理中: {video_id}")

        # 動画情報を取得
        info = get_loom_info(video_id)
        if info.get('title'):
            data['title'] = info['title']
            print(f"  タイトル: {info['title'][:50]}...")
        if info.get('description'):
            data['ai_summary'] = info['description']

        # 文字起こしを取得
        transcript = get_loom_transcript(video_id)

        if transcript:
            data['transcript'] = transcript
            data['transcribed_at'] = datetime.now().isoformat()
            data['transcription_method'] = 'loom_whisper'

            # 保存
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"  → 文字起こし成功 ({len(transcript)}文字)")
            success_count += 1
        else:
            print(f"  → 文字起こし取得失敗")
            fail_count += 1

        time.sleep(1)  # レート制限対策

    print("\n" + "=" * 60)
    print(f"完了: 成功 {success_count}件 / スキップ {skip_count}件 / 失敗 {fail_count}件")
    print("=" * 60)

if __name__ == '__main__':
    process_all_loom_videos()
