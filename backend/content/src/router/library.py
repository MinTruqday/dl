from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends
from core.dependency import get_current_user, get_db
from src.schemas.library import ReadingListCreate
from src.services.library import LibraryService

router = APIRouter(prefix="/library")

@router.post("/lists", response_model=APIResponse[Any])
async def create_reading_list(data: ReadingListCreate, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await LibraryService.create_reading_list(data, current_user, db=db),
        message="Fresh custom navigational reading assembly seamlessly constructed securing external hierarchical parameters",
        status=201,
    )

@router.get("/lists", response_model=APIResponse[Any])
async def get_my_lists(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await LibraryService.get_my_reading_lists(current_user, db=db),
        message="Active comprehensive functional dictionary indexing tailored analytical collections retrieved accurately systemwide",
    )

@router.get("/lists/{list_id}", response_model=APIResponse[Any])
async def get_list_by_id(list_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await LibraryService.get_reading_list_by_id(list_id, current_user, db=db),
        message="Specific underlying dimensional architecture framing personalized indexing dictionary compiled precisely digitally",
    )

@router.post("/lists/{list_id}/documents/{document_id}", response_model=APIResponse[Any])
async def add_to_list(list_id: str, document_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await LibraryService.add_document_to_list(list_id, document_id, current_user, db=db),
        message="Targeted digital literary publication properly appended mapping personalized logical categorization system",
    )

@router.delete("/lists/{list_id}/documents/{document_id}", response_model=APIResponse[Any])
async def remove_from_list(list_id: str, document_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(
        data=await LibraryService.remove_document_from_list(list_id, document_id, current_user, db=db),
        message="Targeted structural digital asset strictly divorced decoupling localized reading categorization database",
    )