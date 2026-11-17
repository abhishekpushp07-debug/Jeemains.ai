// The big red share button of the Mission card: the whole block is the button, WhatsApp mark on the left, a bold
// ask and "aur free education ko support karo" beside it. Also the share flow behind it (busy, note, fallback).
import React, { useState } from "react";
import { ActivityIndicator, StyleSheet, View, useWindowDimensions } from "react-native";
import { Press, T, buzz } from "@/src/components/ui";
import { Glyph } from "@/src/components/Glyph";
import { colors, space } from "@/src/theme";
import { sendWhatsApp } from "@/src/rapid/social";
import { ShareOutcome, shareMission, watchReturn } from "./share";

type CardRef = React.RefObject<React.ComponentRef<typeof View> | null>;

/** Shares the card with `caption`. `onShared` runs once the student is back from WhatsApp (or the other app), at most
 *  3 seconds after the share where the app never leaves; never when the share sheet was closed without sending. */
export function useMissionShare(card: CardRef, caption: string, onShared?: () => void) {
  const [busy, setBusy] = useState(false), [note, setNote] = useState("");
  const share = async (toWhatsApp: boolean) => {
    if (busy) return;
    setBusy(true); setNote("");
    const trip = watchReturn();
    try {
      let out: ShareOutcome;
      try { out = await shareMission(card, toWhatsApp, caption); }
      catch { await sendWhatsApp(caption); out = { shared: true, away: true, note: "" }; } // the picture could not go out: the message with the link
      if (!out.shared) { if (onShared) setNote("Share pura nahi hua. Result dekhne ke liye ek baar share karo."); return; }
      if (onShared && out.away) { setNote("WhatsApp par bhej kar wapas aao, result yahin khul jaayega."); await trip.back(); }
      setNote(out.note);
      onShared?.();
    } catch { setNote("Share nahi khula. Dobara try karo."); buzz("error"); }
    finally { trip.stop(); setBusy(false); }
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
