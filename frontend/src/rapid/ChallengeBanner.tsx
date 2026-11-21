import React, { useEffect, useState } from "react";
import { StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Animated, { FadeInUp, useReducedMotion } from "react-native-reanimated";
import { rf } from "@/src/api/client";
import { useAuth } from "@/src/auth";
import { T, buzz } from "@/src/components/ui";
import { Avatar } from "@/src/components/Entry";
import { arena } from "@/src/theme";
import { useScreenInFront } from "@/src/motion";
import { Emblem } from "./Art";
import { Panel, RaisedButton } from "./arena";
import { NightReminder } from "./NightReminder";
import { clock, go, inboxAge, refreshInbox, shortSubject, useInbox } from "./social";

/** Incoming challenge with Accept / Decline and the time left. `floating` pins it under the status bar (Home and inner arena screens). */
export function ChallengeBanner({ floating }: { floating?: boolean }) {
  const inbox = useInbox(), { user } = useAuth(), router = useRouter(), insets = useSafeAreaInsets();
  const reduced = useReducedMotion();
  const c = inbox?.challenges[0];
  const [busy, setBusy] = useState("");
  const [, tick] = useState(0);
  const id = c?.id, front = useScreenInFront();
  // Every open arena screen holds a banner: only the one in front buzzes and counts down.
  useEffect(() => { if (id && front) buzz("warning"); }, [id]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!id || !front) return;
    const iv = setInterval(() => tick((n) => n + 1), 1000);
    return () => clearInterval(iv);
  }, [id, front]);
  if (!c || !user) return <NightReminder floating={floating} />;
  const left = Math.max(0, Math.round(c.expires_in - inboxAge()));
  if (!left) return null;
  const act = async (what: "accept" | "decline") => {
    setBusy(what);
    try {
      const room = await rf<any>(`/challenges/${c.id}/${what}`, user.id, { method: "POST", body: {} });
      if (what === "accept") router.push(go.room({ id: c.id, duel_id: room.duel_id }));
    } catch { /* closed or full: the refreshed inbox removes the banner */ }
    await refreshInbox(user.id);
    setBusy("");
  };
  return <Animated.View entering={reduced ? undefined : FadeInUp.duration(260)} style={floating ? [styles.float, { top: insets.top + 8 }] : undefined}>
    <Panel gold testID="rf-challenge-banner" style={styles.panel}>
      <View style={styles.row}>
        {c.gang ? <Emblem id={c.gang.emblem} size={46} /> : <Avatar icon={c.from.avatar} frame={c.from.frame} size={44} />}
        <View style={styles.flex}>
          <T testID="rf-challenge-banner-title" w="heavy" size={15} color={arena.text} numberOfLines={1}>{c.gang ? `${c.gang.name} · ${c.from.name}’s gang challenge` : `${c.from.name} challenged you`}</T>
          <T testID="rf-challenge-banner-meta" w="bold" size={12} color={arena.aqua} numberOfLines={1}>{shortSubject(c.subject)}{c.chapter ? ` · ${c.chapter}` : ""}{c.single ? "" : ` · ${c.joined}/${c.seats} joined`} · {clock(left)} left</T>
        </View>
      </View>
      <View style={styles.row}>
        <RaisedButton testID="rf-challenge-banner-decline" label="Decline" tone="wine" height={44} busy={busy === "decline"} disabled={!!busy} onPress={() => act("decline")} style={styles.flex} />
        <RaisedButton testID="rf-challenge-banner-accept" label="ACCEPT" icon="swords" height={44} busy={busy === "accept"} disabled={!!busy} onPress={() => act("accept")} style={styles.accept} />
      </View>
    </Panel>
  </Animated.View>;
}

const styles = StyleSheet.create({
  float: { position: "absolute", left: 12, right: 12, zIndex: 40, maxWidth: 536, alignSelf: "center" },
  panel: { padding: 12, gap: 10 }, row: { flexDirection: "row", alignItems: "center", gap: 10 }, flex: { flex: 1, minWidth: 0 }, accept: { flex: 1.4 },
});
