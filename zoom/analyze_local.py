#!/usr/bin/env python3
"""
ローカルファイルから商談を分析

使用方法:
    # 文字起こしファイルのみ
    python analyze_local.py --transcript transcript.txt --assignee "畑 来世人" --customer "ABC株式会社"

    # 動画ファイルのみ（自動文字起こし）
    python analyze_local.py --video meeting.mp4 --assignee "畑 来世人" --write-sheet

    # 文字起こし + 動画
    python analyze_local.py --transcript transcript.txt --video meeting.mp4 --assignee "畑 来世人"

    # テストモード
    python analyze_local.py --test --write-sheet
"""

import os
import sys
import argparse
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from services.gemini_client import (
    analyze_meeting,
    generate_embedding,
    generate_integrated_feedback,
)
from services.supabase_client import (
    get_supabase_client,
    save_knowledge,
    search_similar_knowledge,
)
from services.sheets_client import write_analysis_result


def analyze_local_files(
    transcript_path: str = None,
    transcript_text: str = None,
    video_path: str = None,
    assignee: str = "不明",
    customer_name: str = "不明",
    meeting_date: str = None,
    write_to_sheet: bool = False,
    save_to_supabase: bool = False,
):
    """
    ローカルファイルから商談を分析

    Args:
        transcript_path: 文字起こしファイルのパス
        transcript_text: 文字起こしテキスト（直接指定）
        video_path: 動画ファイルのパス（オプション）
        assignee: 担当者名
        customer_name: 顧客名
        meeting_date: 面談日（YYYY-MM-DD）
        write_to_sheet: スプレッドシートに書き込むか
        save_to_supabase: Supabaseに保存するか
    """
    print("=" * 60)
    print("ローカルファイル分析")
    print("=" * 60)

    # 日付設定
    if not meeting_date:
        meeting_date = datetime.now().strftime("%Y-%m-%d")

    transcript = None
    video_analysis = None

    # 動画から文字起こしを生成（動画のみの場合）
    if video_path and os.path.exists(video_path) and not transcript_path and not transcript_text:
        print(f"\n動画ファイル: {video_path}")
        print("→ 動画から文字起こしと分析を生成します（長時間動画対応）")

        from services.video_utils import analyze_long_video

        video_result = analyze_long_video(video_path)
        transcript = video_result["full_transcript"]
        video_analysis = video_result["overall_analysis"]

        print(f"\n文字起こし生成完了: {len(transcript)}文字")

    # 文字起こしを読み込み
    elif transcript_path:
        print(f"文字起こしファイル: {transcript_path}")
        with open(transcript_path, "r", encoding="utf-8") as f:
            transcript = f.read()
    elif transcript_text:
        transcript = transcript_text

    if not transcript:
        print("エラー: 文字起こしファイル、テキスト、または動画ファイルが必要です")
        return None

    print(f"文字数: {len(transcript)}")
    print(f"担当者: {assignee}")
    print(f"顧客名: {customer_name}")
    print(f"面談日: {meeting_date}")

    # 1. 文字起こし分析
    print("\n→ 文字起こしを分析中...")
    transcript_analysis = analyze_meeting(transcript)

    if not transcript_analysis:
        print("エラー: 分析に失敗しました")
        return None

    print(f"   クロージング結果: {transcript_analysis.get('closing_result', '不明')}")
    print(f"   話す割合: 営業{transcript_analysis.get('talk_ratio', {}).get('sales', '?')}% / 顧客{transcript_analysis.get('talk_ratio', {}).get('customer', '?')}%")

    # 2. 動画分析（文字起こしがある場合で、まだ動画分析されていない場合）
    if video_path and os.path.exists(video_path) and video_analysis is None:
        print(f"\n→ 動画を分析中: {video_path}")
        try:
            from services.video_utils import analyze_long_video
            video_result = analyze_long_video(video_path)
            video_analysis = video_result["overall_analysis"]
        except Exception as e:
            print(f"   動画分析エラー: {e}")

    # 3. 類似成功事例を検索
    print("\n→ 類似成功事例を検索中...")
    similar_successes = []
    summary = transcript_analysis.get("summary", "")

    try:
        if summary:
            embedding = generate_embedding(summary)
            if embedding:
                supabase_client = get_supabase_client()
                similar_successes = search_similar_knowledge(
                    supabase_client,
                    embedding,
                    limit=3,
                    closing_result_filter="成約"
                )
                print(f"   類似事例: {len(similar_successes)}件")
    except Exception as e:
        print(f"   類似事例検索エラー: {e}")

    # 4. 統合フィードバック生成
    print("\n→ フィードバックを生成中...")
    feedback = generate_integrated_feedback(
        transcript_analysis=transcript_analysis,
        video_analysis=video_analysis,
        similar_successes=similar_successes
    )

    # 5. スプレッドシートに書き込み
    if write_to_sheet:
        print("\n→ スプレッドシートに書き込み中...")
        spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID")
        if spreadsheet_id:
            try:
                write_analysis_result(
                    spreadsheet_id=spreadsheet_id,
                    assignee=assignee,
                    meeting_date=meeting_date,
                    customer_name=customer_name,
                    analysis=transcript_analysis,
                    feedback=feedback,
                    video_analysis=video_analysis
                )
                print("   ✅ 書き込み完了")
            except Exception as e:
                print(f"   ❌ 書き込みエラー: {e}")
        else:
            print("   ⚠️ GOOGLE_SPREADSHEET_ID が設定されていません")

    # 6. Supabaseに保存（成約の場合）
    if save_to_supabase and transcript_analysis.get("closing_result") == "成約":
        print("\n→ 成功ナレッジを保存中...")
        try:
            supabase_client = get_supabase_client()
            embedding = generate_embedding(summary) if summary else None
            talk_ratio = transcript_analysis.get("talk_ratio", {})

            save_knowledge(
                client=supabase_client,
                meeting_date=meeting_date,
                assignee=assignee,
                customer_name=customer_name,
                closing_result=transcript_analysis.get("closing_result", "不明"),
                talk_ratio_sales=talk_ratio.get("sales", 0),
                talk_ratio_customer=talk_ratio.get("customer", 0),
                issues_heard=transcript_analysis.get("issues_heard", []),
                proposal=transcript_analysis.get("proposal", []),
                good_points=transcript_analysis.get("good_points", []),
                improvement_points=transcript_analysis.get("improvement_points", []),
                success_keywords=transcript_analysis.get("success_keywords", []),
                summary=summary,
                embedding=embedding
            )
            print("   ✅ 保存完了")
        except Exception as e:
            print(f"   ❌ 保存エラー: {e}")

    # 結果表示
    print("\n" + "=" * 60)
    print("分析結果")
    print("=" * 60)

    print("\n【ヒアリングした課題】")
    for issue in transcript_analysis.get("issues_heard", []):
        print(f"  - {issue}")

    print("\n【良かった点】")
    for point in transcript_analysis.get("good_points", []):
        print(f"  - {point}")

    print("\n【改善点】")
    for point in transcript_analysis.get("improvement_points", []):
        print(f"  - {point}")

    print("\n" + "=" * 60)
    print("フィードバック")
    print("=" * 60)
    print(feedback)

    return {
        "transcript_analysis": transcript_analysis,
        "video_analysis": video_analysis,
        "feedback": feedback,
        "similar_successes": similar_successes
    }


def main():
    parser = argparse.ArgumentParser(
        description="ローカルファイルから商談を分析",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--transcript", "-t",
        help="文字起こしファイルのパス"
    )
    parser.add_argument(
        "--video", "-v",
        help="動画ファイルのパス（長時間動画も自動分割して処理）"
    )
    parser.add_argument(
        "--assignee", "-a",
        default="畑 来世人",
        help="担当者名"
    )
    parser.add_argument(
        "--customer", "-c",
        default="テスト顧客",
        help="顧客名"
    )
    parser.add_argument(
        "--date", "-d",
        help="面談日（YYYY-MM-DD）"
    )
    parser.add_argument(
        "--write-sheet",
        action="store_true",
        help="スプレッドシートに書き込む"
    )
    parser.add_argument(
        "--save-knowledge",
        action="store_true",
        help="成約の場合、Supabaseに保存"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="テストモード（サンプルデータを使用）"
    )

    args = parser.parse_args()

    if args.test:
        # テスト用サンプルデータ
        sample_transcript = """
営業: 本日はお時間いただきありがとうございます。御社の課題についてお聞かせください。

顧客: 最近、月末の請求処理に時間がかかりすぎていて困っています。
毎月3日くらいかかってしまうんです。

営業: 3日ですか、それは大変ですね。具体的にはどの作業に時間がかかっていますか?

顧客: データの集計と確認作業ですね。手作業でやっているので、ミスも心配で...

営業: なるほど、手作業での集計と確認が課題なんですね。
弊社のシステムを導入いただくと、その作業が自動化されて、
3日かかっていた作業が半日で終わるようになります。

顧客: 半日ですか!それはすごいですね。

営業: はい、実際に同業他社様でも同じような課題を解決された事例があります。
導入コストは月額5万円からになります。

顧客: それでは契約をお願いします。来月から使いたいです。

営業: ありがとうございます!では契約書を準備いたします。
        """

        analyze_local_files(
            transcript_text=sample_transcript,
            assignee=args.assignee,
            customer_name="テスト株式会社",
            write_to_sheet=args.write_sheet,
            save_to_supabase=args.save_knowledge
        )
        return

    # 動画のみの場合も対応
    if args.video and not args.transcript:
        print("動画ファイルから分析します（文字起こし自動生成）")
        analyze_local_files(
            video_path=args.video,
            assignee=args.assignee,
            customer_name=args.customer,
            meeting_date=args.date,
            write_to_sheet=args.write_sheet,
            save_to_supabase=args.save_knowledge
        )
        return

    if not args.transcript and not args.video:
        parser.print_help()
        print("\n使用例:")
        print("  python analyze_local.py --test")
        print("  python analyze_local.py --video meeting.mp4 --assignee '畑 来世人' --write-sheet")
        print("  python analyze_local.py --transcript meeting.txt --assignee '畑 来世人'")
        print("  python analyze_local.py --transcript meeting.txt --video meeting.mp4 --write-sheet")
        return

    analyze_local_files(
        transcript_path=args.transcript,
        video_path=args.video,
        assignee=args.assignee,
        customer_name=args.customer,
        meeting_date=args.date,
        write_to_sheet=args.write_sheet,
        save_to_supabase=args.save_knowledge
    )


if __name__ == "__main__":
    main()
