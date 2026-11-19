async def run_test(page, output_dir, page_url):
    import hashlib
    from pathlib import Path

    try:
        await page.set_viewport_size({"width": 375, "height": 667})
        print("Step 1: Mobile viewport set")

        await page.wait_for_load_state("domcontentloaded")
        await page.wait_for_timeout(800)
        print("Step 2: Page loaded")

        base_url = "https://handoff-zip-hub--8kn8pvyh.preview.emergentagent.com/api/marketing/launch"
        downloads_dir = Path("/app/test_reports/artifacts_iter54/ui_downloads")
        downloads_dir.mkdir(parents=True, exist_ok=True)

        await page.evaluate("""(baseUrl) => {
          const container = document.createElement('div');
          container.setAttribute('data-testid', 'iter54-download-container');
          container.style.position = 'fixed';
          container.style.left = '8px';
          container.style.bottom = '8px';
          container.style.zIndex = '999999';
          container.style.background = '#fff';
          container.style.padding = '8px';
          container.style.border = '1px solid #ccc';

          const links = [
            { id: 'iter54-zip-download-link', name: 'launch-pack.zip', href: `${baseUrl}/launch-pack.zip` },
            { id: 'iter54-vertical-download-link', name: 'vertical.mp4', href: `${baseUrl}/vertical.mp4?download=1` },
            { id: 'iter54-landscape-download-link', name: 'landscape.mp4', href: `${baseUrl}/landscape.mp4?download=1` }
          ];

          links.forEach((link) => {
            const a = document.createElement('a');
            a.setAttribute('data-testid', link.id);
            a.href = link.href;
            a.textContent = `Download ${link.name}`;
            a.style.display = 'block';
            a.style.padding = '10px';
            a.style.marginBottom = '6px';
            a.style.background = '#e9ecef';
            a.style.color = '#000';
            a.style.fontSize = '14px';
            container.appendChild(a);
          });

          document.body.appendChild(container);
        }""", base_url)
        print("Step 3: User-gesture download links injected")

        expected = [
            {
                "selector": "[data-testid='iter54-zip-download-link']",
                "filename": "JEELIVE-Launch-Videos-45s.zip",
                "sha": "aceeaa6329a41e32109521acb6f9da1118c81b0816b1c27ab33577dbec339822",
                "bytes": 15097795,
                "save": downloads_dir / "iter54_launch_pack.zip",
            },
            {
                "selector": "[data-testid='iter54-vertical-download-link']",
                "filename": "JEELIVE-launch-45s-vertical.mp4",
                "sha": "c31dbcd1b216662be59c39c1ce8c528b2ae0d15e2db8a4410ea4ced44c172e98",
                "bytes": 7724316,
                "save": downloads_dir / "iter54_vertical.mp4",
            },
            {
                "selector": "[data-testid='iter54-landscape-download-link']",
                "filename": "JEELIVE-launch-45s-landscape.mp4",
                "sha": "0d74c017eefd9e92c0f3557abad908d4c9496f937034e272761ac26c6c4a6d21",
                "bytes": 7373179,
                "save": downloads_dir / "iter54_landscape.mp4",
            },
        ]

        for item in expected:
            try:
                await page.wait_for_selector(item["selector"], timeout=10000)
                async with page.expect_download(timeout=120000) as dl_info:
                    await page.click(item["selector"], force=True)
                download = await dl_info.value
                suggested = download.suggested_filename
                await download.save_as(str(item["save"]))
                data = item["save"].read_bytes()
                digest = hashlib.sha256(data).hexdigest()
                print(f"Download success: {item['selector']}")
                print(f"Suggested filename: {suggested}")
                print(f"Saved bytes: {len(data)}")
                print(f"SHA256: {digest}")
                if suggested != item["filename"]:
                    raise Exception(f"Filename mismatch. expected={item['filename']} got={suggested}")
                if len(data) != item["bytes"]:
                    raise Exception(f"Size mismatch. expected={item['bytes']} got={len(data)}")
                if digest != item["sha"]:
                    raise Exception(f"SHA mismatch. expected={item['sha']} got={digest}")
                print(f"Validation passed for {item['filename']}")
            except Exception as inner:
                print(f"Download validation failed for {item['selector']}: {str(inner)}")
                raise

        await page.screenshot(path="/app/test_reports/artifacts_iter54/ui_downloads/automation_output/20261028_124415_ba5e637e02f8/iter54_download_links_state.jpeg", type="jpeg", quality=40, full_page=False)
        print("Step 4: Download verification screenshot captured")

        # Get error messages using specific selectors
        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*=\"error\"], [id*=\"error\"]'));
        return errorElements.map(el => el.textContent).join(', ');
        }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")

        print("User-gesture download verification completed")
    except Exception as e:
        print(f"User-gesture download verification failed: {str(e)}")
        await page.screenshot(path="/app/test_reports/artifacts_iter54/ui_downloads/automation_output/20261028_124415_ba5e637e02f8/iter54_download_failure.jpeg", type="jpeg", quality=40, full_page=False)
