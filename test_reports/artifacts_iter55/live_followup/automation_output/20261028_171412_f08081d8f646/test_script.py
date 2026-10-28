async def run_test(page, output_dir, page_url):
    import ast
    try:
        scope={'page':page}
        code=compile(open('/app/tests/iter55_live_readonly_ui.py').read(), '/app/tests/iter55_live_readonly_ui.py', 'exec', flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        await eval(code,scope)
    except Exception as e:
        print('FAIL runner',str(e))
