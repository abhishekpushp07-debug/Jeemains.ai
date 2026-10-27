import { Platform } from "react-native";
import * as Crypto from "expo-crypto";
import Constants from "expo-constants";
import { storage } from "@/src/utils/storage";
import { PrivateAssetQueue } from "@/src/assets/PrivateAssetQueue";
import { Image as ExpoImage } from "expo-image";
import { clearImageGrants, imageGrant, registerImageGrants } from "@/src/assets/assetGrants";
import { configureImageDisk, purgeImageDisk } from "@/src/assets/deviceCache/cache";
import { ImageResponse, loadOriginalImage } from "@/src/assets/imageDownload";
import { resources } from "@/src/resourceCache";

// Native talks to jeelive.ai directly (cookie session, no extra hop).
// Web preview cannot carry jeelive.ai cookies cross-origin, so it uses a thin pass-through proxy.
const WEB = Platform.OS === "web";
const extra = Constants.expoConfig?.extra;
const CANONICAL_API = (extra?.jeeliveApi || process.env.EXPO_PUBLIC_JEELIVE_API) as string;
const BASE = WEB ? `${extra?.backendUrl || process.env.EXPO_PUBLIC_BACKEND_URL}/api/jl` : CANONICAL_API;
export const websiteLoginUrl = () => new URL("/login", CANONICAL_API).href;
export const RF_BASE = `${extra?.backendUrl || process.env.EXPO_PUBLIC_BACKEND_URL}/api/rf`;

export const uuid = () => Crypto.randomUUID();

export class ApiError extends Error {
  status: number;
  retryAfterMs: number;
  code?: string;
  constructor(message: string, status = 0, retryAfterMs = 0, code?: string) {
    super(message);
    this.status = status;
    this.retryAfterMs = retryAfterMs;
    this.code = code;
  }
}

let sid: string | null = null;
let sidFlight: Promise<string> | null = null;
async function sessionHandle() {
  if (!WEB) return null;
  if (sid) return sid;
  if (!sidFlight) sidFlight = (async () => {
    sid = await storage.getItem<string | null>("jl_sid", null);
    if (!sid) { sid = uuid(); await storage.setItem("jl_sid", sid); }
    return sid;
  })().finally(() => { sidFlight = null; });
  return sidFlight;
}
export async function resetSessionHandle() {
  sid = null;
  if (WEB) await storage.removeItem("jl_sid");
}

async function headers(json: boolean) {
  const h: Record<string, string> = { Accept: "application/json" };
  if (json) h["Content-Type"] = "application/json";
  const s = await sessionHandle();
  if (s) h["X-JL-Sid"] = s;
  return h;
}

let refreshing: Promise<boolean> | null = null;
async function boundedAuthFetch(url: string, options: RequestInit, ms = 32000, message = "Account service is taking longer than usual. Please try again."): Promise<Response> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), ms);
  try { return await fetch(url, { ...options, signal: controller.signal }); }
  catch (error: any) {
    if (controller.signal.aborted) throw new ApiError(message, 503);
    throw error;
  } finally { clearTimeout(timeout); }
}
let nativeAccessCookie = "";
function captureNativeAccess(res: Response) {
  if (WEB) return;
  // Native fetch exposes response cookie headers; browser HttpOnly cookies are
  // never read. Keep only the access cookie in RAM, never PIN or refresh token.
  const raw = res.headers.get("set-cookie") || "";
  const value = /(?:^|,\s*)access_token=([^;,]*)/.exec(raw)?.[1];
  if (value) nativeAccessCookie = value.replace(/^"|"$/g, "");
}
let onAuthLost: (() => void) | null = null;
export const setAuthLostHandler = (fn: (() => void) | null) => (onAuthLost = fn);

function refresh(): Promise<boolean> {
  if (!refreshing) {
    refreshing = (async () => {
      try {
        const r = await boundedAuthFetch(BASE + "/auth/refresh", { method: "POST", credentials: "include", headers: await headers(true), body: "{}" });
        captureNativeAccess(r);
        return r.ok;
      } catch {
        return false;
      }
    })().finally(() => setTimeout(() => (refreshing = null), 0));
  }
  return refreshing;
}

const retryAfter = (r: Response) => {
  const hint = r.headers.get("Retry-After");
  if (!hint) return 0;
  const n = Number(hint);
  const ms = Number.isFinite(n) ? n * 1000 : Date.parse(hint) - Date.now();
  return Number.isFinite(ms) ? Math.max(0, ms) : 0;
};

export type RawResult<T> = { status: number; data: T; retryAfterMs: number };

export async function apiRaw<T = any>(path: string, opts: { method?: string; body?: unknown; signal?: AbortSignal } = {}, retry = true): Promise<RawResult<T>> {
  const method = opts.method || "GET";
  const body = opts.body === undefined ? (method === "GET" ? undefined : "{}") : JSON.stringify(opts.body);
  let res: Response;
  try {
    // Account-scoped JSON freshness is controlled by our explicit cache, never
    // a browser HTTP cache shared across different X-JL-Sid sessions.
    const options = { method, body, credentials: "include" as const, headers: await headers(body !== undefined), signal: opts.signal,
      ...(WEB ? { cache: "no-store" as const } : {}) };
    res = !opts.signal && (path.startsWith("/auth/") || method === "GET")
      ? await boundedAuthFetch(BASE + path, options, 32000, path.startsWith("/auth/") ? undefined : "The server is taking longer than usual. Please try again.")
      : await fetch(BASE + path, options);
  } catch (e: any) {
    if (e?.name === "AbortError") throw e;
    if (e instanceof ApiError) throw e;
    throw new ApiError("Connection interrupted. Your last saved work is safe. Please try again.", 0);
  }
  const credentialSubmission = ["/auth/phone", "/auth/phone/signup", "/auth/login"].includes(path);
  if (path.startsWith("/auth/")) captureNativeAccess(res);
  const refreshable = !credentialSubmission && !["/auth/refresh", "/auth/logout", "/auth/session"].includes(path);
  if (res.status === 401 && refreshable) {
    if (retry && await refresh()) return apiRaw<T>(path, opts, false);
    onAuthLost?.();
  }
  let payload: any = null;
  try {
    payload = await res.json();
  } catch {}
  if (!res.ok) {
    const d = payload?.error?.message || payload?.detail;
    const msg = typeof d === "string" ? d : Array.isArray(d) ? d.map((x: any) => x.msg).join(". ") : "This request could not finish. Please try again.";
    throw new ApiError(msg, res.status, retryAfter(res), payload?.error?.code);
  }
  const data = payload && Object.prototype.hasOwnProperty.call(payload, "data") && payload.meta?.api_version ? payload.data : payload;
  return { status: res.status, data, retryAfterMs: retryAfter(res) };
}

export const api = async <T = any>(path: string, opts: { method?: string; body?: unknown; signal?: AbortSignal } = {}) => (await apiRaw<T>(path, opts)).data;
export const post = <T = any>(path: string, body: unknown = {}) => api<T>(path, { method: "POST", body });
export const put = <T = any>(path: string, body: unknown) => api<T>(path, { method: "PUT", body });
export const del = <T = any>(path: string) => api<T>(path, { method: "DELETE", body: {} });

// Protected original bytes: bounded memory-only cache + priority/dedup queue.
// On web use Blob URLs to avoid base64 conversion/copies; native stays in RAM.
async function fetchPrivateAsset(path: string, signal: AbortSignal, extraHeaders: Record<string, string> = {}, retry = true): Promise<ImageResponse> {
  if (!/^\/attempts\/[^/]+\/questions\/[^/]+\/asset\/(question|solution)\/\d+(\?score_version=[^&]+)?$/.test(path)) throw new ApiError("Unsupported private image path.");
  const h = await headers(false);
  h.Accept = "image/png,image/*";
  Object.assign(h, extraHeaders);
  const ctl = new AbortController();
  const stop = () => ctl.abort();
  signal.addEventListener("abort", stop, { once: true });
  if (signal.aborted) ctl.abort();
  const timer = setTimeout(stop, 25000);
  try {
    const res = await fetch(BASE + path, { credentials: "include", headers: h, signal: ctl.signal });
    if (res.status === 401) {
      if (retry && await refresh()) return fetchPrivateAsset(path, signal, extraHeaders, false);
      onAuthLost?.();
    }
    if (!res.ok && res.status !== 304) throw new ApiError(res.status === 429 ? "Image service is busy. Wait a moment and retry." : "The original image could not load. Retry.", res.status, retryAfter(res));
    const bytes = res.status === 304 ? new Uint8Array() : new Uint8Array(await res.arrayBuffer());
    if (signal.aborted || ctl.signal.aborted) throw Object.assign(new Error("Image loading stopped."), { name: "AbortError" });
    return { status: res.status, headers: res.headers, bytes };
  } catch (e) {
    if (signal.aborted || e instanceof ApiError) throw e;
    throw new ApiError("Image connection interrupted. Tap retry when online.", 0);
  } finally { clearTimeout(timer); signal.removeEventListener("abort", stop); }
}
export const privateAssets = new PrivateAssetQueue((path, signal) => loadOriginalImage(path, signal, fetchPrivateAsset), 6, 48 * 1024 * 1024, path => !!imageGrant(path));
let assetOwner: string | null = null;
export const getAssetAccount = () => assetOwner;
let assetEpoch = 0;
export const getAssetEpoch = () => assetEpoch;
const scopeListeners = new Set<() => void>();
export const onAssetScopeReset = (listener: () => void) => { scopeListeners.add(listener); return () => { scopeListeners.delete(listener); }; };
function resetImageMemory() { assetEpoch++; privateAssets.pause(); clearImageGrants(); scopeListeners.forEach(fn => fn()); void ExpoImage.clearMemoryCache().catch(() => {}); }
privateAssets.pause();
export const clearAssetCache = (purgeDisk = false) => { assetOwner = null; resources.clear(); resetImageMemory(); if (purgeDisk) purgeImageDisk(); };
export const setAssetAccount = (uid: string) => {
  if (assetOwner !== uid) { resources.clear(); resetImageMemory(); configureImageDisk(uid, CANONICAL_API); }
  assetOwner = uid; privateAssets.resume();
};
export const registerAssetManifest = (id: string, rows: any[], solutions: boolean, version = "original", renew = false) => {
  if (assetOwner) registerImageGrants(id, rows, solutions, version, path => privateAssets.invalidate(path), renew);
};
export const assetDataUri = (path: string) => privateAssets.get(path, 100);

// Rapid Fire (JEELIVE companion service)
let rfGrant: { token: string; uid: string; until: number } | null = null;
let grantFlight: Promise<string> | null = null;
let rfGeneration = 0;
export function clearRapidAccess() {
  const old = rfGrant;
  rfGrant = null; nativeAccessCookie = ""; rfGeneration++;
  if (old) void fetch(RF_BASE + "/access/revoke", { method: "POST", headers: { Authorization: `Bearer ${old.token}` } }).catch(() => {});
}
export async function rapidAccess(userId: string): Promise<string> {
  if (rfGrant?.uid === userId && rfGrant.until > Date.now() + 30000) return rfGrant.token;
  if (grantFlight) { await grantFlight; if (rfGrant?.uid === userId) return rfGrant.token; }
  const generation = rfGeneration;
  grantFlight = (async () => {
    if (!WEB && !nativeAccessCookie && !await refresh()) throw new ApiError("Reconnect your account to open Rapid Fire.", 401);
    const h: Record<string, string> = { "Content-Type": "application/json" };
    if (WEB) h["X-JL-Sid"] = (await sessionHandle())!;
    const exchange = () => boundedAuthFetch(RF_BASE + "/access", { method: "POST", headers: h, body: JSON.stringify(WEB ? {} : { access_cookie: nativeAccessCookie }) });
    let res = await exchange();
    if (res.status === 401 && await refresh()) res = await exchange();
    const result = await res.json().catch(() => null);
    if (!res.ok || result?.user_id !== userId || generation !== rfGeneration) throw new ApiError(result?.detail || "Your Rapid Fire session could not be verified. Please sign in again.", res.status);
    rfGrant = { token: result.token, uid: result.user_id, until: Date.parse(result.expires_at) };
    return result.token as string;
  })().finally(() => { grantFlight = null; });
  return grantFlight;
}
export async function rf<T = any>(path: string, userId: string, opts: { method?: string; body?: unknown } = {}, retry = true): Promise<T> {
  let res: Response;
  const publicPath = /^\/(catalog|cards)(\?|$)/.test(path);
  const token = publicPath ? null : await rapidAccess(userId);
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), 15000);
  try {
    res = await fetch(RF_BASE + path, {
      signal: ctl.signal,
      method: opts.method || "GET",
      headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: opts.body === undefined ? undefined : JSON.stringify(opts.body),
    });
  } catch {
    clearTimeout(timer);
    throw new ApiError(ctl.signal.aborted ? "Rapid Fire is taking too long. Check your connection and retry." : "You're offline. Rapid Fire needs a connection to load cards.", 0);
  }
  clearTimeout(timer);
  if (res.status === 401 && retry) { rfGrant = null; return rf<T>(path, userId, opts, false); }
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(typeof data?.detail === "string" ? data.detail : "Rapid Fire is unavailable right now. Retry.", res.status);
  if (opts.method && opts.method !== "GET") resources.invalidate(`u.${userId}.rf`);
  return data as T;
}
