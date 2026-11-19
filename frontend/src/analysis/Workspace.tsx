// Analysis 2.0 on the phone: the same 8 sections, Personal / Comparative switch and question lists as jeelive.ai.
// AnalysisBody goes inside the page's scroll; AnalysisBar stays fixed at the bottom of the screen.
import React, { useCallback, useEffect, useRef, useState } from "react";
import { ActivityIndicator, GestureResponderEvent, ScrollView, StyleSheet, View, useWindowDimensions } from "react-native";
import Animated, { FadeIn, useReducedMotion } from "react-native-reanimated";
import { storage } from "@/src/utils/storage";
import { ErrorBox, Icon, IconName, Press, Skeleton, T } from "@/src/components/ui";
import { DSheet } from "@/src/components/design";
import { colors, radius, space } from "@/src/theme";
import type { AnalysisState } from "./useAnalysis";
import { An, Open, SectionProps, TONE, index } from "./format";
import { QRow, swipeGuard } from "./parts";
import { Overview } from "./Overview";
import { Performance } from "./Performance";
import { Potential } from "./Potential";
import { Quality } from "./Quality";
import { TimeSection } from "./TimeSection";
import { Difficulty } from "./Difficulty";
import { Journey } from "./Journey";
import { QsByQs } from "./QsByQs";
import { CompareBody, ComparePicker } from "./Compare";
import { Leaderboard } from "./Leaderboard";
import { downloadReport, shareScorecard } from "./report";

export const SECTIONS: [string, string, React.ComponentType<SectionProps>, string][] = [
  ["overview", "Overview", Overview, "Ek nazar mein poora paper: Score, Rank, marks ka hisaab aur agle mock ke 3 kaam."],
  ["performance", "Performance", Performance, "Har subject aur chapter mein kitne marks bane aur kahan gaye."],
  ["potential", "Score Potential", Potential, "Seedha hisaab: kin galtiyon ko theek karke kitne marks aur kaunsi Rank mil sakti thi."],
  ["quality", "Attempt Quality", Quality, "Har sawaal ko ek tag: sahi time mein sahi, jaldbaazi, overtime ya concept gap."],
  ["time", "Time kahan gaya", TimeSection, "Aapka time kis subject, kis sawaal aur paper ke kis hisse mein gaya."],
  ["difficulty", "Difficulty", Difficulty, "Easy, Moderate aur Tough sawaalon par aapka haal, aur Easy marks ka leak."],
  ["journey", "Question Journey", Journey, "Aap paper mein kis raaste chale: kaun sa sawaal kab khola, kab wapas aaye, kab jawab badla."],
  ["qs", "Qs by Qs", QsByQs, "Har sawaal ki poori report ek jagah: aapka time, Par time aur class ka haal."],
];
const NAV_NAME: Record<string, string> = { time: "Time" };
const known = (k?: string | null) => !!k && SECTIONS.some(s => s[0] === k);
const VS = /^(topper|top10|average|user:[0-9a-f]{16})$/;
const LAST = "analysis.section";

export type AnalysisNav = { key: string; compare: boolean; vs: string; open: (key: string) => void; setCompare: (on: boolean) => void; setVs: (vs: string) => void };

/** Which section is open, Personal or Comparative, and who to compare with. Reopening the same result returns to its last section. */
export function useAnalysisNav(id: string, onSection: () => void): AnalysisNav {
  const [key, setKey] = useState("overview");
  const [compare, setCompare] = useState(false);
  const [vs, setVsRaw] = useState("topper");
  const touched = useRef(false);
  useEffect(() => {
    let live = true;
    void storage.getItem<string>(LAST, "").then(saved => {
      const [at, k] = String(saved || "").split("|");
      if (live && !touched.current && at === id && known(k)) setKey(k);
    });
    return () => { live = false; };
  }, [id]);
  const open = useCallback((next: string) => {
    const k = next === "questions" ? "qs" : next;
    if (!known(k)) return;
    touched.current = true;
    setKey(k);
    void storage.setItem(LAST, `${id}|${k}`);
    onSection();
  }, [id, onSection]);
  const setVs = useCallback((v: string) => { if (VS.test(v)) setVsRaw(v); }, []);
  return { key, compare, vs, open, setCompare, setVs };
}

function Act({ testID, icon, label, onPress, busy, disabled, primary, stacked }: { testID: string; icon: IconName; label: string; onPress: () => void; busy?: boolean; disabled?: boolean; primary?: boolean; stacked?: boolean }) {
  const ink = primary ? colors.onBrandPrimary : colors.onSurface;
  // On a narrow phone the icon sits above the words, so even "Galat + chhode dobara" is never cut.
  return <Press testID={testID} onPress={onPress} disabled={disabled || busy} accessibilityLabel={label} accessibilityState={{ busy: !!busy }} style={[styles.act, stacked && styles.actStacked, primary && styles.actOn]}>
    {busy ? <ActivityIndicator size="small" color={ink} /> : <Icon name={icon} size={18} color={ink} />}
    <T w="heavy" size={stacked ? 12.5 : 13} color={ink} numberOfLines={2} style={styles.actLabel}>{label}</T>
  </Press>;
}

function DrillList({ drill, an, onClose, onOpen }: { drill: { title: string; ids: string[] } | null; an: An; onClose: () => void; onOpen: Open }) {
  const byId = index(an);
  const rows = (drill?.ids || []).map(i => byId[i]).filter(Boolean);
  return <DSheet visible={!!drill} onClose={onClose} testID="a2-drill" title={drill?.title}>
    <T testID="a2-drill-title" size={12.5} color={colors.muted}>{rows.length} sawaal. Kisi par tap karo, uska solution khulega.</T>
    <View style={{ gap: 8 }}>
      {rows.map(q => <QRow key={q.id} testID={"a2-drill-q-" + q.number} q={q} an={an} onPress={() => { onClose(); onOpen(q.id); }} />)}
    </View>
  </DSheet>;
}

function Pager({ at, open }: { at: number; open: (key: string) => void }) {
  const prev = SECTIONS[at - 1], next = SECTIONS[at + 1];
  return <View style={styles.pager}>
    {prev ? <Press testID="a2-prev-section" onPress={() => open(prev[0])} accessibilityLabel={"Pichhla: " + prev[1]} style={styles.page}>
      <Icon name="arrow-left" size={17} color={colors.onSurface} />
      <View style={{ flex: 1, minWidth: 0 }}><T size={9.5} w="heavy" color={colors.custom_eyebrow} style={styles.caps}>PICHHLA</T><T size={13} w="heavy" numberOfLines={2}>{prev[1]}</T></View>
    </Press> : <View style={{ flex: 1 }} />}
    {next ? <Press testID="a2-next-section" onPress={() => open(next[0])} accessibilityLabel={"Agla: " + next[1]} style={[styles.page, styles.pageNext]}>
      <View style={{ flex: 1, minWidth: 0, alignItems: "flex-end" }}><T size={9.5} w="heavy" color={colors.custom_whiteA70} style={styles.caps}>AGLA</T><T size={13} w="heavy" color={colors.onBrandPrimary} numberOfLines={2} style={{ textAlign: "right" }}>{next[1]}</T></View>
      <Icon name="arrow-right" size={17} color={colors.onBrandPrimary} />
    </Press> : <View style={{ flex: 1 }} />}
  </View>;
}

export function AnalysisBody({ id, state, nav, onOpen, onSolutions, onRetry, slot }: {
  id: string; state: AnalysisState; nav: AnalysisNav; onOpen: Open; onSolutions: () => void; onRetry?: () => void; slot?: React.ReactNode;
}) {
  const { data: an, error, offline, loading, reload } = state;
  const reduced = useReducedMotion();
  const narrow = useWindowDimensions().width < 360;
  const [drill, setDrill] = useState<{ title: string; ids: string[] } | null>(null);
  const [busy, setBusy] = useState<"" | "pdf" | "png">("");
  const [note, setNote] = useState<{ ok: boolean; text: string } | null>(null);
  // A sideways swipe moves to the next or the previous section; a tap that was really a swipe opens nothing.
  const touch = useRef<{ x: number; y: number; moved: boolean } | null>(null);
  if (!an) return <View testID="analysis2" style={styles.root}>
    <ErrorBox error={error} retry={reload} testID="a2-error" />
    {!error ? <View testID="a2-loading" style={styles.root}><T size={13} w="bold" color={colors.muted}>Analysis khul raha hai…</T><Skeleton h={230} /><Skeleton h={120} /><Skeleton h={160} /></View> : null}
  </View>;

  const at = Math.max(0, SECTIONS.findIndex(s => s[0] === nav.key));
  const [key, label, Section, about] = SECTIONS[at];
  const calm = () => !touch.current?.moved;
  const start = (e: GestureResponderEvent) => { swipeGuard.blocked = false; touch.current = { x: e.nativeEvent.pageX, y: e.nativeEvent.pageY, moved: false }; };
  const move = (e: GestureResponderEvent) => {
    const t = touch.current;
    if (!t || t.moved) return;
    const dx = Math.abs(e.nativeEvent.pageX - t.x);
    if (dx > 16 && dx > Math.abs(e.nativeEvent.pageY - t.y)) t.moved = true;
  };
  const finish = (e: GestureResponderEvent) => {
    const t = touch.current;
    if (!t) return;
    setTimeout(() => { if (touch.current === t) t.moved = false; }, 80);
    if (swipeGuard.blocked) return;
    const dx = e.nativeEvent.pageX - t.x, dy = e.nativeEvent.pageY - t.y;
    if (Math.abs(dx) < 80 || Math.abs(dx) < 2.5 * Math.abs(dy)) return;
    const next = SECTIONS[at + (dx < 0 ? 1 : -1)];
    if (next) nav.open(next[0]);
  };
  const run = async (kind: "pdf" | "png", work: (id: string, an: An) => Promise<string>) => {
    setBusy(kind); setNote(null);
    try { const text = await work(id, an); if (text) setNote({ ok: true, text }); }
    catch (e: any) { if (e?.name !== "AbortError") setNote({ ok: false, text: e?.message || "File abhi nahi ban paayi. Thodi der mein dobara try karo." }); }
    setBusy("");
  };

  return <View testID="analysis2" style={styles.root}>
    <View testID="a2-top-bar" style={styles.top}>
      <T w="heavy" size={10.5} color={colors.brandText} style={styles.kicker}>ANALYSIS · {at + 1} / {SECTIONS.length}{nav.compare ? " · COMPARATIVE" : ""}</T>
      <T testID="a2-section-title" w="heavy" size={26} style={styles.title}>{label}</T>
      <T size={13} color={colors.muted}>{about}</T>
      <View style={styles.acts}>
        <Act testID="a2-download-report" icon="tray-arrow-down" label="Report download" stacked={narrow} busy={busy === "pdf"} disabled={!!busy} onPress={() => run("pdf", downloadReport)} />
        <Act testID="a2-share-scorecard" icon="share-variant-outline" label="Share" stacked={narrow} busy={busy === "png"} disabled={!!busy} onPress={() => run("png", shareScorecard)} />
        {onRetry ? <Act testID="a2-retry-mistakes" icon="restart" label="Galat + chhode dobara" stacked={narrow} onPress={onRetry} /> : null}
        <Act testID="a2-view-solutions" icon="book-open-variant" label="Solutions dekho" stacked={narrow} primary onPress={onSolutions} />
      </View>
      {note ? <T testID="a2-actions-note" size={12.5} w="bold" color={note.ok ? colors.success : colors.error}>{note.text}</T> : null}
    </View>
    {offline ? <View testID="a2-offline" accessibilityRole="alert" style={styles.offline}>
      <Icon name="wifi-off" size={16} color={TONE.warn.ink} />
      <T size={12.5} w="bold" color={TONE.warn.ink} style={{ flex: 1 }}>Internet nahi hai. Yeh pichhli baar khula hua analysis hai.</T>
    </View> : null}
    <ErrorBox error={error} retry={reload} testID="a2-error" />
    {nav.compare ? <ComparePicker id={id} value={nav.vs} onChange={nav.setVs} /> : null}
    <Animated.View key={key + (nav.compare ? ":c" : "")} testID={"a2-section-" + key} entering={reduced ? undefined : FadeIn.duration(220)} style={styles.root}
      onTouchStart={start} onTouchMove={move} onTouchEnd={finish} onTouchCancel={() => { touch.current = null; }}>
      {nav.compare && !an.compare && loading ? <Skeleton h={150} /> : null}
      {nav.compare ? <CompareBody an={an} part={key} /> : null}
      {nav.compare && key === "overview" && an.class?.state === "ready" ? <Leaderboard id={id} value={nav.vs} onPick={nav.setVs} /> : null}
      <Section an={an} id={id} onDrill={(title, ids) => { if (calm()) setDrill({ title, ids }); }} onOpen={qid => { if (calm()) onOpen(qid); }} go={nav.open} slot={key === "overview" ? slot : undefined} />
      <Pager at={at} open={nav.open} />
    </Animated.View>
    <DrillList drill={drill} an={an} onClose={() => setDrill(null)} onOpen={onOpen} />
  </View>;
}

const MODES: [boolean, string, IconName, string][] = [[false, "Personal", "account", "a2-mode-personal"], [true, "Comparative", "account-group", "a2-mode-compare"]];

/** Fixed at the bottom of the screen: Personal / Comparative, then the 8 sections as scrolling pills. */
export function AnalysisBar({ nav, inset }: { nav: AnalysisNav; inset: number }) {
  const scroller = useRef<React.ElementRef<typeof ScrollView>>(null);
  const xs = useRef<Record<string, number>>({});
  useEffect(() => {
    const x = xs.current[nav.key];
    if (x != null) scroller.current?.scrollTo({ x: Math.max(0, x - 56), animated: true });
  }, [nav.key]);
  return <View testID="a2-bottom-bar" style={[styles.bar, { paddingBottom: inset + 8 }]}>
    <View style={styles.mode} accessibilityRole="tablist" accessibilityLabel="Personal ya Comparative">
      {MODES.map(([value, name, icon, testID]) => {
        const on = nav.compare === value;
        return <Press key={testID} testID={testID} accessibilityRole="tab" accessibilityState={{ selected: on }} accessibilityLabel={name} onPress={() => nav.setCompare(value)} scaleTo={0.98} hitSlop={{ top: 4, bottom: 4 }}
          style={[styles.modeItem, on && styles.modeOn]}>
          <Icon name={icon} size={15} color={on ? colors.onSurfaceInverse : colors.custom_softText} />
          <T size={12.5} w={on ? "heavy" : "bold"} color={on ? colors.onSurfaceInverse : colors.custom_softText}>{name}</T>
        </Press>;
      })}
    </View>
    <ScrollView ref={scroller} horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.nav} accessibilityLabel="Analysis sections">
      {SECTIONS.map(([k, name], i) => {
        const on = k === nav.key;
        return <View key={k} onLayout={e => { xs.current[k] = e.nativeEvent.layout.x; }}>
          <Press testID={"a2-nav-" + k} accessibilityRole="tab" accessibilityState={{ selected: on }} accessibilityLabel={`${i + 1}. ${name}`} onPress={() => nav.open(k)} scaleTo={0.97}
            style={[styles.navItem, on && styles.navOn]}>
            <T size={10.5} w="mono" color={on ? colors.custom_whiteA70 : colors.custom_eyebrow}>{i + 1}</T>
            <T size={12.5} w={on ? "heavy" : "bold"} color={on ? colors.onBrandPrimary : colors.custom_softText}>{NAV_NAME[k] || name}</T>
          </Press>
        </View>;
      })}
    </ScrollView>
  </View>;
}

const styles = StyleSheet.create({
  root: { gap: space.md },
  top: { gap: 4 },
  kicker: { letterSpacing: 1.7 },
  title: { letterSpacing: -0.9 },
  caps: { letterSpacing: 1.2 },
  acts: { flexDirection: "row", flexWrap: "wrap", gap: 8, marginTop: 12 },
  act: { flexBasis: "45%", flexGrow: 1, minWidth: 0, minHeight: 50, borderRadius: 14, borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_card, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8, paddingHorizontal: 12, paddingVertical: 8 },
  actOn: { backgroundColor: colors.brandPrimary, borderColor: colors.brandPrimary },
  actStacked: { flexDirection: "column", gap: 4, minHeight: 62, paddingHorizontal: 6 },
  actLabel: { textAlign: "center", lineHeight: 16, flexShrink: 1 },
  offline: { flexDirection: "row", alignItems: "center", gap: 8, padding: space.md, borderRadius: 14, borderWidth: 1, borderColor: TONE.warn.line, backgroundColor: TONE.warn.soft },
  pager: { flexDirection: "row", gap: space.sm },
  page: { flex: 1, minWidth: 0, minHeight: 56, flexDirection: "row", alignItems: "center", gap: 8, paddingHorizontal: space.md, borderRadius: 16, borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_card },
  pageNext: { backgroundColor: colors.brandPrimary, borderColor: colors.brandPrimary },
  bar: { gap: 6, paddingTop: 8, paddingHorizontal: space.md, backgroundColor: colors.custom_bar, borderTopWidth: 1, borderTopColor: colors.custom_barLine, borderTopLeftRadius: 20, borderTopRightRadius: 20 },
  mode: { flexDirection: "row", padding: 3, gap: 2, borderRadius: radius.pill, backgroundColor: colors.custom_cardRaised, borderWidth: 1, borderColor: colors.custom_cardLine },
  modeItem: { flex: 1, minHeight: 38, borderRadius: radius.pill, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 6 },
  modeOn: { backgroundColor: colors.onSurface },
  nav: { gap: 6, paddingRight: space.md },
  navItem: { minHeight: 44, paddingHorizontal: 14, borderRadius: radius.pill, flexDirection: "row", alignItems: "center", gap: 6 },
  navOn: { backgroundColor: colors.brandPrimary },
});
