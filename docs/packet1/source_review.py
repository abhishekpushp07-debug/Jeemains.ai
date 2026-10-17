"""Fail-closed source-review ledger validation; never equate indexing with approval.

Usage: python docs/packet1/source_review.py docs/packet1/review_ledger.v1.json
Only hashes, offsets, safe summaries and evidence references are persisted.
Original specification text/credentials are never echoed by this tool.
"""
from datetime import datetime
import hashlib
import json
from pathlib import Path
from typing import Annotated, Literal
import sys
import fitz
from pydantic import BaseModel, ConfigDict, Field, field_validator

ROOT = Path(__file__).resolve().parents[2]
Digest = Annotated[str, Field(pattern=r'^[0-9a-f]{64}$')]
Id = Annotated[str, Field(pattern=r'^[A-Z][A-Z0-9_-]{2,99}$')]


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class Evidence(Strict):
    path: str = Field(min_length=1, max_length=300)
    sha256: Digest
    # An existing file is not proof that its assertions passed or that it is signed.
    interpretation: Literal['traceability_only_not_verified_pass'] = 'traceability_only_not_verified_pass'


class AtomicRequirement(Strict):
    id: Id
    obligation: str = Field(min_length=10, max_length=1600)
    packet: int = Field(ge=1, le=10)
    owner_role: Literal['application_lead','content_reviewer','analytics_lead','security_operator','database_operator','performance_operator']
    boundaries: list[Annotated[str, Field(min_length=2, max_length=120)]] = Field(min_length=1, max_length=20)
    acceptance_cases: list[Annotated[str, Field(min_length=3, max_length=160)]] = Field(min_length=1, max_length=30)
    evidence: list[Evidence] = Field(default_factory=list, max_length=30)
    semantic_review: Literal['PENDING_INDEPENDENT_REVIEW','AGENT_REVIEWED_NOT_OPERATOR_APPROVED'] = 'PENDING_INDEPENDENT_REVIEW'


class Span(Strict):
    start_codepoint: int = Field(ge=0)
    end_codepoint: int = Field(gt=0)
    quote_sha256: Digest
    kind: Literal['requirement','context','layout']
    requirement_id: Id | None = None
    rationale: str = Field(default='', max_length=500)


class ReviewedBlock(Strict):
    block_id: str = Field(pattern=r'^PDF0[1-5]-P[0-9]{3}-B[0-9]{3}$')
    original_text_sha256: Digest
    reviewed_at: datetime
    reviewer_role: Literal['engineering_agent','academic_reviewer']
    spans: list[Span] = Field(min_length=1, max_length=300)

    @field_validator('reviewed_at')
    @classmethod
    def timezone_required(cls, value):
        if value.tzinfo is None or value.utcoffset().total_seconds() != 0:
            raise ValueError('Review timestamp must be timezone-aware UTC')
        return value


class ReviewLedger(Strict):
    schema_version: Literal['source-review-v1']
    requirements: list[AtomicRequirement] = Field(default_factory=list, max_length=20000)
    blocks: list[ReviewedBlock] = Field(default_factory=list, max_length=10000)


def sha(value):
    return hashlib.sha256(value.encode('utf-8') if isinstance(value, str) else value).hexdigest()


def trusted_source_blocks():
    metadata = json.loads((ROOT/'docs/source_guides/manifest.json').read_text())
    texts = {}
    pages = set()
    for item in metadata:
        path = ROOT/'docs/source_guides'/item['name']
        if path.parent != ROOT/'docs/source_guides' or sha(path.read_bytes()) != item['sha256']:
            raise ValueError('Original source identity has changed')
        number = int(item['name'][:2])
        with fitz.open(path) as doc:
            if len(doc) != item['pages']:
                raise ValueError('Original source page count has changed')
            for page in doc:
                pid = f'PDF{number:02d}-P{page.number+1:03d}'
                pages.add(pid)
                for index, block in enumerate(page.get_text('blocks')):
                    if block[6] == 0 and block[4].strip():
                        texts[f'{pid}-B{index:03d}'] = block[4]
    if len(pages) != 177:
        raise ValueError('Incomplete source page inventory')
    return texts, pages


def validate_ledger(ledger: ReviewLedger, texts: dict[str,str], pages: set[str], evidence_root=ROOT):
    requirement_ids = [r.id for r in ledger.requirements]
    block_ids = [b.block_id for b in ledger.blocks]
    if len(set(requirement_ids)) != len(requirement_ids) or len(set(block_ids)) != len(block_ids):
        raise ValueError('Duplicate review identities')
    requirements = {r.id:r for r in ledger.requirements}
    used, reviewed = set(), set()
    for block in ledger.blocks:
        if block.block_id not in texts or sha(texts[block.block_id]) != block.original_text_sha256:
            raise ValueError('Review block source hash mismatch')
        text, cursor = texts[block.block_id], 0
        for span in block.spans:
            if span.start_codepoint != cursor or not span.start_codepoint < span.end_codepoint <= len(text):
                raise ValueError('Review spans must form an exact ordered partition without gaps or overlaps')
            excerpt = text[span.start_codepoint:span.end_codepoint]
            if sha(excerpt) != span.quote_sha256:
                raise ValueError('Review span no longer matches source content')
            if span.kind == 'requirement':
                if span.requirement_id not in requirements:
                    raise ValueError('Mandatory span has no owned requirement')
                used.add(span.requirement_id)
            elif span.requirement_id is not None or not span.rationale.strip():
                raise ValueError('Context/layout spans need rationale and no requirement binding')
            cursor = span.end_codepoint
        if cursor != len(text):
            raise ValueError('Review leaves trailing source text unaccounted for')
        reviewed.add(block.block_id)
    orphan_requirements = set(requirements) - used
    if orphan_requirements:
        raise ValueError('Requirement claims have no exact source span')
    root = evidence_root.resolve()
    for requirement in ledger.requirements:
        for evidence in requirement.evidence:
            relative = Path(evidence.path)
            if relative.is_absolute() or '..' in relative.parts or relative.parts[0] not in ('test_reports','tests','docs','backend','frontend'):
                raise ValueError('Evidence path is outside approved repository boundaries')
            target = root / relative
            if not target.resolve().is_relative_to(root) or any(root.joinpath(*relative.parts[:i]).is_symlink() for i in range(1, len(relative.parts)+1)) or not target.is_file():
                raise ValueError('Evidence must be an existing in-repository regular file')
            if target.name.startswith('.') or '.env' in target.name:
                raise ValueError('Secret/config files are not review evidence')
            if sha(target.read_bytes()) != evidence.sha256:
                raise ValueError('Evidence artifact changed after review')
    full_pages = sum(all(b in reviewed for b in texts if b.startswith(page+'-')) and any(b.startswith(page+'-') for b in texts) for page in pages)
    mechanical = len(reviewed) == len(texts) and bool(texts)
    return {
        'schema_version':'source-review-result-v1', 'source_pages':len(pages), 'source_blocks':len(texts),
        'partitioned_blocks':len(reviewed), 'partitioned_pages':full_pages,
        'bound_requirements':len(used), 'mechanical_partition_complete':mechanical,
        'semantic_completeness_proven':False, 'operator_approval_present':False,
        'packet1_exit':'BLOCKED',
        'remaining_block_ids':sorted(set(texts)-reviewed),
        'note':'Exact source-span accounting does not establish semantic atomicity, passed tests, academic approval, signatures or capacity qualification.',
    }


def main():
    if len(sys.argv) != 2:
        raise SystemExit('Usage: source_review.py repository-relative-review-ledger.json')
    path = (ROOT / sys.argv[1]).resolve()
    if not path.is_relative_to(ROOT/'docs/packet1'):
        raise SystemExit('Review ledgers must be under docs/packet1')
    try:
        ledger = ReviewLedger.model_validate_json(path.read_bytes())
        texts, pages = trusted_source_blocks()
        result = validate_ledger(ledger,texts,pages)
    except Exception:
        raise SystemExit('Review validation failed. Check schema, source hashes, span partitions and evidence boundaries. No source text or input values were logged.')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
