// Tiny usage log for the CEO dashboard (page and tool names only) and where a new student came from. Never blocks a page.
import { API } from './api';

const VID = 'jl.vid', SRC = 'jl.src';
const WORD = /^[A-Za-z0-9 ._+-]{1,80}$/;
const PAGES = [[/^\/$/, 'landing'], [/^\/home/, 'home'], [/^\/rank/, 'rank'], [/^\/mission/, 'mission'],
  [/^\/series\/all-india-jee\/analysis/, 'aits_analysis'], [/^\/series/, 'aits'], [/^\/my-tests/, 'my_tests'], [/^\/misfire/, 'misfire'],
  [/^\/results\//, 'result'], [/^\/attempts\//, 'test'], [/^\/sets\//, 'paper'], [/^\/exams\/jee-main\/pyq/, 'pyq'], [/^\/exams/, 'exams'],
  [/^\/competitions/, 'competitions'], [/^\/book-series/, 'books'], [/^\/profile/, 'profile'], [/^\/signup/, 'signup'], [/^\/login/, 'login']];

export const pageOf = path => PAGES.find(([re]) => re.test(path))?.[1];

function visitor() {
  try {
    let v = localStorage.getItem(VID);
    if (!v) { v = crypto.randomUUID ? crypto.randomUUID() : `v-${Date.now()}-${Math.random().toString(36).slice(2, 12)}`; localStorage.setItem(VID, v); }
    return v;
  } catch { return undefined; }
}

export function track(name, props) {
  try {
    fetch(API + '/events', { method: 'POST', credentials: 'include', keepalive: true, headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, vid: visitor(), ...(props ? { props } : {}) }) }).catch(() => {});
  } catch {}
}

/** First visit only: campaign words in the link, the site that sent the visitor, and the first page. */
export function captureSource() {
  try {
    if (localStorage.getItem(SRC)) return;
    const q = new URLSearchParams(window.location.search), out = {};
    for (const k of ['utm_source', 'utm_medium', 'utm_campaign']) { const v = q.get(k); if (v && WORD.test(v)) out[k] = v; }
    let host = '';
    try { host = document.referrer ? new URL(document.referrer).hostname : ''; } catch {}
    if (host && host !== window.location.hostname && /^[A-Za-z0-9.-]{1,120}$/.test(host)) out.referrer = host;
    const path = window.location.pathname.slice(0, 80);
    if (/^\/[A-Za-z0-9/_-]*$/.test(path)) out.landing = path;
    localStorage.setItem(SRC, JSON.stringify(out));
  } catch {}
}

/** `{ source }` for the sign-up body, or nothing. */
export function withSource() {
  try {
    const s = JSON.parse(localStorage.getItem(SRC) || '{}');
    return s && Object.keys(s).length ? { source: s } : {};
  } catch { return {}; }
}
