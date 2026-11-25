// Matched: the JEE Main questions that matched ours. Month, then day, then shift; a shift opens its questions and the
// way into its paper.
// Open to everyone, signed in or not (it is one of the public routes in app/_layout.tsx).
import React, { useMemo, useState } from "react";
import { RefreshControl, ScrollView, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { LinearGradient } from "expo-linear-gradient";
import { useAuth } from "@/src/auth";
import { useCached } from "@/src/useCached";
import { useListFocus } from "@/src/useListFocus";
import { Empty, ErrorBox, Press, Skeleton, T } from "@/src/components/ui";
import { ScreenHeader } from "@/src/components/design";
import { Glyph } from "@/src/components/Glyph";
import { GlossWord } from "@/src/components/GlossWord";
import { ScreenMotion } from "@/src/motion";
import { PillRow } from "@/src/misfire/parts";
import { colors, space, subjectColor } from "@/src/theme";
import { MatchedIndex, SHORT, ShiftSummary, byMonth, countLine, dayLabel, getIndex } from "@/src/matched/api";
import { MatchedHero } from "@/src/matched/MatchedCard";

function ShiftRow({ s, onPress }: { s: ShiftSummary; onPress: () => void }) {
  return <Press testID={`matched-shift-${s.id}`} onPress={onPress} scaleTo={0.985} accessibilityLabel={`Shift ${s.shift}. ${countLine(s)}. Open`} style={styles.rowPress}>
    <LinearGradient colors={[colors.custom_card, colors.custom_goldSoft]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.row}>
      <LinearGradient colors={[colors.custom_matchedFrom, colors.custom_matchedTo]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.shift}>
        <T w="bold" size={8.5} color={colors.custom_matchedInk} style={{ letterSpacing: 1.2 }}>SHIFT</T>
        <GlossWord testID={`matched-shift-${s.id}-number`} size={19} look="ink">{String(s.shift)}</GlossWord>
      </LinearGradient>
      <View style={{ flex: 1, minWidth: 0, gap: 6 }}>
        <T testID={`matched-shift-${s.id}-count`} w="heavy" size={17}>{s.matched} <T w="semibold" size={13} color={colors.muted}>{s.asked ? `of ${s.asked} matched` : "matched"}</T></T>
        {s.asked ? <View style={styles.track}><View style={[styles.fill, { width: `${Math.max(4, Math.round(s.matched / s.asked * 100))}%` }]} /></View> : null}
        {s.subjects.length ? <View style={styles.chips}>
          {s.subjects.map(x => <View key={x.name} style={styles.chip}>
            <View style={[styles.dot, { backgroundColor: subjectColor(x.name) }]} />
            <T w="bold" size={11.5} color={colors.custom_softText}>{SHORT[x.name] || x.name} {x.n}</T>
          </View>)}
        </View> : null}
      </View>
      <View style={styles.go}><Glyph name="arrow-right" size={16} color={colors.custom_matchedInk} stroke={2.2} /></View>
    </LinearGradient>
  </Press>;
}

export default function Matched() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuth();
  const res = useCached<MatchedIndex>("matched.index", getIndex);
  useListFocus(res.revalidate);
  const d = res.data;
  const months = useMemo(() => byMonth(d?.shifts || []), [d]);
  const [month, setMonth] = useState("");
  const current = months.find(m => m.key === month) || months[0];
  return <ScreenMotion>
    <View testID="matched-screen" style={{ flex: 1, backgroundColor: colors.surface, paddingTop: insets.top + space.sm }}>
      <ScreenHeader testID="matched-header" title="Matched" eyebrow="JEE Main" backTestID="matched-back"
        onBack={() => (router.canGoBack() ? router.back() : router.replace(user ? "/(tabs)" : "/entry"))} />
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingHorizontal: space.lg, paddingBottom: insets.bottom + space.xxl, gap: space.lg }}
        refreshControl={<RefreshControl testID="matched-refresh" refreshing={res.refreshing} onRefresh={res.reload} />}>
        <MatchedHero total={d?.total || 0} shifts={d?.shifts.length || 0} />
        <ErrorBox testID="matched-error" error={res.error} retry={res.reload} />
        {!d ? (res.error ? null : <View testID="matched-loading" style={{ gap: space.md }}><Skeleton h={84} /><Skeleton h={84} /></View>)
          : !current ? <Empty testID="matched-empty" icon="calendar-check-outline" title="Pehla shift hote hi yahan aayega"
            body="JEE Main ke har shift ke baad yahan woh questions dikhenge jo hamare questions se match hue: unka question, aur uske saamne hamara." />
            : <>
              {months.length > 1
                ? <PillRow prefix="matched-month" value={current.key} onChange={setMonth} items={months.map(m => ({ key: m.key, label: m.label, count: m.matched }))} />
                : <T testID="matched-month-only" w="heavy" size={17}>{current.label}</T>}
              {current.days.map(day => <View key={day.day} testID={`matched-day-${day.day}`} style={{ gap: space.sm }}>
                <T w="bold" size={12} color={colors.custom_eyebrow} style={{ letterSpacing: 1.6 }}>{dayLabel(day.day).toUpperCase()}</T>
                {day.shifts.map(s => <ShiftRow key={s.id} s={s} onPress={() => router.push(`/matched/${s.id}` as any)} />)}
              </View>)}
            </>}
      </ScrollView>
    </View>
  </ScreenMotion>;
}

const styles = StyleSheet.create({
  rowPress: { borderRadius: 20 },
  row: { flexDirection: "row", alignItems: "center", gap: space.md, minHeight: 84, paddingVertical: 12, paddingHorizontal: 14, borderRadius: 20, borderWidth: 1, borderColor: colors.custom_cardLineStrong },
  shift: { width: 54, height: 54, borderRadius: 27, alignItems: "center", justifyContent: "center" },
  track: { height: 6, borderRadius: 3, overflow: "hidden", backgroundColor: colors.custom_cardLine },
  fill: { height: 6, borderRadius: 3, backgroundColor: colors.custom_matchedTo },
  go: { width: 34, height: 34, borderRadius: 17, alignItems: "center", justifyContent: "center", backgroundColor: colors.custom_glossYellow },
  chips: { flexDirection: "row", flexWrap: "wrap", gap: 6 },
  chip: { flexDirection: "row", alignItems: "center", gap: 5, height: 24, paddingHorizontal: 9, borderRadius: 12, backgroundColor: colors.custom_card, borderWidth: 1, borderColor: colors.custom_cardLine },
  dot: { width: 7, height: 7, borderRadius: 4 },
});
