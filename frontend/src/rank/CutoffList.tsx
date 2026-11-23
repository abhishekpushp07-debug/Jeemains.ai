// The answer of the Cut off tool: the heading, the optional score box ("sirf eligible dikhao"), then one card per row with
// every round's cut-off in small boxes (green = the student's rank is inside that round, amber = on the edge), 25 at a time,
// and the nearest misses under a filtered list.
import React, { useState } from "react";
import { ActivityIndicator, StyleSheet, View } from "react-native";
import { Press, T } from "@/src/components/ui";
import { rankColors as colors, radius, space } from "@/src/theme";
import { CutoffBy, CutoffCell, CutoffOut, CutoffRow, fmt, fmtRange, Level, ScoreKind, Tag as Chance } from "./api";
import { EXAM, KIND, LEVEL, TAG } from "./tones";
import { NumberField, Strip, Tag, Toggle } from "./controls";
import { CardsHeading, cardStyles } from "./CollegeCard";
import { edgeOf } from "./SeatList";
import { FormButton, InForm } from "./accent";
import { readScore, SCORE } from "./profile";
import type { Pick } from "./Cutoff";

const PAGE = 25;
const LEVELS: Level[] = ["tough", "normal", "easy"];
const CHANCES: Chance[] = ["safe", "likely", "borderline"];
const KIND_LABEL: Record<ScoreKind, string> = { marks: "Marks", percentile: "Percentile", rank: "Rank" };

export function CutoffList({ data, busy, pick, onPick, kinds, level, onLevel }: {
  data: CutoffOut; busy: boolean; pick: Pick; onPick: (x: Partial<Pick>) => void; kinds: ScoreKind[]; level: Level; onLevel: (l: Level) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const [shown, setShown] = useState(PAGE);
  const you = data.you, rule = SCORE[data.exam][pick.kind]!;
  const kind = data.kind ? KIND[data.kind as keyof typeof KIND] ?? (data.exam === "jee" ? null : EXAM[data.exam]) : null;
  const what = { jee: { college: "branches", branch: "college-branch" }, comedk: { college: "courses", branch: "college-course" }, bitsat: { college: "programs", branch: "campus" } }[data.exam][data.by];
  const count = you ? `${data.eligible} / ${data.total} ${what} eligible${data.rows.length < (data.eligible ?? 0) ? ` · top ${data.rows.length} dikh rahe` : ""}`
    : data.limit && data.total > data.limit ? `Top ${data.limit} of ${data.total} ${what} · sabse zyada demand wale pehle`
    : `${data.total} ${what} · ${data.metric === "score" ? "5 saal ke cutoff score" : "har round ki closing rank"}`;
  const apply = () => {
    const v = readScore(data.exam, pick.kind, pick.text);
    if (typeof v !== "number") { setProblem(v ?? "Pehle apna score daalo."); return; }
    setProblem(null); setEditing(false); setShown(PAGE);
    onPick({ score: { [pick.kind]: v } });
  };
  const showAll = () => { setEditing(false); setProblem(null); setShown(PAGE); onPick({ score: null }); };

  return <View testID="cut-list" style={cardStyles.list}>
    <Strip title={data.title} testID="cut-head" right={busy ? <ActivityIndicator size="small" color={colors.muted} /> : kind ? <Tag label={kind.label} ink={kind.ink} soft={kind.soft} /> : undefined}>
      <T size={12.5} color={colors.muted}>{data.sub}</T>
      <T testID="cut-count" w="bold" size={13.5}>{count}</T>
      <InForm.Provider value>
        {you && !editing ? <View testID="cut-you" style={styles.box}>
          <T w="bold" size={10.5} color={colors.custom_eyebrow} style={styles.caps}>AAPKA SCORE</T>
          <T testID="cut-you-line" w="bold" size={13.5}>{you.line}</T>
          {[you.cat_rank, you.pwd_rank].map(x => x ? <T key={x.label} size={12} color={colors.custom_softText}>{x.label}: {fmtRange(x.range)}</T> : null)}
          <View style={styles.wrap}>
            {CHANCES.map(c => <Tag key={c} testID={`cut-count-${c}`} label={`${TAG[c].label} ${you.counts[c]}`} ink={TAG[c].ink} soft={TAG[c].soft} />)}
          </View>
          <T testID="cut-you-key" size={11.5} color={colors.custom_dim}>
            {data.metric === "score" ? "Hara box = 2026 ka cutoff aap clear karte ho. Peela = kinare par, pakka nahi." : "Hara box = us round mein aap andar. Peela = kinare par, pakka nahi."}
          </T>
          {you.check ? <T testID="cut-you-check" size={11.5} color={colors.custom_flame}>{you.check}</T> : null}
          <View style={styles.actions}>
            <Press testID="cut-edit" onPress={() => setEditing(true)} style={styles.action} accessibilityRole="button"><T w="bold" size={13}>Score badlo</T></Press>
            <Press testID="cut-clear" onPress={showAll} style={styles.action} accessibilityRole="button"><T w="bold" size={13}>Sab cutoffs dikhao</T></Press>
          </View>
        </View> : <View testID="cut-score" style={styles.box}>
          <T w="bold" size={14}>Sirf wahi dekhna hai jahan aap eligible ho?</T>
          <T size={12} color={colors.muted}>Apna score daalo (optional). Sirf Safe, Likely aur Borderline options bachenge.</T>
          {kinds.length > 1 ? <View style={styles.wrap}>
            {kinds.map(k => <Toggle key={k} testID={`cut-kind-${k}`} label={KIND_LABEL[k]} on={pick.kind === k} onPress={() => { if (k !== pick.kind) onPick({ kind: k, text: "" }); setProblem(null); }} />)}
          </View> : null}
          <View style={styles.wrap}>
            <NumberField testID="cut-score-input" label={rule.label} placeholder={rule.hint} value={pick.text} onChange={text => { onPick({ text }); setProblem(null); }}
              max={rule.len} decimal={rule.decimal} signed={rule.signed} onSubmit={apply} />
          </View>
          {data.exam === "jee" && pick.kind === "marks" ? <>
            <T w="semibold" size={12} color={colors.muted}>Aapki shift ka paper kaisa tha?</T>
            <View style={styles.wrap}>
              {LEVELS.map(l => <Toggle key={l} testID={`cut-level-${l}`} label={LEVEL[l].label} on={level === l} ink={LEVEL[l].ink} soft={LEVEL[l].soft} onPress={() => onLevel(l)} />)}
            </View>
          </> : null}
          {problem ? <T testID="cut-score-error" w="semibold" size={13} color={colors.error}>{problem}</T> : null}
          <FormButton testID="cut-apply" label="Eligible dikhao" busy={busy && !!pick.score} onPress={apply} />
          {pick.score ? <Press testID="cut-clear" onPress={showAll} style={styles.link} accessibilityRole="button"><T w="bold" size={13} color={colors.custom_softText}>Sab cutoffs dikhao</T></Press> : null}
        </View>}
      </InForm.Provider>
    </Strip>

    {data.rows.length === 0 ? <T testID="cut-empty" size={13.5} color={colors.muted}>
      {you ? `Is score par yahan 2026 mein koi option eligible nahi tha.${data.near.length ? " Neeche dekho, kitna door ho." : ""}` : "Aapki category, gender aur home state ke liye yahan 2026 ki koi seat nahi thi."}
    </T> : null}
    {data.rows.slice(0, shown).map((r, i) => <Row key={r.id} r={r} by={data.by} metric={data.metric} n={i + 1} testID={`cut-row-${i}`} />)}
    {data.rows.length > shown ? <Press testID="cut-more" onPress={() => setShown(shown + PAGE)} style={styles.more} accessibilityRole="button">
      <T w="bold" size={14}>Aur dikhao ({data.rows.length - shown} baaki)</T>
    </Press> : null}
    {data.near.length ? <View testID="cut-near" style={cardStyles.list}>
      <CardsHeading icon="flag-checkered" title="BAS THODA SA DOOR" sub="Thoda aur, aur ye bhi aapke" ink={colors.custom_flame} />
      {data.near.map((r, i) => <Row key={r.id} r={r} by={data.by} metric={data.metric} testID={`cut-near-${i}`} near />)}
    </View> : null}
    <View style={{ gap: 4 }}>{data.notes.map(n => <T key={n} size={11.5} color={colors.custom_dim}>{n}</T>)}</View>
  </View>;
}

type Box = CutoffCell & { past?: boolean };

/** One college-branch: who and where, every round in boxes of 4 (5 when that is all there are), then the final line. */
function Row({ r, by, metric, n, testID, near }: { r: CutoffRow; by: CutoffBy; metric: CutoffOut["metric"]; n?: number; testID: string; near?: boolean }) {
  // A round the college does not have (JAC Delhi stops at R4) is left out; last year's final closes the set.
  const boxes: Box[] = [...r.cells.filter(c => !c.na), ...(r.prev ? [{ label: r.prev.label, close: r.prev.close, past: true }] : [])];
  const per = boxes.length <= 5 ? boxes.length : 4;
  const lines = Array.from({ length: Math.ceil(boxes.length / per) }, (_, i) => boxes.slice(i * per, i * per + per));
  const need = r.need.level ? `≈ ${r.need.marks}+ marks (${LEVEL[r.need.level].label} paper)` : `≈ ${r.need.marks}+ marks / 180`;
  const final = metric === "score" ? `${r.final.label} cutoff: ${r.final.close} / 390`
    : [`Closing ${r.final.label}: ${fmt(r.final.close)} ${r.rank_type}`, need, r.seats ? `${r.seats} seats` : null, r.fee ? `₹${fmt(r.fee)} / saal` : null].filter(Boolean).join(" · ");
  return <View testID={testID} style={styles.card}>
    <View style={[styles.edge, { backgroundColor: edgeOf(r.tag, near) }]} />
    <View style={styles.head}>
      {n ? <T w="heavy" size={12} color={colors.custom_dim} style={styles.num}>{n}</T> : null}
      <View style={{ flex: 1, minWidth: 0, gap: 3 }}>
        <T testID={`${testID}-title`} w="bold" size={14.5} numberOfLines={3}>{by === "college" ? r.branch : r.college}</T>
        {by === "branch" ? <T size={13} color={colors.custom_softText} numberOfLines={3}>{r.branch}</T> : null}
        <T size={11.5} color={colors.muted} numberOfLines={2}>{by === "branch" ? `${r.place} · ${r.path}` : r.path}</T>
      </View>
      {r.tag ? <Tag testID={`${testID}-tag`} label={TAG[r.tag].label} ink={TAG[r.tag].ink} soft={TAG[r.tag].soft} /> : null}
    </View>
    {lines.map((line, i) => <View key={i} style={styles.boxes}>
      {line.map(c => <RoundBox key={c.label} c={c} />)}
      {Array.from({ length: per - line.length }, (_, k) => <View key={k} style={styles.gap} />)}
    </View>)}
    <T testID={`${testID}-final`} size={12} color={colors.custom_softText}>{final}</T>
    {r.gap ? <T testID={`${testID}-gap`} w="semibold" size={12} color={colors.custom_flame}>{r.gap}</T> : null}
  </View>;
}

function RoundBox({ c }: { c: Box }) {
  const ink = !c.close ? colors.custom_dim : c.state === "in" ? TAG.safe.ink : c.state === "edge" ? TAG.borderline.ink : c.past || c.state === "out" ? colors.custom_softText : colors.onSurface;
  return <View style={[styles.round, c.past && styles.past, c.state === "in" && styles.in, c.state === "edge" && styles.onEdge]}
    accessibilityLabel={`${c.label}: ${c.close ? fmt(c.close) : "nahi"}${c.state === "in" ? ", aap andar" : c.state === "edge" ? ", kinare par" : ""}`}>
    <T w="bold" size={9.5} color={colors.custom_eyebrow} numberOfLines={1}>{c.label}{c.crl && c.close ? " · CRL" : ""}</T>
    <T w="heavy" size={13} color={ink} numberOfLines={1} adjustsFontSizeToFit minimumFontScale={0.75}>{c.close ? fmt(c.close) : "—"}</T>
  </View>;
}

const styles = StyleSheet.create({
  caps: { letterSpacing: 2 },
  wrap: { flexDirection: "row", flexWrap: "wrap", gap: space.sm },
  box: { gap: space.sm, padding: space.md, borderRadius: 16, borderWidth: 1, borderColor: colors.custom_fTealLine, backgroundColor: colors.custom_cardRaised },
  actions: { flexDirection: "row", gap: space.sm },
  action: { flex: 1, minWidth: 0, minHeight: 44, borderRadius: radius.pill, borderWidth: 1, borderColor: colors.custom_cardLineStrong, alignItems: "center", justifyContent: "center", paddingHorizontal: space.sm },
  link: { minHeight: 44, alignItems: "center", justifyContent: "center" },
  more: { minHeight: 48, borderRadius: radius.pill, borderWidth: 1, borderColor: colors.custom_cardLineStrong, alignItems: "center", justifyContent: "center" },
  card: { gap: space.sm, paddingVertical: 14, paddingLeft: 16, paddingRight: 14, borderRadius: 18, borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_card, overflow: "hidden" },
  edge: { position: "absolute", left: 0, top: 0, bottom: 0, width: 4 },
  head: { flexDirection: "row", alignItems: "flex-start", gap: space.sm },
  num: { minWidth: 18, paddingTop: 2 },
  boxes: { flexDirection: "row", gap: 6 },
  round: { flex: 1, minWidth: 0, alignItems: "center", gap: 2, paddingVertical: 7, paddingHorizontal: 3, borderRadius: 10, borderWidth: 1, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_cardRaised },
  gap: { flex: 1 },
  past: { borderStyle: "dashed" },
  in: { backgroundColor: colors.custom_successSoft, borderColor: colors.success },
  onEdge: { backgroundColor: colors.custom_flameSoft, borderColor: colors.custom_flame },
});
