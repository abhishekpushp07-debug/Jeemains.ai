from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class ScheduleInput(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    start_at: str = Field(min_length=20, max_length=40)
    revision: int = Field(ge=0)

class LiveInput(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    live: bool
    revision: int = Field(ge=0)

class ImportIssue(BaseModel):
    message: str
    question: int | None = None
    sheet: str | None = None
    row: int | None = None
    field: str | None = None

class ImportedQuestion(BaseModel):
    id: str
    number: int
    subject: str
    type: str
    text: str
    options: dict[str, str]
    answer: str
    solution: str
    render_mode: str
    render_reason: str = ''
    q_refs: list[dict] = []
    s_refs: list[dict] = []
    issues: list[str] = []
    pairing_evidence: str = ''
    source_row: int | None = None

class ImportView(BaseModel):
    id: str
    title: str
    format: str
    status: str
    message: str = ''
    questions: list[ImportedQuestion] = []
    issues: list[ImportIssue] = []
    count: int = 0
    exam: str = 'JEE Main'
    duration_minutes: int = 180
    set_id: str | None = None
    start_at: float | None = None
    end_at: float | None = None
    live_enabled: bool = False
    revision: int = 0
    server_now: float

class ImportList(BaseModel):
    items: list[ImportView]
