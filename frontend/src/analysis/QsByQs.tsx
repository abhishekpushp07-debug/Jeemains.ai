import React, { useState } from "react";
import { StyleSheet, View } from "react-native";
import { Icon, Press, T } from "@/src/components/ui";
import { DSheet, Pill } from "@/src/components/design";
import { colors, space } from "@/src/theme";
import { An, Open, OUT_ICON, OUT_TONE, Q, RESULT, SectionProps, TONE, mmss, pc } from "./format";
import { B, Block, ChipButton, EmptyLine, Pills, TagChip, ToneTag } from "./parts";

const FILTERS: [string, string][] = [["all", "Sab"], ["wrong", "Galat"], ["skipped", "Chhode"], ["careless", "Careless"], ["overtime", "Overtime"], ["confused", "Confused"], ["marked", "Marked"], ["changed", "Jawab badla"]];
const TEST: Record<string, (q: Q) => boolean> = {
  all: () => true, wrong: q => q.outcome === "incorrect", skipped: q => q.outcome === "skipped", careless: q => q.tag === "wasted",
  overtime: q => ["slow_correct", "costly_overtime"].includes(q.tag), confused: q => q.tag === "confused", marked: q => q.marked, changed: q => !!q.changed,
};
const SORT: Record<string, [string, (a: Q, b: Q) => number]> = {
  number: ["Sawaal number", (a, b) => a.number - b.number], time: ["Sabse zyada time", (a, b) => (b.time || 0) - (a.time || 0)],
  hard: ["Class mein sabse mushkil", (a, b) => (a.class?.correct ?? 101) - (b.class?.correct ?? 101)], marks: ["Sabse zyada marks gaye", (a, b) => a.marks - b.marks],
};
const PAGE = 25;

function Card({ q, an, them, label, onOpen }: { q: Q; an: An; them: Record<string, number> | null; label: string; onOpen: Open }) {
  const c = q.class, L = an.copy.levels, tone = OUT_TONE[q.outcome] || "mute";
  return <Press testID={"a2-qs-card-" + q.number} onPress={() => onOpen(q.id)} scaleTo={0.99} accessibilityLabel={`Q${q.number}, ${q.subject}, ${RESULT[q.outcome]}. Solution kholo`}
    style={[styles.card, { borderLeftColor: TONE[tone].fill }]}>
    <View style={styles.top}>
      <T w="heavy" size={15}>Q{q.number}</T>
      <T size={12} color={colors.muted} numberOfLines={1} style={{ flex: 1 }}>{q.subject} · {L[q.difficulty] || "—"}</T>
      <ToneTag label={`${RESULT[q.outcome]} ${q.marks > 0 ? "+" : ""}${q.marks}`} tone={tone} icon={OUT_ICON[q.outcome]} />
    </View>
    {an.performance.has_chapters && q.topic ? <T size={11.5} color={colors.muted} numberOfLines={1}>{q.topic}</T> : null}
    <T size={12.5} color={colors.custom_softText}>Aapka <B>{q.response || "—"}</B> · Sahi <B>{q.answer}</B>{q.changed ? ` · badla ${q.changed}` : ""}</T>
    <T size={12} color={colors.custom_softText}>Time <B>{mmss(q.time)}</B> · Par {mmss(q.par)}{them ? ` · ${label} ${mmss(them[q.id] || null)}` : ""}{q.visits != null ? ` · ${q.visits} baar dekha` : ""}</T>
    {c ? <T size={12} color={colors.muted}>Class: {pc(c.correct)} sahi · avg {mmss(c.avg_time)}{c.topper_time > 0 ? ` · Topper ${mmss(c.topper_time)}` : ""}{c.top_wrong ? ` · ${c.top_wrong.percent}% ne ${c.top_wrong.option} chuna` : ""}</T> : null}
    <View style={styles.bottom}><TagChip tag={q.tag} copy={an.copy} /><Icon name="chevron-right" size={18} color={colors.custom_dim} /></View>
  </Press>;
}

export function QsByQs({ an, onOpen }: SectionProps) {
  const [f, setF] = useState("all");
  const [subject, setSubject] = useState("all");
  const [sort, setSort] = useState("number");
  const [sorting, setSorting] = useState(false);
  const [shown, setShown] = useState(PAGE);
  const subjects: string[] = [...new Set<string>(an.questions.map((q: Q) => q.subject))];
  const base: Q[] = an.questions.filter((q: Q) => subject === "all" || q.subject === subject);
  const rows = base.filter(TEST[f]).sort(SORT[sort][1]);
  const them = an.compare?.available ? an.compare.times : null;
  const pickFilter = (set: (v: string) => void) => (v: string) => { set(v); setShown(PAGE); };
  return <Block id="qs" kicker="QS BY QS" title="Har sawaal ka hisaab" note={`${rows.length} / ${an.questions.length} sawaal. Kisi bhi sawaal par tap karo, uska solution khulega.`}>
    {subjects.length > 1 ? <Pills id="qs-subject" value={subject} onChange={pickFilter(setSubject)} items={[["all", "Sab subjects"], ...subjects.map(s => [s, s] as [string, string])]} /> : null}
    <Pills id="qs-filter" value={f} onChange={pickFilter(setF)} items={FILTERS.map(([k, l]) => [k, `${l} (${base.filter(TEST[k]).length})`])} />
    <ChipButton testID="a2-qs-sort" onPress={() => setSorting(true)} label={`Sort: ${SORT[sort][0]}`}>
      <Icon name="sort" size={15} color={colors.custom_softText} /><T size={12.5} w="bold">Sort: {SORT[sort][0]}</T><Icon name="chevron-down" size={15} color={colors.custom_softText} />
    </ChipButton>
    {!rows.length ? <EmptyLine testID="a2-qs-empty">Is filter mein koi sawaal nahi.</EmptyLine> : null}
    <View testID="a2-qs-cards" style={{ gap: 8 }}>{rows.slice(0, shown).map(q => <Card key={q.id} q={q} an={an} them={them} label={an.compare?.label || ""} onOpen={onOpen} />)}</View>
    {rows.length > shown ? <Pill testID="a2-qs-more" kind="outline" size="sm" label={`Aur ${Math.min(PAGE, rows.length - shown)} sawaal dikhao (${rows.length - shown} baaki)`} onPress={() => setShown(shown + PAGE)} /> : null}
    <DSheet visible={sorting} onClose={() => setSorting(false)} testID="a2-qs-sort-sheet" title="Sawaal kis order mein">
      {Object.entries(SORT).map(([k, [label]]) => <Press key={k} testID={"a2-qs-sort-" + k} onPress={() => { setSort(k); setShown(PAGE); setSorting(false); }} accessibilityState={{ selected: sort === k }} style={styles.option}>
        <T size={15} w={sort === k ? "heavy" : "medium"} style={{ flex: 1 }}>{label}</T>
        {sort === k ? <Icon name="check" size={20} color={colors.brandText} /> : null}
      </Press>)}
    </DSheet>
  </Block>;
}

const styles = StyleSheet.create({
  card: { gap: 5, padding: space.md, borderRadius: 14, borderWidth: 1, borderLeftWidth: 4, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_bar },
  top: { flexDirection: "row", alignItems: "center", gap: 8 },
  bottom: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginTop: 2 },
  option: { minHeight: 52, flexDirection: "row", alignItems: "center", gap: space.md, borderBottomWidth: 1, borderBottomColor: colors.custom_barLine },
});
