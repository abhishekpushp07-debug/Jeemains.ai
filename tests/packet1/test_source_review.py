"""Real behavioral tests for source-review ledger validation.

Tests actual validator using importlib spec from docs, exact source partition counts,
gap/overlap/trailing/digest rejection, evidence file validation, and trusted source blocks.
No app code or dependency edits. Uses isolated test environment.
"""
import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
import pytest

pytestmark = pytest.mark.asyncio(loop_scope='session')

ROOT = Path(__file__).resolve().parents[2]


async def test_current_capacity_pages_are_exactly_bound_not_approved(source_review):
    ledger = source_review.ReviewLedger.model_validate_json((ROOT/'docs/packet1/review_ledger.v1.json').read_bytes())
    texts, pages = source_review.trusted_source_blocks()
    result = source_review.validate_ledger(ledger, texts, pages)
    assert result['partitioned_pages'] == 2
    assert result['partitioned_blocks'] == 38
    assert result['bound_requirements'] == 65
    assert {b.block_id[:10] for b in ledger.blocks} == {'PDF05-P003','PDF05-P055'}
    assert result['semantic_completeness_proven'] is False
    assert result['packet1_exit'] == 'BLOCKED'
    assert len(result['remaining_block_ids']) == 3261



def load_source_review_module():
    """Load source_review.py using importlib spec (not web import)."""
    spec = importlib.util.spec_from_file_location(
        "source_review",
        ROOT / "docs/packet1/source_review.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["source_review"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def source_review():
    """Import source_review validator using importlib spec."""
    return load_source_review_module()


@pytest.fixture
def tiny_text_fixture():
    """Create tiny known text fixtures with sha256 for testing."""
    text1 = "This is a test requirement text."
    text2 = "This is context information."
    text3 = "Layout spacing element."
    
    return {
        'PDF01-P001-B000': text1,
        'PDF01-P001-B001': text2,
        'PDF01-P001-B002': text3,
    }


def sha(value):
    """Compute SHA256 hash."""
    return hashlib.sha256(value.encode('utf-8') if isinstance(value, str) else value).hexdigest()



@pytest.mark.parametrize('kind', ['file_symlink','parent_symlink','secret_file'])
async def test_evidence_rejects_symlink_components_and_secret_file(source_review,tmp_path,kind):
    docs = tmp_path/'docs'
    docs.mkdir()
    proof = docs/'proof.txt'
    proof.write_text('synthetic proof only')
    expected = 'Evidence must be an existing'
    if kind == 'file_symlink':
        (docs/'link.txt').symlink_to(proof)
        relative = 'docs/link.txt'
    elif kind == 'parent_symlink':
        (docs/'alias').symlink_to(docs,target_is_directory=True)
        relative = 'docs/alias/proof.txt'
    else:
        (docs/'.env').write_bytes(proof.read_bytes())
        relative = 'docs/.env'
        expected = 'Secret/config'
    text = 'Synthetic requirement.'
    ledger = source_review.ReviewLedger.model_validate({
        'schema_version':'source-review-v1',
        'requirements':[{'id':'REQ_PROOF','obligation':'Synthetic evidence validation obligation','packet':1,
            'owner_role':'application_lead','boundaries':['test-boundary'],'acceptance_cases':['test-only'],
            'evidence':[{'path':relative,'sha256':sha(proof.read_bytes())}]}],
        'blocks':[{'block_id':'PDF01-P001-B000','original_text_sha256':sha(text),
            'reviewed_at':datetime.now(timezone.utc),'reviewer_role':'engineering_agent',
            'spans':[{'start_codepoint':0,'end_codepoint':len(text),'quote_sha256':sha(text),
                'kind':'requirement','requirement_id':'REQ_PROOF'}]}],
    })
    with pytest.raises(ValueError,match=expected):
        source_review.validate_ledger(ledger,{'PDF01-P001-B000':text},{'PDF01-P001'},evidence_root=tmp_path)


async def test_trusted_source_blocks_verifies_177_pages_3299_blocks(source_review):
    """Test that trusted_source_blocks returns exactly 177 pages and 3299 blocks."""
    texts, pages = source_review.trusted_source_blocks()
    
    assert len(pages) == 177, f"Expected 177 pages, got {len(pages)}"
    assert len(texts) == 3299, f"Expected 3299 blocks, got {len(texts)}"
    
    # Verify all block IDs have correct format
    for block_id in texts.keys():
        assert block_id.startswith('PDF0')
        assert '-P' in block_id
        assert '-B' in block_id
    
    print(f"✓ Trusted source blocks: 177 pages, 3299 blocks verified")


async def test_empty_ledger_results_in_blocked_exit(source_review):
    """Test that empty review ledger results in packet BLOCKED."""
    ledger = source_review.ReviewLedger.model_validate({'schema_version':'source-review-v1','requirements':[],'blocks':[]})
    texts, pages = source_review.trusted_source_blocks()
    
    result = source_review.validate_ledger(ledger, texts, pages)
    
    assert result['schema_version'] == 'source-review-result-v1'
    assert result['source_pages'] == 177
    assert result['source_blocks'] == 3299
    assert result['partitioned_blocks'] == 0
    assert result['partitioned_pages'] == 0
    assert result['bound_requirements'] == 0
    assert result['mechanical_partition_complete'] is False
    assert result['semantic_completeness_proven'] is False
    assert result['operator_approval_present'] is False
    assert result['packet1_exit'] == 'BLOCKED'
    assert len(result['remaining_block_ids']) == 3299
    
    print(f"✓ Empty ledger results in 0 reviewed, packet BLOCKED")


async def test_valid_utc_typed_review_ledger_validates(source_review, tiny_text_fixture):
    """Test that valid UTC-typed review ledger validates correctly."""
    texts = tiny_text_fixture
    pages = {'PDF01-P001'}
    
    # Create valid ledger with UTC timestamp
    ledger_data = {
        'schema_version': 'source-review-v1',
        'requirements': [
            {
                'id': 'REQ_TEST_001',
                'obligation': 'Test requirement obligation text here',
                'packet': 1,
                'owner_role': 'application_lead',
                'boundaries': ['test boundary'],
                'acceptance_cases': ['test case'],
                'evidence': [],
                'semantic_review': 'PENDING_INDEPENDENT_REVIEW',
            }
        ],
        'blocks': [
            {
                'block_id': 'PDF01-P001-B000',
                'original_text_sha256': sha(texts['PDF01-P001-B000']),
                'reviewed_at': datetime.now(timezone.utc),
                'reviewer_role': 'engineering_agent',
                'spans': [
                    {
                        'start_codepoint': 0,
                        'end_codepoint': len(texts['PDF01-P001-B000']),
                        'quote_sha256': sha(texts['PDF01-P001-B000']),
                        'kind': 'requirement',
                        'requirement_id': 'REQ_TEST_001',
                        'rationale': '',
                    }
                ],
            }
        ],
    }
    
    ledger = source_review.ReviewLedger.model_validate(ledger_data)
    result = source_review.validate_ledger(ledger, texts, pages)
    
    assert result['partitioned_blocks'] == 1
    assert result['bound_requirements'] == 1
    
    print(f"✓ Valid UTC-typed review ledger validates")


async def test_naive_timestamp_rejected(source_review, tiny_text_fixture):
    """Test that naive (non-UTC) timestamp is rejected."""
    texts = tiny_text_fixture
    pages = {'PDF01-P001'}
    
    # Create ledger with naive timestamp (no timezone)
    ledger_data = {
        'schema_version': 'source-review-v1',
        'requirements': [],
        'blocks': [
            {
                'block_id': 'PDF01-P001-B000',
                'original_text_sha256': sha(texts['PDF01-P001-B000']),
                'reviewed_at': datetime.now(),  # Naive timestamp
                'reviewer_role': 'engineering_agent',
                'spans': [
                    {
                        'start_codepoint': 0,
                        'end_codepoint': len(texts['PDF01-P001-B000']),
                        'quote_sha256': sha(texts['PDF01-P001-B000']),
                        'kind': 'context',
                        'requirement_id': None,
                        'rationale': 'test context',
                    }
                ],
            }
        ],
    }
    
    with pytest.raises(ValueError, match='timezone-aware UTC'):
        source_review.ReviewLedger.model_validate(ledger_data)
    
    print(f"✓ Naive timestamp rejected")


async def test_span_gap_rejected(source_review, tiny_text_fixture):
    """Test that gaps in span coverage are rejected."""
    texts = tiny_text_fixture
    pages = {'PDF01-P001'}
    
    text = texts['PDF01-P001-B000']
    
    # Create ledger with gap in spans (0-10, then 15-end, missing 10-15)
    ledger_data = {
        'schema_version': 'source-review-v1',
        'requirements': [],
        'blocks': [
            {
                'block_id': 'PDF01-P001-B000',
                'original_text_sha256': sha(text),
                'reviewed_at': datetime.now(timezone.utc),
                'reviewer_role': 'engineering_agent',
                'spans': [
                    {
                        'start_codepoint': 0,
                        'end_codepoint': 10,
                        'quote_sha256': sha(text[0:10]),
                        'kind': 'context',
                        'requirement_id': None,
                        'rationale': 'first part',
                    },
                    {
                        'start_codepoint': 15,  # Gap from 10 to 15
                        'end_codepoint': len(text),
                        'quote_sha256': sha(text[15:]),
                        'kind': 'context',
                        'requirement_id': None,
                        'rationale': 'second part',
                    }
                ],
            }
        ],
    }
    
    ledger = source_review.ReviewLedger.model_validate(ledger_data)
    
    with pytest.raises(ValueError, match='gaps or overlaps'):
        source_review.validate_ledger(ledger, texts, pages)
    
    print(f"✓ Span gap rejected")


async def test_span_overlap_rejected(source_review, tiny_text_fixture):
    """Test that overlapping spans are rejected."""
    texts = tiny_text_fixture
    pages = {'PDF01-P001'}
    
    text = texts['PDF01-P001-B000']
    
    # Create ledger with overlapping spans
    ledger_data = {
        'schema_version': 'source-review-v1',
        'requirements': [],
        'blocks': [
            {
                'block_id': 'PDF01-P001-B000',
                'original_text_sha256': sha(text),
                'reviewed_at': datetime.now(timezone.utc),
                'reviewer_role': 'engineering_agent',
                'spans': [
                    {
                        'start_codepoint': 0,
                        'end_codepoint': 15,
                        'quote_sha256': sha(text[0:15]),
                        'kind': 'context',
                        'requirement_id': None,
                        'rationale': 'first part',
                    },
                    {
                        'start_codepoint': 10,  # Overlaps with previous span
                        'end_codepoint': len(text),
                        'quote_sha256': sha(text[10:]),
                        'kind': 'context',
                        'requirement_id': None,
                        'rationale': 'second part',
                    }
                ],
            }
        ],
    }
    
    ledger = source_review.ReviewLedger.model_validate(ledger_data)
    
    with pytest.raises(ValueError, match='gaps or overlaps'):
        source_review.validate_ledger(ledger, texts, pages)
    
    print(f"✓ Span overlap rejected")


async def test_trailing_text_rejected(source_review, tiny_text_fixture):
    """Test that trailing unaccounted text is rejected."""
    texts = tiny_text_fixture
    pages = {'PDF01-P001'}
    
    text = texts['PDF01-P001-B000']
    
    # Create ledger that doesn't cover entire text
    ledger_data = {
        'schema_version': 'source-review-v1',
        'requirements': [],
        'blocks': [
            {
                'block_id': 'PDF01-P001-B000',
                'original_text_sha256': sha(text),
                'reviewed_at': datetime.now(timezone.utc),
                'reviewer_role': 'engineering_agent',
                'spans': [
                    {
                        'start_codepoint': 0,
                        'end_codepoint': len(text) - 5,  # Leave trailing text
                        'quote_sha256': sha(text[0:len(text)-5]),
                        'kind': 'context',
                        'requirement_id': None,
                        'rationale': 'partial coverage',
                    }
                ],
            }
        ],
    }
    
    ledger = source_review.ReviewLedger.model_validate(ledger_data)
    
    with pytest.raises(ValueError, match='trailing'):
        source_review.validate_ledger(ledger, texts, pages)
    
    print(f"✓ Trailing text rejected")


async def test_span_digest_wrong_rejected(source_review, tiny_text_fixture):
    """Test that wrong span digest is rejected."""
    texts = tiny_text_fixture
    pages = {'PDF01-P001'}
    
    text = texts['PDF01-P001-B000']
    
    # Create ledger with wrong span digest
    ledger_data = {
        'schema_version': 'source-review-v1',
        'requirements': [],
        'blocks': [
            {
                'block_id': 'PDF01-P001-B000',
                'original_text_sha256': sha(text),
                'reviewed_at': datetime.now(timezone.utc),
                'reviewer_role': 'engineering_agent',
                'spans': [
                    {
                        'start_codepoint': 0,
                        'end_codepoint': len(text),
                        'quote_sha256': 'a' * 64,  # Wrong digest
                        'kind': 'context',
                        'requirement_id': None,
                        'rationale': 'test',
                    }
                ],
            }
        ],
    }
    
    ledger = source_review.ReviewLedger.model_validate(ledger_data)
    
    with pytest.raises(ValueError, match='no longer matches source'):
        source_review.validate_ledger(ledger, texts, pages)
    
    print(f"✓ Wrong span digest rejected")


async def test_block_digest_wrong_rejected(source_review, tiny_text_fixture):
    """Test that wrong block digest is rejected."""
    texts = tiny_text_fixture
    pages = {'PDF01-P001'}
    
    text = texts['PDF01-P001-B000']
    
    # Create ledger with wrong block digest
    ledger_data = {
        'schema_version': 'source-review-v1',
        'requirements': [],
        'blocks': [
            {
                'block_id': 'PDF01-P001-B000',
                'original_text_sha256': 'b' * 64,  # Wrong block digest
                'reviewed_at': datetime.now(timezone.utc),
                'reviewer_role': 'engineering_agent',
                'spans': [
                    {
                        'start_codepoint': 0,
                        'end_codepoint': len(text),
                        'quote_sha256': sha(text),
                        'kind': 'context',
                        'requirement_id': None,
                        'rationale': 'test',
                    }
                ],
            }
        ],
    }
    
    ledger = source_review.ReviewLedger.model_validate(ledger_data)
    
    with pytest.raises(ValueError, match='source hash mismatch'):
        source_review.validate_ledger(ledger, texts, pages)
    
    print(f"✓ Wrong block digest rejected")


async def test_unknown_block_rejected(source_review, tiny_text_fixture):
    """Test that unknown block ID is rejected."""
    texts = tiny_text_fixture
    pages = {'PDF01-P001'}
    
    # Create ledger with unknown block ID (valid pattern but not in texts)
    ledger_data = {
        'schema_version': 'source-review-v1',
        'requirements': [],
        'blocks': [
            {
                'block_id': 'PDF01-P099-B999',  # Valid pattern but unknown block
                'original_text_sha256': 'c' * 64,
                'reviewed_at': datetime.now(timezone.utc),
                'reviewer_role': 'engineering_agent',
                'spans': [
                    {
                        'start_codepoint': 0,
                        'end_codepoint': 10,
                        'quote_sha256': 'd' * 64,
                        'kind': 'context',
                        'requirement_id': None,
                        'rationale': 'test',
                    }
                ],
            }
        ],
    }
    
    ledger = source_review.ReviewLedger.model_validate(ledger_data)
    
    with pytest.raises(ValueError, match='source hash mismatch'):
        source_review.validate_ledger(ledger, texts, pages)
    
    print(f"✓ Unknown block rejected")


async def test_duplicate_block_rejected(source_review, tiny_text_fixture):
    """Test that duplicate block IDs are rejected."""
    texts = tiny_text_fixture
    pages = {'PDF01-P001'}
    
    text = texts['PDF01-P001-B000']
    
    # Create ledger with duplicate block
    ledger_data = {
        'schema_version': 'source-review-v1',
        'requirements': [],
        'blocks': [
            {
                'block_id': 'PDF01-P001-B000',
                'original_text_sha256': sha(text),
                'reviewed_at': datetime.now(timezone.utc),
                'reviewer_role': 'engineering_agent',
                'spans': [
                    {
                        'start_codepoint': 0,
                        'end_codepoint': len(text),
                        'quote_sha256': sha(text),
                        'kind': 'context',
                        'requirement_id': None,
                        'rationale': 'first',
                    }
                ],
            },
            {
                'block_id': 'PDF01-P001-B000',  # Duplicate
                'original_text_sha256': sha(text),
                'reviewed_at': datetime.now(timezone.utc),
                'reviewer_role': 'engineering_agent',
                'spans': [
                    {
                        'start_codepoint': 0,
                        'end_codepoint': len(text),
                        'quote_sha256': sha(text),
                        'kind': 'context',
                        'requirement_id': None,
                        'rationale': 'second',
                    }
                ],
            }
        ],
    }
    
    ledger = source_review.ReviewLedger.model_validate(ledger_data)
    
    with pytest.raises(ValueError, match='Duplicate review identities'):
        source_review.validate_ledger(ledger, texts, pages)
    
    print(f"✓ Duplicate block rejected")


async def test_unknown_requirement_rejected(source_review, tiny_text_fixture):
    """Test that span with unknown requirement ID is rejected."""
    texts = tiny_text_fixture
    pages = {'PDF01-P001'}
    
    text = texts['PDF01-P001-B000']
    
    # Create ledger with span referencing unknown requirement
    ledger_data = {
        'schema_version': 'source-review-v1',
        'requirements': [],
        'blocks': [
            {
                'block_id': 'PDF01-P001-B000',
                'original_text_sha256': sha(text),
                'reviewed_at': datetime.now(timezone.utc),
                'reviewer_role': 'engineering_agent',
                'spans': [
                    {
                        'start_codepoint': 0,
                        'end_codepoint': len(text),
                        'quote_sha256': sha(text),
                        'kind': 'requirement',
                        'requirement_id': 'UNKNOWN_REQ',  # Not in requirements list
                        'rationale': '',
                    }
                ],
            }
        ],
    }
    
    ledger = source_review.ReviewLedger.model_validate(ledger_data)
    
    with pytest.raises(ValueError, match='no owned requirement'):
        source_review.validate_ledger(ledger, texts, pages)
    
    print(f"✓ Unknown requirement rejected")


async def test_unbound_requirement_rejected(source_review, tiny_text_fixture):
    """Test that requirement with no span binding is rejected (orphan)."""
    texts = tiny_text_fixture
    pages = {'PDF01-P001'}
    
    text = texts['PDF01-P001-B000']
    
    # Create ledger with orphan requirement (not bound to any span)
    ledger_data = {
        'schema_version': 'source-review-v1',
        'requirements': [
            {
                'id': 'ORPHAN_REQ',
                'obligation': 'This requirement has no source span',
                'packet': 1,
                'owner_role': 'application_lead',
                'boundaries': ['test'],
                'acceptance_cases': ['test'],
                'evidence': [],
            }
        ],
        'blocks': [
            {
                'block_id': 'PDF01-P001-B000',
                'original_text_sha256': sha(text),
                'reviewed_at': datetime.now(timezone.utc),
                'reviewer_role': 'engineering_agent',
                'spans': [
                    {
                        'start_codepoint': 0,
                        'end_codepoint': len(text),
                        'quote_sha256': sha(text),
                        'kind': 'context',
                        'requirement_id': None,
                        'rationale': 'just context',
                    }
                ],
            }
        ],
    }
    
    ledger = source_review.ReviewLedger.model_validate(ledger_data)
    
    with pytest.raises(ValueError, match='no exact source span'):
        source_review.validate_ledger(ledger, texts, pages)
    
    print(f"✓ Unbound requirement rejected (orphan)")


async def test_offset_end_overbound_rejected(source_review, tiny_text_fixture):
    """Test that span end offset beyond text length is rejected."""
    texts = tiny_text_fixture
    pages = {'PDF01-P001'}
    
    text = texts['PDF01-P001-B000']
    
    # Create ledger with end offset beyond text length
    ledger_data = {
        'schema_version': 'source-review-v1',
        'requirements': [],
        'blocks': [
            {
                'block_id': 'PDF01-P001-B000',
                'original_text_sha256': sha(text),
                'reviewed_at': datetime.now(timezone.utc),
                'reviewer_role': 'engineering_agent',
                'spans': [
                    {
                        'start_codepoint': 0,
                        'end_codepoint': len(text) + 100,  # Beyond text length
                        'quote_sha256': 'e' * 64,
                        'kind': 'context',
                        'requirement_id': None,
                        'rationale': 'test',
                    }
                ],
            }
        ],
    }
    
    ledger = source_review.ReviewLedger.model_validate(ledger_data)
    
    with pytest.raises(ValueError, match='gaps or overlaps'):
        source_review.validate_ledger(ledger, texts, pages)
    
    print(f"✓ Offset end overbound rejected")


async def test_evidence_file_hash_validation(source_review, tmp_path):
    """Test that evidence file hash is validated."""
    texts = {'PDF01-P001-B000': 'Test text'}
    pages = {'PDF01-P001'}
    
    # Create a temporary evidence file under /app/tests/packet1/_evidence_tmp
    evidence_dir = ROOT / 'tests/packet1/_evidence_tmp'
    evidence_dir.mkdir(exist_ok=True)
    
    evidence_file = evidence_dir / 'test_evidence.txt'
    evidence_content = b'Test evidence content'
    evidence_file.write_bytes(evidence_content)
    evidence_hash = sha(evidence_content)
    
    try:
        # Create ledger with correct evidence hash
        ledger_data = {
            'schema_version': 'source-review-v1',
            'requirements': [
                {
                    'id': 'REQ_WITH_EVIDENCE',
                    'obligation': 'Test requirement with evidence',
                    'packet': 1,
                    'owner_role': 'application_lead',
                    'boundaries': ['test'],
                    'acceptance_cases': ['test'],
                    'evidence': [
                        {
                            'path': 'tests/packet1/_evidence_tmp/test_evidence.txt',
                            'sha256': evidence_hash,
                            'interpretation': 'traceability_only_not_verified_pass',
                        }
                    ],
                }
            ],
            'blocks': [
                {
                    'block_id': 'PDF01-P001-B000',
                    'original_text_sha256': sha(texts['PDF01-P001-B000']),
                    'reviewed_at': datetime.now(timezone.utc),
                    'reviewer_role': 'engineering_agent',
                    'spans': [
                        {
                            'start_codepoint': 0,
                            'end_codepoint': len(texts['PDF01-P001-B000']),
                            'quote_sha256': sha(texts['PDF01-P001-B000']),
                            'kind': 'requirement',
                            'requirement_id': 'REQ_WITH_EVIDENCE',
                            'rationale': '',
                        }
                    ],
                }
            ],
        }
        
        ledger = source_review.ReviewLedger.model_validate(ledger_data)
        result = source_review.validate_ledger(ledger, texts, pages, evidence_root=ROOT)
        
        assert result['bound_requirements'] == 1
        
        # Now test with wrong hash
        ledger_data['requirements'][0]['evidence'][0]['sha256'] = 'f' * 64
        ledger = source_review.ReviewLedger.model_validate(ledger_data)
        
        with pytest.raises(ValueError, match='Evidence artifact changed'):
            source_review.validate_ledger(ledger, texts, pages, evidence_root=ROOT)
        
        print(f"✓ Evidence file hash validated")
    
    finally:
        # Cleanup
        if evidence_file.exists():
            evidence_file.unlink()
        if evidence_dir.exists() and not list(evidence_dir.iterdir()):
            evidence_dir.rmdir()


async def test_evidence_path_traversal_rejected(source_review):
    """Test that evidence path traversal attempts are rejected."""
    texts = {'PDF01-P001-B000': 'Test text'}
    pages = {'PDF01-P001'}
    
    # Create ledger with path traversal attempt
    ledger_data = {
        'schema_version': 'source-review-v1',
        'requirements': [
            {
                'id': 'REQ_TRAVERSAL',
                'obligation': 'Test requirement',
                'packet': 1,
                'owner_role': 'application_lead',
                'boundaries': ['test'],
                'acceptance_cases': ['test'],
                'evidence': [
                    {
                        'path': '../../../etc/passwd',  # Path traversal
                        'sha256': 'a' * 64,
                        'interpretation': 'traceability_only_not_verified_pass',
                    }
                ],
            }
        ],
        'blocks': [
            {
                'block_id': 'PDF01-P001-B000',
                'original_text_sha256': sha(texts['PDF01-P001-B000']),
                'reviewed_at': datetime.now(timezone.utc),
                'reviewer_role': 'engineering_agent',
                'spans': [
                    {
                        'start_codepoint': 0,
                        'end_codepoint': len(texts['PDF01-P001-B000']),
                        'quote_sha256': sha(texts['PDF01-P001-B000']),
                        'kind': 'requirement',
                        'requirement_id': 'REQ_TRAVERSAL',
                        'rationale': '',
                    }
                ],
            }
        ],
    }
    
    ledger = source_review.ReviewLedger.model_validate(ledger_data)
    
    with pytest.raises(ValueError, match='outside approved repository boundaries'):
        source_review.validate_ledger(ledger, texts, pages, evidence_root=ROOT)
    
    print(f"✓ Evidence path traversal rejected")


async def test_evidence_env_file_rejected(source_review):
    """Test that .env files are rejected as evidence."""
    texts = {'PDF01-P001-B000': 'Test text'}
    pages = {'PDF01-P001'}
    
    # Create ledger with .env file as evidence
    ledger_data = {
        'schema_version': 'source-review-v1',
        'requirements': [
            {
                'id': 'REQ_ENV',
                'obligation': 'Test requirement',
                'packet': 1,
                'owner_role': 'application_lead',
                'boundaries': ['test'],
                'acceptance_cases': ['test'],
                'evidence': [
                    {
                        'path': 'backend/.env',
                        'sha256': 'a' * 64,
                        'interpretation': 'traceability_only_not_verified_pass',
                    }
                ],
            }
        ],
        'blocks': [
            {
                'block_id': 'PDF01-P001-B000',
                'original_text_sha256': sha(texts['PDF01-P001-B000']),
                'reviewed_at': datetime.now(timezone.utc),
                'reviewer_role': 'engineering_agent',
                'spans': [
                    {
                        'start_codepoint': 0,
                        'end_codepoint': len(texts['PDF01-P001-B000']),
                        'quote_sha256': sha(texts['PDF01-P001-B000']),
                        'kind': 'requirement',
                        'requirement_id': 'REQ_ENV',
                        'rationale': '',
                    }
                ],
            }
        ],
    }
    
    ledger = source_review.ReviewLedger.model_validate(ledger_data)
    
    with pytest.raises(ValueError, match='Secret/config files'):
        source_review.validate_ledger(ledger, texts, pages, evidence_root=ROOT)
    
    print(f"✓ .env file as evidence rejected")


async def test_mechanical_100_percent_still_not_approved(source_review, tiny_text_fixture):
    """Test that even 100% mechanical partition does not mean operator approval."""
    texts = tiny_text_fixture
    pages = {'PDF01-P001'}
    
    # Create ledger that covers all blocks
    ledger_data = {
        'schema_version': 'source-review-v1',
        'requirements': [],
        'blocks': []
    }
    
    for block_id, text in texts.items():
        ledger_data['blocks'].append({
            'block_id': block_id,
            'original_text_sha256': sha(text),
            'reviewed_at': datetime.now(timezone.utc),
            'reviewer_role': 'engineering_agent',
            'spans': [
                {
                    'start_codepoint': 0,
                    'end_codepoint': len(text),
                    'quote_sha256': sha(text),
                    'kind': 'context',
                    'requirement_id': None,
                    'rationale': 'mechanical coverage',
                }
            ],
        })
    
    ledger = source_review.ReviewLedger.model_validate(ledger_data)
    result = source_review.validate_ledger(ledger, texts, pages)
    
    assert result['mechanical_partition_complete'] is True
    assert result['semantic_completeness_proven'] is False
    assert result['operator_approval_present'] is False
    
    print(f"✓ Mechanical 100% coverage does not imply approval")
