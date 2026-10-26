# Iteration 152: Home palette swap (JEE Main royal-blue/platinum, All India banner ruby/onyx) computed-style + regression checks.
# Paste into browser_automation (expects `page`). Read-only route fixtures; all mutations blocked.
import json
BASE='https://campus-search-debug.preview.emergentagent.com'
writes=[]
GUEST={'v':False}
async def handler(route):
    req=route.request; u=req.url.split('?')[0]
    if req.method not in ('GET','HEAD','OPTIONS'):
        writes.append(req.method+' '+u); await route.fulfill(status=403,content_type='application/json',body='{"detail":"blocked"}'); return
    if u.endswith('/auth/session'): body={"user":None} if GUEST['v'] else {"user":{"id":"visual-home152","name":"Visual check","role":"student","access_type":"unverified_phone","phone_last4":"0000"}}
    elif u.endswith('/series/all-india-jee/streak'): body={"user_id":"visual-home152","stage":"prelaunch","completed_count":0,"current_streak":0,"best_streak":0,"milestones":[],"days":[],"today_state":"prelaunch","next_milestone":None,"policy":"fixture"}
    elif u.endswith('/series/all-india-jee/history'): body={"items":[]}
    elif u.endswith('/series/all-india-jee'): body={"server_now":1790000000,"today":"2026-10-26","first_date":"2026-12-01","last_date":"2027-01-31","today_slot":None,"slots":[]}
    else: body={}
    await route.fulfill(status=200,content_type='application/json',body=json.dumps(body))

STYLES_JS = """() => { const q=s=>document.querySelector(s); const cs=(s,p)=>{const e=q(s); return e?getComputedStyle(e)[p]:null};
 const out={};
 for (const s of ['jee-main','bitsat','comedk']) { const c=`[data-testid="exam-home-exam-card-${s}"]`;
   out[s]={bg:cs(c,'backgroundImage'), border:cs(c,'borderTopColor'), color:cs(c,'color'), h2:cs(c+' h2 a','color'), small:cs(c+' small','color'), p:cs(c+' p','color'), nav:cs(c+' nav a','color'), ctaBg:cs(c+' .exam-primary','backgroundImage'), ctaInk:cs(c+' .exam-primary','color')}; }
 const b='[data-testid="all-india-series-banner"]';
 out.banner={bg:cs(b,'backgroundImage'), bgc:cs(b,'backgroundColor'), border:cs(b,'borderTopColor'), h2:cs(b+' h2','color'), p:cs(b+' p','color'), primaryBg:cs('[data-testid="series-explore-button"]','backgroundImage'), primaryBgc:cs('[data-testid="series-explore-button"]','backgroundColor'), primaryInk:cs('[data-testid="series-explore-button"]','color'), primaryBorder:cs('[data-testid="series-explore-button"]','borderTopColor'), badge:cs('[data-testid="series-live-badge"]','backgroundColor')};
 out.overflow={sw:document.documentElement.scrollWidth, cw:document.documentElement.clientWidth};
 return out; }"""

async def run(vw, vh):
    await page.set_viewport_size({"width":vw,"height":vh})
    await page.goto(BASE+'/home', wait_until='domcontentloaded'); await page.wait_for_selector('[data-testid="exam-home-exam-card-jee-main"]', timeout=15000)
    await page.wait_for_timeout(2500)
    st = await page.evaluate(STYLES_JS)
    print(f'== {vw}x{vh} STYLES', json.dumps(st))
    j=st['jee-main']; b=st['banner']; bi=st['bitsat']; co=st['comedk']
    chk={
     'jee_royal_blue': 'rgb(6, 17, 46)' in j['bg'] and 'rgb(24, 53, 122)' in j['bg'],
     'jee_platinum_cta': 'rgb(251, 252, 255)' in j['ctaBg'] and j['ctaInk']=='rgb(18, 41, 82)',
     'jee_no_ruby': '28, 14, 19' not in j['bg'] and 'rgb(182, 17, 42)' not in j['ctaBg'],
     'banner_ruby_onyx': 'rgb(26, 7, 10)' in b['bg'] and 'rgb(13, 12, 16)' in b['bg'],
     'banner_ruby_cta': 'rgb(182, 17, 42)' in b['primaryBgc'] or 'rgb(182, 17, 42)' in b['primaryBg'],
     'banner_no_blue': '11, 45, 128' not in (b['bg']+b['bgc']),
     'bitsat_amber': 'rgb(255, 193, 91)' in bi['bg'] and bi['h2']=='rgb(40, 24, 6)',
     'comedk_teal': 'rgb(4, 24, 26)' in co['bg'] and co['ctaInk']=='rgb(6, 55, 51)',
     'no_overflow': st['overflow']['sw']<=st['overflow']['cw'],
    }
    print(f'== {vw}x{vh} CHECKS', chk)
    hrefs = await page.evaluate("""() => Object.fromEntries([...document.querySelectorAll('[data-testid^="exam-direct-"],[data-testid^="exam-home-title-link-"],[data-testid="series-banner-hub"]')].map(a=>[a.dataset.testid,a.getAttribute('href')]))""")
    print('HREFS', hrefs)
    # shine toggle pause
    await page.click('[data-testid="exam-shine-toggle"]')
    ps = await page.evaluate("""() => [...document.querySelectorAll('.exam-home .bold-exam-card')].map(c=>getComputedStyle(c,'::before').animationPlayState)""")
    print('PAUSED states', ps)
    await page.click('[data-testid="exam-shine-toggle"]')
    ps2 = await page.evaluate("""() => [...document.querySelectorAll('.exam-home .bold-exam-card')].map(c=>getComputedStyle(c,'::before').animationPlayState)""")
    print('RESUMED states', ps2)
    # modal
    await page.click('[data-testid="series-explore-button"]'); await page.wait_for_selector('[data-testid="series-explainer"]', timeout=5000)
    print('MODAL open', await page.is_visible('[data-testid="series-explainer"]'))
    await page.keyboard.press('Escape'); await page.wait_for_timeout(600)
    print('MODAL closed', await page.locator('[data-testid="series-explainer"]').count()==0)
    await page.screenshot(path=f'.screenshots/home152_{vw}.jpeg', quality=40, full_page=False)

try:
    await page.route('**/api/**', handler)
    await run(1920,800)
    await run(390,844)
    # reduced motion
    await page.emulate_media(reduced_motion='reduce'); await page.reload(wait_until='domcontentloaded'); await page.wait_for_timeout(1500)
    rm = await page.evaluate("""() => [...document.querySelectorAll('.exam-home .bold-exam-card, .flagship-banner')].map(c=>getComputedStyle(c,'::before').display+'/'+getComputedStyle(c,'::before').animationName)""")
    print('REDUCED MOTION before display', rm)
    await page.emulate_media(reduced_motion='no-preference')
    # scope: landing guest banner + series hub
    GUEST['v']=True
    await page.set_viewport_size({"width":1920,"height":800})
    await page.goto(BASE+'/', wait_until='domcontentloaded'); await page.wait_for_timeout(2500)
    lb = await page.evaluate("""() => { const b=document.querySelector('[data-testid="all-india-series-banner"]'); if(!b) return 'no banner'; const p=document.querySelector('[data-testid="series-explore-button"]'); return {bgc:getComputedStyle(b).backgroundColor,bg:getComputedStyle(b).backgroundImage,inHome:!!b.closest('.exam-home'),primary:p&&getComputedStyle(p).backgroundColor} }""")
    print('LANDING banner', lb, 'url', page.url)
    GUEST['v']=False
    await page.goto(BASE+'/series/all-india-jee', wait_until='domcontentloaded'); await page.wait_for_timeout(2500)
    sh = await page.evaluate("""() => ({examHome:!!document.querySelector('.exam-home'), flagshipInHome:!!document.querySelector('.exam-home .flagship-banner'), h1span:(()=>{const s=document.querySelector('.series-hub h1 span');return s&&getComputedStyle(s).color})()})""")
    print('SERIES HUB', sh, page.url)
    await page.goto(BASE+'/exams/jee-main', wait_until='domcontentloaded'); await page.wait_for_timeout(1500)
    eh = await page.evaluate("""() => ({cards:document.querySelectorAll('.bold-exam-card').length, banner:document.querySelectorAll('.flagship-banner').length})""")
    print('EXAM HUB (also .exam-home)', eh)
    print('BLOCKED WRITES', writes)
except Exception as e:
    print('ERROR', e)
