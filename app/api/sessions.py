from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_session_service, get_workspace_review_service
from app.api.schemas import (
    AddChatMessageRequest,
    AgentControlRequest,
    AgentPromptRequest,
    ChatMessageResponse,
    ClaimControlRequest,
    CreateSessionRequest,
    JoinRequest,
    PresenceResponse,
    PromptSuggestionActionRequest,
    PromptSuggestionResponse,
    SessionResponse,
    WorkspaceReviewResponse,
)
from app.domain.services import SessionService, WorkspaceReviewService

router = APIRouter()


def to_response(session) -> SessionResponse:
    return SessionResponse(
        id=session.id,
        repo_url=session.repo_url,
        branch=session.branch,
        status=session.status.value,
        workspace_path=session.workspace_path,
        agent_session_id=session.agent_session_id,
        agent_status=session.agent_status.value,
        agent_output=session.agent_output,
        agent_output_status=session.agent_output_status.value,
        agent_output_error=session.agent_output_error,
        controller_id=session.controller_id,
        viewers=sorted(session.viewers),
        chat_messages=[
            ChatMessageResponse.model_validate(message.__dict__)
            for message in session.chat_messages
        ],
        prompt_suggestions=[
            PromptSuggestionResponse(
                id=suggestion.id,
                text=suggestion.text,
                reason=suggestion.reason,
                source_message_ids=suggestion.source_message_ids,
                status=suggestion.status.value,
                created_at=suggestion.created_at,
            )
            for suggestion in session.prompt_suggestions
        ],
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


@router.get("/sessions/{session_id}/chat", response_model=list[ChatMessageResponse])
def list_chat(
    session_id: str,
    service: SessionService = Depends(get_session_service),
) -> list[ChatMessageResponse]:
    return [
        ChatMessageResponse.model_validate(message.__dict__)
        for message in service.list_chat_messages(session_id)
    ]


@router.post("/sessions/{session_id}/chat", response_model=ChatMessageResponse)
def post_chat_message(
    session_id: str,
    request: AddChatMessageRequest,
    service: SessionService = Depends(get_session_service),
) -> ChatMessageResponse:
    try:
        message = service.post_chat_message(session_id, request.author_id, request.body)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return ChatMessageResponse.model_validate(message.__dict__)


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


@router.post("/sessions/{session_id}/agent/prompt", response_model=SessionResponse)
def prompt_agent(
    session_id: str,
    request: AgentPromptRequest,
    service: SessionService = Depends(get_session_service),
) -> SessionResponse:
    try:
        session = service.prompt_agent(session_id, request.user_id, request.text)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return to_response(session)


@router.post("/sessions/{session_id}/agent/steer", response_model=SessionResponse)
def steer_agent(
    session_id: str,
    request: AgentPromptRequest,
    service: SessionService = Depends(get_session_service),
) -> SessionResponse:
    try:
        session = service.steer_agent(session_id, request.user_id, request.text)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return to_response(session)


@router.post("/sessions/{session_id}/agent/abort", response_model=SessionResponse)
def abort_agent(
    session_id: str,
    request: AgentControlRequest,
    service: SessionService = Depends(get_session_service),
) -> SessionResponse:
    try:
        session = service.abort_agent(session_id, request.user_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return to_response(session)


@router.post(
    "/sessions/{session_id}/prompt-suggestions/{suggestion_id}/accept",
    response_model=SessionResponse,
)
def accept_prompt_suggestion(
    session_id: str,
    suggestion_id: str,
    request: PromptSuggestionActionRequest,
    service: SessionService = Depends(get_session_service),
) -> SessionResponse:
    try:
        session = service.accept_prompt_suggestion(session_id, request.user_id, suggestion_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return to_response(session)


@router.post(
    "/sessions/{session_id}/prompt-suggestions/{suggestion_id}/dismiss",
    response_model=SessionResponse,
)
def dismiss_prompt_suggestion(
    session_id: str,
    suggestion_id: str,
    request: PromptSuggestionActionRequest,
    service: SessionService = Depends(get_session_service),
) -> SessionResponse:
    try:
        session = service.dismiss_prompt_suggestion(session_id, request.user_id, suggestion_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return to_response(session)


@router.get("/sessions/{session_id}/workspace/review", response_model=WorkspaceReviewResponse)
def get_workspace_review(
    session_id: str,
    service: WorkspaceReviewService = Depends(get_workspace_review_service),
) -> WorkspaceReviewResponse:
    try:
        review = service.get_review(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return WorkspaceReviewResponse.model_validate(review.__dict__)


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
