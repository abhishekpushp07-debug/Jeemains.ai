(sel) => {
  const root = document.querySelector(sel);
  if (!root) return {missing: sel};
  const rb = root.getBoundingClientRect();
  const out = [];
  root.querySelectorAll('div[dir="auto"], span').forEach(el => {
    const b = el.getBoundingClientRect();
    if (b.width === 0) return;
    const cs = getComputedStyle(el);
    if (el.getAttribute('aria-hidden') === 'true' || cs.visibility === 'hidden' || cs.opacity === '0') return;
    const t = (el.textContent || '').trim().slice(0, 40);
    if (!t) return;
    if (el.scrollWidth > el.clientWidth + 1 && el.children.length === 0) out.push('H-OVERFLOW:' + t + ' ' + el.scrollWidth + '>' + el.clientWidth);
    if (el.scrollHeight > el.clientHeight + 2 && el.children.length === 0 && cs.overflow !== 'visible') out.push('V-CLIP:' + t + ' ' + el.scrollHeight + '>' + el.clientHeight);
    if (b.right > rb.right + 1 || b.left < rb.left - 1) out.push('OUTSIDE:' + t + ' [' + Math.round(b.left) + ',' + Math.round(b.right) + '] root[' + Math.round(rb.left) + ',' + Math.round(rb.right) + ']');
  });
  return {w: Math.round(rb.width), h: Math.round(rb.height), issues: out.slice(0, 15)};
}
