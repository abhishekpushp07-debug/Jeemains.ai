"""Time-capture request models. No other app imports here, so every route module can use them without import cycles."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

MAX_BATCH = 200


class Event(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    n: int = Field(ge=1, le=100000)
    k: Literal['v', 'a', 'm']  # v = on-screen stretch, a = answer changed, m = mark for review toggled
    q: str = Field(min_length=36, max_length=36)
    a: float = Field(ge=0, le=4e9, allow_inf_nan=False)  # server-clock second: stretch start, or the moment of the change
    b: float | None = Field(default=None, ge=0, le=4e9, allow_inf_nan=False)  # stretch end
    v: str | None = Field(default=None, max_length=30)  # new answer, or '1' / '0' for the mark


class Batch(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    sid: str = Field(pattern=r'^[A-Za-z0-9_-]{8,40}$')
    events: list[Event] = Field(min_length=1, max_length=MAX_BATCH)
