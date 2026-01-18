#!/usr/bin/env python3
"""
Gemini APIで動画を直接文字起こしするスクリプト
- Google Driveからダウンロードした動画などに使用
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime

try:
    import google.generativeai as genai
except ImportError:
    print("google-generativeaiが必要です: pip install google-generativeai")
    sys.exit(1)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")


def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}", flush=True)


def transcribe_video(video_path, output_path=None):
    """動画をGemini APIで文字起こし"""
    video_path = Path(video_path)

    if not video_path.exists():
        log(f"ファイルが見つかりません: {video_path}", "ERROR")
        return False

    if output_path is None:
        output_path = video_path.parent / f"{video_path.stem}_transcript.txt"
    else:
        output_path = Path(output_path)

    log(f"処理開始: {video_path.name}")
    log(f"ファイルサイズ: {video_path.stat().st_size / 1024 / 1024:.2f} MB")

    try:
        # Geminiにアップロード
        log("Geminiにアップロード中...")
        uploaded_file = genai.upload_file(str(video_path))

        # 処理完了を待つ
        while uploaded_file.state.name == "PROCESSING":
            log("  処理中...")
            time.sleep(5)
            uploaded_file = genai.get_file(uploaded_file.name)

        if uploaded_file.state.name == "FAILED":
            log("アップロード失敗", "ERROR")
            return False

        log("文字起こし中...")
        model = genai.GenerativeModel("gemini-2.0-flash")

        prompt = """この動画の内容を文字起こししてください。

以下の形式でタイムスタンプ付きで出力してください：
[MM:SS] 発言内容

例：
[00:00] こんにちは、今日は...
[00:15] それでは始めましょう

注意点：
- 日本語で出力してください
- 話者が複数いる場合は区別してください
- 重要なポイントは強調してください
"""

        response = model.generate_content([prompt, uploaded_file])

        # アップロードファイルを削除
        try:
            genai.delete_file(uploaded_file.name)
        except:
            pass

        transcript = response.text

        # 保存
        header = f"""# 動画 文字起こし

**動画ファイル**: {video_path.name}
**ファイルサイズ**: {video_path.stat().st_size / 1024 / 1024:.2f} MB
**抽出日時**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**処理方法**: Gemini API 直接文字起こし

---

"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(header + transcript)

        log(f"保存完了: {output_path}")
        return True

    except Exception as e:
        log(f"エラー: {e}", "ERROR")
        return False


def main():
    if not GEMINI_API_KEY:
        log("GEMINI_API_KEY が設定されていません", "ERROR")
        log("export GEMINI_API_KEY=your-api-key を実行してください")
        return

    genai.configure(api_key=GEMINI_API_KEY)

    if len(sys.argv) < 2:
        print("使用方法: python3 transcribe_video_with_gemini.py <動画ファイルパス> [出力ファイルパス]")
        print("")
        print("例:")
        print("  python3 transcribe_video_with_gemini.py video.mp4")
        print("  python3 transcribe_video_with_gemini.py video.mp4 output.txt")
        return

    video_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    print("=" * 60)
    print("Gemini API 動画文字起こしスクリプト")
    print("=" * 60)

    transcribe_video(video_path, output_path)

    print("=" * 60)
    print("処理完了")
    print("=" * 60)


if __name__ == "__main__":
    main()
