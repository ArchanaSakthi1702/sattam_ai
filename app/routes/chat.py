from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    BackgroundTasks
)
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from uuid import UUID

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models import User

from app.schemas.chat_schemas import ChatRequest

from app.services.file_service import FileService
from app.services.chat_service import ChatService
from app.services.document_extraction_service import DocumentExtractionService

from app.config import get_settings

settings = get_settings()



router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.get("/my-sessions")
async def get_sessions(
    limit: int = 20,
    cursor: datetime | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ChatService.get_sessions(
        db=db,
        user=current_user,
        limit=limit,
        cursor=cursor,
    )



@router.get("/{session_id}/messages")
async def get_chat_history(
    session_id: UUID,
    limit: int = 50,
    cursor: datetime | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ChatService.get_chat_history(
        db=db,
        user=current_user,
        session_id=session_id,
        limit=limit,
        cursor=cursor,
    )


@router.post("")
async def chat(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send a message to an existing chat session.
    """

    try:
        return await ChatService.send_message(
            db=db,
            user=current_user,
            session_id=payload.session_id,
            message=payload.message,
            file_ids=payload.file_ids
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
    
 
@router.post("/upload")
async def upload_file(
    session_id: UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await FileService.upload_file(
            db=db,
            user=current_user,
            session_id=session_id,
            file=file,
            background_tasks=background_tasks
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
    


@router.get("/my-files")
async def get_files(
    limit: int = 20,
    cursor: datetime | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await FileService.get_files(
        db=db,
        user=user,
        limit=limit,
        cursor=cursor,
    )

@router.delete("/delete-file/{file_id}")
async def delete_file(
    file_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        await FileService.delete_file(
            db=db,
            user=current_user,
            file_id=file_id,
        )

        return {
            "message": "File deleted successfully"
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.delete("/delete-session/{session_id}")
async def delete_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        await ChatService.delete_session(
            db=db,
            user=current_user,
            session_id=session_id,
        )

        return {
            "message": "Session deleted successfully"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )