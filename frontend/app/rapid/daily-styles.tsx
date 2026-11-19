import React, { useEffect, useRef, useState } from "react";
import { StyleSheet, View, useWindowDimensions } from "react-native";
import { useRouter } from "expo-router";
import { useAuth } from "@/src/auth";
import { T } from "@/src/components/ui";
import { arena } from "@/src/theme";
import { withRapid } from "@/src/rapid/ui";
import { InnerScreen } from "@/src/rapid/parts";
import { RaisedButton } from "@/src/rapid/arena";
import { AllIndiaCard, playScene } from "@/src/rapid/AllIndiaCard";
import { DAILY_STYLES, DailyLook, setDailyLook, useDaily, useDailyLook } from "@/src/rapid/daily";

/**
 * The five scenes of the All India Rapid card one below the other, with today's real numbers on each. Only the card in the
 * middle of the screen moves and plays its sound (light on older phones). A tap picks the style; it never starts today's one-try round.
 */
function DailyStyles() {
  const uid = useAuth().user?.id || "", router = useRouter();
  const d = useDaily(uid).data, look = useDailyLook();
  const size = Math.min(useWindowDimensions().width, 560) - 32;
  const tops = useRef<Record<number, number>>({}), [live, setLive] = useState(1);
  const onScroll = (y: number, h: number) => {
    const mid = y + h / 2;
    const near = DAILY_STYLES.reduce((best, s) => (Math.abs((tops.current[s.id] ?? 0) + size / 2 - mid) < Math.abs((tops.current[best] ?? 0) + size / 2 - mid) ? s.id : best), 1 as number);
    if (near !== live) setLive(near);
  };
  useEffect(() => { const t = setTimeout(() => playScene(live as DailyLook), 350); return () => clearTimeout(t); }, [live]); // hear the card in view
  const pick = (id: DailyLook) => { setDailyLook(id); router.back(); };
  return <InnerScreen testID="rf-daily-styles" title="All India card" sub="5 styles · tap one to use it" onScroll={onScroll}>
    {DAILY_STYLES.map((s) => <View key={s.id} testID={`rf-daily-style-${s.id}`} style={styles.item} onLayout={(e) => { tops.current[s.id] = e.nativeEvent.layout.y + 40; }}>
      <View style={styles.head}>
        <T w="heavy" size={15} color={arena.gold}>Style {s.id} · {s.name}</T>
        <T w="bold" size={12} color={arena.muted}>{s.line}</T>
      </View>
      <AllIndiaCard d={d} look={s.id} size={size} paused={s.id !== live} testID={`rf-daily-style-card-${s.id}`} onPress={() => pick(s.id)} />
      <RaisedButton testID={`rf-daily-style-use-${s.id}`} label={look === s.id ? "IN USE ✓" : "USE THIS STYLE"} tone={look === s.id ? "wine" : "teal"} disabled={look === s.id} onPress={() => pick(s.id)} />
    </View>)}
  </InnerScreen>;
}

const styles = StyleSheet.create({ item: { gap: 10, marginBottom: 14 }, head: { gap: 2 } });
export default withRapid(DailyStyles);
