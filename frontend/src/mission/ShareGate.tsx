// Shown after every test submission, before the result: the Mission card on royal night blue, "Aapka result taiyaar
// hai", and a red "Share to view results" button above and below the card. One share (WhatsApp or any other app)
// opens the result; closing the share sheet without sending keeps it locked.
import React, { useRef, useState } from "react";
import { ScrollView, StyleSheet, View, useWindowDimensions } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { LinearGradient } from "expo-linear-gradient";
import { StatusBar } from "expo-status-bar";
import Animated, { FadeIn, FadeInDown, ZoomIn, useReducedMotion } from "react-native-reanimated";
import { Press, T, buzz } from "@/src/components/ui";
import { Glyph } from "@/src/components/Glyph";
import { colors, space } from "@/src/theme";
import { useCardWidth } from "./parts";
import { MissionCard } from "./MissionCard";
import { ShareButton, useMissionShare } from "./ShareButton";

/** stage: "ready" result is out, "grading" still being scored, "sealed" released later. */
export function ShareGate({ title, stage, onOpen, onBack }: { title?: string; stage: "ready" | "grading" | "sealed"; onOpen: () => void; onBack: () => void }) {
  const insets = useSafeAreaInsets();
  const w = useCardWidth();
  const narrow = useWindowDimensions().width < 360;
  const reduced = useReducedMotion();
  const enter = (i: number) => reduced ? undefined : FadeInDown.delay(90 * i).duration(380);
  const card = useRef<React.ComponentRef<typeof View>>(null);
  const [thanks, setThanks] = useState(false);
  const { busy, note, share } = useMissionShare(card, () => {
    setThanks(true); buzz("success");
    setTimeout(onOpen, 900); // a short thank-you, then the result
  });
  const heading = stage === "ready" ? "Aapka result taiyaar hai 🎉" : stage === "grading" ? "Aapka result ban raha hai ⏳" : "Aapka result jald khulega 🔒";
  const action = (where: string) => thanks
    ? <Animated.View entering={reduced ? undefined : ZoomIn.duration(260)} testID={`share-gate-thanks${where === "top" ? "" : "-bottom"}`} style={styles.thanks}>
      <Glyph name="heart" size={22} color={colors.onBrandPrimary} />
      <T w="heavy" size={17} color={colors.onBrandPrimary}>Shukriya! Result khul raha hai…</T>
    </Animated.View>
    : <ShareButton testID={where === "top" ? "share-gate-share" : "share-gate-share-bottom"} title="Share to view results" busy={busy} onPress={() => share(true)} />;

  return <View testID="share-gate" style={{ flex: 1, backgroundColor: colors.custom_mBlueNight }}>
    <StatusBar style="light" />
    <LinearGradient colors={[colors.custom_mBlueMid, colors.custom_mBlueTo, colors.custom_mBlueNight]} locations={[0, 0.45, 1]} style={StyleSheet.absoluteFill} />
    <ScrollView contentContainerStyle={{ paddingTop: insets.top + space.sm, paddingBottom: insets.bottom + space.xl, paddingHorizontal: space.lg, gap: space.lg }}>
      <View style={styles.bar}>
        <Press testID="share-gate-back" onPress={onBack} accessibilityLabel="Back" haptic={false} style={styles.back}>
          <Glyph name="chevron-left" size={24} color={colors.custom_mWhite} />
        </Press>
        <View style={styles.badge}><Glyph name="check" size={20} color={colors.custom_mNavy} stroke={2.4} /></View>
        <View style={styles.back} />
      </View>

      <Animated.View entering={enter(0)} style={styles.head}>
        <T w="heavy" size={10.5} color={colors.custom_mGold} style={{ letterSpacing: 2.4 }}>TEST SUBMIT HO GAYA</T>
        <T testID="share-gate-title" w="heavy" size={narrow ? 20 : 24} color={colors.custom_mWhite} style={styles.center}>{heading}</T>
        {title ? <T size={13} color={colors.custom_mInk} numberOfLines={1} style={styles.center}>{title}</T> : null}
        <View style={styles.lock}>
          <Glyph name="lock-outline" size={14} color={colors.custom_mGold} />
          <T w="semibold" size={narrow ? 11.5 : 12.5} color={colors.custom_mInk}>Score, rank aur solutions bas ek share door</T>
        </View>
      </Animated.View>

      <Animated.View entering={enter(1)}>{action("top")}</Animated.View>

      <Animated.View entering={enter(2)} style={styles.cardWrap}>
        <View ref={card} collapsable={false}><MissionCard width={w} /></View>
      </Animated.View>

      <Animated.View entering={enter(3)} style={{ gap: space.sm }}>
        {action("bottom")}
        <Press testID="share-gate-more" onPress={() => share(false)} disabled={busy || thanks} accessibilityLabel="Doosre app se share karke result dekho" style={styles.more}>
          <Glyph name="share-variant" size={16} color={colors.custom_mInk} />
          <T w="semibold" size={13} color={colors.custom_mInk}>Doosre app se share karo</T>
        </Press>
        {note ? <Animated.View entering={reduced ? undefined : FadeIn}><T testID="share-gate-note" w="semibold" size={12.5} color={colors.custom_mGold} style={styles.center}>{note}</T></Animated.View> : null}
      </Animated.View>
    </ScrollView>
  </View>;
}

const styles = StyleSheet.create({
  bar: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  back: { width: 44, height: 44, borderRadius: 22, alignItems: "center", justifyContent: "center", backgroundColor: colors.custom_mGlass },
  head: { alignItems: "center", gap: 6 },
  badge: { width: 40, height: 40, borderRadius: 20, alignItems: "center", justifyContent: "center", backgroundColor: colors.custom_mGold },
  center: { textAlign: "center" },
  lock: { flexDirection: "row", alignItems: "center", gap: 6, marginTop: 4, paddingHorizontal: 12, paddingVertical: 7, borderRadius: 999,
    borderWidth: 1, borderColor: colors.custom_mLine, backgroundColor: colors.custom_mGlass },
  cardWrap: { alignSelf: "center", borderRadius: 22, shadowColor: colors.custom_mBlueNight, shadowOpacity: 0.6, shadowRadius: 22, shadowOffset: { width: 0, height: 12 }, elevation: 10 },
  thanks: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: space.sm, minHeight: 64, borderRadius: 18, backgroundColor: colors.success },
  more: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 6, minHeight: 44 },
});
