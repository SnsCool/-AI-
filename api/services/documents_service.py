"""
ドキュメント管理サービス
- notion_docs/の読み取り
- 関連コンテンツの取得
"""

import os
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class DocumentInfo:
    id: str
    title: str
    path: str
    has_transcript: bool
    has_pdf_text: bool
    has_link_content: bool
    transcript_count: int
    pdf_text_count: int
    link_content_count: int


@dataclass
class AssociatedContent:
    type: str  # 'transcript', 'pdf_text', 'link_content'
    filename: str
    content: str
    title: Optional[str] = None


@dataclass
class DocumentDetail:
    id: str
    title: str
    path: str
    content: str
    associated_content: List[AssociatedContent]


class DocumentsService:
    def __init__(self, base_path: Optional[str] = None):
        if base_path:
            self.base_path = Path(base_path)
        else:
            # デフォルトはプロジェクトルートのnotion_docs
            self.base_path = Path(__file__).parent.parent.parent / "notion_docs"

    def list_documents(
        self,
        search: Optional[str] = None,
        filter_type: Optional[str] = None,
    ) -> dict:
        """ドキュメント一覧を取得"""
        docs = self._scan_documents(self.base_path)

        # 検索フィルター
        if search:
            search_lower = search.lower()
            docs = [
                d for d in docs
                if search_lower in d.title.lower() or search_lower in d.path.lower()
            ]

        # コンテンツタイプフィルター
        if filter_type == "transcript":
            docs = [d for d in docs if d.has_transcript]
        elif filter_type == "pdf":
            docs = [d for d in docs if d.has_pdf_text]
        elif filter_type == "link":
            docs = [d for d in docs if d.has_link_content]
        elif filter_type == "enriched":
            docs = [d for d in docs if d.has_transcript or d.has_pdf_text or d.has_link_content]

        # パスでソート
        docs.sort(key=lambda d: d.path)

        return {
            "docs": [self._doc_to_dict(d) for d in docs],
            "total": len(docs),
            "stats": {
                "with_transcripts": len([d for d in docs if d.has_transcript]),
                "with_pdf_text": len([d for d in docs if d.has_pdf_text]),
                "with_link_content": len([d for d in docs if d.has_link_content]),
            }
        }

    def get_document(self, doc_id: str) -> Optional[dict]:
        """ドキュメント詳細を取得"""
        import base64

        try:
            # Base64URLデコード
            doc_path = base64.urlsafe_b64decode(doc_id.encode()).decode("utf-8")
        except Exception:
            return None

        full_path = self.base_path / doc_path
        index_path = full_path / "index.md"

        # セキュリティチェック
        try:
            full_path.resolve().relative_to(self.base_path.resolve())
        except ValueError:
            return None

        if not index_path.exists():
            return None

        # メインコンテンツを読み込み
        content = index_path.read_text(encoding="utf-8")

        # 関連コンテンツを読み込み
        associated = []
        for file in full_path.iterdir():
            if file.name.endswith("_transcript.txt"):
                associated.append(AssociatedContent(
                    type="transcript",
                    filename=file.name,
                    content=file.read_text(encoding="utf-8"),
                    title=self._extract_title(file),
                ))
            elif file.name.endswith("_text.txt"):
                associated.append(AssociatedContent(
                    type="pdf_text",
                    filename=file.name,
                    content=file.read_text(encoding="utf-8"),
                    title=self._extract_title(file),
                ))
            elif file.name.startswith("link_") and file.name.endswith("_content.txt"):
                associated.append(AssociatedContent(
                    type="link_content",
                    filename=file.name,
                    content=file.read_text(encoding="utf-8"),
                    title=self._extract_title(file),
                ))

        # タイプ順でソート
        type_order = {"transcript": 0, "pdf_text": 1, "link_content": 2}
        associated.sort(key=lambda x: type_order.get(x.type, 99))

        return {
            "doc": {
                "id": doc_id,
                "title": full_path.name,
                "path": doc_path,
                "content": content,
                "associated_content": [
                    {
                        "type": a.type,
                        "filename": a.filename,
                        "content": a.content,
                        "title": a.title,
                    }
                    for a in associated
                ],
                "stats": {
                    "transcripts": len([a for a in associated if a.type == "transcript"]),
                    "pdf_texts": len([a for a in associated if a.type == "pdf_text"]),
                    "link_contents": len([a for a in associated if a.type == "link_content"]),
                }
            }
        }

    def _scan_documents(self, dir_path: Path, rel_path: str = "") -> List[DocumentInfo]:
        """ディレクトリを再帰的にスキャン"""
        docs = []

        if not dir_path.exists():
            return docs

        for item in dir_path.iterdir():
            if item.is_dir():
                item_rel_path = f"{rel_path}/{item.name}" if rel_path else item.name
                index_path = item / "index.md"

                if index_path.exists():
                    # 関連ファイルをカウント
                    files = list(item.iterdir())
                    transcripts = [f for f in files if f.name.endswith("_transcript.txt")]
                    pdf_texts = [f for f in files if f.name.endswith("_text.txt")]
                    link_contents = [f for f in files if f.name.startswith("link_") and f.name.endswith("_content.txt")]

                    import base64
                    doc_id = base64.urlsafe_b64encode(item_rel_path.encode()).decode()

                    docs.append(DocumentInfo(
                        id=doc_id,
                        title=item.name,
                        path=item_rel_path,
                        has_transcript=len(transcripts) > 0,
                        has_pdf_text=len(pdf_texts) > 0,
                        has_link_content=len(link_contents) > 0,
                        transcript_count=len(transcripts),
                        pdf_text_count=len(pdf_texts),
                        link_content_count=len(link_contents),
                    ))

                # 再帰的にサブディレクトリをスキャン
                docs.extend(self._scan_documents(item, item_rel_path))

        return docs

    def _doc_to_dict(self, doc: DocumentInfo) -> dict:
        return {
            "id": doc.id,
            "title": doc.title,
            "path": doc.path,
            "hasTranscript": doc.has_transcript,
            "hasPdfText": doc.has_pdf_text,
            "hasLinkContent": doc.has_link_content,
            "transcriptCount": doc.transcript_count,
            "pdfTextCount": doc.pdf_text_count,
            "linkContentCount": doc.link_content_count,
        }

    def _extract_title(self, file_path: Path) -> Optional[str]:
        """ファイルからタイトルを抽出"""
        try:
            content = file_path.read_text(encoding="utf-8")

            # Markdownヘッダーから抽出
            import re
            match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            if match:
                return match.group(1).strip()

            # **タイトル**: 形式から抽出
            match = re.search(r"\*\*(?:タイトル|動画タイトル|Title)\*\*:\s*(.+)$", content, re.MULTILINE)
            if match:
                return match.group(1).strip()

        except Exception:
            pass

        return None
