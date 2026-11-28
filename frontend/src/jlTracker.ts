// jlTracker.ts · JLive Command Expo tracker v1 (generated for JLive App). No native modules beyond AsyncStorage, expo-constants, expo-router.
import AsyncStorage from "@react-native-async-storage/async-storage";
import Constants from "expo-constants";
import { usePathname } from "expo-router";
import { useEffect } from "react";
import { AppState, AppStateStatus, Linking, Platform } from "react-native";

const KEY = "pk_2jVih2x9csjvI_-9_QR-KPH6";
const ENDPOINT = "https://student-radar-5.emergent.host/api/collect/v1/batch";
const QMAX = 200, AGE = 24 * 3600e3, BATCH = 20, TICK = 5000, HB = 15000, IDLE = 30 * 60e3;
type Ev = { event_id: string; event_name: string; occurred_at: string; anon_id: string; uid?: string; session_id: string; props: Record<string, string | number | boolean | null>; context: Record<string, unknown>; _t: number };

let q: Ev[] = [], anon = "", uid: string | undefined, optedOut = false, ready = false, sending = false, fails = 0, until = 0;
let ssn = { id: "", t: 0 }, screen = "/", started = false;
let shown = "", counted = ""; // the path on screen now / the last one sent as screen_view

const uuid = () => "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => { const r = (Math.random() * 16) | 0; return (c === "x" ? r : (r & 3) | 8).toString(16); });
const save = () => AsyncStorage.setItem("jl_q", JSON.stringify(q.slice(-QMAX))).catch(() => {});
const ctx = () => ({ screen, platform: Platform.OS, os: Platform.OS === "ios" ? "iOS" : Platform.OS === "android" ? "Android" : Platform.OS, device_type: "mobile", app_version: Constants.expoConfig?.version ?? "unknown" });

function session(): string {
  const now = Date.now();
  if (!ssn.id || now - ssn.t > IDLE) { ssn = { id: uuid(), t: now }; push("session_start"); }
  ssn.t = now; AsyncStorage.setItem("jl_ssn", JSON.stringify(ssn)).catch(() => {});
  return ssn.id;
}

function push(name: string, props: Ev["props"] = {}) {
  try {
    if (!ready || (optedOut && name !== "opt_in")) return;
    const sid = name === "session_start" ? ssn.id : session();
    q.push({ event_id: uuid(), event_name: name, occurred_at: new Date().toISOString(), anon_id: anon, uid, session_id: sid, props, context: ctx(), _t: Date.now() });
    q = q.filter((e) => Date.now() - e._t < AGE).slice(-QMAX);
    save();
    if (q.length >= BATCH) flush();
  } catch {}
}

export async function flush() {
  if (!ready || sending || !q.length || Date.now() < until) return;
  sending = true;
  const list = q.slice(0, 50);
  try {
    const r = await fetch(ENDPOINT, { method: "POST", headers: { "Content-Type": "text/plain", "X-JL-Key": KEY }, body: JSON.stringify({ key: KEY, sdk: "expo/1", events: list.map(({ _t, ...e }) => e) }) });
    if (r.ok || (r.status >= 400 && r.status < 429)) { const done = new Set(list.map((e) => e.event_id)); q = q.filter((e) => !done.has(e.event_id)); fails = 0; save(); } else throw new Error(String(r.status));
  } catch { fails = Math.min(fails + 1, 6); until = Date.now() + 2 ** fails * TICK; }
  sending = false;
}

export async function init() {
  AsyncStorage.getItem("jl_ref").then((r) => { const o = r ? JSON.parse(r) : null; if (o && Date.now() - o.t < 2592e6) refCode = o.c; }).catch(() => {})
    .finally(() => { Linking.getInitialURL().then(captureRef).catch(() => {}); Linking.addEventListener("url", (e) => captureRef(e.url)); });
  if (started) return; started = true;
  try {
    const [a, u, o, raw, s] = await Promise.all(["jl_anon", "jl_uid", "jl_optout", "jl_q", "jl_ssn"].map((k) => AsyncStorage.getItem(k)));
    anon = a || uuid(); if (!a) AsyncStorage.setItem("jl_anon", anon).catch(() => {});
    uid = u || undefined; optedOut = o === "1"; q = raw ? JSON.parse(raw) : []; if (s) ssn = JSON.parse(s);
  } catch { anon = anon || uuid(); }
  ready = true;
  push("app_open");
  viewed(); // the screen the app opened on
  setInterval(flush, TICK);
  setInterval(() => { if (AppState.currentState === "active") push("heartbeat"); }, HB);
  AppState.addEventListener("change", (st: AppStateStatus) => {
    if (st === "active") push("heartbeat"); else { push("app_background"); flush(); }
  });
  const EU = (globalThis as any).ErrorUtils;
  if (EU?.getGlobalHandler) {
    const prev = EU.getGlobalHandler();
    EU.setGlobalHandler((err: Error, fatal?: boolean) => { try { push("app_crash_observed", { category: String(err?.name || "Error").slice(0, 60), fatal: !!fatal }); flush(); } catch {} prev?.(err, fatal); });
  }
}

export const track = (name: string, props?: Ev["props"]) => push(name, props);
let refCode: string | null = null;
function captureRef(url: string | null | undefined) {
  const m = url && /[?&]ref=([0-9A-Za-z]{8})(?:&|$)/.exec(url);
  if (m && !refCode) { refCode = m[1].toUpperCase(); AsyncStorage.setItem("jl_ref", JSON.stringify({ c: refCode, t: Date.now() })).catch(() => {}); }
}
export function getRef(): string | null { return refCode; }
export function identify(id: string) { if (!id) return; uid = String(id); AsyncStorage.setItem("jl_uid", uid).catch(() => {}); push("identify", refCode ? { ref: refCode } : {}); flush(); }
export function reset() { uid = undefined; anon = uuid(); ssn = { id: "", t: 0 }; AsyncStorage.multiRemove(["jl_uid", "jl_ssn"]).catch(() => {}); AsyncStorage.setItem("jl_anon", anon).catch(() => {}); }
// opt_out stays queued (alone) until it is delivered; nothing else is recorded until opt_in.
export function optOut() { push("opt_out"); optedOut = true; q = q.filter((e) => e.event_name === "opt_out"); save(); AsyncStorage.setItem("jl_optout", "1").catch(() => {}); flush(); }
export function optIn() { optedOut = false; AsyncStorage.removeItem("jl_optout").catch(() => {}); push("opt_in"); }

function viewed() { if (ready && shown && shown !== counted) { counted = shown; push("screen_view"); } }
export function ScreenTracker(): null {
  const path = usePathname();
  useEffect(() => { if (path) { shown = screen = path; viewed(); } }, [path]);
  return null;
}
