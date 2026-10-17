"""
Packet 1 Command Contracts Tests

Tests pure-function behavior of command_contracts.py:
- Reordered objects produce same canonical hash
- Changed actor/target/version/body behave per scope-vs-intent
- Strict bool/int/float/NaN/Unicode/depth/nodes/size validation
- Unknown fields rejected
- Reduced exact marks
- UUIDs canonical lowercase
- Source anchors positive page/rect
- Candidate payload rejects answer/solution/source fields
"""
import pytest
import json
from uuid import uuid4


def test_canonical_bytes_deterministic():
    """Test canonical_bytes produces deterministic output for reordered objects"""
    from tejas.command_contracts import canonical_bytes
    
    # Same data, different key order
    obj1 = {"z": 3, "a": 1, "m": 2}
    obj2 = {"a": 1, "m": 2, "z": 3}
    obj3 = {"m": 2, "z": 3, "a": 1}
    
    bytes1 = canonical_bytes(obj1)
    bytes2 = canonical_bytes(obj2)
    bytes3 = canonical_bytes(obj3)
    
    assert bytes1 == bytes2 == bytes3
    
    # Should be sorted by key
    expected = b'{"a":1,"m":2,"z":3}'
    assert bytes1 == expected
    
    print(f"✓ Reordered objects produce same canonical bytes")


def test_canonical_bytes_rejects_floats():
    """Test canonical_bytes rejects floats/NaN/Infinity"""
    from tejas.command_contracts import canonical_bytes
    
    # Float should be rejected
    with pytest.raises(ValueError, match="exact integers"):
        canonical_bytes({"value": 3.14})
    
    # NaN should be rejected
    with pytest.raises(ValueError, match="exact integers"):
        canonical_bytes({"value": float('nan')})
    
    # Infinity should be rejected
    with pytest.raises(ValueError, match="exact integers"):
        canonical_bytes({"value": float('inf')})
    
    print(f"✓ Floats/NaN/Infinity rejected")


def test_canonical_bytes_strict_types():
    """Test canonical_bytes enforces strict types"""
    from tejas.command_contracts import canonical_bytes
    
    # Valid types
    valid = {
        "null": None,
        "bool": True,
        "int": 42,
        "str": "hello",
        "array": [1, 2, 3],
        "object": {"nested": "value"}
    }
    result = canonical_bytes(valid)
    assert result is not None
    
    # Custom objects rejected
    class CustomObj:
        pass
    
    with pytest.raises(ValueError):
        canonical_bytes({"custom": CustomObj()})
    
    print(f"✓ Strict type validation enforced")


def test_canonical_bytes_depth_limit():
    """Test canonical_bytes enforces depth limit"""
    from tejas.command_contracts import canonical_bytes, MAX_DEPTH
    
    # Build deeply nested object
    deep = {"level": 0}
    current = deep
    for i in range(1, MAX_DEPTH + 5):
        current["nested"] = {"level": i}
        current = current["nested"]
    
    # Should exceed depth limit
    with pytest.raises(ValueError, match="exceeds its budget"):
        canonical_bytes(deep)
    
    print(f"✓ Depth limit enforced (MAX_DEPTH={MAX_DEPTH})")


def test_canonical_bytes_item_limit():
    """Test canonical_bytes enforces item count limit"""
    from tejas.command_contracts import canonical_bytes, MAX_ITEMS
    
    # Too many items
    large = {f"key_{i}": i for i in range(MAX_ITEMS + 10)}
    
    with pytest.raises(ValueError, match="Too many"):
        canonical_bytes(large)
    
    print(f"✓ Item count limit enforced (MAX_ITEMS={MAX_ITEMS})")


def test_canonical_bytes_string_size_limit():
    """Test canonical_bytes enforces string size limit"""
    from tejas.command_contracts import canonical_bytes, MAX_STRING_BYTES
    
    # String too large
    large_str = "x" * (MAX_STRING_BYTES + 100)
    
    with pytest.raises(ValueError, match="exceeds its budget"):
        canonical_bytes({"text": large_str})
    
    print(f"✓ String size limit enforced (MAX_STRING_BYTES={MAX_STRING_BYTES})")


def test_canonical_bytes_body_size_limit():
    """Test canonical_bytes enforces total body size limit"""
    from tejas.command_contracts import canonical_bytes, MAX_BODY_BYTES
    
    # Create object that exceeds body size
    # Use many medium strings to exceed total
    large_body = {f"field_{i}": "x" * 1000 for i in range(100)}
    
    with pytest.raises(ValueError, match="exceeds its byte budget"):
        canonical_bytes(large_body)
    
    print(f"✓ Body size limit enforced (MAX_BODY_BYTES={MAX_BODY_BYTES})")


def test_command_intent_scope_vs_intent_digest():
    """Test CommandIntent scope_digest vs intent_digest behavior"""
    from tejas.command_contracts import CommandIntent
    
    tenant_id = str(uuid4())
    actor_id = str(uuid4())
    target_id = str(uuid4())
    
    # Same scope, different body
    intent1 = CommandIntent(
        tenant_id=tenant_id,
        actor_id=actor_id,
        operation="COMMIT",
        target_id=target_id,
        request_key="test-key-001",
        expected_version=1,
        writer_generation=1,
        body={"answer": "A"}
    )
    
    intent2 = CommandIntent(
        tenant_id=tenant_id,
        actor_id=actor_id,
        operation="COMMIT",
        target_id=target_id,
        request_key="test-key-001",
        expected_version=1,
        writer_generation=1,
        body={"answer": "B"}  # Different body
    )
    
    # Same scope digest (same tenant/actor/operation/target/key)
    assert intent1.scope_digest() == intent2.scope_digest()
    
    # Different intent digest (different body)
    assert intent1.intent_digest() != intent2.intent_digest()
    
    print(f"✓ Scope digest vs intent digest behave correctly")


def test_command_intent_changed_actor_different_scope():
    """Test changed actor produces different scope"""
    from tejas.command_contracts import CommandIntent
    
    tenant_id = str(uuid4())
    target_id = str(uuid4())
    
    intent1 = CommandIntent(
        tenant_id=tenant_id,
        actor_id=str(uuid4()),  # Actor 1
        operation="COMMIT",
        target_id=target_id,
        request_key="test-key-001",
        expected_version=1,
        writer_generation=1,
        body={"answer": "A"}
    )
    
    intent2 = CommandIntent(
        tenant_id=tenant_id,
        actor_id=str(uuid4()),  # Actor 2 (different)
        operation="COMMIT",
        target_id=target_id,
        request_key="test-key-001",
        expected_version=1,
        writer_generation=1,
        body={"answer": "A"}
    )
    
    # Different actors = different scope
    assert intent1.scope_digest() != intent2.scope_digest()
    
    print(f"✓ Changed actor produces different scope")


def test_command_intent_changed_version_different_intent():
    """Test changed version produces different intent"""
    from tejas.command_contracts import CommandIntent
    
    tenant_id = str(uuid4())
    actor_id = str(uuid4())
    target_id = str(uuid4())
    
    intent1 = CommandIntent(
        tenant_id=tenant_id,
        actor_id=actor_id,
        operation="COMMIT",
        target_id=target_id,
        request_key="test-key-001",
        expected_version=1,
        writer_generation=1,
        body={"answer": "A"}
    )
    
    intent2 = CommandIntent(
        tenant_id=tenant_id,
        actor_id=actor_id,
        operation="COMMIT",
        target_id=target_id,
        request_key="test-key-001",
        expected_version=2,  # Different version
        writer_generation=1,
        body={"answer": "A"}
    )
    
    # Same scope (version not in scope)
    assert intent1.scope_digest() == intent2.scope_digest()
    
    # Different intent (version in intent)
    assert intent1.intent_digest() != intent2.intent_digest()
    
    print(f"✓ Changed version produces different intent")


def test_command_intent_canonical_uuid():
    """Test CommandIntent enforces canonical lowercase UUIDs"""
    from tejas.command_contracts import CommandIntent
    
    # Lowercase UUID should work
    valid_uuid = str(uuid4())
    
    intent = CommandIntent(
        tenant_id=valid_uuid,
        actor_id=valid_uuid,
        operation="COMMIT",
        target_id=valid_uuid,
        request_key="test-key-001",
        expected_version=1,
        writer_generation=1,
        body={"answer": "A"}
    )
    
    assert intent.tenant_id == valid_uuid
    
    # Uppercase UUID should be rejected
    uppercase_uuid = str(uuid4()).upper()
    
    with pytest.raises(ValueError, match="canonical lowercase"):
        CommandIntent(
            tenant_id=uppercase_uuid,
            actor_id=valid_uuid,
            operation="COMMIT",
            target_id=valid_uuid,
            request_key="test-key-001",
            expected_version=1,
            writer_generation=1,
            body={"answer": "A"}
        )
    
    print(f"✓ Canonical lowercase UUIDs enforced")


def test_command_intent_unknown_fields_rejected():
    """Test CommandIntent rejects unknown fields (extra='forbid')"""
    from tejas.command_contracts import CommandIntent
    
    valid_uuid = str(uuid4())
    
    # Unknown field should be rejected
    with pytest.raises(Exception):  # Pydantic ValidationError
        CommandIntent(
            tenant_id=valid_uuid,
            actor_id=valid_uuid,
            operation="COMMIT",
            target_id=valid_uuid,
            request_key="test-key-001",
            expected_version=1,
            writer_generation=1,
            body={"answer": "A"},
            unknown_field="should_fail"  # Extra field
        )
    
    print(f"✓ Unknown fields rejected")


def test_exact_marks_reduced():
    """Test ExactMarks enforces reduced fractions"""
    from tejas.command_contracts import ExactMarks
    
    # Reduced fraction should work
    marks1 = ExactMarks(numerator=3, denominator=4)
    assert marks1.numerator == 3
    assert marks1.denominator == 4
    
    # Zero as 0/1
    marks2 = ExactMarks(numerator=0, denominator=1)
    assert marks2.numerator == 0
    assert marks2.denominator == 1
    
    # Non-reduced should be rejected
    with pytest.raises(ValueError, match="reduced"):
        ExactMarks(numerator=2, denominator=4)  # Should be 1/2
    
    with pytest.raises(ValueError, match="reduced"):
        ExactMarks(numerator=0, denominator=2)  # Should be 0/1
    
    print(f"✓ Reduced exact marks enforced")


def test_source_anchor_positive_page():
    """Test SourceAnchor enforces positive page numbers"""
    from tejas.command_contracts import SourceAnchor
    
    source_id = str(uuid4())
    
    # Valid page (1-based)
    anchor = SourceAnchor(
        source_id=source_id,
        source_sha256="a" * 64,
        source_role="questions",
        page_1based=1,
        coordinate_system="pdf_points_top_left_v1",
        rect_millipoints=(0, 0, 1000, 1000)
    )
    assert anchor.page_1based == 1
    
    # Zero page should be rejected
    with pytest.raises(Exception):
        SourceAnchor(
            source_id=source_id,
            source_sha256="a" * 64,
            source_role="questions",
            page_1based=0,  # Invalid
            coordinate_system="pdf_points_top_left_v1",
            rect_millipoints=(0, 0, 1000, 1000)
        )
    
    print(f"✓ Positive page numbers enforced")


def test_source_anchor_positive_rect():
    """Test SourceAnchor enforces positive rectangle dimensions"""
    from tejas.command_contracts import SourceAnchor
    
    source_id = str(uuid4())
    
    # Valid rectangle
    anchor = SourceAnchor(
        source_id=source_id,
        source_sha256="a" * 64,
        source_role="questions",
        page_1based=1,
        coordinate_system="pdf_points_top_left_v1",
        rect_millipoints=(100, 200, 300, 400)  # x1 < x2, y1 < y2
    )
    assert anchor.rect_millipoints == (100, 200, 300, 400)
    
    # Invalid rectangle (x1 >= x2)
    with pytest.raises(ValueError, match="positive dimensions"):
        SourceAnchor(
            source_id=source_id,
            source_sha256="a" * 64,
            source_role="questions",
            page_1based=1,
            coordinate_system="pdf_points_top_left_v1",
            rect_millipoints=(300, 200, 100, 400)  # x1 > x2
        )
    
    # Invalid rectangle (y1 >= y2)
    with pytest.raises(ValueError, match="positive dimensions"):
        SourceAnchor(
            source_id=source_id,
            source_sha256="a" * 64,
            source_role="questions",
            page_1based=1,
            coordinate_system="pdf_points_top_left_v1",
            rect_millipoints=(100, 400, 300, 200)  # y1 > y2
        )
    
    print(f"✓ Positive rectangle dimensions enforced")


def test_candidate_question_rejects_answer_field():
    """Test CandidateQuestion rejects answer/solution/source fields"""
    from tejas.command_contracts import CandidateQuestion
    
    question_id = str(uuid4())
    
    # Valid candidate question (no answer/solution)
    candidate = CandidateQuestion(
        question_id=question_id,
        package_sha256="a" * 64,
        response_kind="single_choice",
        stem="What is 2+2?",
        options={"1": "3", "2": "4", "3": "5", "4": "6"},
        asset_ids=[],
        accessible_text="What is two plus two?"
    )
    assert candidate.question_id == question_id
    
    # Should reject answer field (extra='forbid')
    with pytest.raises(Exception):
        CandidateQuestion(
            question_id=question_id,
            package_sha256="a" * 64,
            response_kind="single_choice",
            stem="What is 2+2?",
            options={"1": "3", "2": "4", "3": "5", "4": "6"},
            answer="2"  # Forbidden field
        )
    
    # Should reject solution field
    with pytest.raises(Exception):
        CandidateQuestion(
            question_id=question_id,
            package_sha256="a" * 64,
            response_kind="single_choice",
            stem="What is 2+2?",
            options={"1": "3", "2": "4", "3": "5", "4": "6"},
            solution="The answer is 4"  # Forbidden field
        )
    
    print(f"✓ Candidate question rejects answer/solution fields")


def test_candidate_question_oversized_text_rejected():
    """Test CandidateQuestion rejects oversized text"""
    from tejas.command_contracts import CandidateQuestion
    
    question_id = str(uuid4())
    
    # Oversized stem
    with pytest.raises(Exception):
        CandidateQuestion(
            question_id=question_id,
            package_sha256="a" * 64,
            response_kind="single_choice",
            stem="x" * 40000,  # Exceeds max_length=30000
            options={"1": "A"}
        )
    
    # Oversized accessible_text
    with pytest.raises(Exception):
        CandidateQuestion(
            question_id=question_id,
            package_sha256="a" * 64,
            response_kind="single_choice",
            stem="Question",
            options={"1": "A"},
            accessible_text="x" * 40000  # Exceeds max_length=30000
        )
    
    print(f"✓ Oversized text rejected")


def test_frozen_dto_semantics():
    """Test frozen=True prevents mutation"""
    from tejas.command_contracts import CommandIntent
    
    valid_uuid = str(uuid4())
    
    intent = CommandIntent(
        tenant_id=valid_uuid,
        actor_id=valid_uuid,
        operation="COMMIT",
        target_id=valid_uuid,
        request_key="test-key-001",
        expected_version=1,
        writer_generation=1,
        body={"answer": "A"}
    )
    
    # Should not be able to mutate
    with pytest.raises(Exception):
        intent.expected_version = 2
    
    print(f"✓ Frozen DTO semantics enforced")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
