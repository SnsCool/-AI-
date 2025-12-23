"""
Google Driveサービス - Drive API連携
"""

import os
from typing import Optional

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    DRIVE_AVAILABLE = True
except ImportError:
    DRIVE_AVAILABLE = False


class DriveService:
    """Google Drive API サービス"""

    SCOPES = [
        'https://www.googleapis.com/auth/drive.readonly',
        'https://www.googleapis.com/auth/drive.metadata.readonly'
    ]

    def __init__(self):
        self.service = None
        if DRIVE_AVAILABLE:
            self._initialize_service()

    def _initialize_service(self):
        """サービスアカウントで認証"""
        credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH")
        if not credentials_path or not os.path.exists(credentials_path):
            return

        try:
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=self.SCOPES
            )
            self.service = build('drive', 'v3', credentials=credentials)
        except Exception as e:
            print(f"Drive認証エラー: {e}")

    async def search_files(
        self,
        query: str,
        limit: int = 10,
        mime_types: list[str] = None
    ) -> list[dict]:
        """ファイルを検索"""
        if not self.service:
            return []

        try:
            # 検索クエリ構築
            q_parts = [f"fullText contains '{query}'"]

            if mime_types:
                mime_conditions = " or ".join(
                    f"mimeType='{mt}'" for mt in mime_types
                )
                q_parts.append(f"({mime_conditions})")

            q_parts.append("trashed=false")
            search_query = " and ".join(q_parts)

            response = self.service.files().list(
                q=search_query,
                pageSize=limit,
                fields="files(id, name, mimeType, webViewLink, createdTime, modifiedTime)"
            ).execute()

            files = []
            for file in response.get("files", []):
                files.append({
                    "id": file.get("id"),
                    "source_type": "drive",
                    "title": file.get("name"),
                    "url": file.get("webViewLink", ""),
                    "mime_type": file.get("mimeType"),
                    "created_at": file.get("createdTime", "")[:10] if file.get("createdTime") else None,
                    "modified_at": file.get("modifiedTime", "")[:10] if file.get("modifiedTime") else None
                })

            return files

        except Exception as e:
            print(f"Drive検索エラー: {e}")
            return []

    async def get_file_content(self, file_id: str) -> str:
        """ファイルのコンテンツを取得"""
        if not self.service:
            return ""

        try:
            # Google Docsの場合はテキストとしてエクスポート
            file = self.service.files().get(
                fileId=file_id,
                fields="mimeType"
            ).execute()

            mime_type = file.get("mimeType", "")

            if "google-apps.document" in mime_type:
                # Google Docs
                content = self.service.files().export(
                    fileId=file_id,
                    mimeType="text/plain"
                ).execute()
                return content.decode('utf-8') if isinstance(content, bytes) else content

            elif "google-apps.spreadsheet" in mime_type:
                # Google Sheets（最初のシートをCSVでエクスポート）
                content = self.service.files().export(
                    fileId=file_id,
                    mimeType="text/csv"
                ).execute()
                return content.decode('utf-8') if isinstance(content, bytes) else content

            # その他のファイルはメタデータのみ
            return ""

        except Exception as e:
            print(f"ファイルコンテンツ取得エラー: {e}")
            return ""

    async def list_folder(
        self,
        folder_id: str = "root",
        limit: int = 100
    ) -> list[dict]:
        """フォルダ内のファイル一覧を取得"""
        if not self.service:
            return []

        try:
            response = self.service.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                pageSize=limit,
                fields="files(id, name, mimeType, webViewLink, createdTime)"
            ).execute()

            return [
                {
                    "id": f.get("id"),
                    "source_type": "drive",
                    "title": f.get("name"),
                    "url": f.get("webViewLink", ""),
                    "mime_type": f.get("mimeType"),
                    "created_at": f.get("createdTime", "")[:10] if f.get("createdTime") else None
                }
                for f in response.get("files", [])
            ]

        except Exception as e:
            print(f"フォルダ一覧取得エラー: {e}")
            return []
