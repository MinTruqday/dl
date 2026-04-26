from api.dependencies import get_current_user_optional, get_current_user, require_role
from fastapi import APIRouter, Depends, Response, Query
from models.user import UserInDB, RoleEnum
from services.document import DocumentService
from models.document import DocumentCreate, DocumentResponse, DocumentContentUpdate
from typing import List, Any, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/documents")

@router.get("/tags-and-categories")
async def get_tags_categories():
    return await DocumentService.get_tags_categories()

@router.get("/trending")
async def get_trending_documents(limit: int = 5):
    return await DocumentService.get_trending_documents(limit)

@router.post("/", response_model=DocumentResponse)
async def create_document(
    doc_in: DocumentCreate,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
) -> Any:
    return await DocumentService.create_document(doc_in, current_user)

@router.put("/{document_id}/content", response_model=DocumentResponse)
async def update_document_content(
    document_id: str,
    content_in: DocumentContentUpdate,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
) -> Any:
    return await DocumentService.update_document_content(document_id, content_in, current_user)

@router.post("/{document_id}/publish", response_model=DocumentResponse)
async def publish_document(
    document_id: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
) -> Any:
    return await DocumentService.publish_document(document_id, current_user)

@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    limit: int = 10, 
    offset: int = 0,
    q: Optional[str] = None,
    sort_by: str = "latest",
    category: Optional[str] = None,
    tag: Optional[str] = None
) -> Any:
    return await DocumentService.list_documents(limit, offset, q, sort_by, category, tag)

@router.get("/semantic-search")
async def semantic_search(query: str, limit: int = 10):
    return await DocumentService.get_semantic_search(query, limit)

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document_by_id(
    document_id: str,
    password: Optional[str] = Query(None),
    current_user: UserInDB = Depends(get_current_user_optional)
) -> Any:
    return await DocumentService.get_document_by_id(document_id, current_user, password)


@router.post("/{document_id}/compile")
async def request_compilation(
    document_id: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
) -> Any:
    return await DocumentService.request_compilation(document_id, current_user)

@router.get("/slug/{slug}", response_model=DocumentResponse)
async def get_document_by_slug(slug: str) -> Any:
    return await DocumentService.get_document_by_slug(slug)

@router.put("/{document_id}/cover", response_model=DocumentResponse)
async def update_cover(
    document_id: str,
    cover_url: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
) -> Any:
    return await DocumentService.update_cover(document_id, cover_url, current_user)

class ChapterCreate(BaseModel):
    title: str
    content: str
    is_premium: bool = False
    price_dl: int = 0

class InviteCoauthorRequest(BaseModel):
    email: str

@router.post("/{document_id}/chapters", response_model=DocumentResponse)
async def add_chapter(
    document_id: str,
    chapter_in: ChapterCreate,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
) -> Any:
    return await DocumentService.add_chapter(document_id, chapter_in, current_user)

@router.post("/{document_id}/coauthors")
async def invite_coauthor(
    document_id: str,
    req: InviteCoauthorRequest,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
):
    return await DocumentService.invite_coauthor(document_id, req.email, current_user)

@router.get("/{document_id}/export/epub")
async def export_epub(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    content = await DocumentService.export_epub(document_id, current_user)
    headers = {"Content-Disposition": f'attachment; filename="DocLib_{document_id}.epub"'}
    return Response(content=content, media_type="application/epub+zip", headers=headers)

@router.get("/{document_id}/qrcode")
async def generate_qr_code(document_id: str):
    content = await DocumentService.generate_qr_code(document_id)
    return Response(content=content, media_type="image/png")

@router.post("/{document_id}/series")
async def link_series(document_id: str, series_id: str, current_user: UserInDB = Depends(get_current_user)):
    return await DocumentService.link_series(document_id, series_id, current_user)

@router.post("/{document_id}/warnings")
async def set_warnings(document_id: str, warnings: List[str], current_user: UserInDB = Depends(get_current_user)):
    return await DocumentService.set_warnings(document_id, warnings, current_user)

@router.post("/{document_id}/custom-design")
async def set_custom_design(document_id: str, custom_css: Optional[str] = None, custom_font: Optional[str] = None, current_user: UserInDB = Depends(get_current_user)):
    return await DocumentService.set_custom_design(document_id, custom_css, custom_font, current_user)

@router.get("/recommendations/ai")
async def get_ai_recommendations(limit: int = 10, current_user: UserInDB = Depends(get_current_user_optional)):
    return await DocumentService.get_ai_recommendations(limit)

@router.get("/{document_id}/seo-meta")
async def get_seo_meta(document_id: str):
    return await DocumentService.get_seo_meta(document_id)
