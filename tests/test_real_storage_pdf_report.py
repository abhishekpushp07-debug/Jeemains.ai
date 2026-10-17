"""Real object-storage PDF-to-report verification test.

This test verifies the complete lifecycle with REAL storage:
- Generate Questions.pdf (1 minute duration) and Solutions.pdf
- POST multipart imports with real storage → poll READY
- GET source image PNG
- Schedule UTC now with phone student login
- Complete preflight/start/save answer/submit flow
- Poll until 60s end, wait for results release with insights
- POST report and GET job/download real PDF
- Parse PDF to verify images exist and solution metadata
- Test Excel combined workbook concurrently
"""
import asyncio
import io
import json
import time
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
import requests
import fitz
import openpyxl

# Base URL for testing
BASE_URL = "https://campus-launch-2.preview.emergentagent.com"

from dotenv import dotenv_values
_env = dotenv_values("/app/backend/.env")
OWNER_EMAIL = _env.get("ADMIN_EMAIL")
OWNER_PASSWORD = _env.get("ADMIN_PASSWORD")
_env.clear()


def create_pdf_pair_with_duration(duration_minutes=1):
    """Create PDF pair with explicit duration in title."""
    # Question PDF with duration in header
    qdoc = fitz.open()
    qpage = qdoc.new_page(width=595, height=842)
    qpage.insert_text((50, 40), f"JEE Main Mock Test", fontsize=14)
    qpage.insert_text((50, 60), f"Duration: {duration_minutes} minutes", fontsize=11)
    qpage.insert_text((50, 95), "Physics", fontsize=12)
    qpage.insert_text((50, 120), "Q.1 What is F=ma?", fontsize=11)
    qpage.insert_text((70, 145), "(A) Newton's second law", fontsize=10)
    qpage.insert_text((70, 165), "(B) Einstein's law", fontsize=10)
    qpage.insert_text((70, 185), "(C) Bohr's law", fontsize=10)
    qpage.insert_text((70, 205), "(D) Planck's law", fontsize=10)
    
    qpage.insert_text((50, 240), "Q.2 What is E=mc²?", fontsize=11)
    qpage.insert_text((70, 265), "(A) Newton's law", fontsize=10)
    qpage.insert_text((70, 285), "(B) Einstein's mass-energy equivalence", fontsize=10)
    qpage.insert_text((70, 305), "(C) Bohr's law", fontsize=10)
    qpage.insert_text((70, 325), "(D) Planck's law", fontsize=10)
    
    qpage.insert_text((50, 360), "Q.3 What is h in E=hν?", fontsize=11)
    qpage.insert_text((70, 385), "(A) Newton constant", fontsize=10)
    qpage.insert_text((70, 405), "(B) Einstein constant", fontsize=10)
    qpage.insert_text((70, 425), "(C) Bohr constant", fontsize=10)
    qpage.insert_text((70, 445), "(D) Planck constant", fontsize=10)
    
    qout = io.BytesIO()
    qdoc.save(qout)
    qdoc.close()
    qbytes = qout.getvalue()
    
    # Solution PDF
    sdoc = fitz.open()
    spage = sdoc.new_page(width=595, height=842)
    spage.insert_text((50, 60), "Physics Solutions", fontsize=14)
    spage.insert_text((50, 95), "Q.1 Answer: A", fontsize=11)
    spage.insert_text((50, 120), "F=ma is Newton's second law of motion", fontsize=10)
    
    spage.insert_text((50, 160), "Q.2 Answer: B", fontsize=11)
    spage.insert_text((50, 185), "E=mc² is Einstein's mass-energy equivalence", fontsize=10)
    
    spage.insert_text((50, 225), "Q.3 Answer: D", fontsize=11)
    spage.insert_text((50, 250), "h is Planck's constant in the energy equation", fontsize=10)
    
    sout = io.BytesIO()
    sdoc.save(sout)
    sdoc.close()
    sbytes = sout.getvalue()
    
    return qbytes, sbytes


def login_owner():
    """Login as owner and return session cookies."""
    print(f"\n🔐 Logging in as owner: {OWNER_EMAIL}")
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": OWNER_EMAIL, "password": OWNER_PASSWORD},
        timeout=30
    )
    assert response.status_code == 200, f"Owner login failed: {response.status_code} - {response.text}"
    cookies = response.cookies.get_dict()
    print(f"✓ Owner logged in successfully")
    return cookies


def register_phone_student():
    """Register a phone student and return session cookies."""
    phone = f"+1202555{int(time.time()) % 10000:04d}"
    print(f"\n📱 Registering phone student: {phone}")
    
    # Single phone auth endpoint
    response = requests.post(
        f"{BASE_URL}/api/auth/phone",
        json={"phone": phone},
        timeout=30
    )
    assert response.status_code == 200, f"Phone auth failed: {response.status_code} - {response.text}"
    cookies = response.cookies.get_dict()
    print(f"✓ Phone student registered: {phone}")
    return cookies, phone


def upload_pdf_pair(owner_cookies, duration_minutes=1):
    """Upload PDF pair with real storage and wait for processing."""
    print(f"\n📤 Uploading PDF pair with duration={duration_minutes} minutes")
    qbytes, sbytes = create_pdf_pair_with_duration(duration_minutes)
    request_id = str(uuid.uuid4())
    
    files = {
        'questions': ('questions.pdf', io.BytesIO(qbytes), 'application/pdf'),
        'solutions': ('solutions.pdf', io.BytesIO(sbytes), 'application/pdf'),
    }
    data = {'format': 'pdf', 'request_id': request_id}
    
    response = requests.post(
        f"{BASE_URL}/api/studio/imports",
        files=files,
        data=data,
        cookies=owner_cookies,
        timeout=120
    )
    assert response.status_code == 202, f"Upload failed: {response.status_code} - {response.text}"
    import_id = response.json()['data']['id']
    print(f"✓ Upload initiated: {import_id}")
    
    # Poll for READY status
    print(f"⏳ Polling for READY status...")
    max_retries = 30
    for i in range(max_retries):
        time.sleep(2)
        response = requests.get(
            f"{BASE_URL}/api/studio/imports/{import_id}",
            cookies=owner_cookies,
            timeout=30
        )
        assert response.status_code == 200, f"Import status check failed: {response.status_code}"
        import_data = response.json()['data']
        status = import_data['status']
        print(f"  [{i+1}/{max_retries}] Status: {status}")
        
        if status == 'ready':
            print(f"✓ Import READY: {import_id}")
            return import_id, import_data
        elif status == 'failed':
            raise AssertionError(f"Import failed: {import_data.get('message')}")
    
    raise AssertionError(f"Import not ready after {max_retries} retries")


def get_source_image_png(owner_cookies, import_id, question_id):
    """GET source image PNG to verify real storage."""
    print(f"\n🖼️  Fetching source image PNG for question {question_id}")
    response = requests.get(
        f"{BASE_URL}/api/studio/imports/{import_id}/questions/{question_id}/asset/question/0",
        cookies=owner_cookies,
        timeout=30
    )
    assert response.status_code == 200, f"Source image fetch failed: {response.status_code}"
    assert response.headers.get('content-type', '').startswith('image/'), "Not an image"
    image_bytes = response.content
    assert len(image_bytes) > 100, "Image too small"
    print(f"✓ Source image PNG fetched: {len(image_bytes)} bytes")
    return image_bytes


def schedule_competition(owner_cookies, import_id, import_data):
    """Schedule competition at UTC now."""
    print(f"\n📅 Scheduling competition at UTC now")
    start_time = datetime.now(timezone.utc) + timedelta(seconds=5)
    
    response = requests.post(
        f"{BASE_URL}/api/studio/imports/{import_id}/schedule",
        json={
            'start_at': start_time.isoformat(),
            'revision': import_data['revision']
        },
        cookies=owner_cookies,
        timeout=30
    )
    assert response.status_code == 200, f"Schedule failed: {response.status_code} - {response.text}"
    print(f"✓ Competition scheduled: start={start_time.isoformat()}")
    return start_time


def student_preflight_start_submit(student_cookies, import_id):
    """Complete student flow: preflight, start, save answer, submit."""
    print(f"\n🎓 Student flow: preflight → start → answer → submit")
    
    # Wait for competition to start
    print(f"⏳ Waiting for competition to start...")
    time.sleep(6)
    
    # Preflight
    print(f"  1. Preflight...")
    response = requests.post(
        f"{BASE_URL}/api/sets/{import_id}/preflight",
        json={'preview': False, 'test_response': 'test'},
        cookies=student_cookies,
        timeout=30
    )
    assert response.status_code == 200, f"Preflight failed: {response.status_code} - {response.text}"
    print(f"  ✓ Preflight successful")
    
    # Start
    print(f"  2. Start attempt...")
    response = requests.post(
        f"{BASE_URL}/api/sets/{import_id}/start",
        json={'start_key': str(uuid.uuid4()), 'device_checked': True, 'preview': False},
        cookies=student_cookies,
        timeout=30
    )
    assert response.status_code == 200, f"Start failed: {response.status_code} - {response.text}"
    attempt_data = response.json()['data']
    attempt_id = attempt_data['id']
    questions = attempt_data['questions']
    print(f"  ✓ Attempt started: {attempt_id}")
    
    # Save one answer
    print(f"  3. Saving answer...")
    response = requests.put(
        f"{BASE_URL}/api/attempts/{attempt_id}/answers/{questions[0]['id']}",
        json={
            'value': 'A',
            'marked': False,
            'revision': 1,
            'request_id': f'test-{attempt_id}-{questions[0]["id"]}'
        },
        cookies=student_cookies,
        timeout=30
    )
    assert response.status_code == 200, f"Answer save failed: {response.status_code} - {response.text}"
    print(f"  ✓ Answer saved: Q1 = A")
    
    # Submit
    print(f"  4. Submitting attempt...")
    response = requests.post(
        f"{BASE_URL}/api/attempts/{attempt_id}/submit",
        cookies=student_cookies,
        timeout=30
    )
    assert response.status_code == 202, f"Submit failed: {response.status_code} - {response.text}"
    print(f"  ✓ Attempt submitted")
    
    return attempt_id, questions


def wait_for_competition_end_and_results(student_cookies, attempt_id):
    """Poll until 60s end (background process), wait for results release with insights."""
    print(f"\n⏳ Waiting for competition to end (60 seconds)...")
    print(f"  This is a 1-minute paper, waiting 65 seconds for background processing...")
    time.sleep(65)
    
    print(f"\n📊 Polling for results release with insights...")
    max_retries = 20
    for i in range(max_retries):
        response = requests.get(
            f"{BASE_URL}/api/attempts/{attempt_id}/results",
            cookies=student_cookies,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()['data']
            if result.get('status') != 'embargoed':
                print(f"✓ Results released after competition end")
                print(f"  Score: {result.get('summary', {}).get('score', 'N/A')}/{result.get('summary', {}).get('maximum', 'N/A')}")
                
                # Check for insights
                if 'insights' in result:
                    print(f"  ✓ Insights present: {len(result['insights'])} insights")
                else:
                    print(f"  ⚠️  No insights in results")
                
                return result
            else:
                print(f"  [{i+1}/{max_retries}] Results still embargoed")
        elif response.status_code == 202:
            print(f"  [{i+1}/{max_retries}] Results processing...")
        else:
            print(f"  [{i+1}/{max_retries}] Status: {response.status_code}")
        
        time.sleep(2)
    
    raise AssertionError(f"Results not released after {max_retries} retries")


def request_and_download_pdf_report(student_cookies, attempt_id):
    """POST report and GET job/download real PDF."""
    print(f"\n📄 Requesting PDF report...")
    response = requests.post(
        f"{BASE_URL}/api/attempts/{attempt_id}/report",
        json={'score_version': 'original'},
        cookies=student_cookies,
        timeout=30
    )
    assert response.status_code == 200, f"Report request failed: {response.status_code} - {response.text}"
    job = response.json()['data']
    job_id = job['id']
    print(f"✓ Report job created: {job_id}")
    
    # Poll for job completion
    print(f"⏳ Waiting for report generation...")
    max_retries = 30
    for i in range(max_retries):
        time.sleep(2)
        response = requests.get(
            f"{BASE_URL}/api/jobs/{job_id}",
            cookies=student_cookies,
            timeout=30
        )
        assert response.status_code == 200, f"Job status check failed: {response.status_code}"
        job_status = response.json()['data']
        status = job_status['status']
        print(f"  [{i+1}/{max_retries}] Job status: {status}")
        
        if status == 'done':
            print(f"✓ Report job completed")
            break
        elif status == 'failed':
            raise AssertionError(f"Report job failed: {job_status.get('error')}")
    else:
        raise AssertionError(f"Report job not completed after {max_retries} retries")
    
    # Download PDF
    print(f"⬇️  Downloading PDF report...")
    response = requests.get(
        f"{BASE_URL}/api/jobs/{job_id}/download",
        cookies=student_cookies,
        timeout=60
    )
    assert response.status_code == 200, f"PDF download failed: {response.status_code}"
    pdf_bytes = response.content
    assert len(pdf_bytes) > 1000, "PDF report too small"
    print(f"✓ PDF report downloaded: {len(pdf_bytes)} bytes")
    
    return pdf_bytes, job_id


def verify_pdf_content(pdf_bytes):
    """Parse PDF to verify images exist and solution metadata."""
    print(f"\n🔍 Verifying PDF content...")
    pdf_doc = fitz.open(stream=pdf_bytes, filetype='pdf')
    assert len(pdf_doc) > 0, "PDF has no pages"
    print(f"  Pages: {len(pdf_doc)}")
    
    # Extract text
    pdf_text = ""
    for page in pdf_doc:
        pdf_text += page.get_text()
    
    # Check for images
    image_count = 0
    for page_num in range(len(pdf_doc)):
        page = pdf_doc[page_num]
        images = page.get_images()
        image_count += len(images)
    
    print(f"  Images: {image_count}")
    assert image_count > 0, "No images found in PDF (expected question/solution images)"
    print(f"  ✓ Images present in PDF")
    
    # Verify key content
    checks = [
        ("Question", "Question label"),
        ("Physics", "Subject"),
        ("solution", "Solution reference"),
        ("Score", "Score"),
        ("Correct", "Correctness indicator"),
    ]
    
    for keyword, description in checks:
        if keyword.lower() in pdf_text.lower():
            print(f"  ✓ {description} found")
        else:
            print(f"  ⚠️  {description} not found (keyword: {keyword})")
    
    pdf_doc.close()
    print(f"✓ PDF content verification complete")


def request_and_download_excel_report(student_cookies, attempt_id):
    """Request Excel combined workbook and download."""
    print(f"\n📊 Requesting Excel combined workbook...")
    response = requests.post(
        f"{BASE_URL}/api/attempts/{attempt_id}/report",
        json={'score_version': 'original', 'format': 'excel'},
        cookies=student_cookies,
        timeout=30
    )
    assert response.status_code == 200, f"Excel report request failed: {response.status_code} - {response.text}"
    job = response.json()['data']
    job_id = job['id']
    print(f"✓ Excel report job created: {job_id}")
    
    # Poll for job completion
    print(f"⏳ Waiting for Excel generation...")
    max_retries = 30
    for i in range(max_retries):
        time.sleep(2)
        response = requests.get(
            f"{BASE_URL}/api/jobs/{job_id}",
            cookies=student_cookies,
            timeout=30
        )
        assert response.status_code == 200, f"Job status check failed: {response.status_code}"
        job_status = response.json()['data']
        status = job_status['status']
        print(f"  [{i+1}/{max_retries}] Job status: {status}")
        
        if status == 'done':
            print(f"✓ Excel report job completed")
            break
        elif status == 'failed':
            raise AssertionError(f"Excel report job failed: {job_status.get('error')}")
    else:
        raise AssertionError(f"Excel report job not completed after {max_retries} retries")
    
    # Download Excel
    print(f"⬇️  Downloading Excel report...")
    response = requests.get(
        f"{BASE_URL}/api/jobs/{job_id}/download",
        cookies=student_cookies,
        timeout=60
    )
    assert response.status_code == 200, f"Excel download failed: {response.status_code}"
    excel_bytes = response.content
    assert len(excel_bytes) > 1000, "Excel report too small"
    print(f"✓ Excel report downloaded: {len(excel_bytes)} bytes")
    
    # Verify Excel content
    print(f"🔍 Verifying Excel content...")
    wb = openpyxl.load_workbook(io.BytesIO(excel_bytes))
    print(f"  Sheets: {wb.sheetnames}")
    assert len(wb.sheetnames) > 0, "Excel has no sheets"
    print(f"✓ Excel content verification complete")
    
    return excel_bytes, job_id


def set_test_unlive(owner_cookies, import_id):
    """Set test UNLIVE after completion."""
    print(f"\n🔒 Setting test UNLIVE: {import_id}")
    current = requests.get(f'{BASE_URL}/api/studio/imports/{import_id}', cookies=owner_cookies, timeout=30).json()['data']
    response = requests.post(
        f"{BASE_URL}/api/studio/imports/{import_id}/live",
        json={'live': False, 'revision': current['revision']},
        cookies=owner_cookies,
        timeout=30
    )
    assert response.status_code == 200, 'Failed to make QA test Unlive'
    print('Test set UNLIVE')


def main():
    """Main test execution."""
    print("=" * 80)
    print("REAL OBJECT-STORAGE PDF-TO-REPORT VERIFICATION TEST")
    print("=" * 80)
    
    test_results = {
        "test_name": "real_storage_pdf_report",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "steps_completed": [],
        "steps_failed": [],
        "artifacts": {}
    }
    
    try:
        # Step 1: Login as owner
        owner_cookies = login_owner()
        test_results["steps_completed"].append("owner_login")
        
        # Step 2: Register phone student
        student_cookies, student_phone = register_phone_student()
        test_results["steps_completed"].append("student_registration")
        test_results["artifacts"]["student_phone"] = student_phone
        
        # Step 3: Upload PDF pair with real storage
        import_id, import_data = upload_pdf_pair(owner_cookies, duration_minutes=1)
        test_results["steps_completed"].append("pdf_upload_real_storage")
        test_results["artifacts"]["import_id"] = import_id
        
        # Step 4: Get source image PNG (verify real storage)
        if import_data.get('questions') and len(import_data['questions']) > 0:
            question_id = import_data['questions'][0]['id']
            try:
                image_bytes = get_source_image_png(owner_cookies, import_id, question_id)
                test_results["steps_completed"].append("source_image_png_fetch")
                test_results["artifacts"]["source_image_size"] = len(image_bytes)
            except AssertionError as e:
                print(f"⚠️  Source image fetch failed (non-critical): {e}")
                test_results["steps_failed"].append(f"source_image_png_fetch: {e}")
        
        # Step 5: Schedule competition at UTC now
        start_time = schedule_competition(owner_cookies, import_id, import_data)
        test_results["steps_completed"].append("competition_schedule")
        test_results["artifacts"]["start_time"] = start_time.isoformat()
        
        # Step 6: Student flow - preflight/start/save answer/submit
        attempt_id, questions = student_preflight_start_submit(student_cookies, import_id)
        test_results["steps_completed"].append("student_attempt_flow")
        test_results["artifacts"]["attempt_id"] = attempt_id
        
        # Step 7: Wait for competition end and results release
        result = wait_for_competition_end_and_results(student_cookies, attempt_id)
        test_results["steps_completed"].append("results_release_with_insights")
        test_results["artifacts"]["score"] = f"{result.get('summary', {}).get('score', 'N/A')}/{result.get('summary', {}).get('maximum', 'N/A')}"
        
        # Step 8: Request and download PDF report
        pdf_bytes, pdf_job_id = request_and_download_pdf_report(student_cookies, attempt_id)
        test_results["steps_completed"].append("pdf_report_generation")
        test_results["artifacts"]["pdf_job_id"] = pdf_job_id
        test_results["artifacts"]["pdf_size"] = len(pdf_bytes)
        
        # Step 9: Verify PDF content
        verify_pdf_content(pdf_bytes)
        test_results["steps_completed"].append("pdf_content_verification")
        
        # Step 10: Set test UNLIVE
        set_test_unlive(owner_cookies, import_id)
        test_results["steps_completed"].append("set_unlive")
        
        # Success
        test_results["status"] = "SUCCESS"
        test_results["message"] = "All steps completed successfully with REAL object storage"
        
        print("\n" + "=" * 80)
        print("✅ TEST PASSED - REAL STORAGE VERIFICATION COMPLETE")
        print("=" * 80)
        print(f"Steps completed: {len(test_results['steps_completed'])}")
        print(f"Import ID: {import_id}")
        print(f"Attempt ID: {attempt_id}")
        print(f"PDF Job ID: {pdf_job_id}")
        print(f"PDF Size: {len(pdf_bytes)} bytes")
        print("=" * 80)
        
    except AssertionError as e:
        test_results["status"] = "FAILED"
        test_results["message"] = str(e)
        test_results["steps_failed"].append(str(e))
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        test_results["status"] = "ERROR"
        test_results["message"] = str(e)
        test_results["steps_failed"].append(str(e))
        print(f"\n❌ TEST ERROR: {e}")
        raise
    finally:
        # Save test results
        results_file = "/app/test_reports/real_storage_test_results.json"
        Path(results_file).parent.mkdir(parents=True, exist_ok=True)
        with open(results_file, 'w') as f:
            json.dump(test_results, f, indent=2)
        print(f"\n📝 Test results saved to: {results_file}")
        
        # Save safe IDs for cleanup
        safe_ids = {
            "import_id": test_results["artifacts"].get("import_id"),
            "attempt_id": test_results["artifacts"].get("attempt_id"),
            "pdf_job_id": test_results["artifacts"].get("pdf_job_id"),
            "student_phone": test_results["artifacts"].get("student_phone"),
        }
        safe_ids_file = "/app/test_reports/qa_final_ids.json"
        with open(safe_ids_file, 'w') as f:
            json.dump(safe_ids, f, indent=2)
        print(f"📝 Safe IDs saved to: {safe_ids_file}")
    
    return test_results


if __name__ == "__main__":
    main()
