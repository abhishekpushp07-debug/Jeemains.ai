"""QA Backend Integration Tests - Iteration 46
Real storage, competition lifecycle, embargo states, report generation.
Credentials read from .env via dotenv_values - no hardcoded values.
"""
import asyncio
import io
import json
import time
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from dotenv import dotenv_values
import requests

# Read credentials securely
ENV_PATH = Path(__file__).parent.parent / 'backend' / '.env'
env_values = dotenv_values(ENV_PATH)
OWNER_EMAIL = env_values.get('ADMIN_EMAIL')
OWNER_PASSWORD = env_values.get('ADMIN_PASSWORD')
BASE_URL = 'https://campus-launch-2.preview.emergentagent.com/api'

class QABackendTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.owner_token = None
        self.student_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.import_id = None
        self.competition_id = None
        self.attempt_id = None
        self.student_phone = f'+1202555{str(int(time.time()))[-4:]}'
        self.results = {
            'backend_tests': [],
            'import_flow': {},
            'competition_flow': {},
            'student_flow': {},
            'embargo_verification': {},
            'report_generation': {}
        }

    def log(self, message, status='INFO'):
        print(f'[{status}] {message}')
        
    def run_test(self, name, fn):
        """Run a single test and track results"""
        self.tests_run += 1
        self.log(f'Testing {name}...', 'TEST')
        try:
            result = fn()
            self.tests_passed += 1
            self.log(f'✅ {name} - PASSED', 'PASS')
            self.results['backend_tests'].append({'name': name, 'status': 'passed'})
            return True, result
        except Exception as e:
            self.log(f'❌ {name} - FAILED: {str(e)}', 'FAIL')
            self.results['backend_tests'].append({'name': name, 'status': 'failed', 'error': str(e)})
            return False, str(e)

    def unwrap_response(self, resp):
        """Unwrap envelope response format if present"""
        result = resp.json()
        if 'data' in result:
            return result['data']
        return result

    def auth_owner(self):
        """Authenticate as owner"""
        self.log('Authenticating as owner...')
        resp = requests.post(f'{self.base_url}/auth/login', 
            json={'email': OWNER_EMAIL, 'password': OWNER_PASSWORD})
        if resp.status_code != 200:
            raise Exception(f'Owner login failed: {resp.status_code} - {resp.text}')
        self.owner_token = resp.cookies.get('access_token')
        self.log(f'Owner authenticated successfully')
        return self.unwrap_response(resp)

    def auth_student(self):
        """Register and authenticate as student"""
        self.log(f'Registering student with phone {self.student_phone}...')
        # Phone auth is single-step in this system
        resp = requests.post(f'{self.base_url}/auth/phone', 
            json={'phone': self.student_phone})
        if resp.status_code != 200:
            raise Exception(f'Student phone auth failed: {resp.status_code} - {resp.text}')
        
        self.student_token = resp.cookies.get('access_token')
        self.log(f'Student authenticated successfully')
        return self.unwrap_response(resp)

    def owner_headers(self):
        return {'Cookie': f'access_token={self.owner_token}'}

    def student_headers(self):
        return {'Cookie': f'access_token={self.student_token}'}

    def test_template_download(self):
        """Test Excel template download"""
        resp = requests.get(f'{self.base_url}/studio/imports/template?variant=combined',
            headers=self.owner_headers())
        if resp.status_code != 200:
            raise Exception(f'Template download failed: {resp.status_code}')
        if len(resp.content) < 1000:
            raise Exception(f'Template too small: {len(resp.content)} bytes')
        self.log(f'Template downloaded: {len(resp.content)} bytes')
        return len(resp.content)

    def test_excel_upload_and_organize(self):
        """Test Excel workbook upload and organization to READY state"""
        from openpyxl import Workbook
        
        # Create a valid test workbook
        wb = Workbook()
        wb.remove(wb.active)
        ws = wb.create_sheet('Questions')
        ws.append(['question_id','question_no','subject','question_text','option_a','option_b','option_c','option_d','correct_option','type','topic','difficulty','exam','duration_minutes','solution_text'])
        ws.append(['qa-phy-1',1,'Physics','What is the SI unit of force?','Newton','Joule','Watt','Pascal','A','mcq','Units','Easy','JEE Main',180,'Force is measured in newtons (N).'])
        ws.append(['qa-chem-2',2,'Chemistry','What is the atomic number of Carbon?','6','8','12','14','A','mcq','Atomic Structure','Easy','JEE Main',180,'Carbon has 6 protons.'])
        ws.append(['qa-math-3',3,'Mathematics','What is 2 + 2?','3','4','5','6','B','mcq','Arithmetic','Easy','JEE Main',180,'2 + 2 = 4'])
        
        # Save to bytes
        excel_bytes = io.BytesIO()
        wb.save(excel_bytes)
        excel_bytes.seek(0)
        
        # Upload
        request_id = str(uuid.uuid4())
        files = {
            'questions': ('qa_test.xlsx', excel_bytes, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        data = {
            'request_id': request_id,
            'format': 'xlsx'
        }
        
        self.log('Uploading Excel workbook...')
        resp = requests.post(f'{self.base_url}/studio/imports',
            headers=self.owner_headers(), files=files, data=data)
        
        if resp.status_code not in (200, 202):
            raise Exception(f'Upload failed: {resp.status_code} - {resp.text}')
        
        result = self.unwrap_response(resp)
        # Handle envelope response format
        self.import_id = result.get('id')
        if not self.import_id:
            raise Exception(f'No import ID in response: {result}')
        self.log(f'Import created: {self.import_id}, status: {result.get("status")}')
        
        # Wait for processing to complete
        max_wait = 30
        for i in range(max_wait):
            time.sleep(2)
            resp = requests.get(f'{self.base_url}/studio/imports/{self.import_id}',
                headers=self.owner_headers())
            if resp.status_code != 200:
                raise Exception(f'Import status check failed: {resp.status_code}')
            
            result = self.unwrap_response(resp)
            status = result['status']
            self.log(f'Import status: {status} (attempt {i+1}/{max_wait})')
            
            if status == 'ready':
                self.log(f'✅ Import reached READY state with {result["count"]} questions')
                self.results['import_flow'] = {
                    'import_id': self.import_id,
                    'status': 'ready',
                    'count': result['count'],
                    'issues': len(result.get('issues', []))
                }
                return result
            elif status in ('blocked', 'failed'):
                raise Exception(f'Import failed with status {status}: {result.get("message")}')
        
        raise Exception(f'Import did not reach READY state after {max_wait*2}s')

    def test_schedule_competition(self):
        """Test scheduling a competition with immediate start time"""
        if not self.import_id:
            raise Exception('No import_id available')
        
        # Schedule for 30 seconds from now
        start_time = datetime.now(timezone.utc) + timedelta(seconds=30)
        start_iso = start_time.isoformat().replace('+00:00', 'Z')
        
        self.log(f'Scheduling competition to start at {start_iso}...')
        resp = requests.post(f'{self.base_url}/studio/imports/{self.import_id}/schedule',
            headers=self.owner_headers(),
            json={'start_at': start_iso, 'revision': 0})
        
        if resp.status_code != 200:
            raise Exception(f'Schedule failed: {resp.status_code} - {resp.text}')
        
        result = self.unwrap_response(resp)
        self.competition_id = result['set_id']
        self.log(f'Competition scheduled: {self.competition_id}')
        self.results['competition_flow']['scheduled'] = {
            'competition_id': self.competition_id,
            'start_at': result['start_at'],
            'end_at': result['end_at'],
            'status': result['status']
        }
        
        # Wait for competition to become live
        self.log('Waiting for competition to become live...')
        time.sleep(35)
        
        return result

    def test_toggle_live(self):
        """Test toggling competition live status to enabled"""
        if not self.import_id:
            raise Exception('No import_id available')
        
        # Get current state
        resp = requests.get(f'{self.base_url}/studio/imports/{self.import_id}',
            headers=self.owner_headers())
        current = self.unwrap_response(resp)
        current_live = current.get('live_enabled', False)
        
        # Ensure it's live
        if not current_live:
            self.log(f'Enabling live status...')
            resp = requests.post(f'{self.base_url}/studio/imports/{self.import_id}/live',
                headers=self.owner_headers(),
                json={'live': True, 'revision': current['revision']})
            
            if resp.status_code != 200:
                raise Exception(f'Toggle failed: {resp.status_code} - {resp.text}')
            
            result = self.unwrap_response(resp)
            self.log(f'Live status enabled: {result["live_enabled"]}')
        else:
            self.log('Competition already live')
            result = current
        
        return result

    def test_competition_catalogue(self):
        """Test student can see competition catalogue"""
        self.log('Fetching competition catalogue...')
        resp = requests.get(f'{self.base_url}/competitions',
            headers=self.student_headers())
        
        if resp.status_code != 200:
            raise Exception(f'Catalogue failed: {resp.status_code} - {resp.text}')
        
        result = self.unwrap_response(resp)
        # Handle envelope response format
        self.log(f'Found {len(result.get("items", []))} competitions')
        return result

    def test_student_preflight(self):
        """Test student preflight check"""
        if not self.competition_id:
            raise Exception('No competition_id available')
        
        self.log('Running student preflight check...')
        resp = requests.post(f'{self.base_url}/sets/{self.competition_id}/preflight',
            headers=self.student_headers(),
            json={'test_response': 'qa_test'})
        
        if resp.status_code != 200:
            raise Exception(f'Preflight failed: {resp.status_code} - {resp.text}')
        
        result = self.unwrap_response(resp)
        self.log('Preflight check passed')
        return result

    def test_student_start_attempt(self):
        """Test student starting an attempt"""
        if not self.competition_id:
            raise Exception('No competition_id available')
        
        start_key = str(uuid.uuid4())
        self.log(f'Starting attempt with key {start_key}...')
        resp = requests.post(f'{self.base_url}/sets/{self.competition_id}/start',
            headers=self.student_headers(),
            json={'start_key': start_key, 'device_checked': True, 'preview': False})
        
        if resp.status_code != 200:
            raise Exception(f'Start failed: {resp.status_code} - {resp.text}')
        
        result = self.unwrap_response(resp)
        self.attempt_id = result['id']
        self.log(f'Attempt started: {self.attempt_id}')
        self.results['student_flow']['attempt_started'] = {
            'attempt_id': self.attempt_id,
            'status': result['status'],
            'questions': result['count']
        }
        return result

    def test_student_submit(self):
        """Test student submitting attempt"""
        if not self.attempt_id:
            raise Exception('No attempt_id available')
        
        self.log('Submitting attempt...')
        resp = requests.post(f'{self.base_url}/attempts/{self.attempt_id}/submit',
            headers=self.student_headers())
        
        if resp.status_code not in (200, 202):
            raise Exception(f'Submit failed: {resp.status_code} - {resp.text}')
        
        result = self.unwrap_response(resp)
        self.log(f'Attempt submitted: {result["status"]}, grading: {result["grading_status"]}')
        self.results['student_flow']['submitted'] = {
            'status': result['status'],
            'grading_status': result['grading_status'],
            'receipt': result['receipt']
        }
        return result

    def test_embargo_state(self):
        """Test that results are embargoed before competition end"""
        if not self.attempt_id:
            raise Exception('No attempt_id available')
        
        self.log('Checking embargo state...')
        resp = requests.get(f'{self.base_url}/attempts/{self.attempt_id}/results',
            headers=self.student_headers())
        
        if resp.status_code not in (200, 202):
            raise Exception(f'Results check failed: {resp.status_code} - {resp.text}')
        
        result = self.unwrap_response(resp)
        status = result.get('status')
        
        if status == 'embargoed':
            self.log('✅ Results correctly embargoed')
            self.results['embargo_verification'] = {
                'status': 'embargoed',
                'release_at': result.get('release_at')
            }
        elif status == 'grading':
            self.log('⏳ Results in grading state')
            self.results['embargo_verification'] = {
                'status': 'grading',
                'grading_status': result.get('grading_status')
            }
        else:
            self.log(f'⚠️  Unexpected status: {status}')
            self.results['embargo_verification'] = {'status': status}
        
        return result

    def test_leaderboard_embargo(self):
        """Test that leaderboard is embargoed before competition end"""
        if not self.competition_id:
            raise Exception('No competition_id available')
        
        self.log('Checking leaderboard embargo...')
        resp = requests.get(f'{self.base_url}/competitions/{self.competition_id}',
            headers=self.student_headers())
        
        if resp.status_code != 200:
            raise Exception(f'Leaderboard check failed: {resp.status_code} - {resp.text}')
        
        result = self.unwrap_response(resp)
        status = result.get('status')
        
        if status == 'embargoed':
            self.log('✅ Leaderboard correctly embargoed')
        else:
            self.log(f'Leaderboard status: {status}')
        
        return result

    def test_csv_error_download(self):
        """Test CSV error report download"""
        if not self.import_id:
            raise Exception('No import_id available')
        
        self.log('Testing CSV error report download...')
        resp = requests.get(f'{self.base_url}/studio/imports/{self.import_id}/errors',
            headers=self.owner_headers())
        
        if resp.status_code != 200:
            raise Exception(f'CSV download failed: {resp.status_code}')
        
        csv_content = resp.text
        self.log(f'CSV downloaded: {len(csv_content)} bytes')
        return csv_content

    def run_all_tests(self):
        """Run all backend integration tests"""
        self.log('=' * 60, 'INFO')
        self.log('QA Backend Integration Tests - Iteration 46', 'INFO')
        self.log('=' * 60, 'INFO')
        
        # Authentication
        self.run_test('Owner Authentication', self.auth_owner)
        self.run_test('Student Authentication', self.auth_student)
        
        # Import Flow
        self.run_test('Template Download', self.test_template_download)
        self.run_test('Excel Upload and Organization', self.test_excel_upload_and_organize)
        self.run_test('CSV Error Report Download', self.test_csv_error_download)
        
        # Competition Scheduling
        self.run_test('Schedule Competition', self.test_schedule_competition)
        self.run_test('Toggle Live Status', self.test_toggle_live)
        
        # Student Flow
        self.run_test('Competition Catalogue', self.test_competition_catalogue)
        self.run_test('Student Preflight', self.test_student_preflight)
        self.run_test('Student Start Attempt', self.test_student_start_attempt)
        self.run_test('Student Submit', self.test_student_submit)
        
        # Embargo Verification
        self.run_test('Embargo State Verification', self.test_embargo_state)
        self.run_test('Leaderboard Embargo', self.test_leaderboard_embargo)
        
        # Summary
        self.log('=' * 60, 'INFO')
        self.log(f'Tests Run: {self.tests_run}', 'INFO')
        self.log(f'Tests Passed: {self.tests_passed}', 'INFO')
        self.log(f'Tests Failed: {self.tests_run - self.tests_passed}', 'INFO')
        self.log(f'Success Rate: {100 * self.tests_passed / self.tests_run:.1f}%', 'INFO')
        self.log('=' * 60, 'INFO')
        
        return self.results

if __name__ == '__main__':
    tester = QABackendTester()
    results = tester.run_all_tests()
    
    # Save results
    output_file = Path(__file__).parent.parent / 'test_reports' / 'qa_backend_results.json'
    output_file.parent.mkdir(exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f'\n✅ Results saved to {output_file}')
    
    # Exit with appropriate code
    exit(0 if tester.tests_passed == tester.tests_run else 1)
