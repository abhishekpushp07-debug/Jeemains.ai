from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from .documents import BaseDocument


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, allow_inf_nan=False)


class UploadInput(Input):
    filename: str = Field(min_length=1, max_length=180)
    title: str = Field(min_length=1, max_length=160)
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    size: int = Field(gt=0, le=100*1024*1024)
    edition: str = Field(default='', max_length=80)
    section_id: str = Field(default='', max_length=100)
    rights_confirmed: Literal[True]
    auto_publish: bool = False
    release_at: float | None = Field(default=None, gt=0)
    competitive: bool = False
    closes_at: float | None = Field(default=None, gt=0)

    @model_validator(mode='after')
    def schedule(self):
        if self.competitive and (not self.release_at or not self.closes_at or self.closes_at <= self.release_at):
            raise ValueError('Competitive release needs an opening and closing time.')
        return self


class Region(Input):
    role: Literal['question', 'key', 'solution', 'shared', 'instructions', 'ignore']
    mock: str = Field(default='', max_length=120)
    subject: str = Field(default='', max_length=80)
    section: str = Field(default='', max_length=80)
    number: int = Field(default=0, ge=0, le=600)
    rect: list[float] = Field(min_length=4, max_length=4)
    text: str = Field(default='', max_length=30000)
    answer: str = Field(default='', max_length=40)
    option_labels: list[str] = Field(default_factory=list, max_length=8)
    response_type: Literal['mcq', 'integer', 'unresolved'] = 'unresolved'
    continuation: bool = False
    shared_for: list[int] = Field(default_factory=list, max_length=100)
    complete: bool = True
    checked: bool = False

    @model_validator(mode='after')
    def rectangle(self):
        x0,y0,x1,y1=self.rect
        if not 0 <= x0 < x1 <= 1 or not 0 <= y0 < y1 <= 1:
            raise ValueError('Use a positive rectangle within the page.')
        if any(n<1 or n>600 for n in self.shared_for) or len(set(self.shared_for))!=len(self.shared_for):
            raise ValueError('Shared passage question numbers must be unique and within 1–600.')
        if len(set(self.option_labels)) != len(self.option_labels):
            raise ValueError('Option labels must be unique.')
        if any(label not in ('A','B','C','D','1','2','3','4','E','F','G','H') for label in self.option_labels):
            raise ValueError('Unsupported option identifier.')
        return self


class PageMap(Input):
    classification: Literal['cover','contents','instructions','questions','answer_key','solutions','mixed','unresolved'] = 'unresolved'
    regions: list[Region] = Field(default_factory=list, max_length=100)
    issues: list[str] = Field(default_factory=list, max_length=30)


class PageRepair(PageMap):
    revision: int = Field(ge=0)
    note: str = Field(min_length=8, max_length=1000)


class SectionScoring(Input):
    subject: str = Field(min_length=1,max_length=80)
    section: str = Field(min_length=1,max_length=80)
    correct: float = Field(gt=0,le=100)
    wrong: float = Field(ge=-100,le=0)
    skipped: Literal[0] = 0


class RangeMap(Input):
    revision: int = Field(ge=0)
    first_page: int = Field(ge=1)
    last_page: int = Field(ge=1)
    mock: str = Field(min_length=1,max_length=120)
    subject: str = Field(default='',max_length=80)
    role: Literal['question','key','solution']
    note: str = Field(min_length=8,max_length=1000)


class MockRules(Input):
    exam: Literal['JEE Main','BITSAT','COMEDK','Custom']
    minutes: float = Field(gt=0, le=1440)
    expected_questions: int = Field(ge=1, le=600)
    correct: float = Field(gt=0, le=100)
    wrong: float = Field(ge=-100, le=0)
    skipped: Literal[0] = 0
    mechanic: Literal['all_compulsory', 'bitsat_bonus', 'unsupported']
    bonus_count: int = Field(default=0, ge=0, le=12)
    first_number: int = Field(default=1, ge=1, le=600)
    numbering: Literal['continuous', 'per_section'] = 'continuous'
    solution_policy: Literal['original_expected', 'key_only', 'mixed'] = 'original_expected'
    key_only: list[str] = Field(default_factory=list, max_length=600)
    section_scoring: list[SectionScoring] = Field(default_factory=list,max_length=30)
    source_pages: list[int] = Field(min_length=1, max_length=30)
    unsupported: str = Field(default='', max_length=1000)
    note: str = Field(min_length=8, max_length=1000)


class RuleRepair(Input):
    revision: int = Field(ge=0)
    rules: MockRules


class Control(Input):
    revision: int = Field(ge=0)
    action: Literal['pause','resume','retry','remove','publish','publish_ready','new_version','pause_mock','resume_mock','release_now']
    mock_id: str = Field(default='', max_length=80)
    reason: str = Field(default='', max_length=1000)
    release_at: float | None = Field(default=None, gt=0)


class Allowance(Input):
    revision: int = Field(ge=0)
    purpose: Literal['reading','explanations']
    pages: list[int] = Field(default_factory=list, max_length=10000)
    question_ids: list[str] = Field(default_factory=list, max_length=10000)
    max_requests: int = Field(ge=1, le=20000)
    approved: Literal[True]
    request_id: str = Field(min_length=8, max_length=100)


class Book(BaseDocument):
    owner_id: str
    created_at: float
    updated_at: float
    revision: int = 0
    state: str = 'uploading'
    removed: bool = False
    paused: bool = False
    payload: dict = Field(default_factory=dict)


class BookPage(BaseDocument):
    book_id: str
    number: int
    revision: int = 0
    classification: str = 'unresolved'
    regions: list[Region] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)
    text: str = ''
    scanned: bool = False
    context: dict = Field(default_factory=dict)
    provenance: dict = Field(default_factory=dict)


class BookMock(BaseDocument):
    book_id: str
    label: str
    order: int
    revision: int = 0
    generation: int = 1
    state: str = 'held'
    rules: dict = Field(default_factory=dict)
    issues: list[str] = Field(default_factory=list)
    questions: list[dict] = Field(default_factory=list)
    pages: dict = Field(default_factory=dict)
    set_id: str | None = None
    published_generation: int = 0
    history: list[str] = Field(default_factory=list)
    missed_release: bool = False
    original_solution_identities: list[str] = Field(default_factory=list)
    release_override: bool = False
    publish_hold: str = ''
    publish_requested: bool = False
    release_at: float | None = None


class UploadPart(BaseDocument):
    book_id: str
    number: int
    sha256: str
    data: bytes


class BookAllowance(BaseDocument):
    book_id: str
    owner_id: str
    purpose: str
    targets: list
    max_requests: int
    used: int = 0
    cursor: int = 0
    state: str = 'queued'
    created_at: float
    error: str = ''
    results: list[dict] = Field(default_factory=list)
