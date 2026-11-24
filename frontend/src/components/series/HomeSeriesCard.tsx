import React from "react";
import { StyleSheet, View, useWindowDimensions } from "react-native";
import { useRouter } from "expo-router";
import { Press, T } from "@/src/components/ui";
import { Pill, ProgressRing } from "@/src/components/design";
import { Glyph } from "@/src/components/Glyph";
import { colors, pastel, SeriesTone, space } from "@/src/theme";
import { Shine } from "@/src/analysis/Shine";
import { SeriesBackdrop, onyxShine } from "./looks";
import { istDate } from "@/src/navigation";
import { DayInfo, Series, Streak, dayAction, seriesDays, skippedCount } from "@/src/series";

type CardState = { tone: SeriesTone; right: string; status: string; title: string; meta: string; action: { label: string; to: string; icon: any } };

function cardState(s: Series | null, days: DayInfo[]): CardState {
  const meta = "75 Q · 180 min · +4 / −1";
  if (!s) return { tone: "today", right: "", status: "All India JEE", title: "Checking today’s paper…", meta, action: { label: "Open series hub", to: "/live", icon: "arrow-right" } };
  const n = seriesDays(s); // from the website: changes the moment the owner changes the schedule
  if (s.today < s.first_date) return { tone: "upcoming", right: `${n} DAYS`, status: `Starts ${istDate(s.first_date)}`, title: `${n} daily full mocks`, meta, action: { label: `Opens ${istDate(s.first_date)}`, to: "/live", icon: "calendar-clock" } };
  if (s.today > s.last_date) return { tone: "done", right: `${n} / ${n}`, status: "Series complete", title: "Practice archive is open", meta: "Every paper · practise anytime", action: { label: "Open archive", to: "/live", icon: "archive-outline" } };
  const d = days.find(x => x.isToday);
  if (!d) return { tone: "today", right: `${n} DAYS`, status: "Live series", title: s.title, meta, action: { label: "Open series hub", to: "/live", icon: "arrow-right" } };
  const act = dayAction(d);
  const base = { right: `DAY ${d.day} / ${n}`, status: d.label, title: d.slot.title, meta };
  if (d.live && act) return { ...base, tone: d.tone, action: { label: d.live.resumable ? "Resume" : "View result", to: act.to, icon: act.icon } };
  if (d.live) return { ...base, tone: "done", action: { label: "Results at 11:59 PM", to: "/live", icon: "lock-clock" } };
  if (act) return { ...base, tone: "today", action: { label: "Start today’s test", to: act.to, icon: "arrow-right" } };
  if (d.slot.state === "start_closed") return { ...base, tone: "missed", action: { label: "Open series hub", to: "/live", icon: "arrow-right" } };
  return { ...base, tone: "today", action: { label: "Open series hub", to: "/live", icon: "arrow-right" } };
}

const FACTS: [string, string][] = [["75", "questions"], ["180", "minutes"], ["+4 / −1", "marking"]];

/**
 * The one dark object on a light home: onyx → ruby card with a red glow (All India identity). Its own colours are drawn
 * as they are; over them sit a soft gloss and a glass glint that crosses from corner to corner, and ruby, gold and rose
 * run round its edge.
 */
export function HomeSeriesCard({ series, streak, days, error }: { series: Series | null; streak: Streak | null; days: DayInfo[]; error?: string }) {
  const router = useRouter();
  const narrow = useWindowDimensions().width < 360;
  const st = cardState(series, days);
  const done = streak?.completed_count ?? 0;
  const total = seriesDays(series);
  const started = !!series && series.today >= series.first_date;
  return (
    <View testID="all-india-series-banner">
      {/* The card's face and shine live in ./looks, shared with the AITS Leaderboard's stage so the two are the same card. */}
      <Shine radius={28} {...onyxShine} backdrop={<SeriesBackdrop />} face={styles.card}>
      <Press testID="series-open-hub-button" onPress={() => router.push("/live")} accessibilityLabel={`All India series. ${st.status}. ${st.title}. Open series hub`} scaleTo={0.985} style={{ gap: space.lg }}>
        <View style={styles.top}>
          <View style={styles.liveChip}>
            <View style={styles.live} />
            <T w="bold" size={10.5} color={colors.onSurfaceInverse} style={styles.caps} numberOfLines={1}>{narrow ? "ALL INDIA" : "ALL INDIA SERIES"}</T>
          </View>
          <View style={{ flex: 1 }} />
          <T testID="series-home-day" w="bold" size={11} color={colors.custom_whiteA70} style={styles.caps} numberOfLines={1}>{st.right}</T>
        </View>
        <View style={styles.body}>
          <View style={{ flex: 1, gap: 6 }}>
            <T testID="series-availability-badge" w="bold" size={10.5} color={pastel[st.tone].tint} style={styles.caps} numberOfLines={1}>{st.status.toUpperCase()}</T>
            <T testID="series-banner-title" w="heavy" size={narrow ? 20 : 23} color={colors.onSurfaceInverse} numberOfLines={2} style={{ letterSpacing: -0.3 }}>{st.title}</T>
          </View>
          <ProgressRing testID="series-home-ring" size={narrow ? 66 : 78} stroke={6} value={total ? done / total : 0} track={colors.custom_whiteA15} color={colors.brandPrimary} label={`${done} of ${total || "—"} days done`}>
            <T w="heavy" size={narrow ? 16 : 18} color={colors.onSurfaceInverse}>{done}</T>
            <T w="bold" size={9.5} color={colors.custom_whiteA70}>of {total || "—"}</T>
          </ProgressRing>
        </View>
        <View testID="series-schedule-facts" accessibilityLabel={st.meta} style={styles.facts}>
          {FACTS.map(([value, label], i) => <View key={label} style={[styles.fact, i > 0 && styles.factLine]}>
            <T w="heavy" size={narrow ? 15 : 17} color={colors.onSurfaceInverse} numberOfLines={1}>{value}</T>
            <T size={11} color={colors.custom_whiteA70} numberOfLines={1}>{label}</T>
          </View>)}
        </View>
      </Press>
      <View style={styles.rule} />
      <View style={styles.streak}>
        {started ? <>
          <Glyph name="fire" size={15} color={colors.custom_flame} />
          <T testID="series-home-streak" w="semibold" size={12.5} color={colors.onSurfaceInverse}>{streak?.current_streak ?? 0}-day streak</T>
          <T size={12.5} color={colors.custom_whiteA70}>·</T>
          <T testID="series-home-skipped" w="semibold" size={12.5} color={colors.onSurfaceInverse}>{skippedCount(days)} skipped</T>
        </> : <T size={12.5} w="medium" color={colors.custom_whiteA70} style={{ flexShrink: 1 }} numberOfLines={1}>{series ? `${istDate(series.first_date)} – ${istDate(series.last_date)} · ${narrow ? "one a day" : "one mock a day"}` : error ? "Live status unavailable. Open the hub to retry." : "Loading schedule…"}</T>}
        <View style={{ flex: 1 }} />
        <View testID="series-100ai-ribbon" style={styles.ai}><T w="bold" size={10} color={colors.onSurfaceInverse} style={{ letterSpacing: 1 }} accessibilityLabel="100% AI — series design branding">100% AI</T></View>
      </View>
      <Pill testID="home-series-cta" label={st.action.label} iconRight={st.action.icon} bg={colors.brandPrimary} ink={colors.onBrandPrimary} style={styles.cta} onPress={() => router.push(st.action.to as any)} />
      </Shine>
    </View>
  );
}

const styles = StyleSheet.create({
  // 19 inside the 2-point running edge: the card is the size it was with its old 1-point line and 20 of padding.
  card: { padding: 19, gap: space.lg, backgroundColor: colors.custom_series },
  top: { flexDirection: "row", alignItems: "center", gap: space.sm },
  liveChip: { flexDirection: "row", alignItems: "center", gap: 7, height: 28, paddingHorizontal: 11, borderRadius: 999, borderWidth: 1, borderColor: colors.custom_webGlassLine, backgroundColor: colors.custom_webGlass, flexShrink: 1 },
  live: { width: 7, height: 7, borderRadius: 4, backgroundColor: colors.brandPrimary },
  caps: { letterSpacing: 2 },
  body: { flexDirection: "row", alignItems: "center", gap: space.lg },
  facts: { flexDirection: "row", borderRadius: 18, borderWidth: 1, borderColor: colors.custom_webGlassLine, backgroundColor: colors.custom_webGlass, paddingVertical: 12 },
  fact: { flex: 1, minWidth: 0, alignItems: "center", gap: 1, paddingHorizontal: 4 },
  factLine: { borderLeftWidth: 1, borderLeftColor: colors.custom_webGlassLine },
  rule: { height: 1, backgroundColor: colors.custom_whiteA15 },
  streak: { flexDirection: "row", alignItems: "center", gap: 6, minHeight: 28 },
  ai: { borderRadius: 999, borderWidth: 1, borderColor: colors.custom_whiteA15, paddingHorizontal: 10, paddingVertical: 4 },
  cta: { borderRadius: 16, shadowColor: colors.brandPrimary, shadowOpacity: 0.35, shadowRadius: 14, shadowOffset: { width: 0, height: 6 } },
});
