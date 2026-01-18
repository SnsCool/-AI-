#!/usr/bin/env python3
"""
Gemini APIを使用した動画文字起こし・PDFテキスト抽出スクリプト
- YouTube/Loom動画: yt-dlpでダウンロード → Geminiで文字起こし
- PDF: Notion APIから再取得 → Geminiでテキスト抽出
"""

import os
import re
import json
import subprocess
import tempfile
import time
import base64
import urllib.request
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# .envから環境変数を読み込み
load_dotenv()

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
NOTION_TOKEN = os.environ.get('NOTION_API_TOKEN')

BASE_DIR = Path(__file__).parent.parent
KNOWLEDGE_BASE = BASE_DIR / 'knowledge_base'
TRANSCRIPTS_DIR = KNOWLEDGE_BASE / 'transcripts'
PDF_TEXTS_DIR = KNOWLEDGE_BASE / 'pdf_texts'

# 処理済みファイル追跡
PROCESSED_FILE = KNOWLEDGE_BASE / 'processed_media.json'

def load_processed():
    if PROCESSED_FILE.exists():
        with open(PROCESSED_FILE, 'r') as f:
            return json.load(f)
    return {'loom': [], 'youtube': [], 'pdf': [], 'audio': [], 'transcribed': []}

def save_processed(data):
    with open(PROCESSED_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ============ Gemini API ============

def gemini_transcribe_audio(audio_path):
    """Gemini APIで音声を文字起こし"""
    if not GEMINI_API_KEY:
        print("    GEMINI_API_KEY未設定")
        return None

    try:
        # 音声ファイルをbase64エンコード
        with open(audio_path, 'rb') as f:
            audio_data = base64.standard_b64encode(f.read()).decode('utf-8')

        # ファイルサイズ確認
        file_size = os.path.getsize(audio_path)
        print(f"    音声ファイルサイズ: {file_size / 1024 / 1024:.1f} MB")

        if file_size > 20 * 1024 * 1024:  # 20MB制限
            print("    ファイルが大きすぎます（20MB上限）")
            return None

        # 拡張子からMIMEタイプを判定
        ext = Path(audio_path).suffix.lower()
        mime_types = {
            '.mp3': 'audio/mp3',
            '.m4a': 'audio/mp4',
            '.wav': 'audio/wav',
            '.webm': 'audio/webm',
            '.ogg': 'audio/ogg',
        }
        mime_type = mime_types.get(ext, 'audio/mp3')

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

        payload = {
            "contents": [{
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": audio_data
                        }
                    },
                    {
                        "text": "この音声を日本語で文字起こししてください。話者が複数いる場合は区別してください。タイムスタンプは不要です。"
                    }
                ]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 8192
            }
        }

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={
            'Content-Type': 'application/json'
        })

        with urllib.request.urlopen(req, timeout=300) as response:
            result = json.loads(response.read().decode('utf-8'))

        if 'candidates' in result and len(result['candidates']) > 0:
            text = result['candidates'][0]['content']['parts'][0]['text']
            return text

        return None

    except Exception as e:
        print(f"    Gemini API エラー: {e}")
        return None

def gemini_extract_pdf_text(pdf_path):
    """Gemini APIでPDFからテキスト抽出"""
    if not GEMINI_API_KEY:
        print("    GEMINI_API_KEY未設定")
        return None

    try:
        with open(pdf_path, 'rb') as f:
            pdf_data = base64.standard_b64encode(f.read()).decode('utf-8')

        file_size = os.path.getsize(pdf_path)
        print(f"    PDFファイルサイズ: {file_size / 1024 / 1024:.1f} MB")

        if file_size > 20 * 1024 * 1024:
            print("    ファイルが大きすぎます")
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

        payload = {
            "contents": [{
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": "application/pdf",
                            "data": pdf_data
                        }
                    },
                    {
                        "text": "このPDFの内容をすべてテキストとして抽出してください。レイアウトは保持しなくて構いません。"
                    }
                ]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 8192
            }
        }

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={
            'Content-Type': 'application/json'
        })

        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode('utf-8'))

        if 'candidates' in result and len(result['candidates']) > 0:
            text = result['candidates'][0]['content']['parts'][0]['text']
            return text

        return None

    except Exception as e:
        print(f"    Gemini API エラー: {e}")
        return None

# ============ yt-dlp ダウンロード ============

def download_audio_ytdlp(video_url, output_dir):
    """yt-dlpで動画から音声をダウンロード（低ビットレートで圧縮）"""
    try:
        output_template = str(output_dir / "%(id)s.%(ext)s")

        cmd = [
            'yt-dlp',
            '-x',  # 音声のみ抽出
            '--audio-format', 'mp3',
            '--audio-quality', '9',  # 最低品質（ファイルサイズ最小化）
            '--postprocessor-args', 'ffmpeg:-ac 1 -ar 16000',  # モノラル、16kHz
            '-o', output_template,
            '--no-playlist',
            '--extractor-args', 'youtube:player_client=android',  # 403エラー回避
            '--quiet',
            video_url
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode != 0:
            print(f"    yt-dlp エラー: {result.stderr[:200]}")
            return None

        # ダウンロードされたファイルを探す
        for f in output_dir.glob("*.mp3"):
            # さらに圧縮が必要な場合
            file_size = f.stat().st_size
            if file_size > 18 * 1024 * 1024:  # 18MB以上なら再圧縮
                compressed = compress_audio(f)
                if compressed:
                    return compressed
            return f
        for f in output_dir.glob("*.m4a"):
            return f
        for f in output_dir.glob("*.webm"):
            return f

        return None

    except subprocess.TimeoutExpired:
        print("    ダウンロードタイムアウト")
        return None
    except Exception as e:
        print(f"    ダウンロードエラー: {e}")
        return None

def compress_audio(audio_path):
    """ffmpegで音声をさらに圧縮"""
    try:
        output_path = audio_path.parent / f"{audio_path.stem}_compressed.mp3"
        cmd = [
            'ffmpeg', '-y', '-i', str(audio_path),
            '-ac', '1',  # モノラル
            '-ar', '16000',  # 16kHz
            '-b:a', '32k',  # 32kbps
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0 and output_path.exists():
            print(f"    → 圧縮成功: {output_path.stat().st_size / 1024 / 1024:.1f} MB")
            return output_path
    except Exception as e:
        print(f"    圧縮エラー: {e}")
    return None

# ============ YouTube処理 ============

def process_youtube_with_gemini():
    """YouTube動画をGeminiで文字起こし"""
    print("\n" + "="*60)
    print("YouTube動画の文字起こし (Gemini)")
    print("="*60)

    processed = load_processed()
    if 'transcribed' not in processed:
        processed['transcribed'] = []

    # 既存のYouTube情報ファイルを読み込み
    youtube_files = list(TRANSCRIPTS_DIR.glob('youtube_*.json'))
    print(f"\n対象動画: {len(youtube_files)}件")

    success_count = 0
    skip_count = 0

    for json_file in youtube_files:
        video_id = json_file.stem.replace('youtube_', '')

        # すでに文字起こし済みならスキップ
        if f"youtube_{video_id}" in processed['transcribed']:
            skip_count += 1
            continue

        with open(json_file, 'r') as f:
            data = json.load(f)

        # すでに文字起こしがあればスキップ
        if data.get('transcript'):
            processed['transcribed'].append(f"youtube_{video_id}")
            skip_count += 1
            continue

        print(f"\n処理中: {video_id}")
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # 音声ダウンロード
            print("  音声ダウンロード中...")
            audio_file = download_audio_ytdlp(video_url, tmppath)

            if not audio_file:
                print("  → ダウンロード失敗")
                continue

            print(f"  → ダウンロード成功: {audio_file.name}")

            # Geminiで文字起こし
            print("  Gemini文字起こし中...")
            transcript = gemini_transcribe_audio(audio_file)

            if transcript:
                data['transcript'] = transcript
                data['transcribed_at'] = datetime.now().isoformat()
                data['transcription_method'] = 'gemini'

                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                print(f"  → 文字起こし成功 ({len(transcript)}文字)")
                processed['transcribed'].append(f"youtube_{video_id}")
                success_count += 1
            else:
                print("  → 文字起こし失敗")

        # API制限対策
        time.sleep(2)

    save_processed(processed)
    print(f"\n完了: 成功 {success_count}件 / スキップ {skip_count}件")

# ============ Loom処理 ============

def process_loom_with_gemini():
    """Loom動画をGeminiで文字起こし"""
    print("\n" + "="*60)
    print("Loom動画の文字起こし (Gemini)")
    print("="*60)

    processed = load_processed()
    if 'transcribed' not in processed:
        processed['transcribed'] = []

    loom_files = list(TRANSCRIPTS_DIR.glob('loom_*.json'))
    print(f"\n対象動画: {len(loom_files)}件")

    success_count = 0
    skip_count = 0

    for json_file in loom_files:
        video_id = json_file.stem.replace('loom_', '')

        if f"loom_{video_id}" in processed['transcribed']:
            skip_count += 1
            continue

        with open(json_file, 'r') as f:
            data = json.load(f)

        if data.get('transcript'):
            processed['transcribed'].append(f"loom_{video_id}")
            skip_count += 1
            continue

        print(f"\n処理中: {video_id}")
        video_url = f"https://www.loom.com/share/{video_id}"

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            print("  音声ダウンロード中...")
            audio_file = download_audio_ytdlp(video_url, tmppath)

            if not audio_file:
                print("  → ダウンロード失敗（Loomはログインが必要な場合があります）")
                continue

            print(f"  → ダウンロード成功: {audio_file.name}")

            print("  Gemini文字起こし中...")
            transcript = gemini_transcribe_audio(audio_file)

            if transcript:
                data['transcript'] = transcript
                data['transcribed_at'] = datetime.now().isoformat()
                data['transcription_method'] = 'gemini'

                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                print(f"  → 文字起こし成功 ({len(transcript)}文字)")
                processed['transcribed'].append(f"loom_{video_id}")
                success_count += 1
            else:
                print("  → 文字起こし失敗")

        time.sleep(2)

    save_processed(processed)
    print(f"\n完了: 成功 {success_count}件 / スキップ {skip_count}件")

# ============ PDF処理 ============

def get_pdf_from_notion(page_id):
    """Notion APIからページ内のPDFを取得"""
    if not NOTION_TOKEN:
        return None

    try:
        url = f"https://api.notion.com/v1/blocks/{page_id}/children"
        req = urllib.request.Request(url, headers={
            'Authorization': f'Bearer {NOTION_TOKEN}',
            'Notion-Version': '2022-06-28'
        })

        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))

        pdfs = []
        for block in data.get('results', []):
            if block.get('type') == 'pdf':
                pdf_data = block.get('pdf', {})
                if pdf_data.get('type') == 'file':
                    pdf_url = pdf_data.get('file', {}).get('url')
                    if pdf_url:
                        pdfs.append(pdf_url)

        return pdfs

    except Exception as e:
        print(f"    Notion API エラー: {e}")
        return None

def download_pdf(url, output_path):
    """PDFをダウンロード"""
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0'
        })
        with urllib.request.urlopen(req, timeout=60) as response:
            with open(output_path, 'wb') as f:
                f.write(response.read())
        return True
    except Exception as e:
        print(f"    ダウンロードエラー: {e}")
        return False

def process_pdfs_with_gemini():
    """PDFをGeminiでテキスト抽出"""
    print("\n" + "="*60)
    print("PDFテキスト抽出 (Gemini)")
    print("="*60)

    # PDFインデックスを読み込み
    pdf_index_file = PDF_TEXTS_DIR / 'pdf_index.json'
    if not pdf_index_file.exists():
        print("PDFインデックスが見つかりません")
        return

    with open(pdf_index_file, 'r') as f:
        pdf_index = json.load(f)

    print(f"\n対象PDF: {pdf_index.get('total', 0)}件")
    print("注: Notion APIからPDFを再取得する必要があります")

    # TODO: Notion APIからPDF URLを再取得する実装
    # 現状はS3リンクが期限切れのため、ページIDからの再取得が必要

    print("\n※ PDF処理にはNotion APIからの再取得が必要です")
    print("   各ページIDからPDFブロックを検索して新しいURLを取得する必要があります")

# ============ メイン ============

def main():
    print("="*60)
    print("Gemini APIによるメディア文字起こし")
    print("="*60)

    if not GEMINI_API_KEY:
        print("\nエラー: GEMINI_API_KEYが設定されていません")
        print(".envファイルにGEMINI_API_KEYを追加してください")
        return

    print(f"\n出力先: {KNOWLEDGE_BASE}")

    # YouTube処理
    process_youtube_with_gemini()

    # Loom処理
    process_loom_with_gemini()

    # PDF処理
    process_pdfs_with_gemini()

    print("\n" + "="*60)
    print("処理完了")
    print("="*60)

if __name__ == '__main__':
    main()
