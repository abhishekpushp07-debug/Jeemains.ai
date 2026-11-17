// The list part: coloured college-type segments, 25 college-branch lines per page, and the near misses.
import React from "react";
import { ActivityIndicator, ScrollView, StyleSheet, View } from "react-native";
import { Press, T } from "@/src/components/ui";
import { rankColors as colors, radius, space } from "@/src/theme";
import { fmt, PredictOut, Seat, Segment } from "./api";
import { KIND, TAG } from "./tones";
import { StarButton, Strip, Tag, Toggle } from "./controls";
import { jeeSaved, toggleSaved, useShortlist } from "./shortlist";

const SEGMENTS: Segment[] = ["all", "NIT", "IIIT", "GFTI", "DELHI"];

/** Final round, 2025 vs 2026, for this same seat path: a higher closing rank this year means it got easier.
 *  ▲ always means tougher and ▼ easier, on JEE, BITSAT and COMEDK alike. */
export function Trend({ y25, y26, testID, label = "JoSAA final" }: { y25?: number | null; y26?: number | null; testID: string; label?: string }) {
  if (!y25 || !y26) return null;
  const d = y26 - y25, same = Math.abs(d) < y25 * 0.03;
  return <T testID={testID} w="semibold" size={12} color={same ? colors.muted : d > 0 ? colors.success : colors.error}>
    {label} · 2025: {fmt(y25)} → 2026: {fmt(y26)}  {same ? "lagbhag same" : d > 0 ? "▼ aasaan hua" : "▲ tough hua"}
  </T>;
}

export function SeatRow({ seat, onPress, testID }: { seat: Seat; onPress: () => void; testID: string }) {
  const kind = KIND[seat.type];
  const saved = useShortlist().some(s => s.id === `jee-${seat.prog}`);
  return <View style={styles.seat}>
  <Press testID={testID} onPress={onPress} scaleTo={0.99} accessibilityLabel={`${seat.college}, ${seat.branch}`} style={styles.seatMain}>
    <View style={{ flex: 1, gap: 3 }}>
      <View style={styles.line}>
        <T w="bold" size={14.5} numberOfLines={1} style={{ flexShrink: 1 }}>{seat.college}</T>
        <Tag label={kind.label} ink={kind.ink} soft={kind.soft} />
      </View>
      <T size={13.5} color={colors.custom_softText} numberOfLines={2}>{seat.branch}{seat.degree ? ` (${seat.degree})` : ""}</T>
      <T size={12} color={colors.muted} numberOfLines={2}>
        Closing {fmt(seat.close)} {seat.rank_type} · {seat.round} · {seat.path}
      </T>
      <Trend y25={seat.y25} y26={seat.y26} testID={`${testID}-trend`} />
      {seat.gap ? <T w="semibold" size={12} color={colors.custom_flame}>{seat.gap}</T> : null}
    </View>
    {seat.tag ? <Tag testID={`${testID}-tag`} label={TAG[seat.tag].label} ink={TAG[seat.tag].ink} soft={TAG[seat.tag].soft} /> : null}
  </Press>
  <StarButton saved={saved} onPress={() => toggleSaved(jeeSaved(seat))} testID={`${testID}-star`} />
  </View>;
}

export function SeatList({ data, segment, onSegment, page, onPage, branchText, onBranch, onOpen, busy }: {
  data: PredictOut; segment: Segment; onSegment: (s: Segment) => void; page: number; onPage: (p: number) => void;
  branchText: string; onBranch: () => void; onOpen: (s: Seat) => void; busy: boolean;
}) {
  return <Strip title="Top college-branch" testID="rank-list"
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
    {data.items.length === 0 ? <T testID="rank-list-empty" size={13.5} color={colors.muted}>
      Is filter mein 2026 ki koi seat aapki rank tak nahi gayi. Branch ya segment badal kar dekho.
    </T> : <View>
      {data.items.map((s, i) => <SeatRow key={`${s.prog}`} seat={s} testID={`rank-seat-${(page - 1) * 25 + i}`} onPress={() => onOpen(s)} />)}
    </View>}
    {data.pages > 1 ? <View style={styles.pager}>
      {Array.from({ length: data.pages }, (_, i) => i + 1).map(p => (
        <Press key={p} testID={`rank-page-${p}`} onPress={() => onPage(p)} accessibilityState={{ selected: p === page }} style={[styles.pageBtn, p === page && styles.pageOn]}>
          <T w="bold" size={13.5} color={p === page ? colors.onSurfaceInverse : colors.onSurface}>Page {p}</T>
        </Press>
      ))}
    </View> : null}
    {data.near.length ? <View testID="rank-near" style={{ gap: space.xs, marginTop: space.sm }}>
      <T w="bold" size={11} color={colors.custom_eyebrow} style={{ letterSpacing: 2 }}>BAS THODA SA DOOR</T>
      {data.near.map((s, i) => <SeatRow key={`n${s.prog}`} seat={s} testID={`rank-near-${i}`} onPress={() => onOpen(s)} />)}
    </View> : null}
  </Strip>;
}

const styles = StyleSheet.create({
  segs: { gap: space.sm, paddingRight: space.sm },
  seat: { flexDirection: "row", borderBottomWidth: 1, borderBottomColor: colors.custom_barLine, alignItems: "flex-start" },
  seatMain: { flex: 1, flexDirection: "row", gap: space.sm, paddingVertical: space.md, alignItems: "flex-start" },
  line: { flexDirection: "row", alignItems: "center", gap: space.sm },
  pager: { flexDirection: "row", gap: space.sm, justifyContent: "center", paddingTop: space.sm },
  pageBtn: { minHeight: 44, minWidth: 96, borderRadius: radius.pill, borderWidth: 1, borderColor: colors.custom_cardLineStrong, alignItems: "center", justifyContent: "center", paddingHorizontal: space.lg },
  pageOn: { backgroundColor: colors.onSurface, borderColor: colors.onSurface },
});
