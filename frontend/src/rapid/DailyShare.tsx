import React, { useRef, useState } from "react";
import { Platform, StyleSheet, View, useWindowDimensions } from "react-native";
import { Image } from "expo-image";
import { LinearGradient } from "expo-linear-gradient";
import { useAuth } from "@/src/auth";
import { shareCard } from "@/src/shareCard";
import { T } from "@/src/components/ui";
import { Avatar } from "@/src/components/Entry";
import { useGameProfile } from "@/src/components/game";
import { allIndia, arena } from "@/src/theme";
import { GoldTitle, RaisedButton } from "./arena";
import { DailyResult, grouped, secs } from "./daily";
import { prettyCode, sendWhatsApp, useFriendCode } from "./social";

// Champion Share Card: today's All India rank and score in the fire world (the student's battleground under the cup).
const ART = { fire: require("../../assets/arena/th_fire_bg.webp"), battle: require("../../assets/arena/battleground.webp"), trophy: require("../../assets/arena/daily_trophy.webp") };
type Me = { name: string; avatar?: string | null; frame?: string | null };

/** The card friends see on WhatsApp: 4:5, drawn in units of the card width so it looks the same on every phone. */
function ChampionCard({ r, me, code, width }: { r: DailyResult; me: Me; code?: string; width: number }) {
  const u = width / 320;
  return <View style={[styles.card, { width, height: width * 1.25, borderRadius: 22 * u }]} collapsable={false}>
    <Image source={ART.fire} style={[styles.abs, { left: -30 * u, top: -60 * u, width: 380 * u, height: 380 * u }]} contentFit="cover" />
    <Image source={ART.battle} style={[styles.abs, { left: -16 * u, top: 40 * u, width: 352 * u, height: 123 * u }]} contentFit="fill" />
    <Image source={ART.trophy} style={[styles.abs, { left: 114 * u, top: 30 * u, width: 92 * u, height: 92 * u }]} contentFit="contain" />
    <LinearGradient colors={[arena.clear, arena.scrim]} locations={[0.3, 0.46]} style={StyleSheet.absoluteFill} />
    <T w="heavy" size={10.5 * u} color={allIndia.hot} style={[styles.kicker, { top: 12 * u }]}>JEELIVE.AI · ALL INDIA RAPID FIRE</T>
    <View style={[styles.body, { paddingHorizontal: 16 * u, paddingBottom: 14 * u, gap: 5 * u }]}>
      <GoldTitle size={32 * u} center>{r.rank ? `#${grouped(r.rank)} IN INDIA` : "ROUND DONE"}</GoldTitle>
      <T w="bold" size={12 * u} color={arena.text} style={styles.center}>of {grouped(r.players)} player{r.players === 1 ? "" : "s"} · {r.day}</T>
      <View style={[styles.stats, { gap: 8 * u }]}>
        <View style={[styles.stat, { borderRadius: 14 * u, paddingVertical: 6 * u }]}><T w="heavy" size={22 * u} color={arena.gold}>{r.correct}/{r.total}</T><T w="bold" size={10 * u} color={arena.muted}>cards right</T></View>
        <View style={[styles.stat, { borderRadius: 14 * u, paddingVertical: 6 * u }]}><T w="heavy" size={22 * u} color={arena.text}>{secs(r.ms)}</T><T w="bold" size={10 * u} color={arena.muted}>total time</T></View>
      </View>
      <View style={[styles.inline, { gap: 8 * u }]}><Avatar icon={me.avatar} frame={me.frame} size={36 * u} /><T w="heavy" size={17 * u} color={arena.text} numberOfLines={1} style={styles.shrink}>{me.name}</T></View>
      <View style={[styles.cta, { borderRadius: 14 * u, paddingVertical: 7 * u, paddingHorizontal: 10 * u }]}>
        <T w="heavy" size={11.5 * u} color={arena.gold} style={styles.center}>Same {r.total} PCM cards for every JEE student. Beat me!</T>
        {code ? <T w="heavy" size={11.5 * u} color={arena.aqua} style={[styles.center, styles.spaced]}>FRIEND CODE {prettyCode(code)}</T> : null}
      </View>
    </View>
  </View>;
}

/**
 * Share today's All India result: a preview of the card, then its photo with the message (Android build: straight into
 * WhatsApp; iPhone: the share sheet; see src/shareCard.ts). The web preview sends the message.
 */
export function DailyShare({ result, onBack }: { result: DailyResult; onBack: () => void }) {
  const uid = useAuth().user?.id, code = useFriendCode(uid).data?.code, p = useGameProfile(uid).data;
  const me: Me = { name: p?.name || "Me", avatar: p?.avatar, frame: p?.equipped?.frame };
  const card = useRef<any>(null), W = useWindowDimensions().width; // the card View, captured as a picture
  const [busy, setBusy] = useState(false), [note, setNote] = useState("");
  const caption = `🔥 ${result.rank ? `I'm #${grouped(result.rank)} in India` : "I finished"} in today's JEELIVE.AI All India Rapid Fire!\n`
    + `${result.correct}/${result.total} cards right in ${secs(result.ms)} · ${grouped(result.players)} player${result.players === 1 ? "" : "s"} today.\n`
    + `Same ${result.total} PCM cards for every JEE student. Can you beat me?${code ? `\nMy Friend Code: ${prettyCode(code)}` : ""}\nhttps://jeelive.ai`;
  const send = async () => {
    setBusy(true); setNote("");
    try { setNote((await shareCard(card, { caption, filename: "JEELIVE-All-India.png" })).note); }
    catch { setNote("Sharing could not open. Try again, or send the message only."); }
    finally { setBusy(false); }
  };
  return <View testID="rf-daily-share" style={styles.sheet}>
    <View ref={card} collapsable={false} testID="rf-daily-share-card"><ChampionCard r={result} me={me} code={code} width={Math.min(320, W - 48)} /></View>
    {note ? <T testID="rf-daily-share-note" w="bold" size={12} color={arena.aqua} style={styles.center}>{note}</T> : null}
    <View style={styles.buttons}>
      <RaisedButton testID="rf-daily-share-send" glyph="whatsapp" height={58} streak label="SEND ON WHATSAPP" sub={Platform.OS === "web" ? "Sends the message" : "Your rank card + message"} busy={busy} onPress={send} />
      <View style={styles.row}>
        {Platform.OS === "web" ? null : <RaisedButton testID="rf-daily-share-text" tone="wine" label="Message only" onPress={() => sendWhatsApp(caption)} style={styles.flex} />}
        <RaisedButton testID="rf-daily-share-back" tone="wine" label="Back" onPress={onBack} style={styles.flex} />
      </View>
    </View>
  </View>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 }, center: { textAlign: "center" }, spaced: { letterSpacing: 2 }, shrink: { flexShrink: 1 }, abs: { position: "absolute" },
  inline: { flexDirection: "row", alignItems: "center", justifyContent: "center", maxWidth: "100%" }, row: { flexDirection: "row", gap: 10 },
  sheet: { alignItems: "center", gap: 12, width: "100%", maxWidth: 460, alignSelf: "center" },
  card: { overflow: "hidden", borderWidth: 3, borderColor: arena.gold, backgroundColor: allIndia.ink },
  kicker: { position: "absolute", left: 0, right: 0, textAlign: "center", letterSpacing: 1.8, textShadowColor: arena.black, textShadowRadius: 6, textShadowOffset: { width: 0, height: 1 } },
  body: { position: "absolute", left: 0, right: 0, bottom: 0, alignItems: "stretch" },
  stats: { flexDirection: "row" }, stat: { flex: 1, alignItems: "center", backgroundColor: arena.panel, borderWidth: 1.5, borderColor: arena.goldDeep },
  cta: { backgroundColor: arena.panel, borderWidth: 1.5, borderColor: arena.rim, gap: 2 },
  buttons: { alignSelf: "stretch", gap: 10 },
});
