// The big red share button of the Mission card: the whole block is the button, WhatsApp mark on the left, a bold
// ask and "aur free education ko support karo" beside it. Also the share flow behind it (busy, note, fallback).
import React, { useState } from "react";
import { ActivityIndicator, StyleSheet, View, useWindowDimensions } from "react-native";
import { Press, T, buzz } from "@/src/components/ui";
import { Glyph } from "@/src/components/Glyph";
import { colors, space } from "@/src/theme";
import { sendWhatsApp } from "@/src/rapid/social";
import { CAPTION } from "./copy";
import { shareMission } from "./share";

type CardRef = React.RefObject<React.ComponentRef<typeof View> | null>;

/** Shares the card; `onShared` runs once the share went out (or the message-only fallback did), never on a closed sheet. */
export function useMissionShare(card: CardRef, onShared?: () => void) {
  const [busy, setBusy] = useState(false), [note, setNote] = useState("");
  const share = async (toWhatsApp: boolean) => {
    if (busy) return;
    setBusy(true); setNote("");
    try {
      const out = await shareMission(card, toWhatsApp);
      if (out.shared) { setNote(out.note); onShared?.(); }
      else if (onShared) setNote("Share pura nahi hua. Result dekhne ke liye ek baar share karo.");
    } catch {
      // The picture could not go out: send the message with the link instead.
      try { await sendWhatsApp(CAPTION); onShared?.(); }
      catch { setNote("Share nahi khula. Dobara try karo."); buzz("error"); }
    } finally { setBusy(false); }
  };
  return { busy, note, share };
}

export function ShareButton({ testID, title, busy, onPress }: { testID: string; title: string; busy: boolean; onPress: () => void }) {
  const narrow = useWindowDimensions().width < 360;
  return <Press testID={testID} onPress={onPress} disabled={busy} scaleTo={0.97} accessibilityRole="button"
    accessibilityLabel={`${title}, aur free education ko support karo`} style={styles.cta}>
    {busy ? <ActivityIndicator color={colors.onBrandPrimary} /> : <Glyph name="whatsapp" size={narrow ? 26 : 30} color={colors.onBrandPrimary} />}
    <View style={{ flex: 1 }}>
      <T w="heavy" size={narrow ? 16 : 18} color={colors.onBrandPrimary}>{title}</T>
      <T w="semibold" size={narrow ? 12 : 13} color={colors.onBrandPrimary} style={{ opacity: 0.92 }}>aur free education ko support karo</T>
    </View>
  </Press>;
}

const styles = StyleSheet.create({
  cta: { flexDirection: "row", alignItems: "center", gap: space.md, minHeight: 64, paddingVertical: space.md, paddingHorizontal: space.lg,
    borderRadius: 18, backgroundColor: colors.brandPrimary },
});
