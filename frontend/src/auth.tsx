import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { AppState } from "react-native";
import { advanceAuthEpoch, ApiError, api, clearAssetCache, clearRapidAccess, post, resetSessionHandle, setAssetAccount, setAuthLostHandler } from "@/src/api/client";
import { storage } from "@/src/utils/storage";
import { draftIndex, discardAllDrafts } from "@/src/drafts";

export type User = { id: string; name: string; phone?: string; role: string; exam?: string; access_type?: string; pin_set?: boolean };
type Ctx = {
  user: User | null; ready: boolean; expired: boolean; sessionError: string; signOutWarning: string;
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
  const generation = useRef(0), checking = useRef<Promise<void> | null>(null);
  const invalidateProbe = useCallback(() => { generation.current++; checking.current = null; }, []);

  const forgetPrivateProfile = useCallback(async (purgeDownloads = false) => {
    clearAssetCache(purgeDownloads); clearRapidAccess(); setUser(null);
    await storage.removeItem("jl_user");
    // Pending drafts remain partitioned by the original server-issued user ID.
  }, []);
  const acceptUser = useCallback(async (u: User, version = generation.current, explicit = false) => {
    if (!u || typeof u.id !== "string" || !u.id) throw new Error("The account response could not be verified. Please sign in again.");
    if (version !== generation.current) return u;
    await storage.setItem("jl_user", JSON.stringify(u));
    if (version !== generation.current) return u;
    if (explicit) await storage.removeItem("jl_signed_out");
    if (version !== generation.current) return u;
    setAssetAccount(u.id);
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
      const s = await api<{ user: User | null }>("/auth/session");
      if (version !== generation.current) return;
      if (s?.user) await acceptUser(s.user, version);
      else { advanceAuthEpoch(); await forgetPrivateProfile(); }
    } catch (error: any) {
      if (version === generation.current && error?.name !== "AbortError") {
        if (error instanceof ApiError && error.status === 401) { advanceAuthEpoch(); setExpired(true); await forgetPrivateProfile(); }
        else setSessionError("Couldn't check your session. Connect to the internet and retry, or sign in below.");
      }
    } finally { if (version === generation.current) setReady(true); }
    })();
    checking.current = probe;
    void probe.finally(() => { if (checking.current === probe) checking.current = null; });
    return probe;
  }, [acceptUser, forgetPrivateProfile]);

  useEffect(() => {
    // A cached profile is not proof of authentication; never render it first.
    let mounted = true;
    Promise.resolve().then(() => { if (mounted) void checkSession(); });
    setAuthLostHandler(() => { invalidateProbe(); setExpired(true); setReady(true); void forgetPrivateProfile(); });
    const listener = AppState.addEventListener("change", state => { if (state === "active") void checkSession(); });
    return () => { mounted = false; invalidateProbe(); advanceAuthEpoch(); setAuthLostHandler(null); listener.remove(); };
  }, [checkSession, forgetPrivateProfile, invalidateProbe]);

  const authenticate = useCallback(async (path: string, body: object) => {
    generation.current++; advanceAuthEpoch();
    const version = generation.current;
    const u = await post<User>(path, body);
    if (version !== generation.current) throw Object.assign(new Error("An older sign-in request was stopped."), { name: "AbortError" });
    generation.current++; advanceAuthEpoch(); // Ignore requests begun mid-login.
    return acceptUser(u, generation.current, true);
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
    generation.current++; advanceAuthEpoch();
    if (user && drafts === "discard") await discardAllDrafts(user.id);
    // Prevent native cookies left after an offline logout from silently signing
    // this installation back in. A successful explicit login removes this guard.
    await storage.setItem("jl_signed_out", true);
    try { await post("/auth/logout", {}); setSignOutWarning(""); }
    catch { setSignOutWarning("Signed out on this device. Server sign-out couldn't be confirmed while offline."); }
    await forgetPrivateProfile(true); await resetSessionHandle(); setExpired(false);
  }, [user, forgetPrivateProfile]);
  const pendingDraftCount = useCallback(async () => user ? (await draftIndex(user.id)).length : 0, [user]);
  const value = useMemo(() => ({ user, ready, expired, sessionError, signOutWarning, signIn, signUp, changePin, signOut, checkSession, pendingDraftCount }),
    [user, ready, expired, sessionError, signOutWarning, signIn, signUp, changePin, signOut, checkSession, pendingDraftCount]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
export function useAuth() { const ctx = useContext(AuthContext); if (!ctx) throw new Error("useAuth outside AuthProvider"); return ctx; }