import React, { useCallback, useRef } from "react";
import { ActivityIndicator, StyleSheet, View } from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import { rf } from "@/src/api/client";
import { useCached } from "@/src/useCached";
import { colors, radius, space } from "@/src/theme";
import { ErrorBox, Icon, Press, T } from "./ui";

export function WeakRevision({ uid, exam }: { uid: string; exam: "JEE" }) {
  const router = useRouter();
  const query = useCached<any>(`u.${uid}.revision.${exam}`, () => rf(`/revision?exam=${exam}`, uid), false);
  const reload = query.reload;
  const first = useRef(true);
  useFocusEffect(useCallback(() => { if (first.current) { first.current = false; return; } reload(); }, [reload]));
  return <View testID="rf-weak-revision" style={styles.revision}>
    <View style={styles.row}>
      <Icon name="restore" size={20} color={colors.brandText} />
      <T testID="rf-revision-title" w="heavy" size={16} style={styles.copy}>Turn misses into wins</T>
      <T testID="rf-revision-exam" size={10} w="heavy" color={colors.custom_neonAmber}>{exam}</T>
    </View>
    <T testID="rf-revision-description" size={12} color={colors.muted}>Your most-missed chapters. One tap to replay.</T>
    <ErrorBox testID="rf-revision-error" error={query.error} retry={query.reload} />
    {query.loading && !query.data ? <ActivityIndicator testID="rf-revision-loading" color={colors.brandText} /> : null}
    {query.data?.items?.slice(0, 3).map((item: any, index: number) => <Press key={item.subject + item.chapter} testID={`rf-revise-chapter-${index}`} style={styles.chapter}
      accessibilityLabel={`Revise ${item.chapter}, ${item.remaining} missed cards`}
      onPress={() => router.push({ pathname: "/rapid/session", params: { exam, subject: item.subject, chapter: item.chapter, revision: "1" } })}>
      <View style={styles.copy}>
        <T testID={`rf-weak-chapter-${index}`} size={14} w="bold">{item.chapter}</T>
        <T testID={`rf-weak-count-${index}`} size={11} color={colors.muted}>{item.subject} · {item.remaining} cards to recover · {item.misses} misses</T>
      </View>
      <View style={styles.replay}><Icon name="replay" size={17} color={colors.brandText} /><T size={11} w="bold" color={colors.brandText}>Replay</T></View>
    </Press>)}
    {query.data && !query.data.items.length ? <T testID="rf-revision-empty" size={13} color={colors.onSurface}>No missed cards waiting. Finish a sprint or duel to build your {exam} revision list.</T> : null}
    <T testID="rf-revision-rule" size={10} color={colors.muted}>Wrong + timed-out cards only. Get one right to clear it.</T>
  </View>;
}

const styles = StyleSheet.create({
  copy: { flex: 1, gap: 3 },
  row: { flexDirection: "row", alignItems: "center", gap: space.sm },
  revision: { padding: space.lg, gap: space.md, borderWidth: 1, borderColor: colors.custom_gameLine, backgroundColor: colors.custom_gameCard, borderRadius: radius.lg },
  chapter: { flexDirection: "row", alignItems: "center", gap: space.sm, paddingVertical: space.md, borderTopWidth: 1, borderColor: colors.custom_gameLine, minHeight: 64 },
  replay: { alignItems: "center", justifyContent: "center", gap: 3, minWidth: 44, minHeight: 44 },
});