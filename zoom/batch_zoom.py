#!/usr/bin/env python3
"""
Zoom面談バッチ処理スクリプト（新版）

全アカウントの録画を取得し、分析してZoom相談一覧シートに出力する。

使用方法:
    python batch_zoom.py
    python batch_zoom.py --dry-run  # テスト実行（書き込みなし）
    python batch_zoom.py --limit 5  # 最大5件処理
"""

import os
import sys
import argparse
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from services.supabase_client import get_supabase_client, save_knowledge, search_similar_knowledge
from services.zoom_client import (
    get_zoom_access_token,
    get_zoom_recordings,
    download_transcript,
)
from services.gemini_client import (
    analyze_meeting,
    generate_embedding,
    generate_detailed_feedback,
)
from services.google_drive_client import create_transcript_doc
from services.sheets_client import (
    write_to_zoom_sheet,
    write_to_data_storage_sheet,
    reconcile_zoom_sheet_with_customer_sheet,
    DEFAULT_SPREADSHEET_ID,
    DEFAULT_SHEET_NAME,
    find_matching_row_by_time,
    update_row_with_analysis,
    get_all_assignee_sheets,
    get_zoom_credentials_from_sheet,
)

# 担当者別シートのスプレッドシートID（照合用）
ASSIGNEE_SPREADSHEET_ID = "1BmcpcMOoG-2fpIiMB-TNUq-qGcLsMy1P-3erqVNSV3c"

# 書き込み先スプレッドシートID（Zoom相談一覧）
DESTINATION_SPREADSHEET_ID = "1R5oMbJ7E-QfDFhHR164y8JKs6XLnkJcw8zBm2IPSn8E"
DESTINATION_SHEET_NAME = "Zoom相談一覧"


def is_recording_processed(supabase_client, recording_id: str) -> bool:
    """録画が処理済みかチェック"""
    result = supabase_client.table("processed_recordings").select("id").eq(
        "recording_id", recording_id
    ).execute()
    return len(result.data) > 0 if result.data else False


def mark_recording_processed(
    supabase_client,
    recording_id: str,
    assignee: str,
    meeting_date: str,
    customer_name: Optional[str] = None
):
    """録画を処理済みとしてマーク"""
    supabase_client.table("processed_recordings").insert({
        "recording_id": recording_id,
        "assignee": assignee,
        "meeting_date": meeting_date,
        "customer_name": customer_name
    }).execute()


def process_single_recording(
    supabase_client,
    spreadsheet_id: str,
    assignee: str,
    access_token: str,
    recording: dict,
    dry_run: bool = False
) -> bool:
    """
    単一の録画を処理

    1. 担当者シートで照合し、G列ステータスを確認
    2. ステータスに応じて処理を分岐
    3. 文字起こしをダウンロード
    4. Geminiで分析
    5. Google Docsに文字起こしを保存
    6. Google Driveに動画をアップロード
    7. Zoom相談一覧シートに書き込み
    8. ステータスに応じて処理済みマークを付与

    G列ステータスによる処理分岐:
    - 着座: 処理→処理済みマーク（完了）
    - 飛び: 処理→処理済みマーク（完了）
    - リスケ/日程調整済: 処理→処理済みマークなし（再更新対象）
    - 事前キャンセル/担当者変更/重複予約: スキップ
    - マッチなし: 処理→処理済みマークなし（再更新対象）
    """
    # スキップ対象のステータス
    SKIP_STATUSES = ["事前キャンセル", "担当者変更", "重複予約"]

    # 処理済みマークをしないステータス（再更新対象）
    NO_MARK_STATUSES = ["リスケ", "リスケ/再日程調整中", "日程調整済", "再日程調整中"]

    # 処理済みマークをするステータス（完了扱い）
    COMPLETE_STATUSES = ["着座", "飛び"]

    meeting_id = recording.get("meeting_id")
    topic = recording.get("topic", "不明")
    start_time = recording.get("start_time", "")
    duration = recording.get("duration", 0)
    transcript_url = recording.get("transcript_url")
    mp4_url = recording.get("mp4_url")
    share_url = recording.get("share_url")  # Zoom共有リンク（認証不要）

    print(f"\n{'='*60}")
    print(f"処理中: {topic}")
    print(f"  ID: {meeting_id}")
    print(f"  開始: {start_time}")
    print(f"  時間: {duration}分")
    print(f"  担当: {assignee}")
    print(f"{'='*60}")

    # 処理済みチェック
    if is_recording_processed(supabase_client, meeting_id):
        print("→ スキップ: 処理済み")
        return True

    # 文字起こしがなければスキップ
    if not transcript_url:
        print("→ スキップ: 文字起こしなし")
        return True

    try:
        # 1. まず担当者シートで照合（G列ステータス確認のため先に実行）
        print("→ 担当者シートで照合中...")
        meeting_datetime = start_time.replace("T", " ").replace("Z", "") if start_time else ""

        # Zoom録画時間をdatetimeに変換
        zoom_start_dt = None
        if start_time:
            try:
                zoom_start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            except:
                pass

        # 担当者シートで照合（顧客名とG列ステータスを取得）
        matched_row = None
        customer_name = topic  # デフォルトはZoomのtopic
        customer_status = None  # G列ステータス
        should_mark_processed = False  # 処理済みマークするかどうか

        if zoom_start_dt:
            matched_row = find_matching_row_by_time(
                spreadsheet_id=ASSIGNEE_SPREADSHEET_ID,
                assignee=assignee,
                zoom_start_time=zoom_start_dt,
                tolerance_minutes=45
            )

        # G列（事前キャンセル）とH列（初回/実施後ステータス）を格納
        cancel_status = ""  # G列
        result_status = ""  # H列

        if matched_row:
            print(f"   → マッチ発見: 行{matched_row['row_num']} ({matched_row['match_type']})")
            print(f"      顧客名: {matched_row['customer_name']}")
            print(f"      予定時間: {matched_row['scheduled_time']}")
            cancel_status = matched_row.get('status', '')
            result_status = matched_row.get('result_status', '')
            print(f"      G列(事前キャンセル): {cancel_status or '(空)'}")
            print(f"      H列(実施後ステータス): {result_status or '(空)'}")

            # 照合シートから顧客名を取得
            customer_name = matched_row['customer_name'] or topic

            # ステータスによる処理分岐
            if cancel_status in SKIP_STATUSES:
                print(f"→ スキップ: ステータスが「{cancel_status}」のため処理不要")
                return True

            if cancel_status in COMPLETE_STATUSES:
                should_mark_processed = True
                print(f"   → ステータス「{cancel_status}」: 処理後に完了マーク")
            elif cancel_status in NO_MARK_STATUSES or any(s in cancel_status for s in NO_MARK_STATUSES):
                should_mark_processed = False
                print(f"   → ステータス「{cancel_status}」: 再更新対象（処理済みマークなし）")
            else:
                # その他のステータス（空欄含む）は完了扱い
                should_mark_processed = True if cancel_status else False
                if cancel_status:
                    print(f"   → ステータス「{cancel_status}」: 処理後に完了マーク")
                else:
                    print(f"   → ステータス空欄: 再更新対象（処理済みマークなし）")
        else:
            print("   → マッチなし: Zoomのtopicを顧客名として使用")
            print("   → 顧客管理シート未登録: 再更新対象（処理済みマークなし）")
            should_mark_processed = False

        # 2. 文字起こしをダウンロード
        print("→ 文字起こしをダウンロード中...")
        transcript = download_transcript(transcript_url, access_token)

        if not transcript or len(transcript) < 100:
            print("→ スキップ: 文字起こしが短すぎます")
            return True

        print(f"   文字数: {len(transcript)}")

        # 3. Gemini分析
        print("→ Geminiで分析中...")
        analysis = analyze_meeting(transcript)

        if not analysis:
            print("→ エラー: 分析に失敗しました")
            return False

        closing_result = analysis.get("closing_result", "不明")
        print(f"   クロージング結果: {closing_result}")

        # 4. 詳細フィードバック生成（新プロンプト使用）
        print("→ 詳細フィードバック生成中...")
        feedback = generate_detailed_feedback(transcript)

        if dry_run:
            print("→ [DRY RUN] 書き込みをスキップ")
            return True

        # 5. Google Docsに文字起こしを保存
        print("→ Google Docsに保存中...")
        meeting_date = start_time[:10] if start_time else datetime.now().strftime("%Y-%m-%d")
        transcript_doc_url = create_transcript_doc(
            transcript=transcript,
            assignee=assignee,
            customer_name=topic,
            meeting_date=meeting_date
        )

        # 6. 動画リンク（Zoom共有URLを使用、ダウンロード不要）
        video_url = share_url  # Zoomの共有リンクをそのまま使用
        if video_url:
            print(f"→ 動画リンク: {video_url}")

        # 7. Zoom相談一覧シートに書き込み（更新あり版）
        print("→ Zoom相談一覧シートに書き込み中...")
        success = write_to_zoom_sheet(
            spreadsheet_id=DESTINATION_SPREADSHEET_ID,
            customer_name=customer_name,  # 照合シートから取得 or Zoomのtopic
            assignee=assignee,            # Zoomアカウント/シート名から
            meeting_datetime=meeting_datetime,  # Zoomから
            duration_minutes=duration,    # Zoomから
            cancel_status=cancel_status,  # E列: 顧客管理シートG列（着座/飛び/リスケ等）
            result_status=result_status,  # F列: 顧客管理シートH列（成約/失注/保留等）
            transcript_doc_url=transcript_doc_url,  # G列
            video_drive_url=video_url,              # H列: Zoom共有リンク
            feedback=feedback,            # I列
            sheet_name=DESTINATION_SHEET_NAME
        )

        if not success:
            return False

        # 7.5. データ格納シートに書き込み（更新なし版、履歴蓄積）
        print("→ データ格納シートに書き込み中...")
        write_to_data_storage_sheet(
            spreadsheet_id=DESTINATION_SPREADSHEET_ID,
            customer_name=customer_name,
            assignee=assignee,
            meeting_datetime=meeting_datetime,
            duration_minutes=duration,
            cancel_status=cancel_status,
            result_status=result_status,
            transcript_doc_url=transcript_doc_url,
            video_drive_url=video_url,  # Zoom共有リンク
            feedback=feedback,
            sheet_name="Zoom相談一覧 データ格納"
        )

        # 8. 成約の場合はナレッジ保存
        summary = analysis.get("summary", "")
        if closing_result == "成約" and summary:
            print("→ 成功ナレッジを保存中...")
            try:
                embedding = generate_embedding(summary)
                talk_ratio = analysis.get("talk_ratio", {})
                save_knowledge(
                    client=supabase_client,
                    meeting_date=meeting_date,
                    assignee=assignee,
                    customer_name=topic,
                    closing_result=closing_result,
                    talk_ratio_sales=talk_ratio.get("sales", 0),
                    talk_ratio_customer=talk_ratio.get("customer", 0),
                    issues_heard=analysis.get("issues_heard", []),
                    proposal=analysis.get("proposal", []),
                    good_points=analysis.get("good_points", []),
                    improvement_points=analysis.get("improvement_points", []),
                    success_keywords=analysis.get("success_keywords", []),
                    summary=summary,
                    embedding=embedding
                )
            except Exception as e:
                print(f"   ナレッジ保存エラー: {e}")

        # 9. 処理済みマーク（ステータスに応じて）
        if should_mark_processed:
            mark_recording_processed(
                supabase_client,
                recording_id=meeting_id,
                assignee=assignee,
                meeting_date=meeting_date,
                customer_name=topic
            )
            print("→ 完了! (処理済みマーク)")
        else:
            print("→ 完了! (再更新対象: 処理済みマークなし)")

        return True

    except Exception as e:
        print(f"→ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_batch_process(
    spreadsheet_id: str = None,
    dry_run: bool = False,
    limit: int = None,
    group: int = None
):
    """
    バッチ処理を実行

    Args:
        spreadsheet_id: スプレッドシートID
        dry_run: テスト実行（書き込みなし）
        limit: 処理する最大件数
        group: グループ番号（1-3）。指定時はそのグループのアカウントのみ処理
    """
    spreadsheet_id = spreadsheet_id or DEFAULT_SPREADSHEET_ID

    print("=" * 60)
    print("Zoom面談分析バッチ処理")
    print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"スプレッドシート: {spreadsheet_id}")
    print(f"シート: {DEFAULT_SHEET_NAME}")
    print(f"DRY RUN: {dry_run}")
    if limit:
        print(f"処理上限: {limit}件")
    if group:
        print(f"グループ: {group}/3")
    print("=" * 60)

    # Supabaseクライアント取得
    supabase_client = get_supabase_client()

    # 全アカウントを取得
    print("\nZoomアカウントを取得中...")
    result = supabase_client.table("zoom_accounts").select("*").execute()
    all_accounts = result.data if result.data else []

    # グループ指定時はアカウントをフィルタリング
    if group and 1 <= group <= 6:
        # アカウントを6グループに分割（1時間で全アカウント処理）
        total = len(all_accounts)
        group_size = (total + 5) // 6  # 切り上げ
        start_idx = (group - 1) * group_size
        end_idx = min(group * group_size, total)
        accounts = all_accounts[start_idx:end_idx]
        print(f"全アカウント数: {total}")
        print(f"グループ{group}/6のアカウント: {start_idx+1}〜{end_idx}番目 ({len(accounts)}件)")
    else:
        accounts = all_accounts
        print(f"アカウント数: {len(accounts)}")

    total_processed = 0
    total_success = 0
    total_failed = 0
    total_skipped = 0

    # 認証エラーの担当者を記録
    auth_errors = []

    for account in accounts:
        assignee = account["assignee"]

        print(f"\n{'#'*60}")
        print(f"担当者: {assignee}")
        print(f"{'#'*60}")

        try:
            # アクセストークン取得（Supabaseの認証情報を使用）
            access_token = None
            used_source = "supabase"

            try:
                access_token = get_zoom_access_token(
                    account["account_id"],
                    account["client_id"],
                    account["client_secret"]
                )
                print(f"認証成功: Supabase")
            except Exception as supabase_error:
                print(f"Supabase認証エラー: {supabase_error}")

                # フォールバック: スプレッドシートから認証情報を取得
                print(f"→ フォールバック: スプレッドシートから認証情報を取得中...")
                sheet_creds = get_zoom_credentials_from_sheet(
                    spreadsheet_id=DESTINATION_SPREADSHEET_ID,
                    assignee=assignee,
                    sheet_name="ZoomKeys"
                )

                if sheet_creds:
                    print(f"   スプレッドシートに認証情報あり")
                    try:
                        access_token = get_zoom_access_token(
                            sheet_creds["account_id"],
                            sheet_creds["client_id"],
                            sheet_creds["client_secret"]
                        )
                        used_source = "spreadsheet"
                        print(f"認証成功: スプレッドシート")
                    except Exception as sheet_error:
                        print(f"スプレッドシート認証エラー: {sheet_error}")
                        # 両方失敗
                        auth_errors.append({
                            "assignee": assignee,
                            "supabase_error": str(supabase_error),
                            "sheet_error": str(sheet_error),
                            "status": "両方失敗（Zoomアプリ再設定が必要）"
                        })
                        print(f"★★★ {assignee}: Supabase・スプレッドシート両方失敗")
                        print(f"    → Zoomアプリの認証情報を確認・再設定してください")
                        total_skipped += 1
                        continue
                else:
                    print(f"   スプレッドシートに認証情報なし")
                    auth_errors.append({
                        "assignee": assignee,
                        "supabase_error": str(supabase_error),
                        "sheet_error": "認証情報なし",
                        "status": "Supabase失敗＋スプレッドシートに情報なし"
                    })
                    print(f"★★★ {assignee}: Supabase失敗、スプレッドシートに情報なし")
                    total_skipped += 1
                    continue

            # 録画一覧取得（最新5件に制限）
            all_recordings = get_zoom_recordings(access_token)
            recordings = all_recordings[:5]  # 最新5件のみ処理
            print(f"録画数: {len(recordings)}/{len(all_recordings)}件 (認証元: {used_source})")

            for recording in recordings:
                if limit and total_processed >= limit:
                    print(f"\n処理上限 {limit}件 に達しました")
                    break

                total_processed += 1
                success = process_single_recording(
                    supabase_client=supabase_client,
                    spreadsheet_id=spreadsheet_id,
                    assignee=assignee,
                    access_token=access_token,
                    recording=recording,
                    dry_run=dry_run
                )

                if success:
                    total_success += 1
                else:
                    total_failed += 1

            if limit and total_processed >= limit:
                break

        except Exception as e:
            print(f"エラー: {e}")
            total_skipped += 1
            continue

    # 再照合処理: E列・F列が空の行を顧客管理シートと照合して更新
    if not dry_run:
        print("\n" + "=" * 60)
        print("再照合処理: Zoom相談一覧の未照合行を更新")
        print("=" * 60)
        updated_count = reconcile_zoom_sheet_with_customer_sheet(
            zoom_spreadsheet_id=DESTINATION_SPREADSHEET_ID,
            customer_spreadsheet_id=ASSIGNEE_SPREADSHEET_ID,
            zoom_sheet_name=DESTINATION_SHEET_NAME
        )
        print(f"再照合で更新した行数: {updated_count}")

    # サマリー
    print("\n" + "=" * 60)
    print("バッチ処理完了")
    print("=" * 60)
    print(f"処理件数: {total_processed}")
    print(f"成功: {total_success}")
    print(f"失敗: {total_failed}")
    print(f"スキップ: {total_skipped}")
    print(f"終了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nスプレッドシート: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")

    # 認証エラーの詳細レポート
    if auth_errors:
        print("\n" + "=" * 60)
        print("★ 認証エラーレポート")
        print("=" * 60)
        print(f"認証エラー件数: {len(auth_errors)}名")
        print()

        # 分類して表示
        both_failed = [e for e in auth_errors if "両方失敗" in e["status"]]
        supabase_only = [e for e in auth_errors if "情報なし" in e["status"]]

        if both_failed:
            print("【Supabase・スプレッドシート両方失敗（Zoomアプリ再設定必要）】")
            for e in both_failed:
                print(f"  - {e['assignee']}")
            print()

        if supabase_only:
            print("【Supabase失敗・スプレッドシートに情報なし】")
            for e in supabase_only:
                print(f"  - {e['assignee']}")
            print()

        print("対応方法:")
        print("  1. Zoom Marketplace (https://marketplace.zoom.us/) にログイン")
        print("  2. Server-to-Server OAuthアプリの認証情報を確認")
        print("  3. Account ID, Client ID, Client Secret を取得")
        print("  4. Supabase zoom_accounts テーブル または")
        print(f"     スプレッドシート「Zoomキー」シートを更新")
        print(f"     ({DESTINATION_SPREADSHEET_ID})")

    return total_failed == 0


def main():
    parser = argparse.ArgumentParser(
        description="Zoom面談分析バッチ処理",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--spreadsheet-id",
        default=os.getenv("GOOGLE_SPREADSHEET_ID") or DEFAULT_SPREADSHEET_ID,
        help="出力先スプレッドシートID"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="テスト実行（書き込みなし）"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="処理する最大件数"
    )
    parser.add_argument(
        "--group",
        type=int,
        choices=[1, 2, 3, 4, 5, 6],
        help="処理するグループ番号（1-6）。指定時はそのグループのアカウントのみ処理"
    )

    args = parser.parse_args()

    success = run_batch_process(
        spreadsheet_id=args.spreadsheet_id,
        dry_run=args.dry_run,
        limit=args.limit,
        group=args.group
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
