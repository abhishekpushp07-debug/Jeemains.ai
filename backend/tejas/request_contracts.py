"""Allowlisted JSON request contracts for the current pilot API.

These protect HTTP ingress, not the later transactional live-cell repository.
No coercion of booleans, numbers or unknown fields is permitted.
"""
import math
from datetime import date
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

Text = Annotated[str, Field(max_length=30000)]
Short = Annotated[str, Field(max_length=300)]
Identity = Annotated[str, Field(min_length=1, max_length=100)]
RequestKey = Annotated[str, Field(min_length=8, max_length=100)]
ScoreVersion = Annotated[str, Field(min_length=1, max_length=100, pattern=r'^[A-Za-z0-9_-]+$')]


class Payload(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, allow_inf_nan=False)


class EmptyPayload(Payload):
    pass


class CompareAttemptsPayload(Payload):
    left: Identity
    right: Identity


class SolvePayload(Payload):
    request_id: RequestKey


class QuestionReportPayload(Payload):
    category: Literal['question', 'key', 'solution', 'display'] = 'question'
    context: Literal['attempt', 'results', 'solutions']
    note: str = Field(default='', max_length=600)


class QuestionReportReviewPayload(Payload):
    status: Literal['open', 'reviewing', 'resolved']
    note: str = Field(default='', max_length=600)


class AiReviewPayload(Payload):
    action: Literal['key_confirmed', 'key_wrong', 'reopen']
    note: str = Field(default='', max_length=600)


class PhonePayload(Payload):
    phone: str = Field(min_length=5, max_length=32)


class LoginPayload(Payload):
    email: EmailStr
    password: str = Field(min_length=8, max_length=64)
    # Explicitly accepted legacy form fields; never role/privilege inputs.
    name: str = Field(default='Reviewer', min_length=1, max_length=80)
    exam: Literal['JEE Main', 'BITSAT'] = 'JEE Main'
    consent: bool = False

    @field_validator('password')
    @classmethod
    def bcrypt_budget(cls, value):
        if len(value.encode('utf-8')) > 72:
            raise ValueError('Password exceeds the permitted byte budget')
        return value


class PreferencePayload(Payload):
    exam: Literal['JEE Main', 'BITSAT']


class RulesPayload(Payload):
    minutes: float = Field(default=0, ge=0, le=1440)
    correct: float = Field(default=4, gt=0, le=100)
    wrong: float = Field(default=-1, ge=-100, le=0)
    skipped: Literal[0] = 0
    numeric_rule: str = Field(default='', max_length=500)
    navigation: Literal['free'] = 'free'
    numeric_policy: Literal['integer_exact'] = 'integer_exact'
    solution_release: Literal['after_submit'] = 'after_submit'

    @field_validator('minutes', 'correct', 'wrong', 'skipped', mode='before')
    @classmethod
    def real_number(cls, value):
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError('Use a finite numeric mark or duration, not a boolean/string')
        return value


class SetPayload(Payload):
    expected_revision: int | None = Field(default=None, ge=1)
    title: str = Field(min_length=3, max_length=160)
    exam: Literal['JEE Main', 'BITSAT'] = 'JEE Main'
    year: str = Field(default='', max_length=10)
    source: str = Field(default='', max_length=500)
    attribution: Short = ''
    audience: Literal['all', 'restricted'] = 'all'
    allowed_emails: list[Annotated[str, Field(max_length=254)]] = Field(default_factory=list, max_length=1000)
    allowed_phones: list[Annotated[str, Field(max_length=32)]] = Field(default_factory=list, max_length=1000)
    profile_mode: Literal['practice'] = 'practice'
    expires: str | None = Field(default='', max_length=10)
    rights_upload: bool = False
    rights_publish: bool = False
    rights_report: bool = False
    rules: RulesPayload = Field(default_factory=RulesPayload)
    change_reason: str = Field(default='', max_length=1000)

    @field_validator('expires')
    @classmethod
    def expiry(cls, value):
        if value and date.fromisoformat(value).isoformat() != value:
            raise ValueError('Use YYYY-MM-DD or an empty expiry')
        return value


class RegionPayload(Payload):
    file_id: Identity
    page: int = Field(ge=1, le=10000)
    rect: list[float] = Field(min_length=4, max_length=4)

    @field_validator('rect', mode='before')
    @classmethod
    def coordinates(cls, values):
        if not isinstance(values, list) or any(type(v) not in (int, float) or not math.isfinite(v) for v in values):
            raise ValueError('Source coordinates must be finite numbers')
        return values

    @model_validator(mode='after')
    def bounds(self):
        x0, y0, x1, y1 = self.rect
        if not 0 <= x0 < x1 <= 100000 or not 0 <= y0 < y1 <= 100000:
            raise ValueError('Source rectangle must have positive bounded dimensions')
        return self


class QuestionPayload(Payload):
    expected_revision: int | None = Field(default=None, ge=1)
    # This is a partial update. Missing fields are omitted, not null assignments.
    number: int = Field(default=1, ge=1, le=10000)
    solution_number: int | None = Field(default=None, ge=1, le=10000)
    subject: Short = ''
    section: Short = ''
    type: Literal['mcq', 'integer'] = 'mcq'
    text: Text = ''
    options: dict[Annotated[str, Field(min_length=1, max_length=16)], Annotated[str, Field(max_length=8192)]] = Field(default_factory=dict, max_length=8)
    answer: str = Field(default='', max_length=128)
    solution: Text = ''
    topic: Short = ''
    difficulty: Short = ''
    render_mode: Literal['source', 'typed'] = 'typed'
    q_refs: list[RegionPayload] = Field(default_factory=list, max_length=40)
    s_refs: list[RegionPayload] = Field(default_factory=list, max_length=40)
    accessible_text: Text = ''
    solution_accessible_text: Text = ''
    review_note: str = Field(default='', max_length=2000)
    disposition: Literal['standard', 'dropped', 'bonus_all', 'multiple_accepted', 'under_review'] = 'standard'
    accepted_answers: list[Annotated[str, Field(max_length=128)]] = Field(default_factory=list, max_length=20)


class ExtractPayload(Payload):
    replace_drafts: bool = False


class PublishPayload(Payload):
    confirm: bool


class WithdrawalPayload(Payload):
    reason: str = Field(min_length=1, max_length=2000)


class SubsetPayload(Payload):
    title: str = Field(default='Revision set', min_length=3, max_length=160)
    question_ids: list[Identity] = Field(min_length=1, max_length=1000)


class PreflightPayload(Payload):
    preview: bool = False
    test_response: str = Field(default='', max_length=30)


class StartPayload(Payload):
    start_key: RequestKey
    device_checked: bool = False
    preview: bool = False


class VisitPayload(Payload):
    question_id: str = Field(min_length=36, max_length=36)


class AnswerPayload(Payload):
    confidence: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    value: str = Field(max_length=128)
    marked: bool = False
    revision: int = Field(ge=1, le=100000)
    request_id: RequestKey


class RetryPayload(Payload):
    start_key: RequestKey
    score_version: ScoreVersion | None = None


class ReportPayload(Payload):
    score_version: ScoreVersion = 'original'


class ReviewerPayload(Payload):
    email: EmailStr
    role: Literal['student', 'reviewer']
    initial_password: str = Field(default='', max_length=64)

    @field_validator('initial_password')
    @classmethod
    def password_budget(cls, value):
        if len(value.encode('utf-8')) > 72:
            raise ValueError('Password exceeds the permitted byte budget')
        return value


class RegradePayload(Payload):
    note: str = Field(min_length=8, max_length=2000)


from .import_models import ScheduleInput, LiveInput

from .reviews import ReviewWrite, ProbabilityInput

from .chapter_books import ChapterAction, ChapterLive

class CronEnvelope(BaseModel):
    model_config = ConfigDict(extra='allow')
    event: Literal['schedule.triggered']
    run_id: str | None = Field(default=None, min_length=1, max_length=200)


from .cohorts import RankScenario
from .smart_models import Clarification, QuestionRepair, WorkBudget, DailyBudget

from .live_series import Assignment

MODELS = {
    'live_series.assign': Assignment,
    'my_tests.save_paper': EmptyPayload,
    'my_tests.compare': CompareAttemptsPayload,
    'manual_solutions.request_solve': SolvePayload,
    'question_reports.report_wrong': QuestionReportPayload,
    'question_reports.review_report': QuestionReportReviewPayload,
    'mock_solutions.review_action': AiReviewPayload,
    'jobs.cron': CronEnvelope,
    'cohorts.air_scenario': RankScenario,
    'smart_imports.set_daily_budget': DailyBudget,
    'smart_imports.clarify': Clarification,
    'smart_imports.repair': QuestionRepair,
    'smart_imports.budget': WorkBudget,
    'chapter_books.publish_book': ChapterAction, 'chapter_books.chapter_live': ChapterLive,
    'reviews.save_review': ReviewWrite, 'reviews.expected_value': ProbabilityInput,
    'attempts.solution_consulted': EmptyPayload,
    'imports.schedule_import': ScheduleInput, 'imports.toggle_live': LiveInput,
    'auth.login': LoginPayload, 'phone.access': PhonePayload, 'auth.preferences': PreferencePayload,
    'content.create_set': SetPayload, 'content.update_set': SetPayload,
    'content.edit_question': QuestionPayload, 'content.extract': ExtractPayload,
    'content.publish': PublishPayload, 'content.withdraw': WithdrawalPayload, 'content.subset': SubsetPayload,
    'attempts.preflight': PreflightPayload, 'attempts.start': StartPayload,
    'attempts.visit_question': VisitPayload, 'answers.save_answer': AnswerPayload,
    'attempts.retry': RetryPayload, 'attempts.report': ReportPayload,
    'reviewers.update_access': ReviewerPayload, 'corrections.regrade': RegradePayload,
}
