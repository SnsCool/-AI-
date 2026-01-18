"""
ドキュメント管理 API
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List

from services.documents_service import DocumentsService

router = APIRouter()
service = DocumentsService()


class DocumentListItem(BaseModel):
    id: str
    title: str
    path: str
    hasTranscript: bool
    hasPdfText: bool
    hasLinkContent: bool
    transcriptCount: int
    pdfTextCount: int
    linkContentCount: int


class DocumentStats(BaseModel):
    with_transcripts: int
    with_pdf_text: int
    with_link_content: int


class DocumentListResponse(BaseModel):
    docs: List[DocumentListItem]
    total: int
    stats: DocumentStats


class AssociatedContentItem(BaseModel):
    type: str
    filename: str
    content: str
    title: Optional[str] = None


class DocumentDetailStats(BaseModel):
    transcripts: int
    pdf_texts: int
    link_contents: int


class DocumentDetail(BaseModel):
    id: str
    title: str
    path: str
    content: str
    associated_content: List[AssociatedContentItem]
    stats: DocumentDetailStats


class DocumentDetailResponse(BaseModel):
    doc: DocumentDetail


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    search: Optional[str] = Query(None, description="検索キーワード"),
    filter: Optional[str] = Query(
        None,
        description="フィルター (transcript, pdf, link, enriched)",
    ),
):
    """
    ドキュメント一覧を取得

    - **search**: タイトルまたはパスで検索
    - **filter**: コンテンツタイプでフィルター
      - `transcript`: 文字起こしがあるドキュメント
      - `pdf`: PDFテキストがあるドキュメント
      - `link`: リンクコンテンツがあるドキュメント
      - `enriched`: 追加コンテンツがあるドキュメント
    """
    result = service.list_documents(search=search, filter_type=filter)
    return result


@router.get("/{doc_id}", response_model=DocumentDetailResponse)
async def get_document(doc_id: str):
    """
    ドキュメント詳細を取得

    - **doc_id**: ドキュメントID (Base64URLエンコードされたパス)
    """
    result = service.get_document(doc_id)

    if not result:
        raise HTTPException(status_code=404, detail="ドキュメントが見つかりません")

    return result
