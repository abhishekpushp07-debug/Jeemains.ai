// The JEE college list: a filter panel (college-type segments, branch, PDF), a tap hint, then every college-branch as its
// own card with "Cutoff dekho ›" (25 per page), the pager and the near misses as cards too.
import React from "react";
import { ActivityIndicator, ScrollView, StyleSheet, View } from "react-native";
import { Press, T } from "@/src/components/ui";
import { rankColors as colors, radius, space } from "@/src/theme";
import { fmt, PredictOut, Seat, Segment } from "./api";
import { KIND, TAG } from "./tones";
import { Strip, Tag, Toggle } from "./controls";
import { CardsHeading, CollegeCard, Stat, TapHint, cardStyles, useCardViews } from "./CollegeCard";
import { jeeSaved, toggleSaved, useShortlist } from "./shortlist";
import { useDreamToggle } from "@/src/dream/useDreamToggle";
import { jeeDream } from "@/src/dream/need";

const SEGMENTS: Segment[] = ["all", "NIT", "IIIT", "GFTI", "DELHI"];

/** The 2025 → 2026 stat box of a card (final round, same seat path; a higher closing rank this year = easier): ▼ Aasaan (closing went up), ▲ Tough, ≈ Same; "Naya" when 2025 had no such seat. */
export function trendStat(y25: number | null | undefined, y26: number | null | undefined, testID: string): Stat {
  if (!y25 || !y26) return { label: "2025 SE", value: "Naya", sub: "2025 mein nahi tha", ink: colors.custom_softText, testID };
  const d = y26 - y25, same = Math.abs(d) < y25 * 0.03;
  return { label: "2025 SE", value: same ? "≈ Same" : d > 0 ? "▼ Aasaan" : "▲ Tough", sub: `${fmt(y25)} → ${fmt(y26)}`,
    ink: same ? colors.custom_softText : d > 0 ? colors.success : colors.error, testID };
}

/** Left edge colour: the chance tag's colour; near misses are amber. */
export const edgeOf = (tag?: keyof typeof TAG | null, near?: boolean) => tag ? TAG[tag].ink : near ? colors.custom_flame : colors.custom_cardLineStrong;

export function SeatRow({ seat, onPress, testID, rank, viewed, pulse }: { seat: Seat; onPress: () => void; testID: string; rank?: number; viewed?: boolean; pulse?: boolean }) {
  const kind = KIND[seat.type];
  const saved = useShortlist().some(s => s.id === `jee-${seat.prog}`);
  const dream = useDreamToggle(`jee-${seat.prog}`, "jee", () => jeeDream(seat));
  return <CollegeCard testID={testID} rank={rank} edge={edgeOf(seat.tag, !!seat.gap)} title={seat.college} a11y={`${seat.college}, ${seat.branch}`} dream={dream}
    tags={<>
      <Tag label={kind.label} ink={kind.ink} soft={kind.soft} />
      {seat.tag ? <Tag testID={`${testID}-tag`} label={TAG[seat.tag].label} ink={TAG[seat.tag].ink} soft={TAG[seat.tag].soft} /> : null}
    </>}
    sub={`${seat.branch}${seat.degree ? ` (${seat.degree})` : ""}`} line={seat.path}
    stats={[
      { label: "CLOSING", value: fmt(seat.close), sub: `${seat.rank_type} · 2026` },
      { label: "ROUND", value: seat.round, sub: "jahan seat mili" },
      trendStat(seat.y25, seat.y26, `${testID}-trend`),
    ]}
    note={seat.gap ? <T w="semibold" size={12} color={colors.custom_flame}>{seat.gap}</T> : null}
    teaser="Har round ka cutoff + sab branches" viewed={viewed} pulse={pulse} onPress={onPress}
    compared={saved} onCompare={() => toggleSaved(jeeSaved(seat))} />;
}

export function SeatList({ data, segment, onSegment, page, onPage, branchText, onBranch, onOpen, busy, tools }: {
  data: PredictOut; segment: Segment; onSegment: (s: Segment) => void; page: number; onPage: (p: number) => void;
  branchText: string; onBranch: () => void; onOpen: (s: Seat) => void; busy: boolean; tools?: React.ReactNode;
}) {
  const views = useCardViews();
  const open = (s: Seat) => { views.mark(`${s.prog}`); onOpen(s); };
  const card = (s: Seat, testID: string, rank?: number, first?: boolean) => <SeatRow key={`${testID}-${s.prog}`} seat={s} rank={rank} testID={testID}
    viewed={views.viewed.has(`${s.prog}`)} pulse={first && views.pulse} onPress={() => open(s)} />;
  return <View testID="rank-list" style={cardStyles.list}>
    <Strip title="Top college-branch" testID="rank-list-head"
      right={busy ? <ActivityIndicator size="small" color={colors.muted} /> : <T size={12} color={colors.muted}>Top {data.total}</T>}>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.segs}>
        {SEGMENTS.map(s => {
          const k = s === "all" ? null : KIND[s];
          return <Toggle key={s} testID={`rank-seg-${s}`} label={`${k ? k.label : "All"} ${data.reach?.[s] ?? data.counts[s] ?? 0}`} on={segment === s}
            ink={k ? k.ink : colors.onSurface} soft={k ? k.soft : undefined} onPress={() => onSegment(s)} />;
        })}
      </ScrollView>
      <View style={styles.line}>
        <Toggle testID="rank-list-branch" label={branchText} caret on={branchText !== "All branches"} onPress={onBranch} />
      </View>
      {data.items.length ? tools : null}
    </Strip>
    {data.items.length === 0 ? <T testID="rank-list-empty" size={13.5} color={colors.muted}>
      Is filter mein 2026 ki koi seat aapki rank tak nahi gayi. Branch ya segment badal kar dekho.
    </T> : <>
      <TapHint testID="rank-tap-hint" viewed={views.viewed.size} />
      {data.items.map((s, i) => card(s, `rank-seat-${(page - 1) * 25 + i}`, (page - 1) * 25 + i + 1, i === 0 && page === 1))}
    </>}
    {data.pages > 1 ? <View style={styles.pager}>
      {Array.from({ length: data.pages }, (_, i) => i + 1).map(p => (
        <Press key={p} testID={`rank-page-${p}`} onPress={() => onPage(p)} accessibilityState={{ selected: p === page }} style={[styles.pageBtn, p === page && styles.pageOn]}>
          <T w="bold" size={13.5} color={p === page ? colors.onSurfaceInverse : colors.onSurface}>Page {p}</T>
        </Press>
      ))}
    </View> : null}
    {data.near.length ? <View testID="rank-near" style={cardStyles.list}>
      <CardsHeading icon="flag-checkered" title="BAS THODA SA DOOR" sub="Thode aur marks, aur ye seats bhi aapki" ink={colors.custom_flame} />
      {data.near.map((s, i) => card(s, `rank-near-${i}`))}
    </View> : null}
  </View>;
}

const styles = StyleSheet.create({
  segs: { gap: space.sm, paddingRight: space.sm },
  line: { flexDirection: "row", alignItems: "center", gap: space.sm },
  pager: { flexDirection: "row", gap: space.sm, justifyContent: "center", paddingTop: space.sm },
  pageBtn: { minHeight: 44, minWidth: 96, borderRadius: radius.pill, borderWidth: 1, borderColor: colors.custom_cardLineStrong, alignItems: "center", justifyContent: "center", paddingHorizontal: space.lg },
  pageOn: { backgroundColor: colors.onSurface, borderColor: colors.onSurface },
});
