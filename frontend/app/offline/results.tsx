// The finished papers this phone keeps (src/offline/papers.ts), newest first within JEE Main, then BITSAT, then the
// rest. Each opens its kept result (./result.tsx). Nothing here asks the server for anything.
import React, { useEffect, useState } from "react";
import { FlatList, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "@/src/auth";
import { setAssetAccount } from "@/src/api/client";
import { DCard as Card, ScreenHeader } from "@/src/components/design";
import { Empty, Icon, Press, Skeleton, T } from "@/src/components/ui";
import { unixDate } from "@/src/navigation";
import { offlineIdentity } from "@/src/offline/identity";
import { KeptRow, keptResults, useKeptResults } from "@/src/offline/papers";
import { colors, space } from "@/src/theme";

export default function KeptResults() {
  const { user, expired } = useAuth();
  const router = useRouter(), insets = useSafeAreaInsets();
  const rows = useKeptResults();
  // undefined = being read; false = this phone may not read kept papers now (signed out, or 7 days without a confirmed session).
  const [open, setOpen] = useState<boolean | undefined>(undefined);
  useEffect(() => {
    let alive = true;
    (async () => {
      const who = expired ? null : user ? { uid: user.id } : await offlineIdentity(); // a session the server ended opens nothing
      if (who && !user) setAssetAccount(who.uid); // the kept store of the account last confirmed on this phone
      if (who) await keptResults();
      if (alive) setOpen(!!who);
    })();
    return () => { alive = false; };
  }, [user, expired]);
  const back = () => (router.canGoBack() ? router.back() : router.replace("/offline" as any));

  return <View testID="kept-results-screen" style={[styles.screen, { paddingTop: insets.top + space.sm }]}>
    <ScreenHeader testID="kept-results-header" backTestID="kept-results-back" title="Mere results" eyebrow="Phone par rakhe · bina internet" onBack={back} />
    {open === undefined ? <View style={styles.body}><Skeleton h={90} /><Skeleton h={90} /></View>
      : <FlatList testID="kept-results-list" data={open ? rows : []} keyExtractor={(row) => row.id} contentContainerStyle={[styles.body, { paddingBottom: insets.bottom + space.xl }]}
        ListEmptyComponent={<Card testID="kept-results-empty"><Empty icon="cloud-off-outline" title={open ? "Abhi koi result phone par nahi hai" : "Pehle ek baar internet ke saath app kholo"}
          body={open ? "Internet ke saath app kholo: aapke diye hue tests ke results aur solutions apne aap phone par aa jaate hain." : "Bina internet results dekhne ke liye is phone par pichhle 7 din mein ek baar sign in hona zaroori hai."} /></Card>}
        renderItem={({ item }) => <Row row={item} onPress={() => router.push({ pathname: "/offline/result", params: { id: item.id } } as any)} />} />}
  </View>;
}

function Row({ row, onPress }: { row: KeptRow; onPress: () => void }) {
  const whole = row.kept >= row.pictures;
  return <Press testID={`kept-row-${row.id}`} onPress={onPress} accessibilityLabel={`${row.title}, ${row.score} of ${row.maximum}`} scaleTo={0.99}>
    <Card style={styles.row}>
      <View style={styles.grow}>
        <T testID={`kept-row-title-${row.id}`} w="heavy" size={15} numberOfLines={2}>{row.title}</T>
        <T size={12} color={colors.muted} numberOfLines={1}>{[row.exam, row.submitted_at ? unixDate(row.submitted_at) : ""].filter(Boolean).join(" · ")}</T>
        <T testID={`kept-row-pictures-${row.id}`} size={11.5} w="bold" color={whole ? colors.success : colors.warning}>
          {whole ? "Solutions aur pictures phone par" : row.at ? `${row.kept} / ${row.pictures} pictures phone par` : "Pictures phone par aa rahi hain"}</T>
        {row.ai?.ready ? <T testID={`kept-row-ai-${row.id}`} size={11.5} w="bold" color={colors.brandText}>{`${row.ai.ready} / ${row.ai.total} AI solutions phone par`}</T> : null}
      </View>
      <View style={styles.right}>
        <T testID={`kept-row-score-${row.id}`} w="heavy" size={18}>{row.score ?? "—"}<T size={12} color={colors.muted}> / {row.maximum ?? "—"}</T></T>
        <Icon name="chevron-right" size={20} color={colors.muted} />
      </View>
    </Card>
  </Press>;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.surface }, body: { padding: space.lg, paddingTop: space.sm, gap: space.md },
  row: { flexDirection: "row", alignItems: "center", gap: space.md }, grow: { flex: 1, minWidth: 0, gap: 3 }, right: { alignItems: "flex-end", gap: 2 },
});
