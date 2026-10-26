import argparse
import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from fontTools.ttLib import TTFont
from playwright.sync_api import sync_playwright

FRONT = Path('/app/frontend')
PROPS = ['backgroundColor','backgroundImage','color','borderTopColor','borderTopWidth','borderRadius','boxShadow','textShadow','fontFamily','fontSize','fontWeight','lineHeight','letterSpacing','padding','gap','minHeight','opacity','outlineColor','outlineWidth','outlineOffset','transition','animation','animationDelay','pointerEvents']
SAMPLE = """(e, props) => {const s=getComputedStyle(e);return Object.fromEntries(props.map(k=>[k,s[k]]));}"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    out = Path(args.output)
    for folder in ('assets/brand', 'assets/fonts', 'assets/icons', 'references', 'reference-css', 'evidence'):
        (out / folder).mkdir(parents=True, exist_ok=True)
    source_css = []
    for path in sorted((FRONT / 'src').glob('*.css')):
        shutil.copy2(path, out / 'reference-css' / path.name)
        source_css.append({'path': 'reference-css/' + path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    for name in ('jeelive-vector.svg', 'jeelive-crimson-icon.png'):
        shutil.copy2(FRONT / 'public/brand' / name, out / 'assets/brand' / name)
    fonts = []
    for family, weights in [('figtree', [400,500,600,700,800]), ('roboto-mono', [400,500,600,700])]:
        package = FRONT / 'node_modules/@fontsource' / family
        shutil.copy2(package / 'LICENSE', out / 'assets/fonts' / (family + '-LICENSE.txt'))
        for weight in weights:
            name = f'{family}-latin-{weight}-normal'
            src = package / 'files' / (name + '.woff2')
            shutil.copy2(src, out / 'assets/fonts' / src.name)
            font = TTFont(src)
            font.flavor = None
            font.save(out / 'assets/fonts' / (name + '.ttf'))
            fonts.append({'family': family, 'weight': weight, 'style': 'normal', 'subset': 'latin', 'woff2': 'assets/fonts/' + src.name, 'ttf': 'assets/fonts/' + name + '.ttf', 'source': '@fontsource/' + family})
    icon_names = ['Atom','Orbit','GraduationCap','ArrowUpRight','ArrowLeft','BookOpen','CalendarDays','Clock3','Play','Pause','Sparkles','CheckCircle2','CircleCheck','X','ChevronRight','Search','User','LogOut','BarChart3','Trophy','Flag','Save','RefreshCw','KeyRound','UsersRound','ShieldCheck','Check','AlertCircle']
    code = "const R=require('react'),S=require('react-dom/server'),L=require('lucide-react');const names=JSON.parse(process.argv[1]);process.stdout.write(JSON.stringify(Object.fromEntries(names.filter(n=>L[n]).map(n=>[n,S.renderToStaticMarkup(R.createElement(L[n],{size:24,strokeWidth:1.5}))]))));"
    icons = json.loads(subprocess.check_output(['node','-e',code,json.dumps(icon_names)], cwd=FRONT))
    for name, svg in icons.items():
        (out / 'assets/icons' / (name + '.svg')).write_text(svg + '\n')
    license_file = FRONT / 'node_modules/lucide-react/LICENSE'
    if license_file.exists(): shutil.copy2(license_file, out / 'assets/icons/LICENSE.txt')
    data = {'schema_version': 1, 'exported_at': datetime.now(timezone.utc).isoformat(), 'source_url': args.url,
            'source': 'Actual live browser computed styles, with exact CSS sources supplied',
            'scope': 'Visual exports only; no accounts, student records, PDFs, solutions or credentials',
            'font_assets': fonts, 'icon_assets': {name: 'assets/icons/' + name + '.svg' for name in icons},
            'home_icon_mapping': {'jee-main': {'icon':'Atom','strokeWidth':1.4}, 'bitsat':{'icon':'Orbit','strokeWidth':1.4}, 'comedk':{'icon':'GraduationCap','strokeWidth':1.4}},
            'reference_css': source_css,
            'css_import_order_from_App_js': re.findall(r'import\s+[\"\']([^\"\']+\.css)[\"\']', (FRONT / 'src/App.js').read_text()),
            'palette_mapping': {'home.jee-main':'royal-blue-platinum','home.all-india':'ruby-onyx','home.bitsat':'bright-amber','home.comedk':'teal-onyx','other_pages':'black-blood-red; follow selector-specific states'},
            'native_note': 'Layer each gradient in order. Convert CSS angles with measured aspect ratio or SVG. Preserve source-image whites. Numeric font weights use available website weights; validate native rasterisation against references.',
            'viewports': {}}
    with sync_playwright() as p:
        browser = p.chromium.launch(args=['--no-sandbox'])
        page = browser.new_page()
        for width in (1920, 390):
            page.set_viewport_size({'width': 1920, 'height': 800} if width == 1920 else {'width': 390, 'height': 844})
            page.goto(args.url, wait_until='networkidle', timeout=60000)
            page.locator('[data-testid="exam-home-exam-card-jee-main"]').wait_for()
            page.evaluate('document.fonts.ready')
            root = page.evaluate("() => {const s=getComputedStyle(document.documentElement); return Object.fromEntries([...s].filter(k=>k.startsWith('--')).map(k=>[k,s.getPropertyValue(k).trim()]));}")
            view = {'viewport': {'width': width, 'height': 800 if width == 1920 else 844}, 'root_css_variables': root, 'home_cards': {}}
            if width == 390:
                page.screenshot(path=str(out / 'references/home-top-390.jpeg'), full_page=False, quality=40, animations='disabled')
            for name, selector in [('all-india','.polished-home .flagship-banner'),('jee-main','.polished-home .exam-tone-jee-main'),('bitsat','.polished-home .exam-tone-bitsat'),('comedk','.polished-home .exam-tone-comedk')]:
                el = page.locator(selector).first
                el.scroll_into_view_if_needed()
                page.mouse.move(0,0)
                page.wait_for_timeout(300)
                styles = {'selector': selector, 'default': el.evaluate(SAMPLE, PROPS),
                          'css_variables': el.evaluate("e=>{const s=getComputedStyle(e);return Object.fromEntries([...s].filter(k=>k.startsWith('--exam-')).map(k=>[k,s.getPropertyValue(k).trim()]));}"),
                          'before': el.evaluate("(e,p)=>{const s=getComputedStyle(e,'::before');return Object.fromEntries(p.map(k=>[k,s[k]]));}", PROPS),
                          'after': el.evaluate("(e,p)=>{const s=getComputedStyle(e,'::after');return Object.fromEntries(p.map(k=>[k,s[k]]));}", PROPS)}
                for child in ('h2','p','small','nav a','.exam-primary','.flagship-primary','.series-100ai-badge'):
                    target = el.locator(child).first
                    if target.count(): styles[child] = target.evaluate(SAMPLE, PROPS)
                page.screenshot(path=str(out / f'references/{name}-{width}.jpeg'), full_page=False, quality=40, animations='disabled')
                if width == 1920:
                    el.hover()
                    page.wait_for_timeout(300)
                    styles['hover'] = el.evaluate(SAMPLE, PROPS)
                    cta = el.locator('.exam-primary,.flagship-primary').first
                    if cta.count():
                        cta.hover()
                        page.wait_for_timeout(200)
                        styles['cta_hover'] = cta.evaluate(SAMPLE, PROPS)
                        cta.focus()
                        styles['cta_focus'] = cta.evaluate(SAMPLE, PROPS)
                view['home_cards'][name] = styles
            view['other_component_states'] = page.evaluate("""props=>{
                const host=document.createElement('div');host.style.cssText='position:fixed;top:0;left:0;visibility:hidden;pointer-events:none';document.body.append(host);
                const cases={
                 'pyq.default':'<div class="pyq-paper-card card"></div>',
                 'library.default':'<article class="test-library-card"></article>',
                 'library.active':'<article class="test-library-card state-active"></article>',
                 'library.completed':'<article class="test-library-card state-completed"></article>',
                 'library.saved':'<article class="test-library-card saved-paper-card"></article>',
                 'series.slot':'<article class="series-slot"></article>',
                 'auth.card':'<section class="auth-card"></section>',
                 'result.score':'<div class="results-page"><div class="score-card" data-target></div></div>',
                 'solution.card':'<section class="focused-solution-card"></section>',
                 'solution.original':'<section class="focused-solution-card"><div class="matched-solution" data-target></div></section>',
                 'solution.source':'<div class="source-canvas-frame"></div>',
                 'solution.number':'<button class="solution-number"></button>',
                 'solution.correct':'<button class="solution-number outcome-correct"></button>',
                 'solution.incorrect':'<button class="solution-number outcome-incorrect"></button>',
                 'solution.selected':'<button class="solution-number" aria-current="true"></button>',
                 'tab.default':'<div class="jeelive-tabs"><button class="jeelive-tab" role="tab" data-state="inactive" data-target></button></div>',
                 'tab.selected':'<div class="jeelive-tabs"><button class="jeelive-tab" role="tab" data-state="active" data-target></button></div>',
                 'button.default':'<button class="jeelive-button inline-flex rounded-md text-sm font-medium disabled:pointer-events-none disabled:opacity-50" data-ui-variant="default"></button>',
                 'button.disabled':'<button disabled class="jeelive-button inline-flex rounded-md text-sm font-medium disabled:pointer-events-none disabled:opacity-50" data-ui-variant="default"></button>'};
                const result={};for(const[name,html]of Object.entries(cases)){host.innerHTML=html;const e=host.querySelector('[data-target]')||host.firstElementChild;const s=getComputedStyle(e);result[name]={context:html,style:Object.fromEntries(props.map(k=>[k,s[k]]))};}host.remove();return result;
            }""", PROPS)
            offenders = page.evaluate("() => [...document.querySelectorAll('*')].filter(e=>e.getBoundingClientRect().right>innerWidth+1).slice(0,5).map(e=>e.className||e.tagName)")
            view['horizontal_overflow'] = offenders
            data['viewports'][str(width)] = view
            print('EXPORTED', width, 'OVERFLOW', offenders)
        browser.close()
    data['motion'] = {'exam_shine_seconds':7,'exam_shine_delays_seconds':[0,1.7,3.4], 'shine_peak_white_alpha':0.13,
                      'reduced_motion':'disable shine/transforms/transitions per reference CSS','paused':'pause all three card shine animations',
                      'references':'Animations disabled for stable still images; exact keyframes are in reference CSS'}
    (out / 'design-tokens.json').write_text(json.dumps(data, indent=2) + '\n')
    shutil.copy2('/app/docs/APP_INTEGRATION.md', out / 'APP_INTEGRATION.md')
    proof = json.loads(Path('/app/test_reports/iter155_isolated_pyq_proof.json').read_text())
    proof.pop('student_id', None)
    proof.pop('attempt_id', None)
    proof.pop('reattempt_id', None)
    proof.pop('db', None)
    proof['flow'] = 'Two sessions, same learner: start/save/resume/submit/original solution; new reattempt retains old result. Actual Expo app not tested.'
    (out / 'evidence/isolated-two-session-proof.json').write_text(json.dumps(proof, indent=2) + '\n')
    print('PUBLIC_ASSETS_EXPORTED', len(fonts), 'fonts', len(icons), 'icons', len(source_css), 'stylesheets')


if __name__ == '__main__':
    main()
