import React, { useState } from "react";
import { StyleSheet, View } from "react-native";
import { Image } from "expo-image";
import Constants from "expo-constants";
import Svg, { Defs, LinearGradient, Stop, Path, Ellipse } from "react-native-svg";
import { rapidColors as colors } from "@/src/theme";
import { Icon } from "./ui";

export type ArtKind = "spark" | "friends" | "coins" | "trophy";
const base = Constants.expoConfig?.extra?.backendUrl || process.env.EXPO_PUBLIC_BACKEND_URL;
export function Art({ kind, size = 64, testID }: { kind: ArtKind; size?: number; testID?: string }) {
  const [failed, setFailed] = useState(false);
  return <View testID={testID} pointerEvents="none" accessibilityElementsHidden style={{ width: size, height: size, overflow: "hidden", borderRadius: size * 0.22 }}>
    <View style={styles.fallback}>{kind === "spark" ? <EnergySpark size={size} /> : <Icon name={kind === "friends" ? "sword-cross" : kind === "coins" ? "circle-multiple" : "trophy"} color={kind === "friends" ? colors.custom_neonViolet : colors.custom_neonAmber} size={size * 0.56} />}</View>
    {!failed ? <Image source={{ uri: `${base}/api/brand/rapid/${kind}.webp` }} testID={testID ? `${testID}-image` : undefined} cachePolicy="memory-disk" contentFit="contain" style={StyleSheet.absoluteFill} onError={() => setFailed(true)} /> : null}
  </View>;
}
function EnergySpark({ size }: { size: number }) {
  return <Svg width={size} height={size} viewBox="0 0 200 200"><Defs><LinearGradient id="rf-spark-fill" x1="0" y1="0" x2="1" y2="1"><Stop offset="0" stopColor={colors.custom_neonCyan} /><Stop offset="1" stopColor={colors.brandPrimary} /></LinearGradient></Defs>
    <Ellipse cx="100" cy="104" rx="65" ry="51" fill="none" stroke={colors.custom_neonViolet} strokeWidth="12" transform="rotate(-30 100 100)" />
    <Path d="M100 30 L68 110 L97 111 L82 173 L143 85 L111 85 L136 30 Z" fill="url(#rf-spark-fill)" stroke={colors.custom_neonCyan} strokeWidth="2" />
  </Svg>;
}
const styles = StyleSheet.create({ fallback: { position: "absolute", top: 0, left: 0, right: 0, bottom: 0, alignItems: "center", justifyContent: "center", backgroundColor: colors.custom_gameBg } });