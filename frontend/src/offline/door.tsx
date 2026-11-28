// The phone's kept things while the app is open (OfflineKeeper), and the way in without a line (OfflineDoor).
// Who may come in: ./identity.ts. While the app is closed the phone's own background run does the same keeping:
// ./background.ts.
import React, { useEffect, useState } from "react";
import { StyleSheet, View } from "react-native";
import { usePathname, useRouter } from "expo-router";
import { nameOf, useAuth } from "@/src/auth";
import { onAppSwitches } from "@/src/api/client";
import { ARENA } from "@/src/arenaMode";
import { Button, T } from "@/src/components/ui";
import { storage } from "@/src/utils/storage";
import { colors, space } from "@/src/theme";
import { scheduleKeeping } from "./background";
import { bankView, openBank, syncBank } from "./bank";
import { forgetConfirmed, noteConfirmed, offlineIdentity } from "./identity";
import { holdKeeping, keepResults } from "./papers";
import { sendRounds, useKeptRounds } from "./rounds";
import { sendAllWaiting } from "@/src/misfire/mock/marking";
import { refreshKnown } from "@/src/misfire/mock/offline";

/** Mounted once, beside the other background helpers: notes each confirmed session, and keeps the phone's copy fresh. */
export function OfflineKeeper() {
  const { user, ready, expired } = useAuth();
  useEffect(() => {
    if (!ready) return;
    if (!user) {
      // The server ended the session: nothing opens without a line, and the phone stops its background run. Signed out
      // on purpose: the same. No line at all (no user, nothing ended): the background run stays, it is meant for that.
      if (expired) { void forgetConfirmed(); void scheduleKeeping(false); }
      else void storage.getItem<boolean>("jl_signed_out", false).then((out) => { if (out) void scheduleKeeping(false); });
      return;
    }
    void noteConfirmed({ uid: user.id, name: nameOf(user) });
    void scheduleKeeping(true);
    // After the first screen has drawn, in the owner's order: rounds played without a line go up (and the right answers
    // of Offline Misfires given without one), Rapid Fire's cards are brought up to date, then the finished papers (JEE
    // Main first, then BITSAT) with their results and pictures, then what Misfire last said is understood.
    const fetchAll = () => sendRounds(user.id).catch(() => {}).then(() => sendAllWaiting()).then(() => syncBank(user.id)).then(() => keepResults(user.id))
      .then(() => refreshKnown(user.id));
    const timer = setTimeout(() => { void fetchAll(); }, 4000);
    // The owner's switch for kept papers arrives a moment after sign-in; if it came late, the papers start then.
    const heard = onAppSwitches(() => { void syncBank(user.id).then(() => keepResults(user.id)); });
    return () => { clearTimeout(timer); heard(); };
  }, [user, ready, expired]);
  // A paper being attempted, or a Rapid Fire round being played (not its lobby), has the line and the phone to itself:
  // nothing is fetched in the background meanwhile.
  const pathname = usePathname();
  // A paper, a Rapid Fire round or a Misfire Mock being taken: nothing is fetched in the background meanwhile.
  useEffect(() => {
    holdKeeping(pathname.startsWith("/attempt/") || pathname.startsWith("/rapid/") || (pathname.startsWith("/misfire/mock/") && pathname !== "/misfire/mock/new")
      || (pathname.startsWith("/offline/misfire/") && pathname !== "/offline/misfire/new"));
  }, [pathname]);
  // Rounds still waiting while the app stays open (the line dropped at the end of a sprint): tried again every 45 seconds.
  const uid = user?.id, waiting = useKeptRounds(uid);
  useEffect(() => {
    if (!uid || !waiting) return;
    const timer = setInterval(() => { void sendRounds(uid).catch(() => {}); }, 45000);
    return () => clearInterval(timer);
  }, [uid, waiting]);
  // The same for Offline Misfire's right answers still waiting (the line dropped after a mock): every 45 seconds.
  useEffect(() => {
    if (!uid) return;
    const timer = setInterval(() => { void sendAllWaiting(); }, 45000);
    return () => clearInterval(timer);
  }, [uid]);
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
