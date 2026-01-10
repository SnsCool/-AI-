#!/usr/bin/env python3
"""
新しいスプレッドシートへの書き込みテスト
"""

import os
from dotenv import load_dotenv

load_dotenv()

from services.sheets_client import get_sheets_client, write_meeting_data
from services.google_drive_client import create_transcript_doc

# テスト設定
SPREADSHEET_ID = os.getenv("GOOGLE_SPREADSHEET_ID")

def test_sheet_access():
    """シートへのアクセステスト"""
    print("=" * 60)
    print("1. シートアクセステスト")
    print("=" * 60)

    try:
        client = get_sheets_client()
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        print(f"✅ スプレッドシート名: {spreadsheet.title}")

        # シート一覧を表示
        worksheets = spreadsheet.worksheets()
        print(f"   シート数: {len(worksheets)}")
        for ws in worksheets:
            print(f"   - {ws.title}")

        # 最初のシートの内容を確認
        sheet1 = spreadsheet.sheet1
        all_values = sheet1.get_all_values()
        print(f"\n   行数: {len(all_values)}")
        if all_values:
            print(f"   ヘッダー: {all_values[0][:8]}")

        return True
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False


def test_create_doc():
    """Google Docs作成テスト"""
    print("\n" + "=" * 60)
    print("2. Google Docs作成テスト")
    print("=" * 60)

    try:
        test_transcript = """営業: 本日はお時間いただきありがとうございます。
顧客: こちらこそよろしくお願いします。
営業: 御社の課題についてお聞かせいただけますか？
顧客: 請求処理に時間がかかっていて困っています。
"""

        doc_url = create_transcript_doc(
            transcript=test_transcript,
            assignee="テスト担当者",
            customer_name="テスト顧客",
            meeting_date="2025-01-05"
        )

        print(f"✅ Doc作成成功: {doc_url}")
        return True, doc_url
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_write_to_sheet(doc_url: str):
    """シート書き込みテスト"""
    print("\n" + "=" * 60)
    print("3. シート書き込みテスト")
    print("=" * 60)

    try:
        # 既存の顧客がいなければ新規行追加
        success = write_meeting_data(
            spreadsheet_id=SPREADSHEET_ID,
            sheet_name="シート1",
            customer_name="テスト顧客",
            assignee="テスト担当者",
            meeting_datetime="2025-01-05 10:00",
            duration_minutes=30,
            transcript_doc_url=doc_url,
            video_drive_url=None,
            feedback="【良い点】\n- ヒアリングが丁寧\n- 課題を明確に引き出せた\n\n【改善点】\n- クロージングをもう少し強く"
        )

        if success:
            print("✅ 書き込み成功")
        else:
            print("❌ 書き込み失敗")

        return success
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("新しいスプレッドシート書き込みテスト")
    print(f"スプレッドシートID: {SPREADSHEET_ID}")
    print()

    # 1. シートアクセステスト
    if not test_sheet_access():
        print("\n⚠️ シートへのアクセスに失敗しました")
        print("   スプレッドシートをサービスアカウントと共有してください:")
        print("   gen-lang-client-0193738574@appspot.gserviceaccount.com")
        return

    # 2. Google Docs作成テスト
    success, doc_url = test_create_doc()
    if not success:
        print("\n⚠️ Google Docs作成に失敗しました")
        return

    # 3. シート書き込みテスト
    test_write_to_sheet(doc_url)

    print("\n" + "=" * 60)
    print("テスト完了")
    print("=" * 60)
    print(f"\nスプレッドシート: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")


if __name__ == "__main__":
    main()
