"""Reusable public-file browser check. Run directly; no auth or learner requests."""
import asyncio
import hashlib
import io
import json
import os
from pathlib import Path
import zipfile

from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv('/app/frontend/.env')
BASE = os.environ['EXPO_PUBLIC_BACKEND_URL'].rstrip('/')
ARTIFACTS = Path('/app/test_reports/artifacts_iter56')
FILES = [
    ('download-mobile-zip', 'JEELIVE-Mobile-Videos-45s.zip', 13403359, '8672f7bb38fcc47146c58ea01b4dfc8cc2de168cf465b84b3543a80cd3ff8c84'),
    ('download-vertical-mp4', 'JEELIVE-Mobile-Vertical-45s.mp4', 7032763, '9e7764a6e4751bb65f32f1a2a3490c7e670d2b742004c09ee879faeb09dfeaa9'),
    ('download-landscape-mp4', 'JEELIVE-Mobile-Landscape-45s.mp4', 6370296, '9bc37d8aebc7bb3e584348014b37183b905b1c56e847d01d9ca096fd02ca7f7a'),
]


async def verify(page):
    results = {'layouts': [], 'downloads': [], 'errors': []}
    url = BASE + '/api/marketing/downloads'
    await page.goto(url)
    try:
        await page.locator('[data-testid="launch-download-page"]').wait_for(state='visible')
        assert await page.locator('script[src*="expo"], script[src*="entry.bundle"]').count() == 0
        for width in [390, 320]:
            await page.set_viewport_size({'width': width, 'height': 844})
            assert not await page.evaluate('document.documentElement.scrollWidth > window.innerWidth')
            for tid, *_ in FILES:
                box = await page.locator(f'[data-testid="{tid}"]').bounding_box()
                assert box['width'] >= 44 and box['height'] >= 44
            assert 'Extract / Unzip' in await page.locator('[data-testid="download-instructions"]').inner_text()
            await page.screenshot(path=str(ARTIFACTS / f'reusable_downloads{width}.jpeg'), quality=40, full_page=False)
            results['layouts'].append({'width': width, 'passed': True})
            print(f'PASS {width}px layout and targets')
    except Exception as error:
        results['errors'].append(repr(error))
        print('FAIL page/layout', repr(error))
    for tid, filename, size, sha in FILES:
        try:
            async with page.expect_download(timeout=60000) as event:
                await page.locator(f'[data-testid="{tid}"]').click(force=True)
            download = await event.value
            assert download.suggested_filename == filename and await download.failure() is None
            raw = Path(await download.path()).read_bytes()
            assert len(raw) == size and hashlib.sha256(raw).hexdigest() == sha
            if filename.endswith('.zip'):
                with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                    assert archive.testzip() is None
                    assert archive.namelist() == [entry[1] for entry in FILES[1:]]
                    for entry in FILES[1:]:
                        assert hashlib.sha256(archive.read(entry[1])).hexdigest() == entry[3]
            assert page.url == url
            assert await page.locator('[data-testid="launch-download-page"]').is_visible()
            results['downloads'].append({'filename': filename, 'bytes': len(raw), 'sha256': sha})
            print('PASS complete click download', filename)
        except Exception as error:
            results['errors'].append({'testID': tid, 'error': repr(error)})
            print('FAIL download', tid, repr(error))
    error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(', ');
    }""")
    print(f'Found error message: {error_text}' if error_text else 'No error messages found on the page')
    (ARTIFACTS / 'browser_reusable_results.json').write_text(json.dumps(results, indent=2))
    assert not results['errors'], results['errors']


async def main():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(accept_downloads=True, viewport={'width': 390, 'height': 844})
        try:
            await verify(await context.new_page())
        finally:
            await browser.close()


if __name__ == '__main__':
    asyncio.run(main())