async def run_test(page, output_dir, page_url):
    import hashlib, json, io, zipfile
    from pathlib import Path
    results = {'layouts': [], 'downloads': [], 'errors': []}
    original_url = page.url
    try:
        await page.set_viewport_size({'width':390,'height':844})
        await page.locator('[data-testid="launch-download-page"]').wait_for(state='visible',timeout=10000)
        assert await page.locator('script[src*="expo"], script[src*="entry.bundle"]').count()==0
        assert await page.locator('[data-testid="download-mobile-zip"]').evaluate('(el)=>el.closest("form").getAttribute("action")') == '/api/marketing/videos.zip'
        print('PASS standalone native form; no Expo scripts')
        for width in [390,320]:
            await page.set_viewport_size({'width':width,'height':844})
            overflow = await page.evaluate('document.documentElement.scrollWidth > window.innerWidth')
            assert not overflow
            sizes=[]
            for tid in ['download-mobile-zip','download-vertical-mp4','download-landscape-mp4']:
                box=await page.locator('[data-testid="'+tid+'"]').bounding_box()
                assert box['height']>=44 and box['width']>=44
                sizes.append({'testID':tid,'width':box['width'],'height':box['height']})
            assert 'Extract / Unzip' in await page.locator('[data-testid="download-instructions"]').inner_text()
            results['layouts'].append({'width':width,'overflow':False,'targets':sizes})
            await page.evaluate('window.scrollTo(0,0)')
            await page.screenshot(path=f"/app/test_reports/artifacts_iter56/download_clicks/automation_output/20261028_175235_3bd5c629db95/downloads{width}.jpeg", type="jpeg", quality=40, full_page=False)
            print(f'PASS {width}px layout, no overflow, all targets>=44px, unzip instructions')
    except Exception as e:
        results['errors'].append(repr(e))
        print('FAIL layout/form',repr(e))
    await page.set_viewport_size({'width':390,'height':844})
    checks = [
        ('download-mobile-zip','JEELIVE-Mobile-Videos-45s.zip',13403359,'8672f7bb38fcc47146c58ea01b4dfc8cc2de168cf465b84b3543a80cd3ff8c84'),
        ('download-vertical-mp4','JEELIVE-Mobile-Vertical-45s.mp4',7032763,'9e7764a6e4751bb65f32f1a2a3490c7e670d2b742004c09ee879faeb09dfeaa9'),
        ('download-landscape-mp4','JEELIVE-Mobile-Landscape-45s.mp4',6370296,'9bc37d8aebc7bb3e584348014b37183b905b1c56e847d01d9ca096fd02ca7f7a')
    ]
    for tid,filename,size,sha in checks:
        try:
            async with page.expect_download(timeout=60000) as event:
                await page.locator('[data-testid="'+tid+'"]').click(force=True)
            download = await event.value
            assert download.suggested_filename==filename
            assert await download.failure() is None
            path=await download.path()
            raw=Path(path).read_bytes()
            assert len(raw)==size and hashlib.sha256(raw).hexdigest()==sha
            if filename.endswith('.zip'):
                with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                    assert archive.testzip() is None
                    assert archive.namelist()==['JEELIVE-Mobile-Vertical-45s.mp4','JEELIVE-Mobile-Landscape-45s.mp4']
                    for entry,expected in zip(archive.namelist(),checks[1:]):
                        assert hashlib.sha256(archive.read(entry)).hexdigest()==expected[3]
            assert page.url==original_url
            assert await page.locator('[data-testid="launch-download-page"]').is_visible()
            results['downloads'].append({'testID':tid,'filename':filename,'bytes':len(raw),'sha256':sha,'page_unchanged':True})
            print('PASS actual click complete file:',filename,len(raw),sha,'page unchanged')
        except Exception as e:
            results['errors'].append({'testID':tid,'error':repr(e)})
            print('FAIL actual click',tid,repr(e))
    error_text = await page.evaluate("""() => { const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]')); return errorElements.map(el => el.textContent).join(", "); }""")
    print(f'Found error message: {error_text}' if error_text else 'No error messages found on the page')
    Path('/app/test_reports/artifacts_iter56/browser_results.json').write_text(json.dumps(results,indent=2))
    print('RESULTS',json.dumps(results))
