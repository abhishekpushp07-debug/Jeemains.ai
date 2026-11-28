// On a finished Misfire Mock's result (test_kind "misfire"): how many of its questions went to "Samajh gaya". The
// website moves them; the app only says what the result tells and has Misfire read its lists afresh.
import React, { useEffect } from "react";
import { StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { Icon, T } from "@/src/components/ui";
import { DCard, Pill } from "@/src/components/design";
import { invalidate } from "@/src/useCached";
import { colors, space } from "@/src/theme";
import { misfireKey } from "../api";
import { understoodOf } from "../web";

export function MisfireUnderstood({ r, uid }: { r: any; uid?: string }) {
  const router = useRouter();
  const said = understoodOf(r);
  useEffect(() => { if (uid) invalidate(misfireKey(uid)); }, [uid, r?.id]);
  return <DCard testID="result-misfire-understood" style={styles.card}>
    <View style={styles.row}>
      <Icon name="check-decagram" size={22} color={colors.custom_chipBlood} />
      <T testID="result-misfire-understood-count" w="heavy" size={16} style={{ flex: 1 }}>{said
        ? `${said.understood}${said.total != null ? ` / ${said.total}` : ""} sawaal “Samajh gaya” mein chale gaye`
        : "Sahi kiye sawaal “Samajh gaya” mein chale jaate hain"}</T>
    </View>
    <T size={12.5} color={colors.muted}>{said
      ? said.understood ? "Jo sahi kiye, woh Misfire ki list se hat gaye. Baaki galtiyan wahin hain, agle mock ke liye." : "Is baar koi sawaal list se nahi hata. Galtiyan Misfire mein wahin hain, dobara try karo."
      : "Yeh mock aapke Misfire se bana tha. Misfire kholo: wahan list taaza dikhegi."}</T>
    <Pill testID="result-misfire-open" kind="outline" size="sm" icon="fire" label="Misfire kholo" onPress={() => router.push({ pathname: "/misfire", params: { tab: "web" } } as any)} />
  </DCard>;
}

const styles = StyleSheet.create({
  card: { gap: space.sm, borderColor: colors.custom_chipBlood, backgroundColor: colors.custom_chipBloodSoft },
  row: { flexDirection: "row", alignItems: "center", gap: space.sm },
});
