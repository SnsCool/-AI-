"""
Google Driveサービス - Drive API連携 + PDF/画像解析
"""

import os
import io
import base64
import json
import tempfile
from typing import Optional

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    DRIVE_AVAILABLE = True
except ImportError:
    DRIVE_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class DriveService:
    """Google Drive API サービス + PDF/画像解析"""

    SCOPES = [
        'https://www.googleapis.com/auth/drive.readonly',
        'https://www.googleapis.com/auth/drive.metadata.readonly'
    ]

    # 解析対象のMIMEタイプ
    ANALYZABLE_TYPES = {
        'application/pdf': 'pdf',
        'image/jpeg': 'image',
        'image/png': 'image',
        'image/gif': 'image',
        'image/webp': 'image',
    }

    def __init__(self):
        self.service = None
        self.gemini_model = None

        if DRIVE_AVAILABLE:
            self._initialize_service()

        if GEMINI_AVAILABLE:
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                self.gemini_model = genai.GenerativeModel("gemini-2.0-flash")

    def _initialize_service(self):
        """サービスアカウントで認証"""
        # 環境変数からJSON文字列を取得（GitHub Actions用）
        credentials_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
        credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH")

        try:
            if credentials_json:
                # JSON文字列から認証
                creds_dict = json.loads(credentials_json)
                credentials = service_account.Credentials.from_service_account_info(
                    creds_dict,
                    scopes=self.SCOPES
                )
                self.service = build('drive', 'v3', credentials=credentials)
            elif credentials_path and os.path.exists(credentials_path):
                # ファイルパスから認証
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
            print("Drive service not initialized")
            return []

        try:
            all_files = {}

            # 1. ファイル名で検索（PDFなどはこれで見つかる）
            name_query_parts = [f"name contains '{query}'", "trashed=false"]
            if mime_types:
                mime_conditions = " or ".join(f"mimeType='{mt}'" for mt in mime_types)
                name_query_parts.append(f"({mime_conditions})")

            name_response = self.service.files().list(
                q=" and ".join(name_query_parts),
                pageSize=limit,
                fields="files(id, name, mimeType, webViewLink, createdTime, modifiedTime)"
            ).execute()

            for file in name_response.get("files", []):
                all_files[file.get("id")] = file

            # 2. 全文検索（Google Docs, テキストファイルなど）
            fulltext_query_parts = [f"fullText contains '{query}'", "trashed=false"]
            if mime_types:
                fulltext_query_parts.append(f"({mime_conditions})")

            try:
                fulltext_response = self.service.files().list(
                    q=" and ".join(fulltext_query_parts),
                    pageSize=limit,
                    fields="files(id, name, mimeType, webViewLink, createdTime, modifiedTime)"
                ).execute()

                for file in fulltext_response.get("files", []):
                    all_files[file.get("id")] = file
            except Exception:
                pass  # 全文検索に失敗しても名前検索の結果は返す

            files = []
            for file in list(all_files.values())[:limit]:
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

    async def get_file_content(self, file_id: str, mime_type: str = None) -> str:
        """ファイルのコンテンツを取得（PDF/画像はGeminiで解析）"""
        if not self.service:
            return ""

        try:
            # MIMEタイプを取得
            if not mime_type:
                file = self.service.files().get(
                    fileId=file_id,
                    fields="mimeType"
                ).execute()
                mime_type = file.get("mimeType", "")

            # Google Docs
            if "google-apps.document" in mime_type:
                content = self.service.files().export(
                    fileId=file_id,
                    mimeType="text/plain"
                ).execute()
                return content.decode('utf-8') if isinstance(content, bytes) else content

            # Google Sheets
            elif "google-apps.spreadsheet" in mime_type:
                content = self.service.files().export(
                    fileId=file_id,
                    mimeType="text/csv"
                ).execute()
                return content.decode('utf-8') if isinstance(content, bytes) else content

            # PDF/画像 → Geminiで解析
            elif mime_type in self.ANALYZABLE_TYPES:
                return await self._analyze_file_with_gemini(file_id, mime_type)

            return ""

        except Exception as e:
            print(f"ファイルコンテンツ取得エラー: {e}")
            return ""

    async def _analyze_file_with_gemini(self, file_id: str, mime_type: str) -> str:
        """PDF/画像をGeminiで解析"""
        if not self.gemini_model:
            print("Gemini model not available for file analysis")
            return ""

        try:
            # ファイルをダウンロード
            request = self.service.files().get_media(fileId=file_id)
            file_data = io.BytesIO()
            downloader = MediaIoBaseDownload(file_data, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()

            file_data.seek(0)
            file_bytes = file_data.read()

            # Geminiで解析
            file_type = self.ANALYZABLE_TYPES.get(mime_type, 'document')

            if file_type == 'pdf':
                prompt = "このPDFの内容を詳しく要約してください。重要な情報、数値、キーポイントを抽出してください。"
            else:
                prompt = "この画像の内容を詳しく説明してください。テキストがあれば読み取ってください。"

            # Geminiにファイルを送信
            response = self.gemini_model.generate_content([
                prompt,
                {"mime_type": mime_type, "data": base64.b64encode(file_bytes).decode('utf-8')}
            ])

            return f"[{file_type.upper()}解析結果]\n{response.text}"

        except Exception as e:
            print(f"Gemini解析エラー: {e}")
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
