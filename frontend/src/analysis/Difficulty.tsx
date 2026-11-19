import React, { useState } from "react";
import { StyleSheet, View } from "react-native";
import { Icon, Press, T } from "@/src/components/ui";
import { colors, space } from "@/src/theme";
import { An, Drill, LEVEL_TONE, SectionProps, TONE, Tone, index, pc, pick } from "./format";
import { Block, Callout, Foot, LinkButton, Meter, Pills, QChips } from "./parts";
import { Bars } from "./charts";

const LEVELS = ["easy", "moderate", "tough", "unrated"];
const COLS: [string, string, Tone][] = [["correct", "Sahi", "good"], ["incorrect", "Galat", "bad"], ["skipped", "Chhode", "mute"]];

function Table({ an, name, levels, onDrill }: { an: An; name: string; levels: any; onDrill: Drill }) {
  const L = an.copy.levels, shown = LEVELS.filter(l => levels[l]?.count);
  const ids = (l: string, o: string) => pick(an, q => q.difficulty === l && q.outcome === o && (name === "all" || q.subject === name));
  return <>
    <View testID="a2-difficulty-table" style={{ gap: 8 }}>
      {shown.map(l => {
        const x = levels[l], tried = x.correct + x.incorrect, acc = tried ? Math.round((1000 * x.correct) / tried) / 10 : null;
        return <View key={l} style={styles.level}>
          <View style={styles.levelHead}>
            <View style={[styles.dot, { backgroundColor: TONE[LEVEL_TONE[l]].fill }]} />
            <T w="heavy" size={14} style={{ flex: 1 }}>{L[l]} <T size={12} color={colors.muted}>({x.count} sawaal)</T></T>
            <T w="heavy" size={13}>Accuracy {pc(acc)}</T>
          </View>
          <View style={styles.meter}><Meter value={acc || 0} tone={LEVEL_TONE[l]} /></View>
          <View style={styles.cells}>
            {COLS.map(([k, label, tone]) => {
              const list = ids(l, k), t = TONE[tone];
              return <Press key={k} testID={`a2-difficulty-${l}-${k}`} disabled={!list.length} onPress={() => onDrill(`${L[l]} · ${label}`, list)} accessibilityLabel={`${L[l]} ${label}: ${x[k]} / ${x.count}. Sawaal dekho`}
                style={[styles.cell, { backgroundColor: t.soft, borderColor: t.line }]}>
                <T w="heavy" size={14} color={tone === "mute" ? colors.onSurface : t.ink}>{x[k]} <T size={11} color={colors.muted}>/ {x.count}</T></T>
                <T size={11} w="bold" color={colors.custom_softText}>{label}</T>
              </Press>;
            })}
          </View>
        </View>;
      })}
    </View>
    <Bars testID="a2-difficulty-chart" height={200} data={shown.map(l => ({ label: L[l], values: [levels[l].correct, levels[l].incorrect, levels[l].skipped] }))}
      series={[{ name: "Sahi", tone: "good" }, { name: "Galat", tone: "bad" }, { name: "Chhode", tone: "mute" }]} />
  </>;
}

function Leak({ leak, onDrill }: { leak: any; onDrill: Drill }) {
  const lost = leak.wrong.length + leak.skipped.length;
  return <Callout testID="a2-leak" icon="water-outline" tone={lost ? "warn" : "good"} title="Leak: Easy sawaal">
    <T size={13} color={colors.custom_softText}>{lost ? `${leak.wrong.length} Easy galat aur ${leak.skipped.length} Easy chhoote. Yahan se ${leak.marks} marks bach sakte the. Easy marks sabse sasta Rank hai.` : "Easy sawaalon mein koi leak nahi mila. Shaandaar!"}</T>
    {lost > 0 ? <LinkButton testID="a2-leak-questions" label={`${lost} sawaal dekho`} icon="arrow-right" onPress={() => onDrill("Leak: Easy sawaal", [...leak.wrong, ...leak.skipped])} /> : null}
  </Callout>;
}

export function Difficulty({ an, onDrill, onOpen }: SectionProps) {
  const d = an.difficulty, byId = index(an);
  const [name, setName] = useState("all");
  const levels = name === "all" ? d.all : d.by_subject.find((s: any) => s.name === name)?.levels || d.all;
  const tough: string[] = name === "all" ? d.tough_solved : d.tough_solved.filter((i: string) => byId[i]?.subject === name);
  const from: Record<string, string> = an.copy.level_sources || {};
  const sources = Object.entries(d.sources || {}).map(([k, n]) => `${n} sawaal ${from[k] || k}`).join(", ");
  return <>
    <Pills id="difficulty-subject" value={name} onChange={setName} items={[["all", "Sab subjects"], ...d.by_subject.map((s: any) => [s.name, s.name] as [string, string])]} />
    <Leak leak={d.leak} onDrill={onDrill} />
    <Block id="difficulty" kicker="EASY · MODERATE · TOUGH" title="Difficulty ke hisaab se" note={`Level kahan se aaya: ${sources}. Jahan data kam hai wahan Not rated likha hai, andaaza nahi lagaya.`}>
      <Table an={an} name={name} levels={levels} onDrill={onDrill} />
      {d.unlock ? <Foot testID="a2-difficulty-unlock">{d.unlock.unrated} sawaal abhi Not rated hain. Jaise-jaise aur students yeh paper denge, unka level students ke result se pakka hota jaayega.</Foot> : null}
    </Block>
    {tough.length > 0 ? <Block id="tough-solved" kicker="AAPKI TAAQAT" title="Tough sawaal jo aapne nikale" note="Yeh woh sawaal hain jo zyadatar students se nahi bane. Inka tareeka yaad rakho.">
      <View style={styles.tough}><Icon name="trophy-outline" size={22} color={colors.custom_gold} /><View style={{ flex: 1 }}><QChips id="tough" ids={tough} an={an} onOpen={onOpen} /></View></View>
    </Block> : null}
  </>;
}

const styles = StyleSheet.create({
  level: { gap: 8, padding: space.md, borderRadius: 16, borderWidth: 1, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_bar },
  levelHead: { flexDirection: "row", alignItems: "center", gap: 8 },
  dot: { width: 9, height: 9, borderRadius: 5 },
  meter: { flexDirection: "row" },
  cells: { flexDirection: "row", gap: 6 },
  cell: { flex: 1, minHeight: 52, borderRadius: 12, borderWidth: 1, alignItems: "center", justifyContent: "center", paddingVertical: 6 },
  tough: { flexDirection: "row", alignItems: "flex-start", gap: space.md },
});
