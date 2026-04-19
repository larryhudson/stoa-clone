from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_session_service
from app.api.schemas import ClaimControlRequest, CreateSessionRequest, JoinRequest, PresenceResponse, SessionResponse
from app.domain.services import SessionService

router = APIRouter()


def to_response(session) -> SessionResponse:
    return SessionResponse(
        id=session.id,
        repo_url=session.repo_url,
        branch=session.branch,
        status=session.status.value,
        workspace_path=session.workspace_path,
        controller_id=session.controller_id,
        viewers=sorted(session.viewers),
    )


@router.post("/sessions", response_model=SessionResponse)
def create_session(
    request: CreateSessionRequest,
    service: SessionService = Depends(get_session_service),
) -> SessionResponse:
    session = service.create_session(request.repo_url, request.branch)
    return to_response(session)


@router.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: str,
    service: SessionService = Depends(get_session_service),
) -> SessionResponse:
    session = service.get_session(session_id)
    return to_response(session)


@router.get("/sessions/{session_id}/events")
def list_events(
    session_id: str,
    service: SessionService = Depends(get_session_service),
) -> list[dict]:
    return service.list_events(session_id)


@router.get("/sessions/{session_id}/presence", response_model=PresenceResponse)
def get_presence(
    session_id: str,
    service: SessionService = Depends(get_session_service),
) -> PresenceResponse:
    return PresenceResponse.model_validate(service.get_presence(session_id))


@router.post("/sessions/{session_id}/start", response_model=SessionResponse)
def start_session(
    session_id: str,
    service: SessionService = Depends(get_session_service),
) -> SessionResponse:
    try:
        session = service.start_session(session_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return to_response(session)


@router.post("/sessions/{session_id}/join", response_model=SessionResponse)
def join_session(
    session_id: str,
    request: JoinRequest,
    service: SessionService = Depends(get_session_service),
) -> SessionResponse:
    session = service.join_session(session_id, request.user_id)
    return to_response(session)


@router.post("/sessions/{session_id}/control/claim", response_model=SessionResponse)
def claim_control(
    session_id: str,
    request: ClaimControlRequest,
    service: SessionService = Depends(get_session_service),
) -> SessionResponse:
    try:
        session = service.claim_control(session_id, request.user_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return to_response(session)


@router.post("/sessions/{session_id}/control/release", response_model=SessionResponse)
def release_control(
    session_id: str,
    request: ClaimControlRequest,
    service: SessionService = Depends(get_session_service),
) -> SessionResponse:
    session = service.release_control(session_id, request.user_id)
    return to_response(session)
