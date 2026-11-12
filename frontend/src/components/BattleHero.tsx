import React from "react";
import { StyleSheet, View } from "react-native";
import { Art } from "@/src/rapid/Art";
import { T } from "@/src/rapid/ui";
import { Avatar } from "./Entry";
import { rapidColors as colors } from "@/src/theme";

// The waiting room shares the lobby's original energy artwork. No looping flash.
export function BattleHero({ me, subjects, chapterPill }: {
  me?: { avatar?: string | null; frame?: string | null; entry?: string | null };
  subjects: React.ReactNode; chapterPill: React.ReactNode; record?: string;
}) {
  return <View testID="rf-waiting-stage" style={styles.stage}><T testID="rf-waiting-brand" size={11} w="heavy" color={colors.custom_neonCyan} style={styles.brand}>JEECIRCLE RAPID FIRE</T><Art kind="friends" size={158} /><View style={styles.identity}><Avatar icon={me?.avatar} frame={me?.frame} size={40} /><T testID="rf-waiting-ready" size={13} w="bold">You’re ready to play</T></View>{subjects}{chapterPill}</View>;
}
const styles = StyleSheet.create({ stage: { alignItems: "center", padding: 22, borderRadius: 26, gap: 18, backgroundColor: colors.custom_gameCard, borderWidth: 1, borderColor: colors.custom_neonViolet + "55" }, brand: { letterSpacing: 2 }, identity: { flexDirection: "row", alignItems: "center", gap: 10 } });