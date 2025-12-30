#!/usr/bin/env python3
"""
音声文字起こしスクリプト

AssemblyAI APIを使用して音声/動画ファイルを
テキストに変換する（話者分離付き）
"""

import argparse
import os
import sys
import time

import assemblyai as aai


def transcribe_audio(audio_url: str, speaker_labels: bool = True) -> str:
    """音声ファイルを文字起こしする"""

    api_key = os.getenv("ASSEMBLYAI_API_KEY")
    if not api_key:
        raise ValueError("ASSEMBLYAI_API_KEY が設定されていません")

    aai.settings.api_key = api_key

    # 設定
    config = aai.TranscriptionConfig(
        language_code="ja",  # 日本語
        speaker_labels=speaker_labels,  # 話者分離
        punctuate=True,  # 句読点追加
        format_text=True,  # テキスト整形
    )

    print(f"[INFO] 文字起こし開始: {audio_url}", file=sys.stderr)

    # 文字起こし実行
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio_url, config=config)

    # 完了待ち
    while transcript.status not in [aai.TranscriptStatus.completed, aai.TranscriptStatus.error]:
        print(f"[INFO] 処理中... ステータス: {transcript.status}", file=sys.stderr)
        time.sleep(5)
        transcript = transcriber.get_transcript(transcript.id)

    if transcript.status == aai.TranscriptStatus.error:
        raise Exception(f"文字起こしエラー: {transcript.error}")

    # 話者分離がある場合はフォーマット
    if speaker_labels and transcript.utterances:
        result = format_with_speakers(transcript.utterances)
    else:
        result = transcript.text

    print(f"[INFO] 文字起こし完了（{len(result)}文字）", file=sys.stderr)
    return result


def format_with_speakers(utterances: list) -> str:
    """話者ごとにフォーマットする"""
    lines = []
    for utterance in utterances:
        speaker = f"話者{utterance.speaker}"
        text = utterance.text
        lines.append(f"【{speaker}】{text}")
    return "\n\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="音声文字起こし")
    parser.add_argument("--audio-url", required=True, help="音声/動画ファイルのURL")
    parser.add_argument("--output", default="transcript.txt", help="出力ファイル")
    parser.add_argument("--no-speaker-labels", action="store_true", help="話者分離を無効化")

    args = parser.parse_args()

    # 文字起こし実行
    result = transcribe_audio(
        audio_url=args.audio_url,
        speaker_labels=not args.no_speaker_labels
    )

    # 結果を保存
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(result)

    print(f"[INFO] 保存完了: {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
