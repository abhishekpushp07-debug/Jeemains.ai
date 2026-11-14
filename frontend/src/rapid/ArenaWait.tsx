import React, { useEffect, useRef, useState } from "react";
import { StyleSheet, View } from "react-native";
import { arena } from "@/src/theme";
import { GameIcon } from "@/src/rapid/Art";
import { GoldTitle, RaisedButton } from "@/src/rapid/arena";
import { Radar } from "@/src/rapid/juice";
import { T } from "@/src/rapid/ui";

/** The server answers "arena_busy" when it is packed: matches already being played go first, new ones wait a few seconds. */
export const isArenaBusy = (e: any) => e?.code === "arena_busy";

/**
 * Waits out a packed arena and tries again by itself (same request id, so a retry can never open two matches).
 * `hold(e)` returns true when the error was a packed arena and the wait has started.
 */
export function useArenaWait(retry: () => void) {
  const [until, setUntil] = useState(0), [now, setNow] = useState(0);
  const again = useRef(retry);
  again.current = retry;
  useEffect(() => {
    if (!until) return;
    const iv = setInterval(() => {
      const t = Date.now();
      setNow(t);
      if (t >= until) { setUntil(0); again.current(); }
    }, 250);
    return () => clearInterval(iv);
  }, [until]);
  const hold = (e: any) => {
    if (!isArenaBusy(e)) return false;
    // A little random spread so thousands of phones don't all knock again in the same second.
    const t = Date.now();
    setNow(t);
    setUntil(t + (e.retryAfterMs || 5000) + Math.random() * 2000);
    return true;
  };
  return { waiting: until > 0, left: Math.max(1, Math.ceil((until - now) / 1000)), hold, cancel: () => setUntil(0) };
}

export function ArenaWait({ left, onCancel, testID = "arena-wait" }: { left: number; onCancel?: () => void; testID?: string }) {
  return <View testID={testID} style={styles.wrap} accessibilityLiveRegion="polite">
    <Radar size={200}><GameIcon name="swords" size={84} /></Radar>
    <GoldTitle size={26} center testID={`${testID}-title`}>The arena is packed!</GoldTitle>
    <T testID={`${testID}-left`} w="heavy" size={14} color={arena.aqua} style={styles.center}>Getting you a seat in {left} s…</T>
    <T size={12} color={arena.muted} style={styles.center}>Thousands of students are playing right now. Your match starts by itself, no need to tap.</T>
    {onCancel ? <RaisedButton testID={`${testID}-cancel`} tone="wine" label="Back to the Arena" onPress={onCancel} style={styles.stretch} /> : null}
  </View>;
}

const styles = StyleSheet.create({
  wrap: { flex: 1, alignItems: "center", justifyContent: "center", gap: 12, paddingHorizontal: 24 },
  center: { textAlign: "center" },
  stretch: { alignSelf: "stretch" },
});
