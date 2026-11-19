// The Mission share card: a short letter from the maker on deep royal blue. "100% MADE BY AI ASTRA" ribbon across the
// top-right corner, a big gold quote mark, his words in serif, his signature with a gold "AP" wax seal, the four
// promises as glass chips, and "Please share karo" at the foot. Once the student's link has brought friends in, a gold
// thank-you note from the maker sits under the signature ("Thank you, Rahul: aapne 12 logon ki free education mein
// help ki"), so the shared picture carries it too. 4:5, drawn in units of its width (u = width / 320).
import React from "react";
import { StyleSheet, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { Glyph } from "@/src/components/Glyph";
import { colors as c } from "@/src/theme";
import { SERIF } from "@/src/rank/tones";
import { CT, Glow } from "./parts";
import { LINK, MAKER, SEGMENTS } from "./copy";
import { shortCount } from "./stats";

export function MissionCard({ width, helped = 0, name = "" }: { width: number; helped?: number; name?: string }) {
  const u = width / 320;
  const thanks = helped > 0;
  const body = thanks ? 15.5 : 16.5; // the letter steps down a touch to make room for the thank-you note
  return <View testID="mission-card" collapsable={false} style={[s.card, { width, height: width * 1.25, borderRadius: 22 * u }]}>
    <LinearGradient colors={[c.custom_mBlueMid, c.custom_mBlueTo, c.custom_mBlueNight]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />
    <Glow color={c.custom_mGold} cx="0%" cy="0%" r="60%" opacity={0.22} />
    {thanks ? <Glow color={c.custom_mGold} cx="50%" cy="100%" r="55%" opacity={0.12} /> : null}

    <View style={{ flex: 1, padding: 22 * u, justifyContent: "space-between" }}>
      <CT w="bold" size={8.5 * u} color={c.custom_mGold} style={{ letterSpacing: 2.2 * u }}>EK CHHOTI SI BAAT</CT>
      <View>
        <CT color={c.custom_mGold} style={{ fontFamily: SERIF, fontSize: (thanks ? 48 : 56) * u, lineHeight: (thanks ? 34 : 40) * u, marginBottom: -4 * u }}>“</CT>
        <CT color={c.custom_mWhite} style={{ fontFamily: SERIF, fontSize: body * u, lineHeight: (thanks ? 21.5 : 23) * u }}>
          Maine ise AI ke saath, apne kharche par, bahut mehnat se banaya hai. Taaki har JEE student <CT color={c.custom_mGold} style={{ fontFamily: SERIF, fontSize: body * u }}>100% free</CT> mein padh sake.
        </CT>
      </View>
      <View style={[s.row, { gap: 10 * u }]}>
        <View style={[s.rule, { width: 22 * u }]} />
        <View style={{ flex: 1 }}>
          <CT color={c.custom_mGold} style={{ fontFamily: SERIF, fontStyle: "italic", fontSize: 17 * u, lineHeight: 21 * u }}>{MAKER}</CT>
          <CT size={9.5 * u} color={c.custom_mInk} style={{ lineHeight: 12 * u }}>Creator, JEELIVE.AI</CT>
        </View>
        <View style={[s.seal, { width: 42 * u, height: 42 * u, borderRadius: 21 * u, borderWidth: 2 * u }]}>
          <LinearGradient colors={[c.custom_mGoldLight, c.custom_mGold, c.custom_mGoldDeep]} start={{ x: 0.2, y: 0 }} end={{ x: 0.8, y: 1 }} style={StyleSheet.absoluteFill} />
          <CT color={c.custom_mNavy} style={{ fontFamily: SERIF, fontSize: 15 * u, lineHeight: 18 * u }}>AP</CT>
        </View>
      </View>
      {thanks ? <Thanks u={u} helped={helped} name={name} /> : null}
      <View style={[s.grid, { gap: 6 * u }]}>
        {SEGMENTS.map(g => <View key={g.title} style={[s.chip, { gap: 6 * u, paddingVertical: (thanks ? 6 : 7) * u, paddingHorizontal: 8 * u, borderRadius: 10 * u, borderWidth: 0.75 * u }]}>
          <Glyph name={g.icon} size={12 * u} color={c.custom_mGold} />
          <View style={{ flex: 1 }}>
            <CT w="bold" size={9.5 * u} color={c.custom_mWhite} numberOfLines={1} style={{ lineHeight: 12 * u }}>{g.title}</CT>
            <CT size={8.5 * u} color={c.custom_mInk} numberOfLines={2} style={{ lineHeight: 11 * u }}>{g.short}</CT>
          </View>
        </View>)}
      </View>
      <View style={s.between}>
        <CT w="heavy" size={10 * u} color={c.custom_mGold} style={{ letterSpacing: 2 * u }}>100% FREE</CT>
        <CT w="bold" size={9 * u} color={c.custom_mWhite}>🙏 Please share karo · {LINK}</CT>
      </View>
    </View>

    {/* Corner ribbon: a gold band across the top-right corner, clipped by the card. */}
    <View style={[s.ribbon, { width: 200 * u, height: 22 * u, top: 37 * u, right: -52 * u, borderTopWidth: 0.75 * u, borderBottomWidth: 0.75 * u }]}>
      <LinearGradient colors={[c.custom_mGoldLight, c.custom_mGold, c.custom_mGoldDeep]} style={StyleSheet.absoluteFill} />
      <CT w="heavy" size={7.5 * u} color={c.custom_mNavy} style={{ letterSpacing: 1.2 * u, lineHeight: 10 * u }}>100% MADE BY AI ASTRA</CT>
    </View>
  </View>;
}

/** The maker's thank-you to the student: gold medal with the count, then the words. Gold hairline frame on glass. */
function Thanks({ u, helped, name }: { u: number; helped: number; name: string }) {
  const n = shortCount(helped);
  return <View testID="mission-card-thanks" style={[s.thanks, { gap: 9 * u, paddingVertical: 6 * u, paddingLeft: 6 * u, paddingRight: 10 * u, borderRadius: 14 * u, borderWidth: 0.75 * u }]}>
    <LinearGradient colors={[c.custom_mGoldWash, c.custom_mGlass]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={StyleSheet.absoluteFill} />
    <View style={[s.medal, { minWidth: 38 * u, height: 38 * u, borderRadius: 19 * u, borderWidth: 1.5 * u, paddingHorizontal: 5 * u }]}>
      <LinearGradient colors={[c.custom_mGoldLight, c.custom_mGold, c.custom_mGoldDeep]} start={{ x: 0.2, y: 0 }} end={{ x: 0.8, y: 1 }} style={StyleSheet.absoluteFill} />
      <CT testID="mission-card-thanks-count" w="heavy" color={c.custom_mNavy} style={{ fontSize: (n.length > 4 ? 10.5 : n.length > 2 ? 12.5 : 15) * u, lineHeight: 16 * u }}>{n}</CT>
      <CT w="heavy" color={c.custom_mNavy} style={{ fontSize: 5.5 * u, lineHeight: 6.5 * u, letterSpacing: 0.8 * u }}>DOST</CT>
    </View>
    <View style={{ flex: 1 }}>
      <CT w="heavy" size={8 * u} color={c.custom_mGold} numberOfLines={1} style={{ letterSpacing: 1.6 * u, lineHeight: 11 * u }}>THANK YOU{name ? `, ${name.toUpperCase()}` : ""} 🙏</CT>
      <CT w="semibold" size={9.5 * u} color={c.custom_mWhite} numberOfLines={2} style={{ lineHeight: 12.5 * u }}>
        Aapne <CT w="heavy" size={9.5 * u} color={c.custom_mGold}>{n} {helped === 1 ? "dost" : "logon"}</CT> ki free education mein help ki
      </CT>
    </View>
  </View>;
}

const s = StyleSheet.create({
  card: { overflow: "hidden", backgroundColor: c.custom_mBlueTo },
  between: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: 8 },
  seal: { alignItems: "center", justifyContent: "center", overflow: "hidden", borderColor: c.custom_mGoldLight },
  row: { flexDirection: "row", alignItems: "center" },
  rule: { height: 1.5, backgroundColor: c.custom_mGold },
  grid: { flexDirection: "row", flexWrap: "wrap" },
  chip: { flexBasis: "47%", flexGrow: 1, flexDirection: "row", alignItems: "center", backgroundColor: c.custom_mGlass, borderColor: c.custom_mLine },
  thanks: { flexDirection: "row", alignItems: "center", overflow: "hidden", borderColor: c.custom_mGoldLine },
  medal: { alignItems: "center", justifyContent: "center", overflow: "hidden", borderColor: c.custom_mGoldLight },
  ribbon: { position: "absolute", alignItems: "center", justifyContent: "center", overflow: "hidden", transform: [{ rotate: "45deg" }],
    borderTopColor: c.custom_mGoldLight, borderBottomColor: c.custom_mGoldDeep },
});
