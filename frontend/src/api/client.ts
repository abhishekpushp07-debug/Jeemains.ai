import { Platform } from "react-native";
import * as Crypto from "expo-crypto";
import Constants from "expo-constants";
import { storage } from "@/src/utils/storage";
import { PrivateAssetQueue } from "@/src/assets/PrivateAssetQueue";
import { Image as ExpoImage } from "expo-image";
import { clearImageGrants, imageGrant, registerImageGrants } from "@/src/assets/assetGrants";
import { configureImageDisk, purgeImageDisk } from "@/src/assets/deviceCache/cache";
import { ImageResponse, loadOriginalImage } from "@/src/assets/imageDownload";

// Native talks to jeelive.ai directly (cookie session, no extra hop).
// Web preview cannot carry jeelive.ai cookies cross-origin, so it uses a thin pass-through proxy.
const WEB = Platform.OS === "web";
const extra = Constants.expoConfig?.extra;
const CANONICAL_API = (extra?.jeeliveApi || process.env.EXPO_PUBLIC_JEELIVE_API) as string;
const BASE = WEB ? `${extra?.backendUrl || process.env.EXPO_PUBLIC_BACKEND_URL}/api/jl` : CANONICAL_API;
export const websiteLoginUrl = () => new URL("/login", CANONICAL_API).href;
export const RF_BASE = `${process.env.EXPO_PUBLIC_BACKEND_URL}/api/rf`;

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
let onAuthLost: (() => void) | null = null;
export const setAuthLostHandler = (fn: (() => void) | null) => (onAuthLost = fn);

function refresh(): Promise<boolean> {
  if (!refreshing) {
    refreshing = (async () => {
      try {
        const r = await fetch(BASE + "/auth/refresh", { method: "POST", credentials: "include", headers: await headers(true), body: "{}" });
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
    res = await fetch(BASE + path, { method, body, credentials: "include", headers: await headers(body !== undefined), signal: opts.signal });
  } catch (e: any) {
    if (e?.name === "AbortError") throw e;
    throw new ApiError("Connection interrupted. Your last saved work is safe. Please try again.", 0);
  }
  const credentialSubmission = ["/auth/phone", "/auth/phone/signup", "/auth/login"].includes(path);
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
export const clearAssetCache = (purgeDisk = false) => { assetOwner = null; resetImageMemory(); if (purgeDisk) purgeImageDisk(); };
export const setAssetAccount = (uid: string) => {
  if (assetOwner !== uid) { resetImageMemory(); configureImageDisk(uid, CANONICAL_API); }
  assetOwner = uid; privateAssets.resume();
};
export const registerAssetManifest = (id: string, rows: any[], solutions: boolean, version = "original", renew = false) => {
  if (assetOwner) registerImageGrants(id, rows, solutions, version, path => privateAssets.invalidate(path), renew);
};
export const assetDataUri = (path: string) => privateAssets.get(path, 100);

// Rapid Fire (JEELIVE companion service)
export async function rf<T = any>(path: string, userId: string, opts: { method?: string; body?: unknown } = {}): Promise<T> {
  let res: Response;
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), 15000);
  try {
    res = await fetch(RF_BASE + path, {
      signal: ctl.signal,
      method: opts.method || "GET",
      headers: { "Content-Type": "application/json", "X-RF-User": userId },
      body: opts.body === undefined ? undefined : JSON.stringify(opts.body),
    });
  } catch {
    clearTimeout(timer);
    throw new ApiError(ctl.signal.aborted ? "Rapid Fire is taking too long. Check your connection and retry." : "You're offline. Rapid Fire needs a connection to load cards.", 0);
  }
  clearTimeout(timer);
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(typeof data?.detail === "string" ? data.detail : "Rapid Fire is unavailable right now. Retry.", res.status);
  return data as T;
}
