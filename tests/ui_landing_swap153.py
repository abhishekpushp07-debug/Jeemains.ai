# Iteration 153: REAL public root "/" (guest, no API mocks) palette swap + regressions; then /home via read-only fixture for comparison.
# Paste into browser_automation (expects `page`). Guest phase only observes requests (no interception).
import json
BASE='https://campus-search-debug.preview.emergentagent.com'
reqlog=[]; writes=[]
page.on('request', lambda r: reqlog.append(r.method+' '+r.url.split('?')[0]) if '/api/' in r.url and r.method not in ('GET','HEAD','OPTIONS') else None)

async def handler(route):
    req=route.request; u=req.url.split('?')[0]
    if req.method not in ('GET','HEAD','OPTIONS'):
        writes.append(req.method+' '+u); await route.fulfill(status=403,content_type='application/json',body='{"detail":"blocked"}'); return
    if u.endswith('/auth/session'): body={"user":{"id":"visual-home153","name":"Visual check","role":"student","access_type":"unverified_phone","phone_last4":"0000"}}
    elif u.endswith('/series/all-india-jee/streak'): body={"user_id":"visual-home153","stage":"prelaunch","completed_count":0,"current_streak":0,"best_streak":0,"milestones":[],"days":[],"today_state":"prelaunch","next_milestone":None,"policy":"fixture"}
    elif u.endswith('/series/all-india-jee/history'): body={"items":[]}
    elif u.endswith('/series/all-india-jee'): body={"server_now":1790000000,"today":"2026-10-26","first_date":"2026-12-01","last_date":"2027-01-31","today_slot":None,"slots":[]}
    else: body={}
    await route.fulfill(status=200,content_type='application/json',body=json.dumps(body))

STYLES_JS = """() => { const q=s=>document.querySelector(s); const cs=(s,p)=>{const e=q(s); return e?getComputedStyle(e)[p]:null};
 const out={};
 for (const s of ['jee-main','bitsat','comedk']) { const c=`[data-testid="exam-home-exam-card-${s}"]`;
   out[s]={bg:cs(c,'backgroundImage'), border:cs(c,'borderTopColor'), color:cs(c,'color'), h2:cs(c+' h2 a','color'), small:cs(c+' small','color'), p:cs(c+' p','color'), top:cs(c+' .bold-exam-top','color'), nav:cs(c+' nav a','color'), ctaBg:cs(c+' .exam-primary','backgroundImage'), ctaInk:cs(c+' .exam-primary','color'), shineAnim:(()=>{const e=q(c);return e&&getComputedStyle(e,'::before').animationName})()}; }
 const b='[data-testid="all-india-series-banner"]';
 out.banner={bg:cs(b,'backgroundImage'), bgc:cs(b,'backgroundColor'), border:cs(b,'borderTopColor'), h2:cs(b+' h2','color'), p:cs(b+' p','color'), primaryBg:cs('[data-testid="series-explore-button"]','backgroundImage'), primaryBgc:cs('[data-testid="series-explore-button"]','backgroundColor'), primaryInk:cs('[data-testid="series-explore-button"]','color'), primaryBorder:cs('[data-testid="series-explore-button"]','borderTopColor')};
 out.overflow={sw:document.documentElement.scrollWidth, cw:document.documentElement.clientWidth};
 out.layout={landing:!!q('[data-testid="free-landing-page"]'), rootCls:(q('[data-testid="free-landing-page"]')||q('[data-testid="exam-home-page"]')||{}).className, examHomeOnPage:!!q('.exam-home'), faq:document.querySelectorAll('[data-testid^="faq-"]:not([data-testid^="faq-answer"])').length, hero:!!q('[data-testid="landing-hero-heading"]'), bodyBg:getComputedStyle(document.body).backgroundColor, headerBg:(()=>{const h=q('header');return h&&getComputedStyle(h).backgroundColor})()};
 return out; }"""

def checks(st):
    j=st['jee-main']; b=st['banner']; bi=st['bitsat']; co=st['comedk']
    return {
     'jee_royal_blue': 'rgb(6, 17, 46)' in j['bg'] and 'rgb(24, 53, 122)' in j['bg'],
     'jee_platinum_cta': 'rgb(251, 252, 255)' in j['ctaBg'] and j['ctaInk']=='rgb(18, 41, 82)',
     'jee_no_old_ruby': '28, 14, 19' not in j['bg'],
     'banner_ruby_onyx': 'rgb(26, 7, 10)' in b['bg'] and 'rgb(13, 12, 16)' in b['bg'],
     'banner_ruby_cta': 'rgb(182, 17, 42)' in (b['primaryBgc']+b['primaryBg']) and b['primaryInk']=='rgb(255, 247, 248)',
     'banner_not_old_flat': b['bg']!='none',
     'bitsat_amber_dark_ink': 'rgb(255, 193, 91)' in bi['bg'] and bi['h2']=='rgb(40, 24, 6)' and bi['p']=='rgb(40, 24, 6)',
     'comedk_teal': 'rgb(4, 24, 26)' in co['bg'] and co['ctaInk']=='rgb(6, 55, 51)',
     'no_overflow': st['overflow']['sw']<=st['overflow']['cw'],
    }

PS_JS = """() => [...document.querySelectorAll('.polished-home .bold-exam-card')].map(c=>getComputedStyle(c,'::before').animationPlayState)"""
HREF_JS = """() => Object.fromEntries([...document.querySelectorAll('[data-testid^="exam-direct-"],[data-testid^="exam-home-title-link-"],[data-testid="series-banner-hub"],[data-testid="landing-final-cta"]')].map(a=>[a.dataset.testid,a.getAttribute('href')]))"""

async def common(tag, vw, vh, url, ready):
    await page.set_viewport_size({"width":vw,"height":vh})
    await page.goto(BASE+url, wait_until='domcontentloaded'); await page.wait_for_selector(ready, timeout=20000)
    await page.wait_for_selector('[data-testid="all-india-series-banner"]', timeout=15000)
    await page.wait_for_timeout(2500)
    st = await page.evaluate(STYLES_JS)
    print(f'== {tag} {vw}x{vh} url={page.url}')
    print('STYLES', json.dumps(st))
    print('CHECKS', checks(st))
    print('HREFS', await page.evaluate(HREF_JS))
    await page.screenshot(path=f'.screenshots/{tag}153_{vw}_top.jpeg', quality=40, full_page=False)
    await page.locator('[data-testid="exam-home-exam-card-grid"]').scroll_into_view_if_needed(); await page.wait_for_timeout(400)
    await page.screenshot(path=f'.screenshots/{tag}153_{vw}_cards.jpeg', quality=40, full_page=False)
    await page.click('[data-testid="exam-shine-toggle"]'); await page.wait_for_timeout(200)
    print('PAUSED', await page.evaluate(PS_JS), await page.get_attribute('[data-testid="exam-shine-toggle"]','aria-pressed'))
    await page.click('[data-testid="exam-shine-toggle"]'); await page.wait_for_timeout(200)
    print('RESUMED', await page.evaluate(PS_JS))
    await page.click('[data-testid="series-explore-button"]'); await page.wait_for_selector('[data-testid="series-explainer"]', timeout=5000)
    print('MODAL open', await page.is_visible('[data-testid="series-explainer"]'))
    await page.keyboard.press('Escape'); await page.wait_for_timeout(600)
    print('MODAL closed', await page.locator('[data-testid="series-explainer"]').count()==0)
    return st

try:
    # ---------- REAL guest root, no route interception ----------
    for vw,vh in [(1920,800),(390,844)]:
        st = await common('landing', vw, vh, '/', '[data-testid="free-landing-page"]')
        if vw==1920:
            await page.click('[data-testid="faq-0"]'); await page.wait_for_timeout(400)
            print('FAQ0 open', await page.is_visible('[data-testid="faq-answer-0"]'))
            LAND=st
    # guest card links -> login redirect
    for tid in ['exam-direct-mocks-jee-main','exam-direct-chapters-bitsat','exam-direct-results-comedk','exam-home-title-link-comedk']:
        await page.goto(BASE+'/', wait_until='domcontentloaded'); await page.wait_for_selector(f'[data-testid="{tid}"]', timeout=15000)
        await page.click(f'[data-testid="{tid}"]'); await page.wait_for_timeout(1500)
        print('GUEST CLICK', tid, '->', page.url)
    # reduced motion on landing
    await page.emulate_media(reduced_motion='reduce'); await page.goto(BASE+'/', wait_until='domcontentloaded'); await page.wait_for_selector('[data-testid="exam-home-exam-card-jee-main"]'); await page.wait_for_timeout(1500)
    print('LANDING REDUCED', await page.evaluate("""() => [...document.querySelectorAll('.polished-home .bold-exam-card, .polished-home .flagship-banner')].map(c=>getComputedStyle(c,'::before').display+'/'+getComputedStyle(c,'::before').animationName)"""))
    await page.emulate_media(reduced_motion='no-preference')
    print('GUEST MUTATION REQUESTS', reqlog)
    # ---------- /home with read-only fixture ----------
    await page.route('**/api/**', handler)
    for vw,vh in [(1920,800),(390,844)]:
        st = await common('home', vw, vh, '/home', '[data-testid="exam-home-page"]')
        if vw==1920: HOME=st
    diff = {k:[(f, LAND[k][f], HOME[k][f]) for f in LAND[k] if LAND[k][f]!=HOME[k][f]] for k in ['jee-main','bitsat','comedk','banner']}
    print('LANDING vs HOME diffs', json.dumps(diff))
    await page.emulate_media(reduced_motion='reduce'); await page.reload(wait_until='domcontentloaded'); await page.wait_for_timeout(1500)
    print('HOME REDUCED', await page.evaluate("""() => [...document.querySelectorAll('.polished-home .bold-exam-card, .polished-home .flagship-banner')].map(c=>getComputedStyle(c,'::before').display)"""))
    await page.emulate_media(reduced_motion='no-preference')
    await page.goto(BASE+'/series/all-india-jee', wait_until='domcontentloaded'); await page.wait_for_timeout(2500)
    print('SERIES HUB polished?', await page.evaluate("()=>!!document.querySelector('.polished-home')"))
    print('BLOCKED WRITES', writes)
except Exception as e:
    import traceback; print('ERROR', e, traceback.format_exc())
