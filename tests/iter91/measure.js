() => {
  const q = id => document.querySelector(`[data-testid="${id}"]`);
  const R = el => { const r = el.getBoundingClientRect(); return {x:+r.x.toFixed(1), y:+r.y.toFixed(1), w:+r.width.toFixed(1), h:+r.height.toFixed(1), b:+r.bottom.toFixed(1), r:+r.right.toFixed(1)}; };
  const out = {vw: innerWidth, docSW: document.documentElement.scrollWidth, bodySW: document.body.scrollWidth};
  const ids = ["mission-screen","mission-share-top","mission-card","mission-share-bottom","mission-share-more","mission-points","mission-disclaimer"];
  out.rects = {}; ids.forEach(i => { const e = q(i); out.rects[i] = e ? R(e) : null; });
  const card = q("mission-card"); const cr = card.getBoundingClientRect();
  out.ratio = +(cr.height/cr.width).toFixed(4);
  // text leaves in card
  const textRect = (el) => { const rg = document.createRange(); rg.selectNodeContents(el); return rg.getBoundingClientRect(); };
  const leaves = [...card.querySelectorAll('div,span')].filter(e => e.childElementCount===0 && e.textContent.trim());
  out.cardTexts = leaves.map(e => { const tr = textRect(e); return {t:e.textContent.trim().slice(0,40), x:+tr.x.toFixed(1), y:+tr.y.toFixed(1), r:+tr.right.toFixed(1), b:+tr.bottom.toFixed(1),
     overflowX: e.scrollWidth > e.clientWidth+1, overflowY: e.scrollHeight > e.clientHeight+1, clamp: getComputedStyle(e).webkitLineClamp, outside: tr.right>cr.right+0.5||tr.bottom>cr.bottom+0.5||tr.x<cr.x-0.5}; });
  // ribbon
  const rib = leaves.find(e => e.textContent.includes("MADE BY AI ASTRA"));
  const eyebrow = leaves.find(e => e.textContent.includes("EK CHHOTI SI BAAT"));
  if (rib) {
    const rg = document.createRange(); rg.selectNodeContents(rib);
    const rects = [...rg.getClientRects()]; const rr = rg.getBoundingClientRect();
    out.ribbonText = {txt: rib.textContent, bbox:{x:rr.x,y:rr.y,r:rr.right,b:rr.bottom}, cardR: cr.right, cardTop: cr.top,
      sw: rib.scrollWidth, cw: rib.clientWidth, ws: getComputedStyle(rib).whiteSpace};
    // check corner glyph positions: rotated text: compute positions of first and last chars
    const n = rib.firstChild; const pts = [];
    if (n && n.nodeType===3) { for (const idx of [0, n.length-1]) { const r2 = document.createRange(); r2.setStart(n, idx); r2.setEnd(n, idx+1); const b = r2.getBoundingClientRect(); pts.push({ch:n.data[idx], cx:+(b.x+b.width/2).toFixed(1), cy:+(b.y+b.height/2).toFixed(1)}); } }
    out.ribbonChars = pts;
    // ribbon band element
    let band = rib.parentElement; while (band && getComputedStyle(band).transform==='none') band = band.parentElement;
    out.ribbonBand = band ? R(band) : null;
    const er = textRect(eyebrow); out.eyebrow = {x:er.x, r:er.right, y:er.y, b:er.bottom};
  }
  // chips: check Titles and short lines fit
  // buttons
  for (const w of ["top","bottom"]) {
    const b = q("mission-share-"+w);
    const ts = [...b.querySelectorAll('div,span')].filter(e => e.childElementCount===0 && e.textContent.trim());
    out["btn_"+w] = {bg: getComputedStyle(b).backgroundColor, text: b.innerText, hasSvg: !!b.querySelector('svg') || !!b.querySelector('[class*=glyph], i, span[style*=font-family]'),
      texts: ts.map(e => ({t:e.textContent, of: e.scrollWidth>e.clientWidth+1, lines: Math.round(e.getBoundingClientRect().height / parseFloat(getComputedStyle(e).lineHeight||16)) , h:e.getBoundingClientRect().height, lh:getComputedStyle(e).lineHeight, ws:getComputedStyle(e).whiteSpace, color:getComputedStyle(e).color})),
      withWA: /with whatsapp/i.test(b.innerText), aria: b.getAttribute('aria-label')};
  }
  // points
  const pts = q("mission-points"); out.pointsText = pts ? pts.innerText.split("\n").filter(Boolean) : null;
  const scr = q("mission-screen"); out.screenText = scr.innerText.slice(0, 200);
  return out;
}
