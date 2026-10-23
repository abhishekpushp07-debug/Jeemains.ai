import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, clearAssetCache, post, resetSessionHandle, setAuthLostHandler } from "@/src/api/client";
import { storage } from "@/src/utils/storage";
import { draftIndex, discardAllDrafts } from "@/src/drafts";

export type User = { id: string; name: string; phone?: string; role: string; exam?: string; access_type?: string };

type Ctx = {
  user: User | null;
  ready: boolean;
  expired: boolean;
  signIn: (phone: string) => Promise<User>;
  signOut: (drafts: "keep" | "discard") => Promise<void>;
  pendingDraftCount: () => Promise<number>;
};

const AuthContext = createContext<Ctx | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);
  const [expired, setExpired] = useState(false);

  useEffect(() => {
    let alive = true;
    (async () => {
      // Instant start: cached profile first, then confirm with the server in the background.
      const cached = await storage.getItem<string | null>("jl_user", null);
      if (cached && alive) {
        try {
          setUser(JSON.parse(cached));
        } catch {}
      }
      if (alive) setReady(true);
      try {
        const s = await api<{ user: User | null }>("/auth/session");
        if (!alive) return;
        if (s?.user) {
          setUser(s.user);
          setExpired(false);
          await storage.setItem("jl_user", JSON.stringify(s.user));
        } else if (cached) {
          setExpired(true);
        }
      } catch {
        /* offline: keep cached profile; server stays authoritative on next call */
      }
    })();
    setAuthLostHandler(() => setExpired(true));
    return () => {
      alive = false;
    };
  }, []);

  const signIn = useCallback(async (phone: string) => {
    const u = await post<User>("/auth/phone", { phone });
    const previous = await storage.getItem<string | null>("jl_user", null);
    if (previous) {
      try {
        if (JSON.parse(previous).id !== u.id) clearAssetCache();
      } catch {}
    }
    setUser(u);
    setExpired(false);
    await storage.setItem("jl_user", JSON.stringify(u));
    return u;
  }, []);

  const signOut = useCallback(
    async (drafts: "keep" | "discard") => {
      if (user && drafts === "discard") await discardAllDrafts(user.id);
      try {
        await post("/auth/logout", {});
      } catch {}
      clearAssetCache();
      await storage.removeItem("jl_user");
      await resetSessionHandle();
      setUser(null);
      setExpired(false);
    },
    [user],
  );

  const pendingDraftCount = useCallback(async () => (user ? (await draftIndex(user.id)).length : 0), [user]);

  const value = useMemo(() => ({ user, ready, expired, signIn, signOut, pendingDraftCount }), [user, ready, expired, signIn, signOut, pendingDraftCount]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const c = useContext(AuthContext);
  if (!c) throw new Error("useAuth outside AuthProvider");
  return c;
}
