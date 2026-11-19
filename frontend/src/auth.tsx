import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { AppState } from "react-native";
import { advanceAuthEpoch, ApiError, api, clearAssetCache, clearRapidAccess, post, resetSessionHandle, setAssetAccount, setAuthLostHandler } from "@/src/api/client";
import { storage } from "@/src/utils/storage";
import { draftIndex, discardAllDrafts } from "@/src/drafts";
import { flushDreams, setDreamAccount } from "@/src/dream/store";

// A busy or unreachable server is not a signed-out student: the session check retries by itself (honouring the
// server's Retry-After, spread a little so a crowd does not come back at the same second) before showing an error.
const SESSION_RETRIES = [2000, 5000, 10000, 20000];
const transient = (e: any) => e instanceof ApiError && (e.status === 0 || e.status === 408 || e.status === 429 || e.status >= 500);
const pause = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));
// After a session ends by itself the sign-in screen keeps the number, so coming back needs only the PIN.
const LAST_PHONE = "jl_last_phone", ENDED = "jl_session_ended";
const shownPhone = (p: unknown) => { const n = typeof p === "string" ? p.replace(/[^\d+]/g, "") : ""; return /^\+91\d{10}$/.test(n) ? n.slice(3) : n; };

export type User = { id: string; name: string; phone?: string; role: string; exam?: string; access_type?: string; pin_set?: boolean };
type Ctx = {
  user: User | null; ready: boolean; expired: boolean; sessionError: string; signOutWarning: string;
  lastPhone: string; forgetPhone: () => void;
  signIn: (phone: string, pin: string) => Promise<User>;
  signUp: (phone: string, pin: string, confirm: string) => Promise<User>;
  changePin: (phone: string, pin: string, confirm: string) => Promise<void>;
  signOut: (drafts: "keep" | "discard") => Promise<void>;
  checkSession: () => Promise<void>;
  pendingDraftCount: () => Promise<number>;
};
const AuthContext = createContext<Ctx | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);
  const [expired, setExpired] = useState(false);
  const [sessionError, setSessionError] = useState("");
  const [signOutWarning, setSignOutWarning] = useState("");
  const [lastPhone, setLastPhone] = useState("");
  const generation = useRef(0), checking = useRef<Promise<void> | null>(null);
  const signedIn = useRef(false), ended = useRef(false);
  const invalidateProbe = useCallback(() => { generation.current++; checking.current = null; }, []);

  const forgetPrivateProfile = useCallback(async (purgeDownloads = false) => {
    // Signing out (purgeDownloads) also removes the phone copy of the dreams; an expired session keeps it to sync later.
    clearAssetCache(purgeDownloads); clearRapidAccess(); setDreamAccount(null, purgeDownloads); signedIn.current = false; setUser(null);
    await storage.removeItem("jl_user");
    // Pending drafts remain partitioned by the original server-issued user ID.
  }, []);
  // A session that ended by itself (7 days unused, or ended by the server): the number stays for the sign-in screen.
  // A fresh install that never had an account here is not "ended"; it just shows sign-in.
  const sessionEnded = useCallback(async (version: number, known = false) => {
    const saved = await storage.getItem<string | null>("jl_user", null);
    if (version !== generation.current) return;
    if (known || saved || ended.current) {
      let phone = await storage.getItem<string | null>(LAST_PHONE, null);
      if (!phone && saved) { // accounts signed in before the number was kept: take it from the saved profile
        try { phone = shownPhone(JSON.parse(saved)?.phone) || null; } catch { phone = null; }
        if (phone) await storage.setItem(LAST_PHONE, phone);
      }
      if (version !== generation.current) return;
      if (phone) setLastPhone(phone);
      ended.current = true; setExpired(true);
      await storage.setItem(ENDED, true);
    }
    await forgetPrivateProfile();
  }, [forgetPrivateProfile]);
  const acceptUser = useCallback(async (u: User, version = generation.current, explicit = false) => {
    if (!u || typeof u.id !== "string" || !u.id) throw new Error("The account response could not be verified. Please sign in again.");
    if (version !== generation.current) return u;
    await storage.setItem("jl_user", JSON.stringify(u));
    if (version !== generation.current) return u;
    if (explicit) await storage.removeItem("jl_signed_out");
    if (ended.current) { ended.current = false; await storage.removeItem(ENDED); }
    if (version !== generation.current) return u;
    signedIn.current = true;
    setAssetAccount(u.id); setDreamAccount(u.id);
    setUser(u); setExpired(false); setSessionError(""); setSignOutWarning(""); setReady(true);
    return u;
  }, []);
  const checkSession = useCallback((): Promise<void> => {
    if (checking.current) return checking.current;
    const version = generation.current;
    const probe = (async () => {
    try {
      if (await storage.getItem<boolean>("jl_signed_out", false)) return;
      setSessionError("");
      for (let attempt = 0; ; attempt++) {
        try {
          const s = await api<{ user: User | null }>("/auth/session");
          if (version !== generation.current) return;
          if (s?.user) await acceptUser(s.user, version);
          else { advanceAuthEpoch(); await sessionEnded(version); }
          return;
        } catch (error: any) {
          if (version !== generation.current || !transient(error) || attempt >= SESSION_RETRIES.length) throw error;
          await pause(Math.max(error.retryAfterMs || 0, SESSION_RETRIES[attempt]) + Math.random() * 1500);
          if (version !== generation.current) return;
        }
      }
    } catch (error: any) {
      if (version === generation.current && error?.name !== "AbortError") {
        if (error instanceof ApiError && error.status === 401) { advanceAuthEpoch(); await sessionEnded(version); }
        else if (error instanceof ApiError && error.status === 429) setSessionError("Abhi bahut students ek saath aa rahe hain. Aapka saved kaam safe hai, thodi der baad Retry dabao.");
        else if (error instanceof ApiError && error.status >= 500) setSessionError("Server abhi busy hai. Aapka account aur saved kaam safe hai, thodi der baad Retry dabao.");
        else setSessionError("Couldn't check your session. Connect to the internet and retry, or sign in below.");
      }
    } finally { if (version === generation.current) setReady(true); }
    })();
    checking.current = probe;
    void probe.finally(() => { if (checking.current === probe) checking.current = null; });
    return probe;
  }, [acceptUser, sessionEnded]);

  useEffect(() => {
    // A cached profile is not proof of authentication; never render it first.
    let mounted = true;
    Promise.resolve().then(() => { if (mounted) void checkSession(); });
    setAuthLostHandler(() => { invalidateProbe(); setReady(true); void sessionEnded(generation.current, true); });
    const listener = AppState.addEventListener("change", state => { if (state === "active") void checkSession(); });
    return () => { mounted = false; invalidateProbe(); advanceAuthEpoch(); setAuthLostHandler(null); listener.remove(); };
  }, [checkSession, sessionEnded, invalidateProbe]);
  useEffect(() => {
    // The kept number and the "session ended" note survive an app restart until the next sign-in.
    void Promise.all([storage.getItem<string | null>(LAST_PHONE, null), storage.getItem<boolean>(ENDED, false)]).then(([phone, was]) => {
      if (phone) setLastPhone(current => current || phone);
      if (was && !signedIn.current) { ended.current = true; setExpired(true); }
    });
  }, []);

  const authenticate = useCallback(async (path: string, body: { phone: string; pin: string; confirm_pin?: string }) => {
    generation.current++; advanceAuthEpoch();
    const version = generation.current;
    const u = await post<User>(path, body);
    if (version !== generation.current) throw Object.assign(new Error("An older sign-in request was stopped."), { name: "AbortError" });
    generation.current++; advanceAuthEpoch(); // Ignore requests begun mid-login.
    const accepted = await acceptUser(u, generation.current, true);
    const phone = shownPhone(body.phone);
    if (phone) { setLastPhone(phone); await storage.setItem(LAST_PHONE, phone); }
    return accepted;
  }, [acceptUser]);
  const signIn = useCallback((phone: string, pin: string) => authenticate("/auth/phone", { phone, pin }), [authenticate]);
  const signUp = useCallback((phone: string, pin: string, confirm: string) => authenticate("/auth/phone/signup", { phone, pin, confirm_pin: confirm }), [authenticate]);
  const changePin = useCallback(async (phone: string, pin: string, confirm: string) => {
    if (!user) throw new Error("Sign in before changing your PIN.");
    await post("/auth/pin", { phone, new_pin: pin, confirm_pin: confirm });
    // Canonical endpoint rotates cookies and revokes other sessions. Never log out
    // the current session or replace/reset the learner or their academic records.
    const current = await api<User>("/auth/me");
    if (current.id !== user.id) throw new Error("Session identity changed unexpectedly. Please sign in again.");
    await acceptUser(current);
  }, [user, acceptUser]);

  const signOut = useCallback(async (drafts: "keep" | "discard") => {
    await flushDreams(); // the last dream changes go up while the session still works
    generation.current++; advanceAuthEpoch();
    if (user && drafts === "discard") await discardAllDrafts(user.id);
    // Prevent native cookies left after an offline logout from silently signing
    // this installation back in. A successful explicit login removes this guard.
    await storage.setItem("jl_signed_out", true);
    try { await post("/auth/logout", {}); setSignOutWarning(""); }
    catch { setSignOutWarning("Signed out on this device. Server sign-out couldn't be confirmed while offline."); }
    await forgetPrivateProfile(true); await resetSessionHandle(); setExpired(false);
    // Signing out on purpose leaves no number behind (a shared phone stays private).
    ended.current = false; setLastPhone("");
    await Promise.all([storage.removeItem(LAST_PHONE), storage.removeItem(ENDED)]);
  }, [user, forgetPrivateProfile]);
  const forgetPhone = useCallback(() => { setLastPhone(""); void storage.removeItem(LAST_PHONE); }, []);
  const pendingDraftCount = useCallback(async () => user ? (await draftIndex(user.id)).length : 0, [user]);
  const value = useMemo(() => ({ user, ready, expired, sessionError, signOutWarning, lastPhone, forgetPhone, signIn, signUp, changePin, signOut, checkSession, pendingDraftCount }),
    [user, ready, expired, sessionError, signOutWarning, lastPhone, forgetPhone, signIn, signUp, changePin, signOut, checkSession, pendingDraftCount]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
export function useAuth() { const ctx = useContext(AuthContext); if (!ctx) throw new Error("useAuth outside AuthProvider"); return ctx; }