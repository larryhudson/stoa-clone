from __future__ import annotations

from fastapi import Request

from app.container import Container
from app.domain.services import FileEditingService, FileService, SessionService


def get_container(request: Request) -> Container:
    return request.app.state.container


def get_session_service(request: Request) -> SessionService:
    return get_container(request).session_service


def get_file_service(request: Request) -> FileService:
    return get_container(request).file_service


def get_file_editing_service(request: Request) -> FileEditingService:
    return get_container(request).file_editing_service
