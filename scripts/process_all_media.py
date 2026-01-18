#!/usr/bin/env python3
"""
Notion docs内の全動画・PDFを処理してナレッジ化するスクリプト
処理結果は knowledge_base/ フォルダに格納（notion_docsは変更しない）
"""

import os
import re
import json
import hashlib
import urllib.request
import tempfile
import time
from pathlib import Path
from datetime import datetime

# 設定
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
BASE_DIR = Path(__file__).parent.parent
NOTION_DOCS = BASE_DIR / 'notion_docs'
KNOWLEDGE_BASE = BASE_DIR / 'knowledge_base'

# 出力ディレクトリ
TRANSCRIPTS_DIR = KNOWLEDGE_BASE / 'transcripts'
PDF_TEXTS_DIR = KNOWLEDGE_BASE / 'pdf_texts'
LINK_CONTENTS_DIR = KNOWLEDGE_BASE / 'link_contents'

# 処理済みファイルを追跡
processed_log = KNOWLEDGE_BASE / 'processed_media.json'

def ensure_dirs():
    """出力ディレクトリを作成"""
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    PDF_TEXTS_DIR.mkdir(parents=True, exist_ok=True)
    LINK_CONTENTS_DIR.mkdir(parents=True, exist_ok=True)

def load_processed():
    """処理済みリストを読み込み"""
    if processed_log.exists():
        with open(processed_log, 'r') as f:
            return json.load(f)
    return {'loom': [], 'youtube': [], 'pdf': [], 'audio': []}

def save_processed(data):
    """処理済みリストを保存"""
    with open(processed_log, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_file_hash(url):
    """URLからハッシュIDを生成"""
    return hashlib.md5(url.encode()).hexdigest()[:12]

# ============ Loom処理 ============

def get_loom_info(video_id):
    """Loom動画の情報を取得"""
    url = f"https://www.loom.com/share/{video_id}"

    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode('utf-8')

        # タイトル抽出
        title_match = re.search(r'<title>([^<]+)</title>', html)
        title = title_match.group(1).replace(' | Loom', '').strip() if title_match else "Loom Video"

        return {
            'title': title,
            'url': url
        }

    except Exception as e:
        print(f"  Loom取得エラー: {e}")
        return None

def process_loom_videos():
    """全Loom動画を処理"""
    print("\n" + "="*60)
    print("Loom動画の情報収集")
    print("="*60)

    processed = load_processed()

    # notion_docs内のLoomリンクを検索
    loom_pattern = re.compile(r'loom\.com/share/([a-z0-9]+)')

    loom_videos = {}
    for md_file in NOTION_DOCS.rglob('*.md'):
        content = md_file.read_text(encoding='utf-8')
        for match in loom_pattern.finditer(content):
            video_id = match.group(1)
            if video_id not in loom_videos:
                loom_videos[video_id] = []
            rel_path = str(md_file.relative_to(NOTION_DOCS))
            if rel_path not in loom_videos[video_id]:
                loom_videos[video_id].append(rel_path)

    print(f"\n発見したLoom動画: {len(loom_videos)}件")

    new_count = 0
    for video_id, source_files in loom_videos.items():
        if video_id in processed['loom']:
            continue

        print(f"  処理中: {video_id}")
        result = get_loom_info(video_id)

        if result:
            output_file = TRANSCRIPTS_DIR / f"loom_{video_id}.json"

            data = {
                'type': 'loom',
                'video_id': video_id,
                'title': result.get('title', 'N/A'),
                'url': f"https://www.loom.com/share/{video_id}",
                'source_files': source_files,
                'processed_at': datetime.now().isoformat(),
                'transcript': None,  # Loom APIで取得可能な場合に追加
                'note': 'Loom動画の文字起こしにはLoom Developer APIが必要です'
            }

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"    → 保存: {output_file.name}")
            processed['loom'].append(video_id)
            new_count += 1

        time.sleep(0.5)

    save_processed(processed)
    print(f"\n新規処理: {new_count}件")

# ============ YouTube処理 ============

def get_youtube_transcript(video_id):
    """YouTube動画の文字起こしを取得"""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        # 日本語→英語→自動の順で試行
        for lang in ['ja', 'en', None]:
            try:
                if lang:
                    transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
                else:
                    transcript_list = YouTubeTranscriptApi.get_transcript(video_id)

                text = '\n'.join([t['text'] for t in transcript_list])
                return {
                    'transcript': text,
                    'language': lang or 'auto',
                }
            except:
                continue

    except ImportError:
        print("    youtube-transcript-api未インストール")
    except Exception as e:
        pass

    return None

def process_youtube_videos():
    """全YouTube動画を処理"""
    print("\n" + "="*60)
    print("YouTube動画の文字起こし処理")
    print("="*60)

    processed = load_processed()

    # YouTube動画IDを抽出
    patterns = [
        re.compile(r'youtube\.com/watch\?v=([a-zA-Z0-9_-]+)'),
        re.compile(r'youtu\.be/([a-zA-Z0-9_-]+)'),
        re.compile(r'youtube\.com/shorts/([a-zA-Z0-9_-]+)'),
    ]

    youtube_videos = {}
    for md_file in NOTION_DOCS.rglob('*.md'):
        content = md_file.read_text(encoding='utf-8')
        for pattern in patterns:
            for match in pattern.finditer(content):
                video_id = match.group(1)
                if video_id not in youtube_videos:
                    youtube_videos[video_id] = []
                rel_path = str(md_file.relative_to(NOTION_DOCS))
                if rel_path not in youtube_videos[video_id]:
                    youtube_videos[video_id].append(rel_path)

    print(f"\n発見したYouTube動画: {len(youtube_videos)}件")

    new_count = 0
    skip_count = 0

    for video_id, source_files in youtube_videos.items():
        if video_id in processed['youtube']:
            continue

        print(f"  処理中: {video_id}")
        result = get_youtube_transcript(video_id)

        output_file = TRANSCRIPTS_DIR / f"youtube_{video_id}.json"

        data = {
            'type': 'youtube',
            'video_id': video_id,
            'url': f"https://www.youtube.com/watch?v={video_id}",
            'source_files': source_files,
            'processed_at': datetime.now().isoformat(),
        }

        if result and result.get('transcript'):
            data['transcript'] = result['transcript']
            data['language'] = result.get('language')
            print(f"    → 字幕取得成功")
            new_count += 1
        else:
            data['transcript'] = None
            data['note'] = '字幕が利用できません'
            print(f"    → 字幕なし")
            skip_count += 1

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        processed['youtube'].append(video_id)
        time.sleep(0.3)

    save_processed(processed)
    print(f"\n文字起こし成功: {new_count}件 / 字幕なし: {skip_count}件")

# ============ PDF処理 ============

def process_pdfs():
    """全PDFの情報を収集（S3リンクは期限切れのため取得不可）"""
    print("\n" + "="*60)
    print("PDF情報収集")
    print("="*60)

    processed = load_processed()

    # S3 PDFリンクを検索
    pdf_pattern = re.compile(r'(https://prod-files-secure\.s3[^)\]\s]+\.pdf[^)\]\s]*)')

    pdfs = {}
    for md_file in NOTION_DOCS.rglob('*.md'):
        content = md_file.read_text(encoding='utf-8')
        for match in pdf_pattern.finditer(content):
            pdf_url = match.group(1)
            url_hash = get_file_hash(pdf_url)
            if url_hash not in pdfs:
                pdfs[url_hash] = {'url': pdf_url, 'files': []}
            rel_path = str(md_file.relative_to(NOTION_DOCS))
            if rel_path not in pdfs[url_hash]['files']:
                pdfs[url_hash]['files'].append(rel_path)

    print(f"\n発見したPDF: {len(pdfs)}件")
    print("\n⚠️ NotionのS3リンクは期限付きのため、PDFの直接ダウンロードは不可")
    print("   → Notion APIからの再取得が必要です")

    # PDF情報をJSON形式で保存
    pdf_index_file = PDF_TEXTS_DIR / 'pdf_index.json'
    pdf_list = []

    for url_hash, data in pdfs.items():
        pdf_list.append({
            'hash': url_hash,
            'source_files': data['files'],
            'note': 'S3リンク期限切れ - Notion APIから再取得が必要'
        })

    with open(pdf_index_file, 'w', encoding='utf-8') as f:
        json.dump({'total': len(pdfs), 'pdfs': pdf_list}, f, indent=2, ensure_ascii=False)

    print(f"  → PDFインデックス保存: {pdf_index_file.name}")

# ============ リンクコンテンツ移動 ============

def organize_link_contents():
    """既存のlink_contentファイルを整理"""
    print("\n" + "="*60)
    print("リンクコンテンツの整理")
    print("="*60)

    # notion_docs内のlink_contentファイルをリスト化
    link_files = list(NOTION_DOCS.rglob('link_*_content.txt'))
    print(f"\n発見したリンクコンテンツ: {len(link_files)}件")

    # インデックス作成
    link_index = []
    for link_file in link_files:
        rel_path = str(link_file.relative_to(NOTION_DOCS))
        link_index.append({
            'file': rel_path,
            'parent': str(link_file.parent.relative_to(NOTION_DOCS))
        })

    index_file = LINK_CONTENTS_DIR / 'link_index.json'
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump({'total': len(link_files), 'links': link_index}, f, indent=2, ensure_ascii=False)

    print(f"  → リンクインデックス保存: {index_file.name}")
    print(f"\n※ リンクコンテンツファイルは notion_docs/ に残します（Notionと同期のため）")

# ============ メイン ============

def print_summary():
    """処理サマリーを表示"""
    print("\n" + "="*60)
    print("処理サマリー")
    print("="*60)

    # knowledge_base内のファイルをカウント
    loom_count = len(list(TRANSCRIPTS_DIR.glob('loom_*.json')))
    youtube_count = len(list(TRANSCRIPTS_DIR.glob('youtube_*.json')))

    # 文字起こしがあるYouTubeをカウント
    youtube_with_transcript = 0
    for f in TRANSCRIPTS_DIR.glob('youtube_*.json'):
        with open(f, 'r') as jf:
            data = json.load(jf)
            if data.get('transcript'):
                youtube_with_transcript += 1

    print(f"""
knowledge_base/ 内のファイル:

📂 transcripts/
  - Loom動画情報: {loom_count}件
  - YouTube情報: {youtube_count}件（うち字幕あり: {youtube_with_transcript}件）

📂 pdf_texts/
  - PDFインデックス: あり

📂 link_contents/
  - リンクインデックス: あり
""")

def main():
    print("="*60)
    print("Notion Docs メディア処理ツール")
    print("="*60)
    print(f"\n入力: {NOTION_DOCS}")
    print(f"出力: {KNOWLEDGE_BASE}")

    # ディレクトリ作成
    ensure_dirs()

    # 各処理を実行
    process_loom_videos()
    process_youtube_videos()
    process_pdfs()
    organize_link_contents()

    # サマリー表示
    print_summary()

    print("\n✅ 処理完了")
    print(f"\n出力先: {KNOWLEDGE_BASE}")

if __name__ == '__main__':
    main()
