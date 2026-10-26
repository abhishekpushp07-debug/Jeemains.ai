import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright

OLD = Path('/app/frontend/public/downloads/app-integration')
NEW = Path('/app/frontend/public/downloads/app-pin-integration')
BASE = 'https://jeelive.ai'


def main():
    spec = json.loads((NEW / 'evidence/canonical-api-contract.json').read_text())
    pyq = json.loads((NEW / 'evidence/canonical-pyq.json').read_text())
    assert spec['pin_signup_route_live'] and spec['pin_change_route_live']
    assert spec['live_nonmutating_checks']['phone_without_pin'] == 422
    assert spec['live_nonmutating_checks']['anonymous_student_directory'] == 401
    assert pyq['total'] == 30 and pyq['questions'] == 2250
    for name in ('assets', 'references', 'reference-css'):
        shutil.copytree(OLD / name, NEW / name, dirs_exist_ok=True)
    shutil.copy2(OLD / 'design-tokens.json', NEW / 'design-tokens.json')
    shutil.copy2(OLD / 'evidence/isolated-two-session-proof.json', NEW / 'evidence/isolated-two-session-proof.json')
    shutil.copy2('/app/docs/APP_INTEGRATION.md', NEW / 'APP_INTEGRATION.md')
    shutil.copy2('/app/docs/NATIVE_PIN_UPDATE.md', NEW / 'NATIVE_PIN_UPDATE.md')
    refs = NEW / 'references/pin-live'
    refs.mkdir(parents=True, exist_ok=True)
    checks = []
    with sync_playwright() as p:
        browser = p.chromium.launch(args=['--no-sandbox'])
        page = browser.new_page()
        for route in ('login', 'signup'):
            for width in (1920, 390):
                page.set_viewport_size({'width': 1920, 'height': 800} if width == 1920 else {'width': 390, 'height': 844})
                page.goto(BASE + '/' + route, wait_until='networkidle', timeout=60000)
                page.locator('[data-testid="student-pin-input"]').wait_for()
                page.evaluate('document.fonts.ready')
                if route == 'signup':
                    page.locator('[data-testid="student-confirm-pin-input"]').wait_for()
                if width == 390:
                    page.locator('[data-testid="auth-title"]').scroll_into_view_if_needed()
                shot = refs / f'{route}-{width}.jpeg'
                page.screenshot(path=str(shot), full_page=False, quality=40)
                overflow = page.evaluate("() => [...document.querySelectorAll('*')].filter(e=>e.getBoundingClientRect().right>innerWidth+1).slice(0,5).map(e=>e.className||e.tagName)")
                assert not overflow, (route, width, overflow)
                checks.append({'url': page.url, 'viewport': {'width': width, 'height': 800 if width == 1920 else 844},
                               'pin_field_visible': page.locator('[data-testid="student-pin-input"]').is_visible(),
                               'confirm_pin_field_present': bool(page.locator('[data-testid="student-confirm-pin-input"]').count()),
                               'horizontal_overflow': overflow, 'screenshot': str(shot.relative_to(NEW))})
                print('LIVE_FORM', route, width, 'PASS')
        browser.close()
    proof = {'checked_at': datetime.now(timezone.utc).isoformat(), 'api_base': BASE + '/api',
             'status': 'LIVE_PIN_CONTRACT_AND_GUEST_UI_VERIFIED', 'live_schema_checks': {
                 'pin_signup_route_live': spec['pin_signup_route_live'], 'pin_change_route_live': spec['pin_change_route_live'],
                 'student_directory_route_live': '/api/admin/students' in spec['paths']},
             'live_nonmutating_checks': spec['live_nonmutating_checks'], 'live_forms': checks,
             'live_pyq_count': pyq['total'], 'live_pyq_question_count': pyq['questions'],
             'live_pyq_verification_role': 'authorised owner on same canonical catalogue endpoint',
             'test_accounts_created': 0, 'test_attempts_created': 0, 'private_data_exported': False,
             'limitations': ['No production student signup/PIN change was performed for QA; functional real-auth flows passed in disposable isolated databases.',
                            'Actual Expo device login/cookie persistence and cross-device identity/result comparison remain for the native agent.',
                            'Existing account without a valid session and without a PIN has no public claim/reset flow.',
                            'Private ingress client-IP protection still requires trusted proxy configuration; per-number limits and auth concurrency are active.']}
    (NEW / 'evidence/live-pin-verification.json').write_text(json.dumps(proof, indent=2) + '\n')
    (NEW / 'README.md').write_text('''# JEELIVE PIN live integration package

PIN login and signup are now live on https://jeelive.ai. Start with NATIVE_PIN_UPDATE.md, then APP_INTEGRATION.md.

Use https://jeelive.ai/api as the canonical API. The preview-host download URL is ONLY artifact hosting, never the native API base.

This ZIP supersedes the older phone-only/pending-PIN handoff. Signup sends phone,pin,confirm_pin; login sends phone,pin; authenticated own PIN change sends phone,new_pin,confirm_pin. PINs are four-digit strings, preserving leading zeroes. No OTP, payment integration or Rapid Fire migration.

Preserve existing user IDs, sessions, saved answers, attempts/results and original solutions. Keep a valid legacy session to set the first PIN; never log out and re-register to work around an existing profile. No public PIN reset exists. Old native NEW sign-ins require the app update.

Evidence includes the live OpenAPI contracts, guest login/signup screenshots, rejected missing-PIN request422, anonymous admin request401, and canonical30PYQ/2250question catalogue read by the authorised owner. Full functional auth and two-session paper flows were tested against real backend code in isolated databases, NOT a production student or actual Expo device. No secret or private student export is included.

Exact design tokens, original licensed fonts/icons/logo, reference CSS and all existing card references are included. Home: JEE royal-blue/platinum, All India ruby/onyx, BITSAT bright amber, COMEDK teal. Other pages retain black/blood-red. Native pixel parity still requires comparison on-device.

SHA256SUMS.json lists every packaged file except itself. Keep the canonical API and Rapid Fire exception unchanged.
''')
    hashes = {}
    for file in sorted(NEW.rglob('*')):
        if not file.is_file() or file.name == 'SHA256SUMS.json':
            continue
        rel = str(file.relative_to(NEW))
        assert file.suffix.lower() not in ('.pdf', '.pem', '.env')
        assert not any(word in file.name.lower() for word in ('credential', 'cookie', 'secret'))
        hashes[rel] = hashlib.sha256(file.read_bytes()).hexdigest()
    (NEW / 'SHA256SUMS.json').write_text(json.dumps(hashes, indent=2) + '\n')
    date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    archive = NEW.parent / f'JEELIVE_PIN_LIVE_App_Integration_{date}.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as zipped:
        for file in sorted(NEW.rglob('*')):
            if file.is_file(): zipped.write(file, str(file.relative_to(NEW)))
    with zipfile.ZipFile(archive) as zipped:
        assert zipped.testzip() is None
        assert 'NATIVE_PIN_UPDATE.md' in zipped.namelist()
        assert 'evidence/live-pin-verification.json' in zipped.namelist()
        for rel, digest in hashes.items():
            assert hashlib.sha256(zipped.read(rel)).hexdigest() == digest
    print(json.dumps({'archive': str(archive), 'files': len(hashes) + 1, 'bytes': archive.stat().st_size,
                      'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'zip_crc_and_manifest': 'PASS'}))


if __name__ == '__main__':
    main()
