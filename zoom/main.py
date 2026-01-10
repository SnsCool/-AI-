#!/usr/bin/env python3
"""
Zoom面談分析システム メインエントリーポイント

使用方法:
    # 文字起こしファイルを分析
    python main.py --file transcript.txt --assignee "田中太郎" --date "2025-01-15"

    # テストモード
    python main.py --test

    # ヘルプ
    python main.py --help
"""

import argparse
import sys
import os
from datetime import datetime

# .envを読み込み
from dotenv import load_dotenv
load_dotenv()

from agents.meeting_analysis import MeetingAnalysisAgent


def run_test():
    """テストモード: サンプルデータで動作確認"""
    print("=" * 60)
    print("テストモード実行中...")
    print("=" * 60)

    # サンプル文字起こし
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

顧客: 検討したいと思います。来週もう一度詳しい資料を持ってきてもらえますか?

営業: もちろんです!来週の火曜日、同じ時間でいかがでしょうか?

顧客: それでお願いします。

営業: ありがとうございます。来週火曜日にまたお伺いします。
    """

    agent = MeetingAnalysisAgent()

    result = agent.analyze_transcript(
        transcript=sample_transcript,
        meeting_date="2025-01-15",
        assignee="テスト担当者",
        customer_name="テスト顧客株式会社"
    )

    print("\n" + "=" * 60)
    print("分析結果")
    print("=" * 60)

    if result["success"]:
        analysis = result["analysis"]
        print(f"\n【クロージング結果】{analysis.get('closing_result', '不明')}")
        print(f"\n【話す割合】営業: {analysis.get('talk_ratio', {}).get('sales', '?')}% / 顧客: {analysis.get('talk_ratio', {}).get('customer', '?')}%")

        print("\n【ヒアリングした課題】")
        for issue in analysis.get("issues_heard", []):
            print(f"  - {issue}")

        print("\n【良かった点】")
        for point in analysis.get("good_points", []):
            print(f"  - {point}")

        print("\n【改善点】")
        for point in analysis.get("improvement_points", []):
            print(f"  - {point}")

        print("\n" + "=" * 60)
        print("フィードバック")
        print("=" * 60)
        print(result["feedback"])
    else:
        print(f"エラー: {result['error']}")

    return result["success"]


def analyze_file(file_path: str, assignee: str, meeting_date: str, customer_name: str = None):
    """ファイルから文字起こしを読み込んで分析"""
    print("=" * 60)
    print(f"ファイル分析: {file_path}")
    print("=" * 60)

    # ファイル読み込み
    if not os.path.exists(file_path):
        print(f"エラー: ファイルが見つかりません: {file_path}")
        return False

    with open(file_path, "r", encoding="utf-8") as f:
        transcript = f.read()

    print(f"文字数: {len(transcript)}")
    print(f"担当者: {assignee}")
    print(f"面談日: {meeting_date}")
    print(f"顧客名: {customer_name or '不明'}")

    agent = MeetingAnalysisAgent()

    result = agent.analyze_transcript(
        transcript=transcript,
        meeting_date=meeting_date,
        assignee=assignee,
        customer_name=customer_name
    )

    if result["success"]:
        analysis = result["analysis"]
        print(f"\n【クロージング結果】{analysis.get('closing_result', '不明')}")

        print("\n" + "=" * 60)
        print("フィードバック")
        print("=" * 60)
        print(result["feedback"])
    else:
        print(f"エラー: {result['error']}")

    return result["success"]


def main():
    parser = argparse.ArgumentParser(
        description="Zoom面談分析システム",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python main.py --test
  python main.py --file transcript.txt --assignee "田中太郎" --date "2025-01-15"
  python main.py --file transcript.txt --assignee "田中太郎" --date "2025-01-15" --customer "ABC株式会社"
        """
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="テストモードを実行"
    )
    parser.add_argument(
        "--file", "-f",
        help="分析する文字起こしファイルのパス"
    )
    parser.add_argument(
        "--assignee", "-a",
        help="担当者名"
    )
    parser.add_argument(
        "--date", "-d",
        help="面談日 (YYYY-MM-DD形式)"
    )
    parser.add_argument(
        "--customer", "-c",
        help="顧客名（オプション）"
    )

    args = parser.parse_args()

    if args.test:
        success = run_test()
        sys.exit(0 if success else 1)

    if args.file:
        if not args.assignee:
            print("エラー: --assignee オプションが必要です")
            sys.exit(1)
        if not args.date:
            print("エラー: --date オプションが必要です")
            sys.exit(1)

        success = analyze_file(
            file_path=args.file,
            assignee=args.assignee,
            meeting_date=args.date,
            customer_name=args.customer
        )
        sys.exit(0 if success else 1)

    parser.print_help()


if __name__ == "__main__":
    main()
