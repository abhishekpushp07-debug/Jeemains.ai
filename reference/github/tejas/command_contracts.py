"""Reference v1 contracts. Not a live-cell transaction or legacy API migration."""
import hashlib
import json
from math import gcd
from typing import Annotated, Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MAX_BODY_BYTES = 64 * 1024
MAX_DEPTH = 16
MAX_ITEMS = 2048
MAX_STRING_BYTES = 8192
MAX_KEY_BYTES = 128
MAX_INT = 2**63 - 1
UInt = Annotated[int, Field(strict=True, ge=0, le=MAX_INT)]
Digest = Annotated[str, Field(pattern=r'^[0-9a-f]{64}$')]
UUIDText = Annotated[str, Field(min_length=36, max_length=36)]


def _immutable(*args, **kwargs):
    raise TypeError('Command bodies are immutable; construct a new intent')


class _FrozenDict(dict):
    __setitem__ = __delitem__ = clear = pop = popitem = setdefault = update = __ior__ = _immutable

    def __deepcopy__(self, memo):
        return self


class _FrozenList(list):
    __setitem__ = __delitem__ = append = clear = extend = insert = pop = remove = reverse = sort = __iadd__ = __imul__ = _immutable

    def __deepcopy__(self, memo):
        return self


def _freeze(value):
    if type(value) is dict:
        return _FrozenDict((key, _freeze(child)) for key, child in value.items())
    if type(value) is list:
        return _FrozenList(_freeze(child) for child in value)
    return value



class StrictContract(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)


def canonical_bytes(value: dict) -> bytes:
    """tejas-command-json-v1; no floats/coercion/Unicode normalization/RFC8785 claim."""
    if type(value) not in (dict, _FrozenDict):
        raise ValueError('Command body must be an object')
    stack, count = [(value, 0)], 0
    while stack:
        item, depth = stack.pop()
        count += 1
        if depth > MAX_DEPTH or count > MAX_ITEMS:
            raise ValueError('Command structure exceeds its budget')
        kind = type(item)
        if kind in (dict, _FrozenDict):
            if len(item) > MAX_ITEMS:
                raise ValueError('Too many fields')
            for key, child in item.items():
                if type(key) is not str or not 1 <= len(key.encode('utf-8')) <= MAX_KEY_BYTES:
                    raise ValueError('Invalid command field name')
                stack.append((child, depth + 1))
        elif kind in (list, _FrozenList):
            if len(item) > MAX_ITEMS:
                raise ValueError('Too many array items')
            stack.extend((child, depth + 1) for child in item)
        elif kind is str:
            if len(item.encode('utf-8')) > MAX_STRING_BYTES:
                raise ValueError('Command text exceeds its budget')
        elif kind is int:
            if not -(2**63) <= item <= MAX_INT:
                raise ValueError('Command integers must fit signed 64 bits')
        elif item is not None and kind is not bool:
            raise ValueError('Use exact integers, not floating point or custom objects')
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
    if len(encoded) > MAX_BODY_BYTES:
        raise ValueError('Command body exceeds its byte budget')
    return encoded


class CommandIntent(StrictContract):
    tenant_id: UUIDText
    actor_id: UUIDText
    operation: Literal['START', 'DRAFT', 'COMMIT', 'CLEAR', 'TAKEOVER', 'SUBMIT', 'PUBLISH', 'REGRADE']
    target_id: UUIDText
    request_key: str = Field(min_length=8, max_length=100)
    expected_version: UInt
    writer_generation: UInt
    body: dict

    @field_validator('tenant_id', 'actor_id', 'target_id')
    @classmethod
    def canonical_uuid(cls, value):
        if str(UUID(value)) != value:
            raise ValueError('Use canonical lowercase UUIDs')
        return value

    @field_validator('request_key')
    @classmethod
    def visible_ascii_key(cls, value):
        if not value.isascii() or any(not 33 <= ord(c) <= 126 for c in value):
            raise ValueError('Request keys use visible ASCII without whitespace')
        return value

    @field_validator('body')
    @classmethod
    def bounded_body(cls, value):
        canonical_bytes(value)
        # Detach input references and prevent nested dict/list mutations.
        return _freeze(json.loads(canonical_bytes(value)))

    def scope_digest(self) -> str:
        scope = self.model_dump(include={'tenant_id', 'actor_id', 'operation', 'target_id', 'request_key'})
        return hashlib.sha256(b'tejas-idempotency-scope-v1\0' + canonical_bytes(scope)).hexdigest()

    def intent_digest(self) -> str:
        # Request key locates the receipt; all semantic preconditions bind its body.
        value = self.model_dump(exclude={'request_key'})
        return hashlib.sha256(b'tejas-command-json-v1\0' + canonical_bytes(value)).hexdigest()


class ExactMarks(StrictContract):
    numerator: int = Field(ge=-(2**63), le=MAX_INT)
    denominator: int = Field(ge=1, le=MAX_INT)

    @model_validator(mode='after')
    def reduced(self):
        if gcd(abs(self.numerator), self.denominator) != 1:
            raise ValueError('Rational marks must be reduced, including zero as 0/1')
        return self


class CommandReceipt(StrictContract):
    receipt_id: UUIDText
    attempt_id: UUIDText
    home_cell_id: str = Field(pattern=r'^cell-[0-9]{2}$')
    request_scope_sha256: Digest
    intent_sha256: Digest
    state: Literal['RECEIVED', 'APPLIED', 'REJECTED', 'SEALED']
    server_seq: UInt
    writer_generation: UInt
    accepted_at_utc_ms: UInt
    pinned_package_sha256: Digest
    # This DTO describes durable facts only; constructing it does not persist them.

    @field_validator('receipt_id', 'attempt_id')
    @classmethod
    def canonical_uuid(cls, value):
        return CommandIntent.canonical_uuid(value)


class SourceAnchor(StrictContract):
    source_id: UUIDText
    source_sha256: Digest
    source_role: Literal['questions', 'solutions', 'key', 'combined']
    page_1based: int = Field(ge=1, le=10000)
    coordinate_system: Literal['pdf_points_top_left_v1']
    rect_millipoints: tuple[UInt, UInt, UInt, UInt]

    @field_validator('source_id')
    @classmethod
    def canonical_uuid(cls, value):
        return CommandIntent.canonical_uuid(value)

    @model_validator(mode='after')
    def rectangle(self):
        x0, y0, x1, y1 = self.rect_millipoints
        if x1 <= x0 or y1 <= y0:
            raise ValueError('Source rectangle must have positive dimensions')
        return self


class CandidateQuestion(StrictContract):
    """Allowlisted reference projection; source/key/solution fields are forbidden."""
    question_id: UUIDText
    package_sha256: Digest
    response_kind: Literal['single_choice', 'multiple_choice', 'integer', 'decimal']
    stem: str = Field(min_length=1, max_length=30000)
    options: dict[str, str] = Field(default_factory=dict, max_length=8)
    asset_ids: list[UUIDText] = Field(default_factory=list, max_length=16)
    accessible_text: str = Field(default='', max_length=30000)

    @field_validator('question_id')
    @classmethod
    def canonical_uuid(cls, value):
        return CommandIntent.canonical_uuid(value)

    @field_validator('options')
    @classmethod
    def option_budget(cls, options):
        if any(not 1 <= len(key) <= 16 or not 1 <= len(text) <= 8192 for key, text in options.items()):
            raise ValueError('Invalid option identity or text length')
        return options

    @field_validator('asset_ids')
    @classmethod
    def asset_identities(cls, values):
        for value in values:
            CommandIntent.canonical_uuid(value)
        if len(values) != len(set(values)):
            raise ValueError('Asset identities must be unique')
        return values
