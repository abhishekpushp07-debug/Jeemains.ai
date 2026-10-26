import React from "react";
import { ActivityIndicator, StyleSheet, View } from "react-native";
import { colors, radius, space } from "@/src/theme";
import { ErrorBox, Icon, T } from "./ui";

export function ExamLeaderboard({ exam, data, error, loading, retry }: { exam: string; data: any; error: string; loading: boolean; retry: () => void }) {
  const board = data?.exam === exam ? data : null;
  return <View testID="rf-leaderboard" style={styles.root}>
    <View style={styles.header}><Icon name="podium-gold" size={21} color={colors.custom_neonAmber} />
      <T testID="rf-leaderboard-title" size={17} w="heavy">{exam} leaderboard</T>
    </View>
    <T testID="rf-leaderboard-scope" size={12} color={colors.muted}>Ranked by your JEE Main practice XP.</T>
    <ErrorBox testID="rf-board-error" error={error} retry={retry} />
    {!board && loading ? <ActivityIndicator testID="rf-board-loading" color={colors.custom_neonAmber} /> : null}
    {board?.you ? <View testID="rf-board-your-stats" style={styles.mine}>
      <T testID="rf-board-your-rank" w="bold" size={13}>{board.you.rank ? `Your rank #${board.you.rank}` : "Your race starts here"}</T>
      <T testID="rf-board-your-xp" w="heavy" size={13} color={colors.custom_neonAmber}>{board.you.xp} {exam} XP</T>
    </View> : null}
    {board?.items?.map((row: any) => <View testID={`rf-board-row-${row.rank}`} key={row.rank} style={[styles.row, row.you && styles.highlight]}>
      <T testID={`rf-board-rank-${row.rank}`} w="heavy" size={14} color={row.rank === 1 ? colors.custom_neonAmber : colors.muted} style={styles.rank}>#{row.rank}</T>
      <T testID={`rf-board-name-${row.rank}`} w="bold" size={14} numberOfLines={1} style={styles.name}>{row.name}{row.you ? " (you)" : ""}</T>
      <T testID={`rf-board-xp-${row.rank}`} w="bold" size={12} color={colors.brandText}>{row.xp} XP</T>
    </View>)}
    {board && !board.items.length ? <T testID="rf-board-empty" size={13} color={colors.muted}>Be the first to earn {exam} XP. Play a sprint!</T> : null}
    <T testID="rf-board-wallet-note" size={10} color={colors.muted}>Your earned coins, streak and overall level stay preserved.</T>
  </View>;
}

const styles = StyleSheet.create({
  root: { gap: space.md },
  header: { flexDirection: "row", alignItems: "center", gap: space.sm },
  mine: { flexDirection: "row", flexWrap: "wrap", justifyContent: "space-between", gap: space.sm, padding: space.md, borderRadius: radius.md, backgroundColor: colors.surfaceTertiary },
  row: { flexDirection: "row", alignItems: "center", gap: space.sm, paddingVertical: space.md, paddingHorizontal: space.sm, borderRadius: radius.md },
  rank: { width: 32 }, name: { flex: 1 }, highlight: { backgroundColor: colors.custom_gameCardHi },
});