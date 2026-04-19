from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_session_service
from app.api.schemas import AddNoteRequest, NoteResponse
from app.domain.services import SessionService

router = APIRouter()


@router.get("/sessions/{session_id}/notes", response_model=list[NoteResponse])
def list_notes(
    session_id: str,
    service: SessionService = Depends(get_session_service),
) -> list[NoteResponse]:
    return [NoteResponse.model_validate(note.__dict__) for note in service.list_notes(session_id)]


@router.post("/sessions/{session_id}/notes", response_model=NoteResponse)
def add_note(
    session_id: str,
    request: AddNoteRequest,
    service: SessionService = Depends(get_session_service),
) -> NoteResponse:
    note = service.add_note(session_id, request.author_id, request.body)
    return NoteResponse.model_validate(note.__dict__)
