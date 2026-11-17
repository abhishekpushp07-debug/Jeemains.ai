// List positions as coins: 1-3 are gold, silver and bronze medals with a soft glow, 4 onwards a navy coin with a gold rim.
// One SVG circle pair + a text number, so it costs nothing in app size.
import React, { useId } from "react";
import { StyleSheet, View } from "react-native";
import { LinearGradient as Fade } from "expo-linear-gradient";
import Svg, { Circle, Defs, LinearGradient, Stop } from "react-native-svg";
import { T } from "@/src/components/ui";
import { rankColors as colors } from "@/src/theme";
import { SERIF } from "./tones";

const TIERS = [
  { light: colors.custom_medalGoldLight, mid: colors.custom_medalGold, deep: colors.custom_medalGoldDeep, ink: colors.custom_medalGoldInk },
  { light: colors.custom_medalSilverLight, mid: colors.custom_medalSilver, deep: colors.custom_medalSilverDeep, ink: colors.custom_medalSilverInk },
  { light: colors.custom_medalBronzeLight, mid: colors.custom_medalBronze, deep: colors.custom_medalBronzeDeep, ink: colors.custom_medalBronzeInk },
];
const SIZE = 30;
const WASH = [colors.custom_washGold, colors.custom_washSilver, colors.custom_washBronze];

/** The top three rows get a soft wash in their medal's colour that fades to the right. */
export function MedalWash({ n }: { n?: number }) {
  if (!n || n > 3) return null;
  return <Fade pointerEvents="none" colors={[WASH[n - 1], colors.custom_clear]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={[StyleSheet.absoluteFill, styles.wash]} />;
}

export function Medal({ n, testID }: { n: number; testID?: string }) {
  const tier = n >= 1 && n <= 3 ? TIERS[n - 1] : null;
  const id = "medal" + useId().replace(/[^a-z0-9]/gi, "");
  return <View testID={testID} style={[styles.wrap, tier && { shadowColor: tier.mid }, tier && styles.glow]}
    accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
    <Svg width={SIZE} height={SIZE} style={StyleSheet.absoluteFill}>
      {tier ? <Defs>
        <LinearGradient id={id} x1="0" y1="0" x2="1" y2="1">
          <Stop offset="0" stopColor={tier.light} />
          <Stop offset="0.5" stopColor={tier.mid} />
          <Stop offset="1" stopColor={tier.deep} />
        </LinearGradient>
      </Defs> : null}
      <Circle cx={SIZE / 2} cy={SIZE / 2} r={SIZE / 2 - 1} fill={tier ? `url(#${id})` : colors.custom_rankMid}
        stroke={tier ? tier.light : colors.custom_rankSilverMuted} strokeWidth={tier ? 1 : 0.8} strokeOpacity={tier ? 0.9 : 0.55} />
      {/* The engraved inner ring that makes it read as a coin. */}
      <Circle cx={SIZE / 2} cy={SIZE / 2} r={SIZE / 2 - 4} fill="none" stroke={tier ? tier.deep : colors.custom_rankSilverMuted} strokeWidth={0.7} strokeOpacity={tier ? 0.55 : 0.3} />
    </Svg>
    <T w="bold" color={tier ? tier.ink : colors.custom_rankSilver} style={[styles.num, n > 9 && styles.numSmall]}>{n}</T>
  </View>;
}

const styles = StyleSheet.create({
  wash: { borderRadius: 12 },
  wrap: { width: SIZE, height: SIZE, borderRadius: SIZE / 2, alignItems: "center", justifyContent: "center", marginTop: 1 },
  glow: { shadowOpacity: 0.55, shadowRadius: 6, shadowOffset: { width: 0, height: 0 }, elevation: 4 },
  num: { fontFamily: SERIF, fontSize: 14, lineHeight: 17 },
  numSmall: { fontSize: 12, lineHeight: 15 },
});
