// Rank journey: the student's All India Rank on every live day whose result is out, drawn on the Score trend card when
// "Rank" is chosen there. Every Rank is the website's own (the "you" row of that day's leaderboard); the phone works out
// nothing. A day's Rank is kept on the phone (a week; the two newest days 10 minutes), so opening the graph again asks
// the website for two days at most, not for the whole series. Days are asked two at a time, newest first, and drawn as
// they arrive. One request for all days would be lighter still; it needs the website (memory/WEBSITE_SERIES_RANK_NOTE.md, part 2).
// A tap on a point opens the AITS Leaderboard on that day.
import React, { useEffect, useState } from "react";
import { StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import Svg, { Circle, Line, Polyline, Rect } from "react-native-svg";
import { api } from "@/src/api/client";
import { useAuth } from "@/src/auth";
import { Press, T } from "@/src/components/ui";
import { colors, space } from "@/src/theme";
import { DayInfo, scorePoints } from "@/src/series";
import { storage } from "@/src/utils/storage";
import { Board, grouped } from "./Board";

type DayRank = { rank: number; n: number; at: number };
type Kept = Record<string, DayRank>; // attempt id -> that day's Rank
const KEY = "aits_ranks_";
const KEEP = 7 * 24 * 3600 * 1000, KEEP_NEW = 10 * 60 * 1000;
const memory = new Map<string, Kept>(); // per student, for this run of the app
const tried = new Map<string, number>(); // a day whose leaderboard had no Rank yet -> when it was last asked (this run only)

/** `state`: "busy" while days are still being asked, "failed" when the website could not be reached for some of them. */
function useDayRanks(uid: string | undefined, ids: string[]) {
  const [ranks, setRanks] = useState<Kept>(() => (uid && memory.get(uid)) || {});
  const [state, setState] = useState<"busy" | "idle" | "failed">("busy");
  const [asked, setAsked] = useState(0);
  const list = ids.join(",");
  useEffect(() => {
    if (!uid || !list) return;
    let live = true;
    (async () => {
      let known = memory.get(uid);
      if (!known) {
        try { known = JSON.parse((await storage.getItem<string>(KEY + uid, "{}")) || "{}") as Kept; } catch { known = {}; }
        memory.set(uid, known);
      }
      const kept = known;
      if (!live) return;
      setRanks({ ...kept });
      const all = list.split(","), now = Date.now();
      // A day with no Rank yet is asked again after 10 minutes, not every time the graph opens ("Dobara" asks at once).
      const due = all.filter((id, i) => (!kept[id] || now - kept[id].at > (i >= all.length - 2 ? KEEP_NEW : KEEP)) && (asked > 0 || now - (tried.get(uid + id) || 0) > KEEP_NEW)).reverse();
      if (!due.length) { setState("idle"); return; }
      setState("busy");
      let failed = false;
      const worker = async () => {
        while (live && !failed && due.length) {
          const id = due.shift()!;
          try {
            const d = await api<Board>(`/attempts/${id}/leaderboard`);
            // A leaderboard that is not ready yet has no Rank to draw; it is asked again later.
            if (d?.state === "ready" && d.you) { kept[id] = { rank: d.you.rank, n: d.n, at: Date.now() }; if (live) setRanks({ ...kept }); }
            else tried.set(uid + id, Date.now());
          } catch { failed = true; }
        }
      };
      await Promise.all([worker(), worker()]);
      void storage.setItem(KEY + uid, JSON.stringify(kept));
      if (live) setState(failed ? "failed" : "idle");
    })();
    return () => { live = false; };
  }, [uid, list, asked]);
  return { ranks, state, retry: () => setAsked(n => n + 1) };
}

const H = 168, TOP = 26, BOTTOM = 26, LEFT = 34, RIGHT = 18; // the Score trend's own frame
const short = (n: number) => (n < 1000 ? String(n) : n < 10000 ? (n / 1000).toFixed(1).replace(/\.0$/, "") + "k" : Math.round(n / 1000) + "k");

export function RankJourney({ days }: { days: DayInfo[] }) {
  const router = useRouter();
  const { user } = useAuth();
  const [w, setW] = useState(0);
  const all = scorePoints(days);
  const { ranks, state, retry } = useDayRanks(user?.id, all.map(p => p.id));
  if (!all.length) return null;
  const pts = all.filter(p => ranks[p.id]).map(p => ({ day: p.day, rank: ranks[p.id].rank, n: ranks[p.id].n }));
  const status = state === "busy" ? `Har din ka Rank aa raha hai · ${pts.length}/${all.length}`
    : state === "failed" ? "Kuch din ka Rank nahi aa paaya."
    : pts.length ? "" : "Rank abhi taiyaar nahi hai. Result khulne ke thodi der baad aata hai.";
  const again = state === "failed" ? <Press testID="series-rank-retry" onPress={retry} hitSlop={12} accessibilityLabel="Rank dobara mangao" style={styles.retry}>
    <T w="heavy" size={11.5} color={colors.custom_seriesRoyalInk}>Dobara</T>
  </Press> : null;
  if (!pts.length) return <View testID="series-rank-journey" style={[styles.center, { height: H }]}>
    <T testID="series-rank-status" size={12.5} color={colors.custom_tabInkSoft} style={styles.centerText}>{status}</T>
    {again}
  </View>;

  const best = pts.reduce((a, p) => (p.rank < a.rank ? p : a), pts[0]);
  const last = pts[pts.length - 1];
  const todayDay = days.find(d => d.isToday)?.day ?? 0;
  const maxDay = Math.max(all[all.length - 1].day, todayDay, all[0].day + 1); // the same days as the Score graph
  const values = pts.map(p => p.rank);
  const lo = Math.min(...values), hi = Math.max(...values), pad = Math.max(2, Math.round((hi - lo) * 0.15));
  const top = Math.max(1, lo - pad), bottom = Math.max(top + 4, hi + pad);
  const plotW = Math.max(1, w - LEFT - RIGHT), plotH = H - TOP - BOTTOM;
  const x = (day: number) => LEFT + ((day - 1) / Math.max(1, maxDay - 1)) * plotW;
  const y = (rank: number) => TOP + ((rank - top) / (bottom - top)) * plotH; // Rank 1 is at the top
  const runs: (typeof pts)[] = [];
  pts.forEach((p, i) => { if (i && p.day - pts[i - 1].day === 1) runs[runs.length - 1].push(p); else runs.push([p]); });
  const gaps = pts.slice(1).map((p, i) => [pts[i], p]).filter(([a, b]) => b.day - a.day > 1);
  const ticks = [...new Set([top, Math.round((top + bottom) / 2), bottom])];
  const xLabels = [...new Set([1, Math.round((1 + maxDay) / 2), maxDay])];
  const tagX = Math.min(w - RIGHT - 44, Math.max(LEFT, x(last.day) - 22));

  return <View testID="series-rank-journey">
    <View style={{ height: H }} onLayout={e => setW(e.nativeEvent.layout.width)}>
      {w ? <View style={StyleSheet.absoluteFill}>
        <Svg width={w} height={H}>
          {ticks.map(t => <Line key={t} x1={LEFT} x2={w - RIGHT} y1={y(t)} y2={y(t)} stroke={colors.custom_tabChip} strokeWidth={1} />)}
          {gaps.map(([a, b]) => <Line key={"g" + a.day} x1={x(a.day)} y1={y(a.rank)} x2={x(b.day)} y2={y(b.rank)} stroke={colors.custom_tabInkSoft} strokeWidth={1.6} strokeDasharray="3 4" />)}
          {runs.filter(r => r.length > 1).map((r, i) => <Polyline key={"l" + i} points={r.map(p => `${x(p.day)},${y(p.rank)}`).join(" ")} fill="none" stroke={colors.custom_royalMid} strokeWidth={2.2} strokeLinejoin="round" strokeLinecap="round" />)}
          {pts.map(p => (p === best || p === last ? null : <Circle key={p.day} cx={x(p.day)} cy={y(p.rank)} r={3} fill={colors.custom_royalMid} />))}
          <Circle cx={x(best.day)} cy={y(best.rank)} r={5} fill={colors.custom_card} stroke={colors.custom_gold} strokeWidth={2} />
          {last !== best ? <Circle cx={x(last.day)} cy={y(last.rank)} r={6} fill={colors.custom_royalMid} stroke={colors.surface} strokeWidth={2} /> : null}
          {last !== best ? <Rect x={tagX} y={y(last.rank) - 26} width={44} height={18} rx={9} fill={colors.custom_royalMid} /> : null}
        </Svg>
        {ticks.map(t => <T key={"t" + t} size={9.5} color={colors.custom_tabInkSoft} style={[styles.yLabel, { top: y(t) - 7 }]}>#{short(t)}</T>)}
        {xLabels.map(d => <T key={"x" + d} size={9.5} color={colors.custom_tabInkSoft} style={[styles.xLabel, { left: x(d) - 20 }]}>D{d}</T>)}
        <T w="heavy" size={9} color={colors.custom_goldDeep} style={[styles.tag, { left: Math.max(LEFT - 4, x(best.day) - 30), top: y(best.rank) - 22 }]}>BEST</T>
        {last !== best ? <T w="heavy" size={10.5} color={colors.custom_seriesRoyalInk} style={[styles.tag, { left: tagX - 8, top: y(last.rank) - 25 }]}>#{short(last.rank)}</T> : null}
        {pts.map(p => <Press key={"p" + p.day} testID={"series-rank-point-" + p.day} haptic={false} onPress={() => router.push({ pathname: "/series-leaderboard", params: { day: String(p.day) } } as any)}
          accessibilityLabel={`Day ${p.day}: Rank ${grouped(p.rank)}, ${grouped(p.n)} students mein. Leaderboard kholo`} style={[styles.hit, { left: x(p.day) - 22, top: y(p.rank) - 22 }]}><View /></Press>)}
      </View> : null}
    </View>
    <View style={styles.foot}>
      <T testID="series-rank-status" size={11} color={colors.custom_tabInkSoft} style={styles.grow}>{status || `Best #${grouped(best.rank)} (Day ${best.day}) · Abhi #${grouped(last.rank)} (Day ${last.day})`}</T>
      {again}
    </View>
  </View>;
}

const styles = StyleSheet.create({
  grow: { flex: 1, minWidth: 0 },
  center: { alignItems: "center", justifyContent: "center", gap: space.sm, paddingHorizontal: space.lg },
  centerText: { textAlign: "center" },
  foot: { flexDirection: "row", alignItems: "center", gap: space.sm, minHeight: 24, paddingHorizontal: space.lg - 2 },
  retry: { minHeight: 28, paddingHorizontal: 12, borderRadius: 14, alignItems: "center", justifyContent: "center", backgroundColor: colors.custom_royalMid },
  yLabel: { position: "absolute", left: 2, width: 28, textAlign: "right" },
  xLabel: { position: "absolute", bottom: 4, width: 40, textAlign: "center" },
  tag: { position: "absolute", width: 60, textAlign: "center" },
  hit: { position: "absolute", width: 44, height: 44, borderRadius: 22 },
});
