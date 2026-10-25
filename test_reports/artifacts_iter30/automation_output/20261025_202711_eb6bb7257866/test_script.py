async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width": 390, "height": 844})
        await page.wait_for_timeout(2000)
        testids = await page.evaluate("""() => Array.from(document.querySelectorAll('[data-testid]')).map(el => el.getAttribute('data-testid'))""")
        print(f"Found testIDs: {testids}")
        placeholders = await page.evaluate("""() => Array.from(document.querySelectorAll('input')).map(el => ({ph: el.getAttribute('placeholder'), type: el.getAttribute('type')}))""")
        print(f"Inputs: {placeholders}")
        print('Selector mapping done')
    except Exception as e:
        print(f'Selector mapping failed: {str(e)}')

