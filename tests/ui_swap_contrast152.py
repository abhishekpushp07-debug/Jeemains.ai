# Iteration 152: lossless pixel contrast for swapped Home JEE card (blue/platinum) + All India banner (ruby/onyx).
# Normal, hover (card + CTA), forced moving-glare offsets. Read-only fixtures. Paste into browser_automation.
import json, base64
BASE='https://campus-search-debug.preview.emergentagent.com'
writes=[]
async def handler(route):
    req=route.request; u=req.url.split('?')[0]
    if req.method not in ('GET','HEAD','OPTIONS'):
        writes.append(req.method+' '+u); await route.fulfill(status=403,content_type='application/json',body='{"detail":"blocked"}'); return
    if u.endswith('/auth/session'): body={"user":{"id":"visual-home152","name":"Visual check","role":"student","access_type":"unverified_phone","phone_last4":"0000"}}
    elif u.endswith('/series/all-india-jee/streak'): body={"user_id":"visual-home152","stage":"prelaunch","completed_count":0,"current_streak":0,"best_streak":0,"milestones":[],"days":[],"today_state":"prelaunch","next_milestone":None,"policy":"fixture"}
    elif u.endswith('/series/all-india-jee/history'): body={"items":[]}
    elif u.endswith('/series/all-india-jee'): body={"server_now":1790000000,"today":"2026-10-26","first_date":"2026-12-01","last_date":"2027-01-31","today_slot":None,"slots":[]}
    else: body={}
    await route.fulfill(status=200,content_type='application/json',body=json.dumps(body))

CSS = """html{scroll-behavior:auto!important}
html.qa-m [data-qa-scope], html.qa-m [data-qa-scope] *{transition:none!important}
html.qa-hide [data-qa-scope] *{color:transparent!important;-webkit-text-fill-color:transparent!important;text-shadow:none!important;text-decoration-color:transparent!important}
html.qa-hide [data-qa-scope] svg{visibility:hidden!important}
html.qa-shine [data-qa-scope]:before{animation:none!important;transform:translateX(var(--qa-x))!important;opacity:1!important}
html.qa-static [data-qa-scope]:before{animation:none!important;opacity:0!important}"""

# collect visible text rects + computed fg, grouped by parent element
TARGETS_JS = """(sel) => { const root=document.querySelector(sel); let hb=0;
 for (const x of [5, innerWidth/2, innerWidth-5]) for (let el of document.elementsFromPoint(x,2)) for(let a=el;a&&a!==document.documentElement;a=a.parentElement){const p=getComputedStyle(a).position; if(p==='sticky'||p==='fixed'){const r=a.getBoundingClientRect(); if(r.top<=1) hb=Math.max(hb,r.bottom);}}
 const groups={}; const w=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
 while(w.nextNode()){ const n=w.currentNode; if(!n.textContent.trim()) continue; const el=n.parentElement; const cs=getComputedStyle(el);
   if(cs.visibility==='hidden'||cs.display==='none') continue;
   const tid=(el.closest('[data-testid]')||el).dataset.testid||''; const key=(tid+'|'+el.tagName+'.'+(el.className&&el.className.baseVal===undefined?String(el.className).split(' ')[0]:'')+'|'+n.textContent.trim().slice(0,22));
   const m=cs.color.match(/[\\d.]+/g).map(Number); const fs=parseFloat(cs.fontSize), fw=parseInt(cs.fontWeight);
   const large = fs>=24 || (fs>=18.66 && fw>=700);
   const r=document.createRange(); r.selectNodeContents(n);
   for(const b of r.getClientRects()){ if(b.width<=0||b.height<=0) continue; if(b.top<hb+1||b.bottom>innerHeight-1||b.left<0||b.right>innerWidth) continue;
     (groups[key]=groups[key]||{key,fg:m.slice(0,3),alpha:m[3]??1,large,fs,fw,rects:[]}).rects.push({x:b.left,y:b.top,w:b.width,h:b.height}); } }
 return {hb, targets:Object.values(groups)}; }"""

SAMPLER = """async ({url, clip, targets}) => {
  const img = new Image(); img.src = url; await img.decode();
  const c = document.createElement('canvas'); c.width = img.width; c.height = img.height;
  const ctx = c.getContext('2d', {willReadFrequently:true}); ctx.drawImage(img,0,0);
  const sx = img.width/clip.width, sy = img.height/clip.height;
  const data = ctx.getImageData(0,0,img.width,img.height).data;
  const lin = v => { v/=255; return v<=0.04045? v/12.92 : Math.pow((v+0.055)/1.055,2.4); };
  const L = (r,g,b) => 0.2126*lin(r)+0.7152*lin(g)+0.0722*lin(b);
  const out = {};
  for (const t of targets) { const Lf = L(...t.fg); const vals=[]; let worst=null;
    for (const r of t.rects) {
      const x0=Math.max(0,Math.floor((r.x-clip.x)*sx)), y0=Math.max(0,Math.floor((r.y-clip.y)*sy));
      const x1=Math.min(img.width,Math.ceil((r.x+r.w-clip.x)*sx)), y1=Math.min(img.height,Math.ceil((r.y+r.h-clip.y)*sy));
      for (let y=y0;y<y1;y++) for (let x=x0;x<x1;x++) { const i=(y*img.width+x)*4; const Lb=L(data[i],data[i+1],data[i+2]);
        const cr=(Math.max(Lf,Lb)+0.05)/(Math.min(Lf,Lb)+0.05); vals.push(cr); if(!worst||cr<worst.cr) worst={cr,rgb:[data[i],data[i+1],data[i+2]]}; } }
    vals.sort((a,b)=>a-b);
    out[t.key] = {n:vals.length, min:vals.length?+vals[0].toFixed(2):null, p1:vals.length?+vals[Math.floor(vals.length*0.01)].toFixed(2):null, worstBg:worst&&worst.rgb, large:t.large, alpha:t.alpha, scale:[+sx.toFixed(2),+sy.toFixed(2)]}; }
  return out; }"""

RESULTS={}
def merge(state, res):
    for k,v in res.items():
        if v['n']==0: continue
        cur=RESULTS.setdefault(k,{'min':99,'state':None,'large':v['large'],'n':0,'alpha':v['alpha']})
        cur['n']+=v['n']
        if v['min']<cur['min']: cur.update(min=v['min'],state=state,worstBg=v['worstBg'],p1=v['p1'])

async def measure(sel, state):
    t = await page.evaluate(TARGETS_JS, sel)
    if not t['targets']: return
    await page.evaluate("()=>document.documentElement.classList.add('qa-hide')"); await page.wait_for_timeout(120)
    vw=page.viewport_size; clip={'x':0,'y':0,'width':vw['width'],'height':vw['height']}
    png = await page.screenshot(type='png', clip=clip)
    await page.evaluate("()=>document.documentElement.classList.remove('qa-hide')")
    url='data:image/png;base64,'+base64.b64encode(png).decode()
    res = await page.evaluate(SAMPLER, {'url':url,'clip':clip,'targets':t['targets']})
    merge(state, res)

async def scroll_to(sel, offset):
    await page.evaluate("""([s,o])=>{const e=document.querySelector(s); const y=e.getBoundingClientRect().top+scrollY-90+o; window.scrollTo({top:y,behavior:'instant'});}""", [sel, offset])
    await page.wait_for_timeout(250)

async def sweep(sel, vw, vh):
    h = await page.evaluate("(s)=>document.querySelector(s).getBoundingClientRect().height", sel)
    offsets=[0]; step=vh-200
    while offsets[-1]+step < h: offsets.append(offsets[-1]+step)
    for off in offsets:
        await scroll_to(sel, off); await page.mouse.move(2, vh-2)
        await page.evaluate("()=>document.documentElement.classList.add('qa-m','qa-static')"); await measure(sel, f'{vw} static')
        await page.evaluate("()=>document.documentElement.classList.remove('qa-static')"); await page.evaluate("()=>document.documentElement.classList.add('qa-shine')")
        for x in [-55,-40,-25,-16,-12,-8,-4,0,4,8,12,16,25,40,55]:
            await page.evaluate("(x)=>document.documentElement.style.setProperty('--qa-x', x+'%')", x)
            await measure(sel, f'{vw} glare {x}%')
        await page.evaluate("()=>document.documentElement.classList.remove('qa-shine')")

async def hover_measure(sel, hover_sel, vw, vh, label):
    await scroll_to(hover_sel, -150)
    await page.evaluate("()=>document.documentElement.classList.add('qa-m')")
    b = await page.locator(hover_sel).bounding_box()
    await page.mouse.move(b['x']+b['width']/2, b['y']+b['height']/2); await page.wait_for_timeout(400)
    await page.evaluate("()=>document.documentElement.classList.add('qa-static')"); await measure(sel, f'{vw} hover {label} static')
    await page.evaluate("()=>{document.documentElement.classList.remove('qa-static');document.documentElement.classList.add('qa-shine')}")
    for x in [-12,-4,0,4,12]:
        await page.evaluate("(x)=>document.documentElement.style.setProperty('--qa-x', x+'%')", x)
        await measure(sel, f'{vw} hover {label} glare {x}%')
    await page.evaluate("()=>document.documentElement.classList.remove('qa-shine')")
    await page.mouse.move(2, vh-2); await page.wait_for_timeout(300)

try:
    await page.route('**/api/**', handler)
    for (vw,vh) in [(1920,800),(390,844)]:
        await page.set_viewport_size({"width":vw,"height":vh})
        await page.goto(BASE+'/home', wait_until='domcontentloaded'); await page.wait_for_selector('[data-testid="exam-home-exam-card-jee-main"]', timeout=15000)
        await page.add_style_tag(content=CSS); await page.wait_for_timeout(2500)
        for sel in ['[data-testid="all-india-series-banner"]','[data-testid="exam-home-exam-card-jee-main"]']:
            await page.evaluate("(s)=>{document.querySelectorAll('[data-qa-scope]').forEach(e=>e.removeAttribute('data-qa-scope'));document.querySelector(s).setAttribute('data-qa-scope','')}", sel)
            await sweep(sel, vw, vh)
        await page.evaluate("()=>{document.querySelectorAll('[data-qa-scope]').forEach(e=>e.removeAttribute('data-qa-scope'));document.querySelector('[data-testid=\"exam-home-exam-card-jee-main\"]').setAttribute('data-qa-scope','')}")
        await hover_measure('[data-testid="exam-home-exam-card-jee-main"]','[data-testid="exam-home-exam-card-jee-main"] p', vw, vh, 'card')
        await hover_measure('[data-testid="exam-home-exam-card-jee-main"]','[data-testid="exam-direct-mocks-jee-main"]', vw, vh, 'cta')
        await hover_measure('[data-testid="exam-home-exam-card-jee-main"]','[data-testid="exam-direct-results-jee-main"]', vw, vh, 'nav')
        await page.evaluate("()=>{document.querySelectorAll('[data-qa-scope]').forEach(e=>e.removeAttribute('data-qa-scope'));document.querySelector('[data-testid=\"all-india-series-banner\"]').setAttribute('data-qa-scope','')}")
        await hover_measure('[data-testid="all-india-series-banner"]','[data-testid="series-explore-button"]', vw, vh, 'primary')
        await hover_measure('[data-testid="all-india-series-banner"]','[data-testid="series-banner-hub"]', vw, vh, 'hub')
        hov = await page.evaluate("()=>1")
        # re-key per viewport
        for k in list(RESULTS.keys()):
            if not k.startswith('@'): RESULTS[f'@{vw} '+k]=RESULTS.pop(k)
    fails=[]
    for k,v in sorted(RESULTS.items()):
        th = 3.0 if v['large'] else 4.5
        flag = 'FAIL' if v['min']<th else 'ok'
        if flag=='FAIL': fails.append(k)
        print(f"{flag} {k} min={v['min']} p1={v.get('p1')} th={th} n={v['n']} at={v['state']} bg={v.get('worstBg')} a={v['alpha']}")
    print('FAILS', len(fails), fails)
    print('BLOCKED WRITES', writes)
except Exception as e:
    import traceback; print('ERROR', e, traceback.format_exc())
