import React, { useRef, useState } from "react";
import { Platform, Share, StyleSheet, View, useWindowDimensions } from "react-native";
import { Image } from "expo-image";
import { LinearGradient } from "expo-linear-gradient";
import * as Clipboard from "expo-clipboard";
import * as Sharing from "expo-sharing";
import { captureRef } from "react-native-view-shot";
import { useAuth } from "@/src/auth";
import { T } from "@/src/components/ui";
import { Avatar } from "@/src/components/Entry";
import { arena, fx } from "@/src/theme";
import { GoldTitle, RaisedButton } from "./arena";
import { Pop } from "./juice";
import { Crown } from "./parts";
import { CrownArt } from "./CrownArt";
import { ordinal, prettyCode, sendWhatsApp, useFriendCode } from "./social";

const ARENA = require("../../assets/arena/bg_colosseum.webp");
export type CrownShareInfo = { name: string; avatar?: string | null; frame?: string | null; no: number; crown: { won: number; real: number }; label: string; size: number; night?: boolean };

/** The crown card friends see on WhatsApp: 4:5, drawn in units of the card width so it looks the same on every phone. */
function CrownCard({ s, code, width }: { s: CrownShareInfo; code?: string; width: number }) {
  const u = width / 320, gold = s.crown.real > 0;
  return <View style={[styles.card, { width, height: width * 1.25, borderRadius: 22 * u }]} collapsable={false}>
    <Image source={ARENA} style={StyleSheet.absoluteFill} contentFit="cover" />
    <LinearGradient colors={[arena.shade, arena.scrim]} locations={[0, 0.75]} style={StyleSheet.absoluteFill} />
    <View style={[styles.cardBody, { padding: 18 * u, gap: 6 * u }]}>
      <T w="heavy" size={11 * u} color={arena.aqua} style={styles.spaced}>JEECIRCLE.AI · RAPID FIRE</T>
      <CrownArt size={150 * u} gold={gold} />
      <GoldTitle size={30 * u} center>CUP CHAMPION</GoldTitle>
      <View style={[styles.inline, { gap: 10 * u }]}><Avatar icon={s.avatar} frame={s.frame} size={44 * u} /><T w="heavy" size={20 * u} color={arena.text} numberOfLines={1} style={styles.shrink}>{s.name}</T></View>
      <View style={[styles.chip, { paddingHorizontal: 12 * u, height: 32 * u, borderRadius: 16 * u, gap: 6 * u }]}>
        <Crown c={s.crown} size="lg" />
        <T w="heavy" size={12 * u} color={gold ? arena.gold : fx.smoke}>{s.no === 1 ? "FIRST CROWN" : `CROWN #${s.no}`} · {gold ? "GOLD" : "SILVER"}</T>
      </View>
      <T w="bold" size={12 * u} color={arena.text} style={styles.center} numberOfLines={1}>{s.night ? "Cup Night" : "Knockout Cup"} · {s.size} players · {s.label}</T>
      <View style={[styles.cta, { borderRadius: 14 * u, paddingVertical: 8 * u, paddingHorizontal: 12 * u, marginTop: 4 * u }]}>
        <T w="heavy" size={13 * u} color={arena.gold} style={styles.center}>Think you’re faster? Beat me!</T>
        {code ? <T w="heavy" size={12 * u} color={arena.aqua} style={[styles.center, styles.spaced]}>FRIEND CODE {prettyCode(code)}</T> : null}
      </View>
    </View>
  </View>;
}

/**
 * Share the crown: a preview of the card, then the phone's share sheet with the picture (pick WhatsApp). On Android the
 * message is copied so it can be pasted as the photo's caption; iPhone sends both. The web preview sends the message.
 */
export function CrownShare({ s, onBack }: { s: CrownShareInfo; onBack: () => void }) {
  const uid = useAuth().user?.id, code = useFriendCode(uid).data?.code;
  const card = useRef<any>(null), W = useWindowDimensions().width; // the card View, captured as a picture
  const [busy, setBusy] = useState(false), [note, setNote] = useState("");
  const caption = `👑 I just won my ${s.no === 1 ? "first" : ordinal(s.no)} ${s.night ? "Cup Night" : "Knockout Cup"} on JEECIRCLE.AI Rapid Fire!\n${s.size} players · ${s.label}. Think you’re faster? Beat me!`
    + `${code ? `\nMy Friend Code: ${prettyCode(code)}` : ""}\nhttps://jeelive.ai`;
  const send = async () => {
    setBusy(true); setNote("");
    try {
      if (Platform.OS === "web") { await sendWhatsApp(caption); return; }
      const uri = await captureRef(card, { format: "png", quality: 1, result: "tmpfile" });
      if (Platform.OS === "ios") { await Share.share({ url: uri, message: caption }); return; }
      await Clipboard.setStringAsync(caption);
      setNote("Message copied. In WhatsApp, paste it as the photo’s caption.");
      if (await Sharing.isAvailableAsync()) await Sharing.shareAsync(uri, { mimeType: "image/png", dialogTitle: "Share your crown" });
      else await sendWhatsApp(caption);
    } catch { setNote("Sharing could not open. Try again, or send the message only."); }
    finally { setBusy(false); }
  };
  return <View testID="crown-share" style={styles.sheet}>
    <Pop><View ref={card} collapsable={false} testID="crown-share-card"><CrownCard s={s} code={code} width={Math.min(320, W - 48)} /></View></Pop>
    {note ? <T testID="crown-share-note" w="bold" size={12} color={arena.aqua} style={styles.center}>{note}</T> : null}
    <View style={styles.buttons}>
      <RaisedButton testID="crown-share-send" glyph="whatsapp" height={58} streak label="SEND ON WHATSAPP" sub={Platform.OS === "web" ? "Sends the message" : "Your crown card + message"} busy={busy} onPress={send} />
      <View style={styles.row}>
        {Platform.OS === "web" ? null : <RaisedButton testID="crown-share-text" tone="wine" label="Message only" onPress={() => sendWhatsApp(caption)} style={styles.flex} />}
        <RaisedButton testID="crown-share-back" tone="wine" label="Back" onPress={onBack} style={styles.flex} />
      </View>
    </View>
  </View>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 }, center: { textAlign: "center" }, spaced: { letterSpacing: 2 }, shrink: { flexShrink: 1 },
  inline: { flexDirection: "row", alignItems: "center", maxWidth: "100%" }, row: { flexDirection: "row", gap: 10 },
  sheet: { alignItems: "center", gap: 12, width: "100%", maxWidth: 460, alignSelf: "center" },
  card: { overflow: "hidden", borderWidth: 3, borderColor: arena.gold, backgroundColor: arena.bgDeep },
  cardBody: { flex: 1, alignItems: "center", justifyContent: "center" },
  chip: { flexDirection: "row", alignItems: "center", backgroundColor: arena.panel, borderWidth: 1.5, borderColor: arena.goldDeep },
  cta: { alignSelf: "stretch", backgroundColor: arena.panel, borderWidth: 1.5, borderColor: arena.rim, gap: 2 },
  buttons: { alignSelf: "stretch", gap: 10 },
});
