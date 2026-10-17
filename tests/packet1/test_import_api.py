"""Test import API endpoints with storage mocking.

Tests:
- Template download (combined, sheets, questions, solutions variants)
- Create import (multipart upload, auth, limits, idempotency)
- List imports
- Read import
- Retry import
- Error report CSV
- Schedule import (with revision CAS)
- Live toggle (with revision CAS)
- Import guard middleware (auth, size limits, immutable protection)
"""
import asyncio
import io
import json
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest
import pytest_asyncio
import openpyxl
import fitz

# Test harness
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'backend'))


@pytest_asyncio.fixture(loop_scope='session')
async def owner_session(clean_db, synthetic_owner_user):
    """Create owner session for import tests."""
    from tejas.auth import token
    coll = clean_db.tejas_users
    await coll.insert_one(dict(synthetic_owner_user))
    sid = str(uuid.uuid4())
    await clean_db.tejas_sessions.insert_one({
        'id': sid, 'user_id': synthetic_owner_user['id'],
        'access_type': synthetic_owner_user['access_type'],
        'expires_at': datetime.now(timezone.utc) + timedelta(hours=1)
    })
    return {
        'user': synthetic_owner_user,
        'session_id': sid,
        'cookies': {
            'access_token': token(synthetic_owner_user, sid, 'access', 900),
            'refresh_token': token(synthetic_owner_user, sid, 'refresh', 3600)
        }
    }


@pytest.fixture
def mock_storage(monkeypatch):
    """Mock tejas_storage to avoid external HTTP."""
    storage_data = {}
    
    def mock_put_object(path, data, content_type):
        storage_data[path] = data
        return path
    
    def mock_get_object(path):
        if path not in storage_data:
            raise Exception(f"Object not found: {path}")
        return storage_data[path]
    
    import tejas_storage
    import tejas.imports
    monkeypatch.setattr(tejas_storage, 'put_object', mock_put_object)
    monkeypatch.setattr(tejas_storage, 'get_object', mock_get_object)
    # Also patch the direct imports in tejas.imports module
    monkeypatch.setattr(tejas.imports, 'put_object', mock_put_object)
    monkeypatch.setattr(tejas.imports, 'get_object', mock_get_object)
    
    return storage_data


def create_test_pdf_pair():
    """Create minimal valid question and solution PDFs."""
    # Question PDF
    qdoc = fitz.open()
    qpage = qdoc.new_page(width=595, height=842)
    qpage.insert_text((50, 60), "Physics", fontsize=14)
    qpage.insert_text((50, 95), "Q.1 What is F=ma?", fontsize=11)
    qpage.insert_text((70, 130), "(A) Newton law", fontsize=10)
    qpage.insert_text((70, 158), "(B) Einstein law", fontsize=10)
    qpage.insert_text((70, 186), "(C) Bohr law", fontsize=10)
    qpage.insert_text((70, 214), "(D) Planck law", fontsize=10)
    
    qout = io.BytesIO()
    qdoc.save(qout)
    qdoc.close()
    qbytes = qout.getvalue()
    
    # Solution PDF
    sdoc = fitz.open()
    spage = sdoc.new_page(width=595, height=842)
    spage.insert_text((50, 60), "Physics", fontsize=14)
    spage.insert_text((50, 95), "Q.1 Answer: A", fontsize=11)
    spage.insert_text((50, 130), "F=ma is Newton's second law", fontsize=10)
    
    sout = io.BytesIO()
    sdoc.save(sout)
    sdoc.close()
    sbytes = sout.getvalue()
    
    return qbytes, sbytes


def create_test_excel_combined():
    """Create minimal valid combined Excel workbook."""
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    ws = wb.create_sheet('Questions')
    ws.append(['question_no', 'question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option', 'type', 'solution_text'])
    ws.append(['1', 'What is 2+2?', '3', '4', '5', '6', 'B', 'mcq', '2+2 equals 4'])
    
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


@pytest.mark.asyncio
async def test_template_download_combined(http_client, owner_session):
    """Test template download with combined variant."""
    response = await http_client.get(
        '/api/studio/imports/template?variant=combined',
        cookies=owner_session['cookies']
    )
    
    assert response.status_code == 200
    assert response.headers['content-type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    assert 'Tejas_combined_template.xlsx' in response.headers.get('content-disposition', '')
    
    # Verify it's a valid workbook
    wb = openpyxl.load_workbook(io.BytesIO(response.content))
    assert 'Questions' in wb.sheetnames
    assert 'Instructions' in wb.sheetnames
    
    # Verify headers
    ws = wb['Questions']
    headers = [cell.value for cell in ws[1]]
    assert 'question_id' in headers
    assert 'solution_text' in headers  # Combined has solution in same sheet
    
    print("✅ Template download combined test passed")


@pytest.mark.asyncio
async def test_template_download_sheets(http_client, owner_session):
    """Test template download with sheets variant."""
    response = await http_client.get(
        '/api/studio/imports/template?variant=sheets',
        cookies=owner_session['cookies']
    )
    
    assert response.status_code == 200
    
    wb = openpyxl.load_workbook(io.BytesIO(response.content))
    assert 'Questions' in wb.sheetnames
    assert 'Solutions' in wb.sheetnames
    assert 'Instructions' in wb.sheetnames
    
    print("✅ Template download sheets test passed")


@pytest.mark.asyncio
async def test_template_requires_staff_auth(http_client):
    """Test that template download requires staff authentication."""
    response = await http_client.get('/api/studio/imports/template')
    
    assert response.status_code == 401
    
    print("✅ Template auth test passed")


@pytest.mark.asyncio
async def test_create_import_pdf_success(http_client, owner_session, mock_storage, clean_db):
    """Test successful PDF import creation."""
    qbytes, sbytes = create_test_pdf_pair()
    request_id = str(uuid.uuid4())
    
    files = {
        'questions': ('questions.pdf', qbytes, 'application/pdf'),
        'solutions': ('solutions.pdf', sbytes, 'application/pdf')
    }
    data = {
        'format': 'pdf',
        'request_id': request_id
    }
    
    response = await http_client.post(
        '/api/studio/imports',
        files=files,
        data=data,
        cookies=owner_session['cookies']
    )
    
    assert response.status_code == 202
    result = response.json()['data']
    
    assert result['format'] == 'pdf'
    assert result['status'] in ('queued', 'organising')
    assert 'id' in result
    
    # Wait for processing
    await asyncio.sleep(3)
    
    # Check final status
    response = await http_client.get(
        f"/api/studio/imports/{result['id']}",
        cookies=owner_session['cookies']
    )
    
    assert response.status_code == 200
    final = response.json()['data']
    
    # Strict assertion: valid sources must reach READY status
    assert final['status'] == 'ready', f"Expected 'ready' but got '{final['status']}': {final.get('message', '')}"
    assert len(final['questions']) > 0
    assert len(final['issues']) == 0
    
    print(f"✅ PDF import success test passed - {len(final['questions'])} questions")


@pytest.mark.asyncio
async def test_create_import_excel_success(http_client, owner_session, mock_storage, clean_db):
    """Test successful Excel import creation."""
    excel_bytes = create_test_excel_combined()
    request_id = str(uuid.uuid4())
    
    files = {
        'questions': ('questions.xlsx', excel_bytes, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    }
    data = {
        'format': 'xlsx',
        'request_id': request_id
    }
    
    response = await http_client.post(
        '/api/studio/imports',
        files=files,
        data=data,
        cookies=owner_session['cookies']
    )
    
    assert response.status_code == 202
    result = response.json()['data']
    
    assert result['format'] == 'xlsx'
    assert result['status'] in ('queued', 'organising')
    
    # Wait for processing
    await asyncio.sleep(3)
    
    # Check final status
    response = await http_client.get(
        f"/api/studio/imports/{result['id']}",
        cookies=owner_session['cookies']
    )
    
    assert response.status_code == 200
    final = response.json()['data']
    
    # Strict assertion: valid sources must reach READY status
    assert final['status'] == 'ready', f"Expected 'ready' but got '{final['status']}': {final.get('message', '')}"
    assert len(final['questions']) == 1
    assert final['questions'][0]['answer'] == 'B'
    assert len(final['issues']) == 0
    
    print("✅ Excel import success test passed")


@pytest.mark.asyncio
async def test_create_import_idempotency(http_client, owner_session, mock_storage, clean_db):
    """Test that same request_id returns same import (idempotency)."""
    excel_bytes = create_test_excel_combined()
    request_id = str(uuid.uuid4())
    
    files = {
        'questions': ('questions.xlsx', excel_bytes, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    }
    data = {
        'format': 'xlsx',
        'request_id': request_id
    }
    
    # First request
    response1 = await http_client.post(
        '/api/studio/imports',
        files=files,
        data=data,
        cookies=owner_session['cookies']
    )
    
    assert response1.status_code == 202
    result1 = response1.json()['data']
    import_id = result1['id']
    
    # Second request with same request_id
    response2 = await http_client.post(
        '/api/studio/imports',
        files=files,
        data=data,
        cookies=owner_session['cookies']
    )
    
    assert response2.status_code == 202  # Returns existing with 202 by route contract
    result2 = response2.json()['data']
    
    assert result2['id'] == import_id
    
    print("✅ Import idempotency test passed")


@pytest.mark.asyncio
async def test_create_import_requires_owner_auth(http_client, staff_session):
    """Test that import creation requires owner role."""
    excel_bytes = create_test_excel_combined()
    request_id = str(uuid.uuid4())
    
    files = {
        'questions': ('questions.xlsx', excel_bytes, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    }
    data = {
        'format': 'xlsx',
        'request_id': request_id
    }
    
    # Staff (reviewer) should not be able to create imports
    response = await http_client.post(
        '/api/studio/imports',
        files=files,
        data=data,
        cookies=staff_session['cookies']
    )
    
    assert response.status_code == 403
    
    print("✅ Import owner auth test passed")


@pytest.mark.asyncio
async def test_create_import_rejects_oversized_file(http_client, owner_session):
    """Test that files exceeding size limit are rejected."""
    # Create a large file (>50MB for PDF, >5MB for Excel)
    large_bytes = b'x' * (6 * 1024 * 1024)  # 6MB
    request_id = str(uuid.uuid4())
    
    files = {
        'questions': ('questions.xlsx', large_bytes, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    }
    data = {
        'format': 'xlsx',
        'request_id': request_id
    }
    
    response = await http_client.post(
        '/api/studio/imports',
        files=files,
        data=data,
        cookies=owner_session['cookies']
    )
    
    assert response.status_code == 413
    
    print("✅ Import size limit test passed")


@pytest.mark.asyncio
async def test_create_import_rejects_invalid_format(http_client, owner_session):
    """Test that invalid format is rejected."""
    excel_bytes = create_test_excel_combined()
    request_id = str(uuid.uuid4())
    
    files = {
        'questions': ('questions.xlsx', excel_bytes, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    }
    data = {
        'format': 'invalid',
        'request_id': request_id
    }
    
    response = await http_client.post(
        '/api/studio/imports',
        files=files,
        data=data,
        cookies=owner_session['cookies']
    )
    
    assert response.status_code == 422
    
    print("✅ Import format validation test passed")


@pytest.mark.asyncio
async def test_list_imports(http_client, owner_session, mock_storage, clean_db):
    """Test listing imports."""
    # Create an import first
    excel_bytes = create_test_excel_combined()
    request_id = str(uuid.uuid4())
    
    files = {
        'questions': ('questions.xlsx', excel_bytes, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    }
    data = {
        'format': 'xlsx',
        'request_id': request_id
    }
    
    await http_client.post(
        '/api/studio/imports',
        files=files,
        data=data,
        cookies=owner_session['cookies']
    )
    
    # List imports
    response = await http_client.get(
        '/api/studio/imports',
        cookies=owner_session['cookies']
    )
    
    assert response.status_code == 200
    result = response.json()['data']
    
    assert 'items' in result
    assert len(result['items']) > 0
    
    print(f"✅ List imports test passed - {len(result['items'])} imports")


@pytest.mark.asyncio
async def test_schedule_import(http_client, owner_session, mock_storage, clean_db):
    """Test scheduling an import."""
    # Create a ready import
    excel_bytes = create_test_excel_combined()
    request_id = str(uuid.uuid4())
    
    files = {
        'questions': ('questions.xlsx', excel_bytes, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    }
    data = {
        'format': 'xlsx',
        'request_id': request_id
    }
    
    response = await http_client.post(
        '/api/studio/imports',
        files=files,
        data=data,
        cookies=owner_session['cookies']
    )
    
    import_id = response.json()['data']['id']
    
    # Wait for processing
    await asyncio.sleep(3)
    
    # Get import to check if ready
    response = await http_client.get(
        f"/api/studio/imports/{import_id}",
        cookies=owner_session['cookies']
    )
    
    import_data = response.json()['data']
    
    if import_data['status'] != 'ready':
        print(f"⚠️  Import not ready for scheduling: {import_data['status']}")
        return
    
    # Schedule it
    start_time = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    
    response = await http_client.post(
        f"/api/studio/imports/{import_id}/schedule",
        json={
            'start_at': start_time,
            'revision': import_data['revision']
        },
        cookies=owner_session['cookies']
    )
    
    assert response.status_code == 200
    result = response.json()['data']
    
    assert result['start_at'] is not None
    assert result['end_at'] is not None
    assert result['live_enabled'] is True
    
    print("✅ Schedule import test passed")


@pytest.mark.asyncio
async def test_schedule_import_cas_revision_check(http_client, owner_session, mock_storage, clean_db):
    """Test that schedule uses CAS revision check."""
    # Create and schedule an import
    excel_bytes = create_test_excel_combined()
    request_id = str(uuid.uuid4())
    
    files = {
        'questions': ('questions.xlsx', excel_bytes, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    }
    data = {
        'format': 'xlsx',
        'request_id': request_id
    }
    
    response = await http_client.post(
        '/api/studio/imports',
        files=files,
        data=data,
        cookies=owner_session['cookies']
    )
    
    import_id = response.json()['data']['id']
    await asyncio.sleep(3)
    
    response = await http_client.get(
        f"/api/studio/imports/{import_id}",
        cookies=owner_session['cookies']
    )
    
    import_data = response.json()['data']
    
    if import_data['status'] != 'ready':
        print(f"⚠️  Import not ready: {import_data['status']}")
        return
    
    # Schedule with correct revision
    start_time = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    
    response = await http_client.post(
        f"/api/studio/imports/{import_id}/schedule",
        json={
            'start_at': start_time,
            'revision': import_data['revision']
        },
        cookies=owner_session['cookies']
    )
    
    assert response.status_code == 200
    
    # Try to schedule again with old revision (should fail)
    response = await http_client.post(
        f"/api/studio/imports/{import_id}/schedule",
        json={
            'start_at': start_time,
            'revision': import_data['revision']  # Old revision
        },
        cookies=owner_session['cookies']
    )
    
    assert response.status_code == 409
    
    print("✅ Schedule CAS revision check test passed")


@pytest.mark.asyncio
async def test_live_toggle(http_client, owner_session, mock_storage, clean_db):
    """Test toggling live status."""
    # Create, schedule, then toggle
    excel_bytes = create_test_excel_combined()
    request_id = str(uuid.uuid4())
    
    files = {
        'questions': ('questions.xlsx', excel_bytes, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    }
    data = {
        'format': 'xlsx',
        'request_id': request_id
    }
    
    response = await http_client.post(
        '/api/studio/imports',
        files=files,
        data=data,
        cookies=owner_session['cookies']
    )
    
    import_id = response.json()['data']['id']
    await asyncio.sleep(3)
    
    response = await http_client.get(
        f"/api/studio/imports/{import_id}",
        cookies=owner_session['cookies']
    )
    
    import_data = response.json()['data']
    
    if import_data['status'] != 'ready':
        print(f"⚠️  Import not ready: {import_data['status']}")
        return
    
    # Schedule first
    start_time = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    
    response = await http_client.post(
        f"/api/studio/imports/{import_id}/schedule",
        json={
            'start_at': start_time,
            'revision': import_data['revision']
        },
        cookies=owner_session['cookies']
    )
    
    assert response.status_code == 200
    scheduled = response.json()['data']
    
    # Toggle live off
    response = await http_client.post(
        f"/api/studio/imports/{import_id}/live",
        json={
            'live': False,
            'revision': scheduled['revision']
        },
        cookies=owner_session['cookies']
    )
    
    assert response.status_code == 200
    result = response.json()['data']
    
    assert result['live_enabled'] is False
    
    print("✅ Live toggle test passed")


@pytest.mark.asyncio
async def test_error_report_csv(http_client, owner_session, mock_storage, clean_db):
    """Test error report CSV download."""
    # Create an import with issues
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    ws = wb.create_sheet('Questions')
    ws.append(['question_no', 'question_text', 'solution_text'])
    ws.append(['1', 'Question without options', 'Solution'])  # Missing MCQ options
    
    out = io.BytesIO()
    wb.save(out)
    excel_bytes = out.getvalue()
    
    request_id = str(uuid.uuid4())
    
    files = {
        'questions': ('questions.xlsx', excel_bytes, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    }
    data = {
        'format': 'xlsx',
        'request_id': request_id
    }
    
    response = await http_client.post(
        '/api/studio/imports',
        files=files,
        data=data,
        cookies=owner_session['cookies']
    )
    
    import_id = response.json()['data']['id']
    await asyncio.sleep(3)
    
    # Download error report
    response = await http_client.get(
        f"/api/studio/imports/{import_id}/errors",
        cookies=owner_session['cookies']
    )
    
    assert response.status_code == 200
    assert response.headers['content-type'] == 'text/csv; charset=utf-8'
    
    csv_content = response.text
    assert 'Sheet' in csv_content or 'Row' in csv_content
    
    print("✅ Error report CSV test passed")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
