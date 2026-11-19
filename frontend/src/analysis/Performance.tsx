import React, { useState } from "react";
import { StyleSheet, View } from "react-native";
import { T } from "@/src/components/ui";
import { colors } from "@/src/theme";
import { An, Drill, SectionProps, TONE, Tone, mmss, pc, pick, slug } from "./format";
import { Block, EmptyLine, Meter, Pills, StatRow, Tile, Tiles, ToneTag } from "./parts";

const HAAL: Record<string, [string, Tone]> = { strong: ["Mazboot", "good"], steady: ["Theek", "info"], weak: ["Kamzor", "bad"] };
const neg = (v: number) => (v ? "−" + v : "0");
const MeterLine = ({ value, max, tone }: { value: number; max: number; tone?: Tone }) => <View style={styles.meter}><Meter value={value} max={max} tone={tone} /></View>;

function AllSubjects({ subjects, setName }: { subjects: any[]; setName: (name: string) => void }) {
  return <Block id="performance" kicker="SAB SUBJECTS" title="Subject vs subject" note="Subject par tap karo, uska poora hisaab khulega.">
    <View testID="a2-subject-table" style={styles.list}>
      {subjects.map(g => <StatRow key={g.name} testID={"a2-subject-row-" + slug(g.name)} title={g.name} right={`${g.score} / ${g.maximum}`} onPress={() => setName(g.name)}
        sub={`Negative ${neg(g.negative)} · Dekha hi nahi ${g.not_seen}${g.time != null ? " · Time " + mmss(g.time) : ""}`}>
        <MeterLine value={Math.max(0, g.score)} max={g.maximum} />
        <View style={styles.pair}>
          <T size={12} color={colors.custom_softText}>Accuracy <T size={12} w="heavy">{pc(g.accuracy)}</T></T>
          <T size={12} color={colors.custom_softText}>Attempt rate <T size={12} w="heavy">{pc(g.attempt_rate)}</T></T>
        </View>
      </StatRow>)}
    </View>
  </Block>;
}

function OneSubject({ an, g, onDrill }: { an: An; g: any; onDrill: Drill }) {
  const ids = (test: (q: any) => boolean) => pick(an, q => q.subject === g.name && test(q));
  return <>
    <Block id="performance" kicker="SUBJECT" title={g.name} note="Is subject mein aapka poora hisaab. Tile par tap karo, sawaal khulenge.">
      <Tiles>
        <Tile id="perf-score" label="Score" value={`${g.score} / ${g.maximum}`} tone="brand" />
        <Tile id="perf-accuracy" label="Accuracy" value={pc(g.accuracy)} sub={`${g.correct} sahi / ${g.attempted}`} ids={ids(q => q.outcome === "correct")} onDrill={onDrill} tone="good" />
        <Tile id="perf-attempt-rate" label="Attempt rate" value={pc(g.attempt_rate)} sub={`${g.skipped} chhode`} ids={ids(q => q.outcome === "skipped")} onDrill={onDrill} />
        <Tile id="perf-negative" label="Negative marks" value={g.negative ? "−" + g.negative : 0} sub={`${g.incorrect} galat`} tone="bad" ids={ids(q => q.outcome === "incorrect")} onDrill={onDrill} />
        <Tile id="perf-not-seen" label="Dekha hi nahi" value={g.not_seen} sub="khula hi nahi" tone="mute" ids={ids(q => q.outcome === "skipped" && !q.seen)} onDrill={onDrill} />
      </Tiles>
      <View testID="a2-type-table" style={styles.list}>
        {Object.entries(g.types as Record<string, any>).map(([t, d]) => <StatRow key={t} testID={"a2-type-row-" + t} title={t === "integer" ? "Numerical" : "MCQ"} caption={`${d.count} sawaal`} right={`${d.score} / ${d.maximum}`}
          sub={`${d.correct} sahi · ${d.incorrect} galat · ${d.skipped} chhode · Accuracy ${pc(d.accuracy)}`} />)}
      </View>
    </Block>
    {g.chapters.length > 0 ? <Block id="chapters" kicker="CHAPTER-WISE" title={`${g.name} ke chapters`} note="3 se kam sawaal wale chapter par Mazboot / Kamzor nahi likha jaata. Chapter par tap karo, uske sawaal khulenge.">
      <View testID="a2-chapter-table" style={styles.list}>
        {g.chapters.map((c: any) => <StatRow key={c.name} testID={"a2-chapter-row-" + slug(c.name)} title={c.name} onPress={() => onDrill(`${g.name} · ${c.name}`, ids(q => q.topic === c.name))}
          tag={c.label && HAAL[c.label] ? <ToneTag label={HAAL[c.label][0]} tone={HAAL[c.label][1]} /> : undefined}
          sub={`${c.count} sawaal · ${c.correct} sahi · ${c.incorrect} galat · ${c.skipped} chhode`}>
          <View style={styles.pair}>
            <T size={12} color={colors.custom_softText}>Accuracy <T size={12} w="heavy">{pc(c.accuracy)}</T></T>
            <T size={12} color={colors.custom_softText}>Marks gaye <T size={12} w="heavy" color={c.lost ? TONE.bad.ink : colors.onSurface}>{neg(c.lost)}</T></T>
          </View>
        </StatRow>)}
      </View>
    </Block> : null}
  </>;
}

function Weak({ weak, onDrill }: { weak: any[]; onDrill: Drill }) {
  if (!weak.length) return null;
  const most = Math.max(1, ...weak.map(w => w.lost));
  return <Block id="weak" kicker="SABSE MEHNGE CHAPTERS" title="Marks kis chapter se gaye" note="Galat jawab (marks + negative) aur chhode sawaalon ke marks milaakar. Chapter par tap karo.">
    <View testID="a2-weak-chapters" style={styles.list}>
      {weak.map(w => <StatRow key={w.subject + w.name} testID={"a2-weak-" + slug(w.name)} title={w.name} caption={`${w.subject} · ${w.wrong} galat, ${w.skipped} chhode`} right={"−" + w.lost} rightTone="bad"
        onPress={() => onDrill(`${w.name} (${w.subject})`, w.questions)}>
        <MeterLine value={w.lost} max={most} tone="bad" />
      </StatRow>)}
    </View>
  </Block>;
}

function Sections({ s }: { s: any }) {
  const m = s.main, b = s.bonus;
  const line = (x: any) => `${x.correct} sahi · ${x.incorrect} galat · ${x.skipped} chhode`;
  return <Block id="sections" kicker="SECTION-WISE" title="Paper ke sections">
    <View testID="a2-section-table" style={styles.list}>
      {s.sections.map((x: any) => <StatRow key={x.name} title={x.name} right={`${x.score} / ${x.maximum}`} sub={line(x)} />)}
      {m ? <StatRow title={`Main total (${m.count})`} right={`${m.score} / ${m.maximum}`} sub={line(m)} /> : null}
      {b ? <StatRow title={`Bonus (${b.count})`} right={b.entered ? `${b.score} / ${b.maximum}` : undefined} sub={b.entered ? line(b) : "Bonus khola hi nahi"} /> : null}
    </View>
  </Block>;
}

export function Performance({ an, onDrill }: SectionProps) {
  const P = an.performance, subjects: any[] = P.subjects;
  const [name, setName] = useState("all");
  const g = subjects.find(s => s.name === name);
  if (!subjects.length) return null;
  return <>
    <Pills id="perf-subject" value={g ? name : "all"} onChange={setName} items={[["all", "Sab subjects"], ...subjects.map(s => [s.name, s.name] as [string, string])]} />
    {g ? <OneSubject an={an} g={g} onDrill={onDrill} /> : <AllSubjects subjects={subjects} setName={setName} />}
    <Weak weak={g ? P.weak.filter((w: any) => w.subject === g.name) : P.weak} onDrill={onDrill} />
    {!g && P.sections ? <Sections s={P.sections} /> : null}
    {!P.has_chapters ? <EmptyLine testID="a2-no-chapters">Is paper ke sawaalon par chapter ka tag nahi hai, isliye chapter-wise hisaab nahi bana.</EmptyLine> : null}
  </>;
}

const styles = StyleSheet.create({
  list: { gap: 8 },
  meter: { flexDirection: "row" },
  pair: { flexDirection: "row", flexWrap: "wrap", columnGap: 16, rowGap: 2 },
});
