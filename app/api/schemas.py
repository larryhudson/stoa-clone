from pydantic import BaseModel


class CreateSessionRequest(BaseModel):
    repo_url: str
    branch: str = "main"


class SessionResponse(BaseModel):
    id: str
    repo_url: str
    branch: str
    status: str
    workspace_path: str | None
    agent_session_id: str | None
    agent_status: str
    agent_output: str
    agent_output_status: str
    agent_output_error: str | None
    controller_id: str | None
    viewers: list[str]


class JoinRequest(BaseModel):
    user_id: str


class ClaimControlRequest(BaseModel):
    user_id: str


class AddNoteRequest(BaseModel):
    author_id: str
    body: str


class NoteResponse(BaseModel):
    author_id: str
    body: str
    created_at: int


class EditFileRequest(BaseModel):
    user_id: str
    path: str
    content: str


class AgentPromptRequest(BaseModel):
    user_id: str
    text: str


class AgentControlRequest(BaseModel):
    user_id: str


class PresenceResponse(BaseModel):
    controller_id: str | None
    viewers: list[str]
