"""
動画文字起こしサービス
- YouTube
- Loom
- Gemini API (直接アップロード)
"""

import os
import time
import tempfile
import re
from pathlib import Path
from datetime import datetime
from typing import Optional

import requests

# YouTube transcript
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    YOUTUBE_AVAILABLE = True
except ImportError:
    YOUTUBE_AVAILABLE = False

# Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class TranscribeService:
    def __init__(self):
        self.gemini_api_key = os.environ.get("GEMINI_API_KEY")
        if self.gemini_api_key and GEMINI_AVAILABLE:
            genai.configure(api_key=self.gemini_api_key)

    def transcribe_youtube(self, video_id: str) -> dict:
        """YouTube動画の字幕を取得"""
        if not YOUTUBE_AVAILABLE:
            return {"success": False, "error": "youtube-transcript-api がインストールされていません"}

        try:
            # 日本語 → 英語 → その他の順で試行
            for languages in [['ja'], ['en'], None]:
                try:
                    if languages:
                        transcript_list = YouTubeTranscriptApi().fetch(video_id, languages=languages)
                    else:
                        transcript_list = YouTubeTranscriptApi().fetch(video_id)
                    break
                except Exception:
                    continue
            else:
                return {"success": False, "error": "字幕が見つかりません"}

            # タイムスタンプ付きテキストに変換
            lines = []
            for entry in transcript_list:
                start = entry.get("start", 0)
                text = entry.get("text", "")
                minutes = int(start // 60)
                seconds = int(start % 60)
                lines.append(f"[{minutes:02d}:{seconds:02d}] {text}")

            transcript_text = "\n".join(lines)

            return {
                "success": True,
                "video_id": video_id,
                "transcript": transcript_text,
                "source": "youtube",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def transcribe_loom(self, loom_url: str) -> dict:
        """Loom動画の字幕を取得"""
        try:
            # LoomページからビデオIDを抽出
            match = re.search(r'loom\.com/share/([a-f0-9]+)', loom_url)
            if not match:
                return {"success": False, "error": "無効なLoom URLです"}

            video_id = match.group(1)

            # Loomページを取得してキャプションURLを探す
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
            response = requests.get(loom_url, headers=headers, timeout=30)

            # キャプションURLを探す
            caption_match = re.search(r'"captions_url"\s*:\s*"([^"]+)"', response.text)
            if not caption_match:
                return {"success": False, "error": "キャプションが見つかりません"}

            captions_url = caption_match.group(1).replace("\\u0026", "&")

            # キャプションを取得
            captions_response = requests.get(captions_url, headers=headers, timeout=30)
            vtt_content = captions_response.text

            # VTTをテキストに変換
            transcript_text = self._parse_vtt(vtt_content)

            return {
                "success": True,
                "video_id": video_id,
                "transcript": transcript_text,
                "source": "loom",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def transcribe_video_with_gemini(self, video_path: str, output_path: Optional[str] = None) -> dict:
        """Gemini APIで動画を直接文字起こし"""
        if not GEMINI_AVAILABLE:
            return {"success": False, "error": "google-generativeai がインストールされていません"}

        if not self.gemini_api_key:
            return {"success": False, "error": "GEMINI_API_KEY が設定されていません"}

        video_path = Path(video_path)
        if not video_path.exists():
            return {"success": False, "error": f"ファイルが見つかりません: {video_path}"}

        try:
            # Geminiにアップロード
            uploaded_file = genai.upload_file(str(video_path))

            # 処理完了を待つ
            while uploaded_file.state.name == "PROCESSING":
                time.sleep(5)
                uploaded_file = genai.get_file(uploaded_file.name)

            if uploaded_file.state.name == "FAILED":
                return {"success": False, "error": "アップロード処理に失敗しました"}

            # 文字起こし
            model = genai.GenerativeModel("gemini-2.0-flash")
            prompt = """この動画の内容を文字起こししてください。

以下の形式でタイムスタンプ付きで出力してください：
[MM:SS] 発言内容

注意点：
- 日本語で出力してください
- 話者が複数いる場合は区別してください
"""
            response = model.generate_content([prompt, uploaded_file])

            # アップロードファイルを削除
            try:
                genai.delete_file(uploaded_file.name)
            except:
                pass

            transcript = response.text

            # 保存
            if output_path:
                output_path = Path(output_path)
            else:
                output_path = video_path.parent / f"{video_path.stem}_transcript.txt"

            header = f"""# 動画 文字起こし

**動画ファイル**: {video_path.name}
**ファイルサイズ**: {video_path.stat().st_size / 1024 / 1024:.2f} MB
**抽出日時**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**処理方法**: Gemini API 直接文字起こし

---

"""
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(header + transcript)

            return {
                "success": True,
                "transcript": transcript,
                "output_path": str(output_path),
                "source": "gemini",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _parse_vtt(self, vtt_content: str) -> str:
        """VTT形式をタイムスタンプ付きテキストに変換"""
        lines = []
        current_time = None

        for line in vtt_content.split("\n"):
            line = line.strip()

            # タイムスタンプ行
            if "-->" in line:
                time_match = re.match(r"(\d{2}):(\d{2}):(\d{2})", line)
                if time_match:
                    hours, minutes, seconds = time_match.groups()
                    total_minutes = int(hours) * 60 + int(minutes)
                    current_time = f"[{total_minutes:02d}:{int(seconds):02d}]"
                continue

            # テキスト行
            if line and not line.startswith("WEBVTT") and not line.isdigit():
                if current_time:
                    lines.append(f"{current_time} {line}")
                    current_time = None

        return "\n".join(lines)
