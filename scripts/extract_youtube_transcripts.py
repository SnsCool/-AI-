#!/usr/bin/env python3
"""
YouTube動画の字幕（文字起こし）を抽出するスクリプト
- HTMLファイルからYouTube動画IDを抽出
- youtube-transcript-apiで字幕を取得
"""

import re
from pathlib import Path
from datetime import datetime

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
except ImportError:
    print("youtube-transcript-api が必要です")
    print("pip install youtube-transcript-api")
    exit(1)

BASE_DIR = Path(__file__).parent.parent
NOTION_DOCS_DIR = BASE_DIR / "notion_docs"


def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}", flush=True)


def extract_youtube_video_id(html_content):
    """HTMLからYouTube動画IDを抽出"""
    patterns = [
        r'"videoId":"([a-zA-Z0-9_-]{11})"',
        r'youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        r'youtu\.be/([a-zA-Z0-9_-]{11})',
        r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, html_content)
        if match:
            return match.group(1)
    return None


def extract_video_title(html_content):
    """HTMLから動画タイトルを抽出"""
    match = re.search(r'"title":"([^"]+)"', html_content)
    if match:
        title = match.group(1)
        # Unicode エスケープをデコード
        try:
            title = title.encode().decode('unicode_escape')
        except:
            pass
        return title
    return "Unknown"


def get_youtube_transcript(video_id):
    """YouTubeから字幕を取得"""
    try:
        ytt = YouTubeTranscriptApi()

        # まず日本語を試す
        try:
            transcript = ytt.fetch(video_id, languages=['ja'])
            if transcript:
                return transcript.to_raw_data()
        except:
            pass

        # 英語を試す
        try:
            transcript = ytt.fetch(video_id, languages=['en'])
            if transcript:
                return transcript.to_raw_data()
        except:
            pass

        # 任意の言語
        try:
            transcript = ytt.fetch(video_id)
            if transcript:
                return transcript.to_raw_data()
        except:
            pass

        return None

    except TranscriptsDisabled:
        log("  字幕が無効になっています", "WARN")
        return None
    except NoTranscriptFound:
        log("  字幕が見つかりません", "WARN")
        return None
    except Exception as e:
        log(f"  字幕取得エラー: {e}", "ERROR")
        return None


def format_transcript(transcript_data):
    """字幕データをタイムスタンプ付きテキストに変換"""
    result = []
    for item in transcript_data:
        start = item.get('start', 0)
        text = item.get('text', '')

        mins = int(start) // 60
        secs = int(start) % 60
        result.append(f"[{mins:02d}:{secs:02d}] {text}")

    return '\n'.join(result)


def process_youtube_html_file(html_path):
    """YouTubeのHTMLファイルを処理して字幕を取得"""
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # YouTubeページか確認
        if 'youtube' not in html_content.lower():
            return False

        # 動画IDを抽出
        video_id = extract_youtube_video_id(html_content)
        if not video_id:
            log("  動画ID抽出失敗", "WARN")
            return False

        log(f"  YouTube動画ID: {video_id}")

        title = extract_video_title(html_content)
        log(f"  動画タイトル: {title}")

        # 字幕を取得
        transcript_data = get_youtube_transcript(video_id)

        if transcript_data:
            transcript_text = format_transcript(transcript_data)

            # 保存先
            transcript_path = html_path.parent / f"{html_path.stem}_transcript.txt"

            header = f"""# YouTube動画 文字起こし

**動画タイトル**: {title}
**動画ID**: {video_id}
**動画URL**: https://www.youtube.com/watch?v={video_id}
**元ファイル**: {html_path.name}
**抽出日時**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

"""
            with open(transcript_path, 'w', encoding='utf-8') as f:
                f.write(header + transcript_text)

            log(f"  保存完了: {transcript_path.name}")
            return True
        else:
            # 字幕がない場合でもメタ情報を保存
            meta_path = html_path.parent / f"{html_path.stem}_info.txt"
            if not meta_path.exists():
                with open(meta_path, 'w', encoding='utf-8') as f:
                    f.write(f"""# YouTube動画 情報

**動画タイトル**: {title}
**動画ID**: {video_id}
**動画URL**: https://www.youtube.com/watch?v={video_id}
**元ファイル**: {html_path.name}
**記録日時**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

※ この動画には自動字幕がありません。動画を直接視聴してください。
""")
                log(f"  メタ情報を保存: {meta_path.name}")
            return False

    except Exception as e:
        log(f"  処理エラー: {e}", "ERROR")
        return False


def main():
    print("=" * 60)
    print("YouTube動画 字幕抽出スクリプト")
    print("=" * 60)

    # video_*.mp4ファイルを探す
    video_files = list(NOTION_DOCS_DIR.rglob("video_*.mp4"))
    log(f"動画ファイル数: {len(video_files)}")

    processed = 0
    skipped = 0

    for video_path in video_files:
        # 既に文字起こしがあればスキップ
        transcript_path = video_path.parent / f"{video_path.stem}_transcript.txt"
        if transcript_path.exists():
            log(f"スキップ（既存）: {video_path.name}")
            skipped += 1
            continue

        log(f"処理中: {video_path.relative_to(NOTION_DOCS_DIR)}")

        # ファイルがHTMLか確認
        try:
            with open(video_path, 'rb') as f:
                first_bytes = f.read(500)

            content_str = first_bytes.decode('utf-8', errors='ignore')

            if 'youtube' in content_str.lower():
                if process_youtube_html_file(video_path):
                    processed += 1
            else:
                log(f"  YouTubeではありません", "INFO")
        except Exception as e:
            log(f"  ファイル読み込みエラー: {e}", "ERROR")

    print("=" * 60)
    print("処理完了")
    print(f"  処理済み: {processed}件")
    print(f"  スキップ: {skipped}件")
    print("=" * 60)


if __name__ == "__main__":
    main()
