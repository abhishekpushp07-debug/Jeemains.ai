import { Platform } from "react-native";
import * as Crypto from "expo-crypto";
import { storage } from "@/src/utils/storage";

// Native talks to jeelive.ai directly (cookie session, no extra hop).
// Web preview cannot carry jeelive.ai cookies cross-origin, so it uses a thin pass-through proxy.
const WEB = Platform.OS === "web";
const BASE = WEB ? `${process.env.EXPO_PUBLIC_BACKEND_URL}/api/jl` : (process.env.EXPO_PUBLIC_JEELIVE_API as string);
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
async function sessionHandle() {
  if (!WEB) return null;
  if (sid) return sid;
  sid = await storage.getItem<string | null>("jl_sid", null);
  if (!sid) {
    sid = uuid();
    await storage.setItem("jl_sid", sid);
  }
  return sid;
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
export const setAuthLostHandler = (fn: () => void) => (onAuthLost = fn);

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
  return Number.isFinite(n) ? n * 1000 : Math.max(0, Date.parse(hint) - Date.now());
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
  if (res.status === 401 && retry && !path.startsWith("/auth/")) {
    if (await refresh()) return apiRaw<T>(path, opts, false);
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

// Authenticated binary (question / solution source image) → data URI, account-scoped memory cache.
const assetCache = new Map<string, string>();
export const clearAssetCache = () => assetCache.clear();
export async function assetDataUri(path: string, retry = true): Promise<string> {
  const hit = assetCache.get(path);
  if (hit) return hit;
  const h = await headers(false);
  h.Accept = "image/png,image/*";
  const res = await fetch(BASE + path, { credentials: "include", headers: h });
  if (res.status === 401 && retry && (await refresh())) return assetDataUri(path, false);
  if (!res.ok) throw new ApiError("The original image could not load. Retry.", res.status);
  const blob = await res.blob();
  const uri: string = await new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve(String(reader.result));
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
  assetCache.set(path, uri);
  return uri;
}

// Rapid Fire (JEELIVE companion service)
export async function rf<T = any>(path: string, userId: string, opts: { method?: string; body?: unknown } = {}): Promise<T> {
  let res: Response;
  try {
    res = await fetch(RF_BASE + path, {
      method: opts.method || "GET",
      headers: { "Content-Type": "application/json", "X-RF-User": userId },
      body: opts.body === undefined ? undefined : JSON.stringify(opts.body),
    });
  } catch {
    throw new ApiError("You're offline. Rapid Fire needs a connection to load cards.", 0);
  }
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(typeof data?.detail === "string" ? data.detail : "Rapid Fire is unavailable right now. Retry.", res.status);
  return data as T;
}
