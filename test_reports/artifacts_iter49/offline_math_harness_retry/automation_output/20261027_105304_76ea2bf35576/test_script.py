async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width": 375, "height": 667})
        print("Step 1: Viewport set")

        html = """<!doctype html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'><meta http-equiv='Content-Security-Policy' content="default-src 'none'; style-src 'unsafe-inline'; font-src data:; script-src 'unsafe-inline'"><style>body{margin:0;background:#111;color:#fff}#content{white-space:pre-wrap}</style><style id='theme'></style></head><body><div id='content'></div><script>window.__msgs=[];window.ReactNativeWebView={postMessage:(m)=>window.__msgs.push(m)};let revision=0,frame=0,last='';const report=()=>{cancelAnimationFrame(frame);frame=requestAnimationFrame(()=>{const h=document.getElementById('content').scrollHeight+8;const key=revision+':'+h;if(key!==last){last=key;window.ReactNativeWebView.postMessage(JSON.stringify({revision,height:h}));}});};window.updateMath=(payload)=>{revision=payload.revision;document.getElementById('theme').textContent=payload.css;document.getElementById('content').innerHTML=payload.body;report();if(document.fonts)document.fonts.ready.then(report);};new ResizeObserver(report).observe(document.getElementById('content'));window.ReactNativeWebView.postMessage(JSON.stringify({ready:true}));</script></body></html>"""

        await page.set_content(html)
        await page.wait_for_timeout(250)

        await page.evaluate("""() => {
          window.updateMath({revision:1, css:'body{background:#111;color:#fff}', body:'<div>First body</div>'});
          window.updateMath({revision:2, css:'body{background:#111;color:#fff}', body:'<div>Second body with \\\\(x^2+y^2\\\\)</div>'});
        }""")
        await page.wait_for_timeout(400)

        msgs = await page.evaluate("window.__msgs || []")
        import json
        parsed = []
        for item in msgs:
            try:
                parsed.append(json.loads(item))
            except Exception:
                pass
        ready_seen = any(isinstance(m, dict) and m.get('ready') for m in parsed)
        revisions = [m.get('revision') for m in parsed if isinstance(m, dict) and m.get('revision') is not None]
        latest_revision = revisions[-1] if revisions else None
        body_text = await page.locator('#content').inner_text()

        csp_block = await page.evaluate("""() => fetch('https://example.com/x.woff2').then(()=>false).catch(()=>true)""")

        print(f"Step 2: ready_seen={ready_seen} revisions={revisions}")
        print(f"Step 3: latest_revision={latest_revision} body={body_text}")
        print(f"Step 4: csp_block={csp_block}")

        assert ready_seen
        assert latest_revision == 2
        assert 'Second body' in body_text

        # Get error messages using specific selectors
        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*=\"error\"], [id*=\"error\"]'));
        return errorElements.map(el => el.textContent).join(", ");
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")

        await page.screenshot(path='/app/test_reports/artifacts_iter49/offline_math_harness_retry/automation_output/20261027_105304_76ea2bf35576/offline_math_harness.jpeg', type="jpeg", quality=40, full_page=False)
    except Exception as e:
        print(f"OfflineMath harness failed: {str(e)}")
        await page.screenshot(path='/app/test_reports/artifacts_iter49/offline_math_harness_retry/automation_output/20261027_105304_76ea2bf35576/offline_math_harness_error.jpeg', type="jpeg", quality=40, full_page=False)

