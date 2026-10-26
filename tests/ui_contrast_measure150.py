# Iteration 150: robust pixel contrast measurement for Home exam cards (BITSAT/COMEDK/JEE). Read-only route fixtures.
# Paste body into browser_automation (expects `page`). VIEWPORT set per run via VW/VH.
import json, base64
BASE='https://campus-search-debug.preview.emergentagent.com'
writes=[]
async def handler(route):
    req=route.request; u=req.url.split('?')[0]
    if req.method not in ('GET','HEAD','OPTIONS'):
        writes.append(req.method+' '+u); await route.fulfill(status=403,content_type='application/json',body='{"detail":"blocked"}'); return
    if u.endswith('/auth/session'): body={"user":{"id":"visual-home150","name":"Visual check","role":"student","access_type":"unverified_phone","phone_last4":"0000"}}
    elif u.endswith('/series/all-india-jee/streak'): body={"user_id":"visual-home150","stage":"prelaunch","completed_count":0,"current_streak":0,"best_streak":0,"milestones":[],"days":[],"today_state":"prelaunch","next_milestone":None,"policy":"fixture"}
    elif u.endswith('/series/all-india-jee/history'): body={"items":[]}
    elif u.endswith('/series/all-india-jee'): body={"server_now":1790000000,"today":"2026-10-26","first_date":"2026-12-01","last_date":"2027-01-31","today_slot":None,"slots":[]}
    else: body={}
    await route.fulfill(status=200,content_type='application/json',body=json.dumps(body))

CSS = """
html{scroll-behavior:auto!important}
html.qa-m .exam-home .bold-exam-card, html.qa-m .exam-home .bold-exam-card *{transition:none!important}
html.qa-hide .exam-home .bold-exam-card :is(small,h2,h2 a,p,nav a,.bold-exam-top span,.exam-primary){color:transparent!important;-webkit-text-fill-color:transparent!important;text-shadow:none!important;text-decoration-color:transparent!important}
html.qa-hide .exam-home .bold-exam-card :is(nav a,.exam-primary) svg{visibility:hidden!important}
html.qa-shine .exam-home .bold-exam-card:before{animation:none!important;transform:translateX(var(--qa-x))!important;opacity:1!important}
html.qa-static .exam-home .bold-exam-card:before{animation:none!important;opacity:0!important}
"""

SAMPLER = """async ({url, clip, targets}) => {
  const img = new Image(); img.src = url; await img.decode();
  const c = document.createElement('canvas'); c.width = img.width; c.height = img.height;
  const ctx = c.getContext('2d', {willReadFrequently:true}); ctx.drawImage(img,0,0);
  const sx = img.width/clip.width, sy = img.height/clip.height;
  const data = ctx.getImageData(0,0,img.width,img.height).data;
  const lin = v => { v/=255; return v<=0.04045? v/12.92 : Math.pow((v+0.055)/1.055,2.4); };
  const L = (r,g,b) => 0.2126*lin(r)+0.7152*lin(g)+0.0722*lin(b);
  const out = {};
  for (const t of targets) {
    const Lf = L(...t.fg); const vals=[]; let worst=null;
    for (const r of t.rects) {
      const x0=Math.max(0,Math.floor((r.x-clip.x)*sx)), y0=Math.max(0,Math.floor((r.y-clip.y)*sy));
      const x1=Math.min(img.width,Math.ceil((r.x+r.w-clip.x)*sx)), y1=Math.min(img.height,Math.ceil((r.y+r.h-clip.y)*sy));
      for (let y=y0;y<y1;y++) for (let x=x0;x<x1;x++) {
        const i=(y*img.width+x)*4; const Lb=L(data[i],data[i+1],data[i+2]);
        const cr=(Math.max(Lf,Lb)+0.05)/(Math.min(Lf,Lb)+0.05); vals.push(cr);
        if(!worst||cr<worst.cr) worst={cr,rgb:[data[i],data[i+1],data[i+2]]};
      }
    }
    vals.sort((a,b)=>a-b);
    out[t.key] = {n: vals.length, min: vals.length?vals[0]:null, p1: vals.length?vals[Math.floor(vals.length*0.01)]:null, med: vals.length?vals[Math.floor(vals.length/2)]:null, worstBg: worst&&worst.rgb, img:[img.width,img.height], scale:[sx,sy]};
  }
  return out;
}"""

TARGETS_JS = """(slugs) => {
  const sel = {top:'.bold-exam-top span', eyebrow:'small', title:'h2 a', body:'p', nav_chapters:'nav a:nth-of-type(1)', nav_results:'nav a:nth-of-type(2)', cta:'.exam-primary'};
  const out=[];
  for (const s of slugs) { const card=document.querySelector(`[data-testid="exam-home-exam-card-${s}"]`);
    for (const [k,q] of Object.entries(sel)) { const el=card.querySelector(q); if(!el) continue;
      const m=getComputedStyle(el).color.match(/[\\d.]+/g).map(Number);
      const rects=[]; const w=document.createTreeWalker(el,NodeFilter.SHOW_TEXT);
      while(w.nextNode()){ const n=w.currentNode; if(!n.textContent.trim()) continue; const r=document.createRange(); r.selectNodeContents(n);
        for(const b of r.getClientRects()) if(b.width>0&&b.height>0) rects.push({x:b.left,y:b.top,w:b.width,h:b.height}); }
      out.push({key:s+'.'+k, fg:m.slice(0,3), alpha:m[3]??1, rects, text:el.textContent.trim().slice(0,40)}); } }
  return out; }"""

HEADER_JS = """() => { let hb=0; for (const x of [5, innerWidth/2, innerWidth-5]) for (let el of document.elementsFromPoint(x,2)) { for(let a=el;a&&a!==document.documentElement;a=a.parentElement){ const p=getComputedStyle(a).position; if((p==='sticky'||p==='fixed')){ const r=a.getBoundingClientRect(); if(r.top<=1) hb=Math.max(hb,r.bottom);} } } return hb; }"""
