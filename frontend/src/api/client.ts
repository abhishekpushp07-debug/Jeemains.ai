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
import { requestDeadline, RequestDeadlineError } from "./requestDeadline";
import { ARENA } from "@/src/arenaMode";

// Every platform talks to jeelive.ai through our thin pass-through proxy: browsers cannot carry jeelive.ai
// cookies cross-origin, and some phones cannot reach jeelive.ai directly ("Connection interrupted" at sign-in).
// The proxy keeps this device's jeelive.ai cookies in a server-side jar named by the X-JL-Sid handle.
const WEB = Platform.OS === "web";
const extra = Constants.expoConfig?.extra;
const CANONICAL_API = (extra?.jeeliveApi || process.env.EXPO_PUBLIC_JEELIVE_API) as string;
// The browser arena is served by our own server, so it always talks to the server it came from.
export const BACKEND = (ARENA ? window.location.origin : extra?.backendUrl || process.env.EXPO_PUBLIC_BACKEND_URL) as string;
// A build made without its server address fails every request the same way as being offline: say which it is.
const NO_SERVER = "This app build is missing its server address. Please install the latest build.";
const offline = (message: string) => new ApiError(BACKEND ? message : NO_SERVER, 0);
const BASE = `${BACKEND}/api/jl`;
export const websiteLoginUrl = () => new URL("/login", CANONICAL_API).href;
export const websiteHomeUrl = () => new URL("/", CANONICAL_API).href;
export const RF_BASE = `${BACKEND}/api/rf`;

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

// The handle unlocks this device's cookie jar, so on a phone it lives in the Keychain.
const SID_KEY = "jl_sid";
let sid: string | null = null;
let sidFlight: Promise<string> | null = null;
async function sessionHandle() {
  if (sid) return sid;
  if (!sidFlight) sidFlight = (async () => {
    // A phone whose Keychain refuses the write keeps it in app storage, so it is not signed out on every launch.
    sid = (WEB ? null : await storage.secureGet<string | null>(SID_KEY, null)) || await storage.getItem<string | null>(SID_KEY, null);
    if (!sid) { sid = uuid(); if (WEB || !await storage.secureSet(SID_KEY, sid)) await storage.setItem(SID_KEY, sid); }
    return sid;
  })().finally(() => { sidFlight = null; });
  return sidFlight;
}
export async function resetSessionHandle() {
  sid = null;
  if (!WEB) await storage.secureRemove(SID_KEY);
  await storage.removeItem(SID_KEY);
}

async function headers(json: boolean) {
  const h: Record<string, string> = { Accept: "application/json" };
  if (json) h["Content-Type"] = "application/json";
  h["X-JL-Sid"] = await sessionHandle();
  return h;
}

let authEpoch = 0, tokenRevision = 0;
export const advanceAuthEpoch = () => { authEpoch++; };
const requireEpoch = (epoch: number) => {
  if (epoch !== authEpoch) throw Object.assign(new Error("An older session request was stopped."), { name: "AbortError" });
};
let refreshing: { epoch: number; promise: Promise<boolean> } | null = null;
// GET /auth/session may rotate the same cookie as POST /auth/refresh. Keep
// those exchanges ordered; ordinary lists/images remain fully concurrent.
let rotationTail: Promise<unknown> = Promise.resolve();
function rotateSession<T>(epoch: number, run: () => Promise<T>): Promise<T> {
  const operation = rotationTail.then(() => { requireEpoch(epoch); return run(); });
  rotationTail = operation.catch(() => {});
  return operation;
}
async function awaitRecovery<T>(operation: Promise<T>, signal?: AbortSignal): Promise<T> {
  // Cancel this waiter, not a renewal shared with another visible screen.
  try { return await requestDeadline(() => operation, 32000, signal); }
  catch (error) {
    if (error instanceof RequestDeadlineError) throw new ApiError("Account verification is taking longer than usual. Please retry.", 503);
    throw error;
  }
}
async function boundedAuthFetch(url: string, options: RequestInit, ms = 32000, message = "Account service is taking longer than usual. Please try again."): Promise<Response> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), ms);
  try { return await fetch(url, { ...options, signal: controller.signal }); }
  catch (error: any) {
    if (controller.signal.aborted) throw new ApiError(message, 503);
    throw error;
  } finally { clearTimeout(timeout); }
}
let onAuthLost: (() => void) | null = null;
export const setAuthLostHandler = (fn: (() => void) | null) => (onAuthLost = fn);

function refresh(): Promise<boolean> {
  const epoch = authEpoch;
  const revision = tokenRevision;
  if (!refreshing || refreshing.epoch !== epoch) {
    const flight = { epoch, promise: Promise.resolve(false) };
    refreshing = flight;
    flight.promise = rotateSession(epoch, async () => {
      try {
        if (revision !== tokenRevision) return true; // queued session check already renewed access
        const h = await headers(true);
        const { r, body } = await requestDeadline(async signal => {
          const r = await fetch(BASE + "/auth/refresh", { method: "POST", credentials: "include", headers: h, body: "{}", signal });
          const body = await r.json().catch(() => null);
          return { r, body };
        }, 32000);
        requireEpoch(epoch);
        if (r.headers.get("content-type")?.includes("text/html")) throw new ApiError("Account verification is temporarily unavailable. Please retry.", 503);
        if (r.ok && body && typeof body === "object" && !Array.isArray(body)) { tokenRevision++; return true; }
        const rejection = body?.error?.message || body?.detail;
        if (r.status === 401 && typeof rejection === "string" && rejection.trim()) return false;
        // Empty/malformed/intermediary401 is not proof that the cookie expired.
        throw new ApiError("Your session could not be renewed right now. Please retry; your saved work is safe.", 503, retryAfter(r));
      } catch (error: any) {
        requireEpoch(epoch);
        if (error instanceof ApiError) throw error;
        throw new ApiError("Connection interrupted while checking your account. Please retry.", 503);
      }
    }).finally(() => { if (refreshing === flight) refreshing = null; });
  }
  return refreshing.promise;
}

const retryAfter = (r: Response) => {
  const hint = r.headers.get("Retry-After");
  if (!hint) return 0;
  const n = Number(hint);
  const ms = Number.isFinite(n) ? n * 1000 : Date.parse(hint) - Date.now();
  return Number.isFinite(ms) ? Math.max(0, ms) : 0;
};

/** Forgot PIN: our server sets the new PIN for this number (no OTP, by the owner's choice). */
export async function resetForgottenPin(phone: string, pin: string, confirm: string) {
  const res = await boundedAuthFetch(`${BACKEND}/api/account/forgot-pin`, {
    method: "POST", headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ phone, new_pin: pin, confirm_pin: confirm }),
  }).catch(error => { throw error instanceof ApiError ? error : offline("Connection interrupted. Please try again."); });
  if (res.ok) return;
  const data = await res.json().catch(() => null);
  throw new ApiError(typeof data?.detail === "string" ? data.detail : "Couldn't set your new PIN. Please try again.", res.status, retryAfter(res));
}

export type RawResult<T> = { status: number; data: T; retryAfterMs: number };

let validation: { epoch: number; promise: Promise<boolean> } | null = null;
async function confirmSessionEnded(epoch: number): Promise<boolean> {
  requireEpoch(epoch);
  if (!validation || validation.epoch !== epoch) {
    const flight = { epoch, promise: Promise.resolve(false) };
    validation = flight;
    flight.promise = apiRaw<{ user: { id: string } | null }>("/auth/session", {}, false, epoch)
      .then(result => result.data.user === null)
      .catch(error => { if (error instanceof ApiError && error.status === 401) return true; throw error; })
      .finally(() => { if (validation === flight) validation = null; });
  }
  const ended = await validation.promise;
  requireEpoch(epoch);
  return ended;
}
async function recoverUnauthorized(epoch: number, revision: number, retry: boolean, signal?: AbortSignal) {
  requireEpoch(epoch);
  if (retry && (revision !== tokenRevision || await awaitRecovery(refresh(), signal))) { requireEpoch(epoch); return true; }
  if (await awaitRecovery(confirmSessionEnded(epoch), signal)) { requireEpoch(epoch); advanceAuthEpoch(); onAuthLost?.(); }
  return false;
}

export async function apiRaw<T = any>(path: string, opts: { method?: string; body?: unknown; signal?: AbortSignal } = {}, retry = true, epoch = authEpoch): Promise<RawResult<T>> {
  requireEpoch(epoch);
  const revision = tokenRevision;
  const method = opts.method || "GET";
  const body = opts.body === undefined ? (method === "GET" ? undefined : "{}") : JSON.stringify(opts.body);
  let res: Response;
  let payload: any = null;
  try {
    // Account-scoped JSON freshness is controlled by our explicit cache, never
    // a browser HTTP cache shared across different X-JL-Sid sessions.
    const options = { method, body, credentials: "include" as const, headers: await headers(body !== undefined), signal: opts.signal,
      ...(WEB ? { cache: "no-store" as const } : {}) };
    // Supplying a cancellation signal must not disable the request deadline.
    // Keep it active through JSON consumption, including slow/chunked bodies.
    const receive = () => requestDeadline(async signal => {
      requireEpoch(epoch);
      const response = await fetch(BASE + path, { ...options, signal });
      const data = response.status === 204 ? null : await response.json().catch(() => {
        if (response.ok) throw new ApiError("The server response was incomplete. Please retry.", 503);
        return null;
      });
      const inner = data?.meta?.api_version ? data.data : data;
      if (path === "/auth/session" && response.ok && typeof inner?.user?.id === "string" && inner.user.id) {
        requireEpoch(epoch); tokenRevision++;
      }
      return { response, data };
    }, 32000, opts.signal);
    const received = path === "/auth/session" ? await awaitRecovery(rotateSession(epoch, receive), opts.signal) : await receive();
    res = received.response; payload = received.data;
  } catch (e: any) {
    if (e?.name === "AbortError") throw e;
    if (e instanceof RequestDeadlineError) throw new ApiError("The server is taking longer than usual. Please try again. Your last saved work is safe.", 503);
    if (e instanceof ApiError) throw e;
    throw offline("Connection interrupted. Your last saved work is safe. Please try again.");
  }
  requireEpoch(epoch);
  const data = payload && Object.prototype.hasOwnProperty.call(payload, "data") && payload.meta?.api_version ? payload.data : payload;
  const credentialSubmission = ["/auth/phone", "/auth/phone/signup", "/auth/login", "/auth/pin"].includes(path);
  if (path === "/auth/session") {
    if (res.ok && (!data || !Object.prototype.hasOwnProperty.call(data, "user") || (data.user !== null && (!data.user || typeof data.user.id !== "string" || !data.user.id)))) {
      throw new ApiError("Your session response could not be verified. Please retry.", 503);
    }
    const denial = payload?.error?.message || payload?.detail;
    if (res.status === 401 && (typeof denial !== "string" || !denial.trim())) throw new ApiError("Account verification is temporarily unavailable. Please retry.", 503);
    // /auth/session can return HTTP200 + user:null when only access has expired.
    // Give the canonical refresh cookie one chance before forgetting the account.
    if (retry && (res.status === 401 || (res.ok && data.user === null)) && await awaitRecovery(refresh(), opts.signal)) return apiRaw<T>(path, opts, false, epoch);
  }
  const refreshable = !credentialSubmission && !["/auth/refresh", "/auth/logout", "/auth/session"].includes(path);
  if (res.status === 401 && refreshable) {
    if (await recoverUnauthorized(epoch, revision, retry, opts.signal)) return apiRaw<T>(path, opts, false, epoch);
  }
  if (!res.ok) {
    const d = payload?.error?.message || payload?.detail;
    const msg = typeof d === "string" ? d : Array.isArray(d) ? d.map((x: any) => x.msg).join(". ") : "This request could not finish. Please try again.";
    throw new ApiError(msg, res.status, retryAfter(res), payload?.error?.code);
  }
  return { status: res.status, data, retryAfterMs: retryAfter(res) };
}

export const api = async <T = any>(path: string, opts: { method?: string; body?: unknown; signal?: AbortSignal } = {}) => (await apiRaw<T>(path, opts)).data;
export const post = <T = any>(path: string, body: unknown = {}) => api<T>(path, { method: "POST", body });
export const put = <T = any>(path: string, body: unknown) => api<T>(path, { method: "PUT", body });
export const del = <T = any>(path: string) => api<T>(path, { method: "DELETE", body: {} });

// Protected original bytes: bounded memory-only cache + priority/dedup queue.
// On web use Blob URLs to avoid base64 conversion/copies; native stays in RAM.
async function fetchPrivateAsset(path: string, signal: AbortSignal, extraHeaders: Record<string, string> = {}, retry = true, epoch = authEpoch): Promise<ImageResponse> {
  requireEpoch(epoch);
  const revision = tokenRevision;
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
    requireEpoch(epoch);
    if (res.status === 401) {
      if (await recoverUnauthorized(epoch, revision, retry, signal)) return fetchPrivateAsset(path, signal, extraHeaders, false, epoch);
    }
    if (!res.ok && res.status !== 304) throw new ApiError(res.status === 429 ? "Image service is busy. Wait a moment and retry." : "The original image could not load. Retry.", res.status, retryAfter(res));
    const bytes = res.status === 304 ? new Uint8Array() : new Uint8Array(await res.arrayBuffer());
    if (signal.aborted || ctl.signal.aborted) throw Object.assign(new Error("Image loading stopped."), { name: "AbortError" });
    return { status: res.status, headers: res.headers, bytes };
  } catch (e) {
    if (signal.aborted || (e as any)?.name === "AbortError" || e instanceof ApiError) throw e;
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
  rfGrant = null; rfGeneration++;
  if (old) void fetch(RF_BASE + "/access/revoke", { method: "POST", headers: { Authorization: `Bearer ${old.token}` } }).catch(() => {});
}
export async function rapidAccess(userId: string): Promise<string> {
  if (!userId) throw new ApiError("Signing you in…", 0); // the account is still loading: nothing to exchange yet
  if (rfGrant?.uid === userId && rfGrant.until > Date.now() + 30000) return rfGrant.token;
  if (grantFlight) { await grantFlight.catch(() => {}); if (rfGrant?.uid === userId && rfGrant.until > Date.now() + 30000) return rfGrant.token; }
  const generation = rfGeneration;
  grantFlight = (async () => {
    const h: Record<string, string> = { "Content-Type": "application/json", "X-JL-Sid": await sessionHandle() };
    const exchange = () => boundedAuthFetch(RF_BASE + "/access", { method: "POST", headers: h, body: "{}" });
    let res = await exchange();
    if (res.status === 401 && await refresh()) res = await exchange();
    const result = await res.json().catch(() => null);
    if (generation !== rfGeneration) return ""; // the session changed while this was in flight: ask again for the new one
    if (!res.ok || result?.user_id !== userId) throw new ApiError(result?.detail || "Your Rapid Fire session could not be verified. Please sign in again.", res.status);
    rfGrant = { token: result.token, uid: result.user_id, until: Date.parse(result.expires_at) };
    return result.token as string;
  })().finally(() => { grantFlight = null; });
  return (await grantFlight) || rapidAccess(userId);
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
  if (!res.ok) throw new ApiError(typeof data?.detail === "string" ? data.detail : "Rapid Fire is unavailable right now. Retry.", res.status, retryAfter(res), data?.code);
  if (opts.method && opts.method !== "GET") resources.invalidate(`u.${userId}.rf`);
  return data as T;
}
