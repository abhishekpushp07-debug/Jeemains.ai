// Who may use the phone's kept things without a line: the account whose session the server last confirmed on this
// phone, for 7 days after that confirmation (the owner's rule). Signing out, or a session the server ended, closes it.
import React, { useEffect, useState } from "react";
import { StyleSheet, View } from "react-native";
import { usePathname, useRouter } from "expo-router";
import { useAuth } from "@/src/auth";
import { onAppSwitches } from "@/src/api/client";
import { ARENA } from "@/src/arenaMode";
import { Button, T } from "@/src/components/ui";
import { storage } from "@/src/utils/storage";
import { colors, space } from "@/src/theme";
import { bankView, openBank, syncBank } from "./bank";
import { holdKeeping, keepResults } from "./papers";
import { sendRounds, useKeptRounds } from "./rounds";

const STAMP = "kept.confirmed.v1", DAYS = 7;
export type Who = { uid: string; name: string };

/** The account that may play from the phone without a line, or null. */
export async function offlineIdentity(): Promise<Who | null> {
  try {
    if (await storage.getItem<boolean>("jl_signed_out", false)) return null;
    const stamp = JSON.parse((await storage.getItem<string | null>(STAMP, null)) || "null");
    const age = Date.now() - Number(stamp?.at);
    // A phone whose clock was set back does not get more days out of it.
    return stamp && typeof stamp.uid === "string" && stamp.uid && age > -86400000 && age < DAYS * 86400000 ? { uid: stamp.uid, name: typeof stamp.name === "string" ? stamp.name : "" } : null;
  } catch { return null; }
}

/** Mounted once, beside the other background helpers: notes each confirmed session, and keeps the phone's copy fresh. */
export function OfflineKeeper() {
  const { user, ready, expired } = useAuth();
  useEffect(() => {
    if (!ready) return;
    if (!user) { if (expired) void storage.removeItem(STAMP); return; } // the server ended the session: nothing opens without a line
    void storage.setItem(STAMP, JSON.stringify({ uid: user.id, name: user.name || "", at: Date.now() }));
    // After the first screen has drawn, in the owner's order: rounds played without a line go up, Rapid Fire's cards are
    // brought up to date, then the finished papers (JEE Main first, then BITSAT) with their results and pictures.
    const fetchAll = () => sendRounds(user.id).catch(() => {}).then(() => syncBank(user.id)).then(() => keepResults(user.id));
    const timer = setTimeout(() => { void fetchAll(); }, 4000);
    // The owner's switch for kept papers arrives a moment after sign-in; if it came late, the papers start then.
    const heard = onAppSwitches(() => { void syncBank(user.id).then(() => keepResults(user.id)); });
    return () => { clearTimeout(timer); heard(); };
  }, [user, ready, expired]);
  // A paper being attempted, or a Rapid Fire round being played (not its lobby), has the line and the phone to itself:
  // nothing is fetched in the background meanwhile.
  const pathname = usePathname();
  useEffect(() => { holdKeeping(pathname.startsWith("/attempt/") || pathname.startsWith("/rapid/")); }, [pathname]);
  // Rounds still waiting while the app stays open (the line dropped at the end of a sprint): tried again every 45 seconds.
  const uid = user?.id, waiting = useKeptRounds(uid);
  useEffect(() => {
    if (!uid || !waiting) return;
    const timer = setInterval(() => { void sendRounds(uid).catch(() => {}); }, 45000);
    return () => clearInterval(timer);
  }, [uid, waiting]);
  return null;
}

/**
 * The way in without a line: shown only when this phone has the cards and a session that was confirmed lately.
 * `after` waits that long first (the app's own session check gets its chance).
 */
export function OfflineDoor({ after = 0, note = "Internet nahi mil raha?" }: { after?: number; note?: string }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  useEffect(() => {
    let alive = true;
    const timer = setTimeout(async () => {
      const [who] = await Promise.all([offlineIdentity(), openBank()]);
      if (alive && who && bankView().ready) setOpen(true);
    }, after);
    return () => { alive = false; clearTimeout(timer); };
  }, [after]);
  if (!open) return null;
  return <View testID="offline-door" style={styles.door}>
    <T testID="offline-door-note" size={13} color={colors.muted} style={styles.center}>{note}</T>
    <Button testID="offline-door-button" kind="secondary" icon="lightning-bolt" label={ARENA ? "Bina internet Rapid Fire khelo" : "Bina internet: Rapid Fire aur results"} onPress={() => router.push("/offline" as any)} />
  </View>;
}

const styles = StyleSheet.create({ door: { gap: space.sm, alignSelf: "stretch", paddingHorizontal: space.lg, maxWidth: 420 }, center: { textAlign: "center" } });
