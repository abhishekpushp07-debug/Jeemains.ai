import React, { useState } from "react";
import { StyleSheet, View } from "react-native";
import { Icon, Press, T } from "@/src/components/ui";
import { DSheet } from "@/src/components/design";
import { colors, space } from "@/src/theme";
import { shortSubject } from "@/src/components/player/PlayerParts";
import { An, TONE, mmss, pc, r1 } from "./format";
import { B, Block, ChipButton, EmptyLine, Grid, Locked, Pills, StatRow, Tile, Tiles } from "./parts";
import { Bars, Lines } from "./charts";
import { useBoard } from "./Leaderboard";

const TARGETS: [string, string][] = [["topper", "Topper"], ["top10", "Top 10%"], ["average", "Class average"]];

/** Who to compare with: the Topper, the Top 10%, the class average, or any student from this paper's leaderboard. */
export function ComparePicker({ id, value, onChange }: { id: string; value: string; onChange: (v: string) => void }) {
  const d = useBoard(id);
  const [open, setOpen] = useState(false);
  const seen = new Set<string>();
  const people: any[] = d?.state === "ready" ? [...d.rows, ...d.around].filter((r: any) => !r.is_you && !seen.has(r.handle) && !!seen.add(r.handle)) : [];
  const student = value.startsWith("user:");
  const chosen = student ? people.find(p => "user:" + p.handle === value) : null;
  return <View testID="a2-compare-picker" style={styles.picker}>
    <T w="heavy" size={13}>Kisse compare karna hai?</T>
    <Pills id="compare" value={student ? "" : value} onChange={onChange} items={TARGETS} />
    {people.length > 0 ? <ChipButton testID="a2-compare-student" on={student} onPress={() => setOpen(true)} label="Leaderboard se student chuno">
      <Icon name="account-search-outline" size={16} color={colors.custom_softText} />
      <T size={12.5} w="bold" numberOfLines={1} style={{ flexShrink: 1 }}>{chosen ? `#${chosen.rank} · ${chosen.name} · ${chosen.score}` : student ? "Chuna hua student" : "Leaderboard se student chuno"}</T>
      <Icon name="chevron-down" size={16} color={colors.custom_softText} />
    </ChipButton> : null}
    <DSheet visible={open} onClose={() => setOpen(false)} testID="a2-compare-student-sheet" title="Student chuno">
      {people.map(p => {
        const on = value === "user:" + p.handle;
        return <Press key={p.handle} testID={"a2-compare-student-" + p.handle} onPress={() => { onChange("user:" + p.handle); setOpen(false); }} accessibilityState={{ selected: on }} style={styles.person}>
          <T w="heavy" size={14} style={styles.rank}>#{p.rank}</T>
          <T size={14} w={on ? "heavy" : "bold"} numberOfLines={1} style={{ flex: 1 }}>{p.name}</T>
          <T w="heavy" size={15}>{p.score}</T>
          {on ? <Icon name="check" size={18} color={colors.brandText} /> : null}
        </Press>;
      })}
    </DSheet>
  </View>;
}

const QUALITY: [string, (t: any) => number][] = [["Perfect", t => t.perfect], ["Careless galti", t => t.wasted], ["Overtime", t => t.slow_correct + t.costly_overtime], ["Confused", t => t.confused], ["Concept gap", t => t.concept_gap]];
const HAS: Record<string, string[]> = { head: ["overview", "potential", "journey", "qs"], subjects: ["overview", "performance"], quality: ["quality"], pace: ["time"], difficulty: ["difficulty"], gap: ["overview", "potential", "performance"] };

const Duo = ({ label, you, them }: { label: string; you: React.ReactNode; them: React.ReactNode }) => (
  <View style={styles.duo}>
    <T size={10} w="heavy" color={colors.custom_eyebrow} style={styles.caps}>{label.toUpperCase()}</T>
    <T w="mono" size={14} color={TONE.brand.ink}>{you}</T>
    <T size={11.5} color={colors.muted}>vs <T w="mono" size={12.5} color={TONE.warn.ink}>{them}</T></T>
  </View>
);

/** Who is which colour, the same in every chart and table of the comparison. */
const Key = ({ label }: { label: string }) => (
  <View testID="a2-compare-key" style={styles.key}>
    <View style={styles.keyItem}><View style={[styles.keyDot, { backgroundColor: TONE.brand.fill }]} /><T size={12} w="heavy">Aap</T></View>
    <View style={styles.keyItem}><View style={[styles.keyDot, { backgroundColor: TONE.warn.fill }]} /><T size={12} w="heavy">{label}</T></View>
  </View>
);

function Gap({ c, an }: { c: any; an: An }) {
  const top = c.by_subject.find((s: any) => s.gap > 0);
  const hard = [...c.by_difficulty].filter((d: any) => d.you != null && d.them != null).sort((a: any, b: any) => (b.them - b.you) - (a.them - a.you))[0];
  const t = c.split_total || { volume: 0, quality: 0 };
  const lines = [
    top ? <T key="s" size={13} color={colors.custom_softText}>Subject: <B>{top.name}</B> mein {top.gap} marks ka gap (aap {top.you}, {c.label} {top.them}).</T> : null,
    hard && hard.them > hard.you ? <T key="d" size={13} color={colors.custom_softText}>Difficulty: <B>{an.copy.levels[hard.level]}</B> sawaalon par Accuracy aap {pc(hard.you)}, {c.label} {pc(hard.them)}.</T> : null,
    c.gap > 0 ? <T key="g" size={13} color={colors.custom_softText}>Kul gap {c.gap} marks: <B>{r1(t.volume)}</B> zyada attempts se, <B>{r1(t.quality)}</B> behtar accuracy se.</T> : null,
  ].filter(Boolean);
  return <Block id="compare-gap" kicker="GAP KA POST-MORTEM" title="Gap sabse bada kahan hai" note="Volume = unhone zyada sawaal attempt kiye. Quality = har attempt par unke marks zyada bane.">
    <View testID="a2-compare-biggest" style={{ gap: 6 }}>
      {lines.length ? lines.map((line, i) => <View key={i} style={styles.bullet}><View style={styles.dot} />{line}</View>) : <EmptyLine>Is paper par aap aage ho. Badhiya!</EmptyLine>}
    </View>
    {c.split?.length > 0 ? <View testID="a2-compare-split" style={{ gap: 8 }}>
      {c.split.map((s: any) => <StatRow key={s.name} title={s.name} sub={s.volume > s.quality ? "Zyada sawaal attempt karo" : s.quality > 0 ? "Accuracy badhao" : "Aap aage ho"}>
        <View style={styles.duos}>
          <View style={styles.duo}><T size={10} w="heavy" color={colors.custom_eyebrow} style={styles.caps}>VOLUME SE</T><T w="mono" size={14}>{s.volume}</T></View>
          <View style={styles.duo}><T size={10} w="heavy" color={colors.custom_eyebrow} style={styles.caps}>QUALITY SE</T><T w="mono" size={14}>{s.quality}</T></View>
        </View>
      </StatRow>)}
    </View> : null}
  </Block>;
}

/** You against a student or a group. Totals and averages only: the other student's answers never reach the phone. */
export function CompareBody({ an, part }: { an: An; part: string }) {
  const c = an.compare;
  if (!c) return null;
  if (!c.available) return <Locked id="compare" testID="a2-compare-off" icon="account-group-outline" title="Compare abhi nahi khula" text={c.reason} />;
  const you = an.you, them = c.profile, mine = an.overview || {}, show = (k: string) => HAS[k].includes(part);
  const theirs: Record<string, any> = Object.fromEntries(them.subjects.map((s: any) => [s.name, s]));
  const duo = [{ name: "Aap", tone: "brand" as const }, { name: c.label as string, tone: "warn" as const }];
  return <View testID="a2-compare" style={{ gap: space.md }}>
    {show("head") ? <Block id="compare-head" kicker="COMPARATIVE" title={`Aap vs ${c.label}`} note="Sirf totals aur averages. Kisi doosre student ke jawab kabhi nahi dikhte.">
      <Key label={c.label} />
      <Tiles>
        <Tile id="compare-you" label="Aapka Score" value={you.score} sub={mine.rank ? `Rank #${mine.rank} · Percentile ${mine.percentile}` : `Accuracy ${pc(you.accuracy)}`} tone="brand" />
        <Tile id="compare-them" label={c.label} value={them.score} sub={c.rank ? `Rank #${c.rank} · Percentile ${c.percentile}` : `Accuracy ${pc(them.accuracy)}`} tone="warn" />
        <Tile id="compare-gap" label="Gap" value={Math.abs(c.gap)} sub={c.gap > 0 ? "marks peeche ho" : c.gap < 0 ? "marks aage ho" : "barabar"} tone={c.gap > 0 ? "bad" : "good"} />
        <Tile id="compare-time" label="Time" value={mmss(you.time)} sub={`${c.label}: ${mmss(them.time)}`} />
      </Tiles>
    </Block> : null}
    {show("gap") ? <Gap c={c} an={an} /> : null}
    {show("subjects") ? <Block id="compare-subjects" kicker="SUBJECT-WISE" title="Subject-wise: aap vs woh" action={<Key label={c.label} />}>
      <Bars testID="a2-compare-subject-chart" height={210} data={c.by_subject.map((s: any) => ({ label: shortSubject(s.name), values: [s.you, s.them] }))} series={duo} />
      <View testID="a2-compare-subject-table" style={{ gap: 8 }}>
        {you.subjects.filter((s: any) => theirs[s.name]).map((s: any) => {
          const o = theirs[s.name];
          return <StatRow key={s.name} title={s.name}>
            <View style={styles.duos}>
              <Duo label="Score" you={s.score} them={o.score} />
              <Duo label="Attempted" you={s.attempted} them={o.attempted} />
              <Duo label="Accuracy" you={pc(s.accuracy)} them={pc(o.accuracy)} />
              <Duo label="Time" you={mmss(s.time)} them={mmss(o.time)} />
            </View>
          </StatRow>;
        })}
      </View>
    </Block> : null}
    {show("quality") ? <Block id="compare-quality" kicker="ATTEMPT QUALITY" title="Attempt Quality: aap vs woh">
      {you.tags && them.tags ? <Grid testID="a2-compare-quality-table" first={1.7} head={["Tag", "Aap", c.label]} rows={QUALITY.map(([name, get]) => ({ key: name, cells: [name, get(you.tags), r1(get(them.tags))] }))} />
        : <EmptyLine testID="a2-compare-quality-off">Dono taraf time record hone par hi Attempt Quality compare hoti hai.</EmptyLine>}
    </Block> : null}
    {show("pace") ? <Block id="compare-pace" kicker="PACE" title="Pace: aap vs woh" note="Paper ka kitna % time beeta, aur tab tak kitne jawab ho chuke the.">
      {you.pace && them.pace ? <Lines testID="a2-compare-pace-chart" xLabel={i => i * 5 + "%"} series={[{ ...duo[0], values: you.pace }, { ...duo[1], values: them.pace, dash: true }]} />
        : <EmptyLine>Is paper par Pace curve uplabdh nahi hai.</EmptyLine>}
    </Block> : null}
    {show("difficulty") ? <Block id="compare-difficulty" kicker="DIFFICULTY" title="Difficulty par Accuracy: aap vs woh">
      <Grid testID="a2-compare-difficulty-table" first={1.4} head={["Level", "Aap", c.label]} rows={c.by_difficulty.map((d: any) => ({ key: d.level, cells: [an.copy.levels[d.level], pc(d.you), pc(d.them)] }))} />
    </Block> : null}
  </View>;
}

const styles = StyleSheet.create({
  picker: { gap: 10, padding: space.md, borderRadius: 18, borderWidth: 1, borderStyle: "dashed", borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_card },
  person: { minHeight: 52, flexDirection: "row", alignItems: "center", gap: space.md, borderBottomWidth: 1, borderBottomColor: colors.custom_barLine },
  rank: { minWidth: 40 },
  duos: { flexDirection: "row", flexWrap: "wrap", rowGap: 10 },
  duo: { width: "50%", gap: 2, paddingRight: 8 },
  caps: { letterSpacing: 1 },
  key: { flexDirection: "row", flexWrap: "wrap", gap: 12, alignItems: "center" },
  keyItem: { flexDirection: "row", alignItems: "center", gap: 6 },
  keyDot: { width: 10, height: 10, borderRadius: 3 },
  bullet: { flexDirection: "row", alignItems: "flex-start", gap: 8 },
  dot: { width: 6, height: 6, borderRadius: 3, marginTop: 7, backgroundColor: colors.brandPrimary },
});
