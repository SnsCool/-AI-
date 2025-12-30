#!/usr/bin/env python3
"""
Google Drive保存スクリプト

フィードバックレポートをGoogle Driveにアップロードする
"""

import argparse
import json
import os
import sys
from datetime import datetime

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


def get_drive_service():
    """Google Drive APIサービスを取得"""
    sa_key_json = os.getenv("GCP_SA_KEY_JSON")
    if not sa_key_json:
        raise ValueError("GCP_SA_KEY_JSON が設定されていません")

    credentials = service_account.Credentials.from_service_account_info(
        json.loads(sa_key_json),
        scopes=["https://www.googleapis.com/auth/drive.file"]
    )

    return build("drive", "v3", credentials=credentials)


def generate_report_markdown(feedback: dict) -> str:
    """フィードバックをMarkdown形式に変換"""
    meta = feedback.get("metadata", {})

    md = f"""# 商談フィードバックレポート

## 基本情報

| 項目 | 値 |
|------|-----|
| 日時 | {meta.get('analyzed_at', 'N/A')} |
| 担当者 | {meta.get('sales_rep', 'N/A')} |
| 顧客 | {meta.get('customer', 'N/A')} |
| 業種 | {meta.get('industry', 'N/A')} |
| 商材 | {meta.get('product', 'N/A')} |
| クロージング | {'成功' if meta.get('is_closed') else '未成約'} |

---

## 総合スコア: {feedback.get('overall_score', 'N/A')} / 5.0

---

## 各項目評価

| 項目 | スコア | 評価理由 |
|------|--------|----------|
"""

    scores = feedback.get("scores", {})
    score_names = {
        "hearing": "ヒアリング力",
        "proposal": "提案力",
        "objection_handling": "異議対応",
        "closing": "クロージング",
        "rapport": "ラポール構築",
        "bant": "BANT確認"
    }

    for key, name in score_names.items():
        score_data = scores.get(key, {})
        score = score_data.get("score", "N/A")
        reason = score_data.get("reason", "N/A")
        md += f"| {name} | {score}/5 | {reason} |\n"

    md += """
---

## 良かった点

"""
    for point in feedback.get("good_points", []):
        md += f"- {point}\n"

    md += """
---

## 改善点

"""
    for point in feedback.get("improvements", []):
        md += f"- {point}\n"

    md += """
---

## 効果的だったフレーズ

"""
    for phrase in feedback.get("key_phrases", []):
        md += f"> {phrase}\n\n"

    md += """
---

## 次回へのアドバイス

"""
    for i, advice in enumerate(feedback.get("advice", []), 1):
        md += f"{i}. {advice}\n"

    if feedback.get("success_factors"):
        md += f"""
---

## 成功/失敗要因分析

{feedback.get('success_factors')}
"""

    return md


def upload_to_drive(feedback: dict, folder_id: str) -> str:
    """Google Driveにアップロード"""
    service = get_drive_service()

    meta = feedback.get("metadata", {})
    date_str = datetime.now().strftime("%Y-%m-%d")
    customer = meta.get("customer", "unknown")
    filename = f"{date_str}_{customer}_フィードバック.md"

    # Markdownレポート生成
    report_md = generate_report_markdown(feedback)

    # 一時ファイルに書き込み
    temp_path = "/tmp/report.md"
    with open(temp_path, 'w', encoding='utf-8') as f:
        f.write(report_md)

    # アップロード
    file_metadata = {
        "name": filename,
        "parents": [folder_id]
    }
    media = MediaFileUpload(temp_path, mimetype="text/markdown")

    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, webViewLink"
    ).execute()

    print(f"[INFO] アップロード完了: {file.get('webViewLink')}", file=sys.stderr)
    return file.get("webViewLink")


def main():
    parser = argparse.ArgumentParser(description="Google Drive保存")
    parser.add_argument("--feedback-file", required=True, help="フィードバックJSONファイル")
    parser.add_argument("--folder-id", required=True, help="保存先フォルダID")

    args = parser.parse_args()

    # フィードバック読み込み
    with open(args.feedback_file, 'r', encoding='utf-8') as f:
        feedback = json.load(f)

    # アップロード
    url = upload_to_drive(feedback, args.folder_id)
    print(url)


if __name__ == "__main__":
    main()
