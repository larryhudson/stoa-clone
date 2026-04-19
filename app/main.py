from __future__ import annotations

from fastapi import FastAPI

from app.api.events import router as events_router
from app.api.files import router as files_router
from app.api.notes import router as notes_router
from app.api.sessions import router as sessions_router
from app.container import Container, build_container


def create_app(container: Container | None = None) -> FastAPI:
    app = FastAPI()
    app.state.container = container or build_container()
    app.include_router(sessions_router)
    app.include_router(files_router)
    app.include_router(notes_router)
    app.include_router(events_router)
    return app


app = create_app()
