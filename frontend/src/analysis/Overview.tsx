import React from "react";
import { StyleSheet, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { Icon, Press, T } from "@/src/components/ui";
import { colors, space } from "@/src/theme";
import { An, Drill, RANK_NOTE, SectionProps, TONE, Tone, mmss, pc, pick, r1, slug } from "./format";
import { B, Block, EmptyLine, Foot, Key, LinkButton, Locked, Meter, Tile, Tiles } from "./parts";
import { Histogram, QGrid, ScoreRing, Split } from "./charts";
import { Learnings } from "./Learnings";

// The Score card is dark red in both themes, so its two tints stay the same in both.
const ON_HERO = { good: "#86EFAC", bad: "#FECDD3" };
const GO: Record<string, string> = { overview: "Overview", performance: "Performance", potential: "Score Potential", quality: "Attempt Quality", time: "Time", difficulty: "Difficulty", journey: "Question Journey", qs: "Qs by Qs" };

function Hero({ an, onDrill, go }: { an: An; onDrill: Drill; go: (s: string) => void }) {
  const o = an.overview, v = o.verdict, p = an.paper;
  const counts: [string, string, number, string[], string][] = [
    ["attempted", "Attempted", o.attempted, pick(an, q => ["correct", "incorrect"].includes(q.outcome)), colors.onSurfaceInverse],
    ["correct", "Sahi", o.correct, pick(an, q => q.outcome === "correct"), ON_HERO.good],
    ["incorrect", "Galat", o.incorrect, pick(an, q => q.outcome === "incorrect"), ON_HERO.bad],
    ["skipped", "Chhode", o.skipped, pick(an, q => q.outcome === "skipped"), colors.custom_whiteA70],
  ];
  const tone = v ? TONE[(v.tone in TONE ? v.tone : "info") as Tone] : TONE.info;
  return <View style={{ gap: space.md }}>
    <LinearGradient testID="result-score-card" colors={[colors.brandSecondary, colors.custom_series]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.hero}>
      <View style={styles.heroHead}>
        <View style={{ flex: 1, minWidth: 0, gap: 2 }}>
          <T testID="result-marking-and-time" w="heavy" size={10.5} color={colors.custom_whiteA70} style={styles.kicker}>
            {`${p.count}\u00A0SAWAAL · ${p.minutes ? p.minutes + "\u00A0MIN" : "UNTIMED"} · +${p.marks.correct}\u00A0/\u00A0${p.marks.wrong}`}
          </T>
          <T w="heavy" size={17.5} color={colors.onSurfaceInverse}>Aapka Score</T>
        </View>
        <View style={styles.version}><T testID="result-score-version-label" w="heavy" size={9.5} color={colors.onSurfaceInverse} style={styles.kicker}>{an.score_version === "original" ? "ORIGINAL" : "REVISED"}</T></View>
      </View>
      <View style={styles.ring}><ScoreRing percentage={o.percentage} score={o.score} maximum={o.maximum} /></View>
      <T size={12} color={colors.custom_whiteA70} style={styles.center}>Paper mein laga <T w="mono" size={12} color={colors.onSurfaceInverse}>{mmss(o.time_used)}</T></T>
      <View style={styles.counts}>
        {counts.map(([key, label, value, ids, ink], i) => (
          <Press key={key} testID={"a2-tile-" + key} disabled={!ids.length} onPress={() => onDrill(label, ids)} accessibilityLabel={`${label}: ${value}. Sawaal dekho`} scaleTo={0.96}
            style={[styles.count, i > 0 && styles.countLine]}>
            <T testID={`a2-tile-${key}-value`} w="mono" size={21} color={ink}>{value}</T>
            <T w="bold" size={10.5} color={colors.custom_whiteA70} numberOfLines={1}>{label}</T>
          </Press>
        ))}
      </View>
    </LinearGradient>
    {v ? <Press testID="a2-verdict" onPress={() => go(v.section)} scaleTo={0.985} style={[styles.verdict, { borderColor: tone.line, borderLeftColor: tone.fill, backgroundColor: tone.soft }]}>
      <T w="bold" size={15}>{v.text}</T>
      <View style={styles.inline}><T w="heavy" size={12.5} color={tone.ink}>{GO[v.section] || "Analysis"} mein poora hisaab</T><Icon name="arrow-right" size={14} color={tone.ink} /></View>
    </Press> : null}
    <Tiles>
      <Tile id="rank" label="Rank" value={o.rank ? "#" + o.rank : "—"} sub={o.rank ? `${o.of} ${o.of === 1 ? "student" : "students"} mein` : RANK_NOTE[an.class.state]} tone="brand" />
      <Tile id="percentile" label="Percentile" value={o.percentile ?? "—"} sub={o.rank ? "is paper par" : "Rank ke saath aayega"} />
      <Tile id="accuracy" label="Accuracy" value={pc(o.accuracy)} sub={`${o.correct} sahi / ${o.attempted} attempted`} tone={o.accuracy >= 75 ? "good" : o.accuracy < 50 ? "bad" : "warn"} />
      <Tile id="time" label="Time" value={mmss(o.time_used)} sub={o.time_on_screen != null ? "Sawaalon par " + mmss(o.time_on_screen) : "paper mein laga"} />
    </Tiles>
  </View>;
}

function Ledger({ led }: { led: An["overview"]["ledger"] }) {
  const chips: [string, string, string | number, Tone][] = [["earned", "Kamaye", "+" + led.earned, "good"], ["negative", "Negative mein kate", led.negative ? "−" + led.negative : 0, "bad"],
    ["left_wrong", "Galat jawab mein reh gaye", led.left_wrong, "warn"], ["left_skipped", "Chhode mein reh gaye", led.left_skipped, "mute"], ["net", "Net Score", led.net, "plain"]];
  return <Block id="ledger" kicker="MARKS KA HISAAB" title="Har mark kahan gaya" note={`Paper ${led.maximum} marks ka tha. Kitne kamaye, kitne kate aur kitne mez par reh gaye.`}>
    <View style={styles.ledger}>
      {chips.map(([k, label, value, tone], i) => <View key={k} style={i === chips.length - 1 ? styles.full : styles.half}>
        <View testID={"a2-ledger-" + k} style={[styles.ledgerChip, { borderColor: TONE[tone].line, backgroundColor: TONE[tone].soft }]}>
          <T size={11.5} w="bold" color={colors.custom_softText}>{label}</T>
          <T w="mono" size={22} color={tone === "mute" ? colors.onSurface : TONE[tone].ink} style={styles.num}>{value}</T>
        </View>
      </View>)}
    </View>
    <Split testID="a2-ledger-bar" label="Kamaye, galat mein aur chhode mein reh gaye marks" parts={[["Kamaye", led.earned, "good"], ["Galat mein", led.left_wrong, "bad"], ["Chhode mein", led.left_skipped, "mute"]]} />
    <Key items={[[`Kamaye ${led.earned}`, "good"], [`Galat mein reh gaye ${led.left_wrong}`, "bad"], [`Chhode mein reh gaye ${led.left_skipped}`, "mute"]]} />
    <Foot testID="a2-ledger-no-negative">Agar ek bhi galat jawab na hota (sirf chhod dete), to Score <B>{led.no_negative}</B> hota. Negative ne <B>{led.negative}</B> marks khaaye.</Foot>
  </Block>;
}

function Standing({ an }: { an: An }) {
  const o = an.overview, d = o.distribution, k = an.class;
  if (!d) {
    const text = k.state === "ready" ? `Abhi sirf ${k.n} student ne yeh paper diya hai. Doosra student aate hi yeh chart khul jaayega.` : (RANK_NOTE[k.state] || RANK_NOTE.ready) + ". Tab tak baaki saara analysis aapke apne data se taiyaar hai.";
    return <Locked id="standing" title="Class mein aap kahan ho" text={text} />;
  }
  const above = k.above, gap = above ? r1(above.score - o.score) : 0;
  return <Block id="standing" kicker={`${d.n} STUDENTS NE YEH PAPER DIYA`} title="Class mein aap kahan khade ho" note="Har column ek Score range hai. Laal column mein aap ho.">
    <Histogram dist={d} />
    <View style={styles.facts}>
      {[["Class average", d.average], ["Median", d.median], ["Top Score", d.top]].map(([label, value]) => <View key={label} style={styles.fact}><T size={11} color={colors.muted}>{label}</T><T w="mono" size={15}>{value}</T></View>)}
    </View>
    <Foot>Aap <B>{o.score}</B> ({o.score >= d.average ? `average se ${r1(o.score - d.average)} upar` : `average se ${r1(d.average - o.score)} neeche`})</Foot>
    {above ? <Foot testID="a2-above" tone="good">Aapse theek upar: <B>{above.name}</B> ({above.score} marks). Sirf <B>{gap}</B> {gap === 1 ? "mark" : "marks"} aur, aur Rank ek upar.</Foot> : null}
  </Block>;
}

function Subjects({ an, onDrill }: { an: An; onDrill: Drill }) {
  return <Block id="subjects" kicker="SUBJECT-WISE" title="Har subject ek nazar mein" note="Card par tap karo: us subject ke galat aur chhode sawaal khulenge.">
    {an.overview.subjects.map((g: any) => {
      const ids = pick(an, q => q.subject === g.name && q.outcome !== "correct");
      return <Press key={g.name} testID={"a2-subject-" + slug(g.name)} disabled={!ids.length} onPress={() => onDrill(`${g.name}: galat + chhode`, ids)} scaleTo={0.985} style={styles.subject}>
        <View style={styles.subjectTop}>
          <T w="heavy" size={15} style={{ flex: 1 }} numberOfLines={1}>{g.name}</T>
          <T w="mono" size={19}>{g.score}<T w="monoRegular" size={12.5} color={colors.muted}> / {g.maximum}</T></T>
        </View>
        <View style={styles.meterRow}><Meter value={Math.max(0, g.score)} max={g.maximum} tone="brand" /></View>
        <T size={12.5} color={colors.custom_softText}><B tone="good">{g.correct} sahi</B> · <B tone="bad">{g.incorrect} galat</B> · {g.skipped} chhode</T>
        <T size={12} color={colors.muted}>Accuracy {pc(g.accuracy)}{g.time != null ? " · Time " + mmss(g.time) : ""}</T>
      </Press>;
    })}
  </Block>;
}

function NextThree({ an, onDrill, go }: { an: An; onDrill: Drill; go: (s: string) => void }) {
  const items: any[] = an.overview.next3 || [];
  return <Block id="next3" kicker="SIRF AAPKE DATA SE · KOI AI NAHI" title="Agle mock ke liye 3 kaam" note="Jahan sabse zyada marks daav par hain, wahi pehle.">
    {items.length ? items.map((x, i) => <View key={x.key} testID={"a2-next-" + x.key} style={styles.next}>
      <View style={styles.nextNo}><T w="mono" size={15} color={colors.onBrandPrimary}>{i + 1}</T></View>
      <View style={{ flex: 1, minWidth: 0, gap: 3 }}>
        <T w="heavy" size={15}>{x.title} <T w="heavy" size={13} color={TONE.good.ink}>+{x.marks} marks</T></T>
        <T size={12.5} color={colors.muted}>{x.detail}</T>
        <View style={styles.links}>
          {x.questions.length > 0 ? <LinkButton testID={"a2-next-questions-" + x.key} label={`${x.questions.length} sawaal dekho`} onPress={() => onDrill(x.title, x.questions)} /> : null}
          <LinkButton testID={"a2-next-open-" + x.key} label="Poora hisaab" icon="arrow-right" onPress={() => go(x.section === "questions" ? "qs" : x.section)} />
        </View>
      </View>
    </View>) : <EmptyLine testID="a2-next-empty">Is attempt mein koi bada sudhaar ka point nahi mila. Ab naye sawaal try karo.</EmptyLine>}
  </Block>;
}

export function Overview({ an, id, onDrill, onOpen, go, slot }: SectionProps) {
  return <>
    <Hero an={an} onDrill={onDrill} go={go} />
    {slot}
    <Ledger led={an.overview.ledger} />
    <NextThree an={an} onDrill={onDrill} go={go} />
    <Standing an={an} />
    <Block id="grid" kicker="HAR SAWAAL EK NAZAR MEIN" title="Question map" note="Hara = sahi, laal = galat, dhundhla = chhoda. Kisi bhi number par tap karo, solution khulega.">
      <QGrid an={an} onOpen={onOpen} />
      <Key items={[["Sahi", "good"], ["Galat", "bad"], ["Chhoda", "mute"], ["Marked for review", "warn"]]} />
    </Block>
    <Subjects an={an} onDrill={onDrill} />
    <Learnings key={an.attempt_id} id={id} an={an} />
  </>;
}

const styles = StyleSheet.create({
  hero: { gap: space.md, borderRadius: 24, padding: 18, borderWidth: 1, borderColor: colors.brandLine },
  kicker: { letterSpacing: 1.4 },
  heroHead: { flexDirection: "row", alignItems: "flex-start", gap: space.sm },
  version: { paddingHorizontal: 9, paddingVertical: 4, borderRadius: 999, borderWidth: 1, borderColor: colors.custom_whiteA15, backgroundColor: colors.custom_whiteA15 },
  ring: { alignItems: "center", paddingVertical: 4 },
  center: { textAlign: "center" },
  num: { letterSpacing: -0.7 },
  counts: { flexDirection: "row", borderRadius: 16, backgroundColor: colors.custom_whiteA15 },
  count: { flex: 1, minHeight: 60, alignItems: "center", justifyContent: "center", paddingVertical: 8, paddingHorizontal: 2 },
  countLine: { borderLeftWidth: 1, borderLeftColor: colors.custom_whiteA15 },
  verdict: { gap: 8, padding: 14, borderRadius: 16, borderWidth: 1, borderLeftWidth: 4 },
  inline: { flexDirection: "row", alignItems: "center", gap: 5 },
  ledger: { flexDirection: "row", flexWrap: "wrap", marginHorizontal: -4, rowGap: 8 },
  half: { width: "50%", paddingHorizontal: 4 }, full: { width: "100%", paddingHorizontal: 4 },
  ledgerChip: { flex: 1, padding: space.md, borderRadius: 14, borderWidth: 1, gap: 2 },
  facts: { flexDirection: "row", gap: 8 },
  fact: { flex: 1, padding: 10, borderRadius: 12, backgroundColor: colors.custom_bar, borderWidth: 1, borderColor: colors.custom_barLine, gap: 1 },
  subject: { padding: space.md, borderRadius: 16, borderWidth: 1, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_bar, gap: 6 },
  subjectTop: { flexDirection: "row", alignItems: "baseline", gap: 8 },
  meterRow: { flexDirection: "row" },
  next: { flexDirection: "row", gap: space.md, padding: space.md, borderRadius: 16, borderWidth: 1, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_bar },
  nextNo: { width: 34, height: 34, borderRadius: 11, backgroundColor: colors.brandPrimary, alignItems: "center", justifyContent: "center" },
  links: { flexDirection: "row", flexWrap: "wrap", columnGap: 18 },
});
