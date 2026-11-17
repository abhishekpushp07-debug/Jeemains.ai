// Our Mission: watch-only. The maker's share card on top with a red "Please share karo" WhatsApp button above and
// below it, then the full story in segments, then the fine print.
import React, { useRef, useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, View, useWindowDimensions } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Animated, { FadeInDown, useReducedMotion } from "react-native-reanimated";
import { Press, T } from "@/src/components/ui";
import { Glyph } from "@/src/components/Glyph";
import { DCard, IconCircle, SectionLabel } from "@/src/components/design";
import { colors, space } from "@/src/theme";
import { usesNativeTabs } from "@/src/navigation";
import { useCardWidth } from "@/src/mission/parts";
import { MissionCard } from "@/src/mission/MissionCard";
import { POINTS } from "@/src/mission/copy";
import { shareMission } from "@/src/mission/share";

export default function Mission() {
  const insets = useSafeAreaInsets();
  const w = useCardWidth();
  const reduced = useReducedMotion();
  const enter = (i: number) => reduced ? undefined : FadeInDown.delay(60 * i).duration(320);
  const card = useRef<React.ComponentRef<typeof View>>(null);
  const narrow = useWindowDimensions().width < 360; // small phones: slightly smaller button text
  const [busy, setBusy] = useState(false), [note, setNote] = useState("");
  const share = async (toWhatsApp: boolean) => {
    if (busy) return;
    setBusy(true); setNote("");
    try { setNote(await shareMission(card, toWhatsApp)); }
    catch { setNote("Share nahi khula. Dobara try karo."); }
    finally { setBusy(false); }
  };
  const button = (where: string) => <Press testID={`mission-share-${where}`} onPress={() => share(true)} disabled={busy} scaleTo={0.97}
    accessibilityRole="button" accessibilityLabel="Please share karo aur free education ko support karo" style={styles.cta}>
    {busy ? <ActivityIndicator color={colors.onBrandPrimary} /> : <Glyph name="whatsapp" size={narrow ? 26 : 30} color={colors.onBrandPrimary} />}
    <View style={{ flex: 1 }}>
      <T w="heavy" size={narrow ? 16 : 18} color={colors.onBrandPrimary}>Please share karo</T>
      <T w="semibold" size={narrow ? 12 : 13} color={colors.onBrandPrimary} style={{ opacity: 0.92 }}>aur free education ko support karo</T>
    </View>
  </Press>;

  return <ScrollView testID="mission-screen" style={{ flex: 1, backgroundColor: colors.surface }}
    contentContainerStyle={{ paddingTop: insets.top + space.lg, paddingBottom: (usesNativeTabs ? insets.bottom : 0) + space.xxl, paddingHorizontal: space.lg, gap: space.lg }}>
    <View style={{ gap: 4 }}>
      <T w="heavy" size={10} color={colors.brandText} style={{ letterSpacing: 2.4 }}>JEELIVE.AI · OUR MISSION</T>
      <T w="heavy" size={22}>Ek share, kisi ki free taiyari</T>
    </View>
    {button("top")}
    <View style={styles.cardWrap}><View ref={card} collapsable={false}><MissionCard width={w} /></View></View>
    <View style={{ gap: space.sm }}>
      {button("bottom")}
      <Press testID="mission-share-more" onPress={() => share(false)} accessibilityLabel="Doosre app mein share karo" style={styles.more}>
        <Glyph name="share-variant" size={16} color={colors.muted} />
        <T w="semibold" size={13} color={colors.muted}>Doosre app mein share karo</T>
      </Press>
      {note ? <T testID="mission-share-note" w="semibold" size={12.5} color={colors.custom_softText} style={{ textAlign: "center" }}>{note}</T> : null}
    </View>

    <View style={{ gap: space.sm, marginTop: space.sm }}>
      <SectionLabel title="Poori baat" />
      <DCard testID="mission-points" style={{ padding: 0 }}>
        {POINTS.map((p, i) => <Animated.View key={p.title} entering={enter(i)} style={[styles.point, i > 0 && styles.pointLine]}>
          <IconCircle icon={p.icon} color={colors.custom_mBlueMid} bg={colors.custom_royalTint} line={colors.custom_royalTintLine} size={40} />
          <View style={{ flex: 1, gap: 3 }}>
            <T w="heavy" size={15}>{p.title}</T>
            <T size={13} color={colors.muted} style={{ lineHeight: 19 }}>{p.body}</T>
          </View>
        </Animated.View>)}
      </DCard>
    </View>

    <T size={11} color={colors.custom_eyebrow} testID="mission-disclaimer">
      200+ marks ek practice target hai, guarantee nahi. “PYQ DNA”, “institute se better” aur “100% made by AI Astra” creator ka design approach aur daava hai, koi independent audit nahi. Supplied solutions hi original source hain. NTA se affiliated nahi.
    </T>
  </ScrollView>;
}

const styles = StyleSheet.create({
  // The whole red block is the share button: WhatsApp mark on the left, the two-line ask beside it.
  cta: { flexDirection: "row", alignItems: "center", gap: space.md, minHeight: 64, paddingVertical: space.md, paddingHorizontal: space.lg,
    borderRadius: 18, backgroundColor: colors.brandPrimary },
  cardWrap: { alignSelf: "center", borderRadius: 22, shadowColor: colors.custom_mNavy, shadowOpacity: 0.3, shadowRadius: 18, shadowOffset: { width: 0, height: 10 }, elevation: 8 },
  more: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 6, minHeight: 44 },
  point: { flexDirection: "row", gap: space.md, padding: space.lg, alignItems: "flex-start" },
  pointLine: { borderTopWidth: 1, borderTopColor: colors.custom_barLine },
});
