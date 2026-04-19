from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_file_editing_service, get_file_service
from app.api.schemas import EditFileRequest
from app.domain.services import FileEditingService, FileService

router = APIRouter()


@router.get("/sessions/{session_id}/files")
def list_files(
    session_id: str,
    service: FileService = Depends(get_file_service),
) -> list[str]:
    return service.list_files(session_id)


@router.get("/sessions/{session_id}/files/content")
def read_file(
    session_id: str,
    path: str,
    service: FileService = Depends(get_file_service),
) -> dict[str, str]:
    try:
        return {"content": service.read_file(session_id, path)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/sessions/{session_id}/files/preview")
def preview_file(
    session_id: str,
    path: str,
    service: FileService = Depends(get_file_service),
) -> dict[str, str]:
    try:
        return {"html": service.render_preview(session_id, path)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/sessions/{session_id}/files/content")
def edit_file(
    session_id: str,
    request: EditFileRequest,
    service: FileEditingService = Depends(get_file_editing_service),
) -> dict[str, str]:
    try:
        service.edit_file(
            session_id=session_id,
            user_id=request.user_id,
            path=request.path,
            new_content=request.content,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "ok"}
