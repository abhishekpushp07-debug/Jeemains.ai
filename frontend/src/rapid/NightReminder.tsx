import React, { useEffect, useState } from "react";
import { Platform, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Animated, { FadeInUp, useReducedMotion } from "react-native-reanimated";
import { useAuth } from "@/src/auth";
import { T, buzz } from "@/src/components/ui";
import { arena } from "@/src/theme";
import { useScreenInFront } from "@/src/motion";
import { Alive, GameIcon } from "./Art";
import { Panel, RaisedButton } from "./arena";
import { LiveDot } from "./juice";
import { countdown, dismissNotice, go, inboxAge, refreshInbox, useInbox } from "./social";

/** 7:55 pm: "your Cup Night seat is ready", with the countdown. Shows where the challenge banner shows, when there is no challenge. */
export function NightReminder({ floating }: { floating?: boolean }) {
  const inbox = useInbox(), { user } = useAuth(), router = useRouter(), insets = useSafeAreaInsets();
  const reduced = useReducedMotion();
  const n = inbox?.notices.find((x) => x.kind === "cup_night" && x.night);
  const [closed, setClosed] = useState(""); // gone at once on this phone, before the server answers
  const [, tick] = useState(0);
  const id = n?.id, front = useScreenInFront();
  // Every open arena screen holds a reminder: only the one in front buzzes and counts down.
  useEffect(() => { if (id && front && Platform.OS !== "web") buzz("warning"); }, [id]); // eslint-disable-line react-hooks/exhaustive-deps -- browsers block vibration until the page is tapped
  useEffect(() => {
    if (!id || !front) return;
    const iv = setInterval(() => tick((k) => k + 1), 1000);
    return () => clearInterval(iv);
  }, [id, front]);
  if (!n?.night || !user || closed === n.id) return null;
  const left = Math.max(0, Math.round(n.night.starts_in - inboxAge()));
  if (!left) return null;
  const done = (open: boolean) => {
    setClosed(n.id);
    dismissNotice(user.id, n.id).then(() => refreshInbox(user.id)).catch(() => {});
    if (open) router.push(go.night());
  };
  return <Animated.View entering={reduced ? undefined : FadeInUp.duration(260)} style={floating ? [styles.float, { top: insets.top + 8 }] : undefined}>
    <Panel gold testID="rf-night-reminder" style={styles.panel}>
      <View style={styles.row}>
        <Alive kind="wiggle"><GameIcon name="trophy" size={46} /></Alive>
        <View style={styles.flex}>
          <View style={styles.row}><LiveDot size={7} /><T w="heavy" size={10.5} color={arena.danger} style={styles.spaced} numberOfLines={1}>CUP NIGHT · {n.night.time_label.toUpperCase()}</T></View>
          <T testID="rf-night-reminder-title" w="heavy" size={15} color={arena.text} numberOfLines={1}>Your seat is ready!</T>
          <T testID="rf-night-reminder-left" w="bold" size={12} color={arena.gold} numberOfLines={2}>Starts in {countdown(left)}. Your first match starts by itself.</T>
        </View>
      </View>
      <View style={styles.row}>
        <RaisedButton testID="rf-night-reminder-later" label="Later" tone="wine" height={44} onPress={() => done(false)} style={styles.flex} />
        <RaisedButton testID="rf-night-reminder-open" label="OPEN" icon="trophy" height={44} onPress={() => done(true)} style={styles.open} />
      </View>
    </Panel>
  </Animated.View>;
}

const styles = StyleSheet.create({
  float: { position: "absolute", left: 12, right: 12, zIndex: 40, maxWidth: 536, alignSelf: "center" },
  panel: { padding: 12, gap: 10 }, row: { flexDirection: "row", alignItems: "center", gap: 8 }, flex: { flex: 1, minWidth: 0 }, open: { flex: 1.4 },
  spaced: { letterSpacing: 1.5 },
});
