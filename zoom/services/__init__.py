"""
Zoom Meeting Analysis Services
"""

from .supabase_client import (
    get_supabase_client,
    save_knowledge,
    search_similar_knowledge,
    get_knowledge_by_assignee,
)
from .gemini_client import (
    analyze_meeting,
    analyze_video,
    generate_embedding,
    generate_feedback,
    generate_integrated_feedback,
)
from .zoom_client import (
    get_zoom_access_token,
    get_zoom_recordings,
    download_file,
    download_transcript,
    get_all_accounts_recordings,
)
from .sheets_client import (
    get_sheets_client,
    get_or_create_sheet,
    write_analysis_result,
    get_spreadsheet_url,
)

__all__ = [
    # Supabase
    "get_supabase_client",
    "save_knowledge",
    "search_similar_knowledge",
    "get_knowledge_by_assignee",
    # Gemini
    "analyze_meeting",
    "analyze_video",
    "generate_embedding",
    "generate_feedback",
    "generate_integrated_feedback",
    # Zoom
    "get_zoom_access_token",
    "get_zoom_recordings",
    "download_file",
    "download_transcript",
    "get_all_accounts_recordings",
    # Google Sheets
    "get_sheets_client",
    "get_or_create_sheet",
    "write_analysis_result",
    "get_spreadsheet_url",
]
