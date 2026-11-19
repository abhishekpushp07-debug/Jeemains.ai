import React, { useState } from "react";
import { StyleSheet, View } from "react-native";
import { T } from "@/src/components/ui";
import { colors } from "@/src/theme";
import { shortSubject } from "@/src/components/player/PlayerParts";
import { An, Open, SectionProps, Tone, index, mmss, pc } from "./format";
import { Block, EmptyLine, Foot, Key, Later, Meter, Pills, QRow, StatRow, Tile, Tiles } from "./parts";
import { Bars, Lines, Split } from "./charts";

const METRIC: Record<string, [string, Tone, string]> = { time: ["Time (min)", "brand", "m"], questions: ["Attempted", "info", ""], accuracy: ["Accuracy %", "good", "%"] };
const PART: [string, string, Tone][] = [["correct", "Sahi par", "good"], ["incorrect", "Galat par", "bad"], ["unanswered", "Bina jawab", "mute"]];

function Where({ t }: { t: any }) {
  const o = t.by_outcome, total = Math.max(1, o.correct + o.incorrect + o.unanswered);
  return <Block id="time" kicker="TIME ON SCREEN" title="Time kahan gaya" note={t.off_screen != null ? "Paper ka time = sawaalon par screen time + screen se bahar (app background, phone lock)." : undefined}>
    <Tiles>
      <Tile id="time-elapsed" label="Paper mein laga" value={mmss(t.elapsed)} tone="brand" />
      <Tile id="time-screen" label="Sawaalon par" value={mmss(t.on_screen)} />
      <Tile id="time-off" label="Screen se bahar" value={mmss(t.off_screen)} tone="mute" />
      <Tile id="time-correct" label="Sahi par" value={mmss(o.correct)} tone="good" />
      <Tile id="time-wrong" label="Galat par" value={mmss(o.incorrect)} tone="bad" />
      <Tile id="time-unanswered" label="Bina jawab" value={mmss(o.unanswered)} tone="mute" />
    </Tiles>
    <Split testID="a2-time-quality-bar" label="Time sahi, galat aur bina jawab wale sawaalon par" parts={PART.map(([k, , tone]) => [k, o[k], tone])} />
    <Key items={PART.map(([k, name, tone]) => [`${name}: ${mmss(o[k])} (${Math.round((100 * o[k]) / total)}%)`, tone])} />
    {o.incorrect + o.unanswered > o.correct ? <Foot tone="warn">Aadhe se zyada time aise sawaalon par gaya jinke marks nahi bane. Score Potential mein dekho yeh time kahan lagta.</Foot> : null}
  </Block>;
}

function Subjects({ t }: { t: any }) {
  const [metric, setMetric] = useState("time");
  const share: Record<string, any> = Object.fromEntries((t.share || []).map((s: any) => [s.name, s]));
  const value = (s: any) => (metric === "time" ? Math.round((s.time || 0) / 6) / 10 : metric === "questions" ? s.attempted : s.accuracy ?? 0);
  return <Block id="time-subjects" kicker="SUBJECT-WISE" title="Kis subject ko kitna time">
    <Pills id="time-metric" value={metric} onChange={setMetric} items={[["time", "Time"], ["questions", "Questions"], ["accuracy", "Accuracy"]]} />
    <Bars testID="a2-time-subject-chart" height={190} unit={METRIC[metric][2]} data={t.by_subject.map((s: any) => ({ label: shortSubject(s.name), values: [value(s)] }))} series={[{ name: METRIC[metric][0], tone: METRIC[metric][1] }]} />
    <View testID="a2-time-table" style={styles.list}>
      {t.by_subject.map((s: any) => {
        const x = share[s.name];
        return <StatRow key={s.name} title={s.name} right={mmss(s.time)} sub={`Attempted ${s.attempted} / ${s.count} · Accuracy ${pc(s.accuracy)}`}>
          {x ? <View style={{ gap: 5 }}>
            <View style={styles.twin}><T size={11} color={colors.muted} style={styles.twinLabel}>Time</T><Meter value={x.time_pct} tone="brand" label="Time ka hissa" /><T size={11.5} w="heavy" style={styles.twinValue}>{pc(x.time_pct)}</T></View>
            <View style={styles.twin}><T size={11} color={colors.muted} style={styles.twinLabel}>Marks</T><Meter value={x.weight_pct} tone="info" label="Marks ka hissa" /><T size={11.5} w="heavy" style={styles.twinValue}>{pc(x.weight_pct)}</T></View>
          </View> : null}
        </StatRow>;
      })}
    </View>
    <Key items={[["Time ka hissa", "brand"], ["Paper mein marks ka hissa", "info"]]} />
  </Block>;
}

function Blocks({ an }: { an: An }) {
  const data = an.time.blocks.map((b: any) => ({ label: `${Math.round(b.from / 60)}–${Math.round(b.to / 60)}m`, values: [b.correct, b.incorrect] }));
  return <Block id="time-journey" kicker="TIME JOURNEY" title="Paper ke har hisse mein kya hua" note={`Har ${Math.round(an.paper.block / 60)} min mein kitne jawab diye, kitne sahi aur kitne galat.`}>
    <Bars testID="a2-time-blocks-chart" stacked data={data} series={[{ name: "Sahi", tone: "good" }, { name: "Galat", tone: "bad" }]} />
  </Block>;
}

function Pace({ an }: { an: An }) {
  const t = an.time, step = an.paper.duration / Math.max(1, t.pace.length - 1), split = t.pace_split;
  return <Block id="pace" kicker="PACE CURVE" title="Jawab kitni tezi se aaye" note="Time ke saath kul kitne jawab ho chuke the. Seedhi line = barabar speed, sapaat hissa = atke hue.">
    <Lines testID="a2-pace-chart" xLabel={i => Math.round((i * step) / 60) + "m"} series={[
      { name: "Sab jawab", tone: "brand", values: t.pace },
      ...(split ? [{ name: "Sahi", tone: "good" as Tone, values: split.correct }, { name: "Galat", tone: "bad" as Tone, values: split.incorrect, dash: true }] : []),
    ]} />
  </Block>;
}

function Looks({ t, last }: { t: any; last: any }) {
  const f = t.first_look;
  return <>
    {f ? <Block id="first-look" kicker="PEHLI NAZAR VS WAPAS AAKAR" title="Kab ke jawab zyada sahi" note="Jawab pehli baar khulte hi diya, ya baad mein wapas aakar.">
      <Tiles>
        <Tile id="look-first" label="Pehli nazar mein" value={pc(f.first.accuracy)} sub={`${f.first.correct} / ${f.first.count} sahi · ${mmss(f.first.time)}`} tone="info" />
        <Tile id="look-return" label="Wapas aakar" value={pc(f.return.accuracy)} sub={`${f.return.correct} / ${f.return.count} sahi · ${mmss(f.return.time)}`} tone="warn" />
      </Tiles>
    </Block> : null}
    <Block id="last-stretch" kicker="AAKHRI 20% TIME" title="Thakaan ka asar">
      {last ? <Tiles>
        <Tile id="last-early" label="Usse pehle" value={pc(last.early.accuracy)} sub={`${last.early.count} jawab`} tone="info" />
        <Tile id="last-late" label="Aakhri 20% mein" value={pc(last.late.accuracy)} sub={`${last.late.count} jawab`} tone={(last.late.accuracy ?? 0) + 10 < (last.early.accuracy ?? 0) ? "bad" : "good"} />
      </Tiles> : <EmptyLine testID="a2-last-stretch-empty">Dono hisson mein kam se kam 5 jawab hone par yeh compare banta hai.</EmptyLine>}
    </Block>
  </>;
}

function Slowest({ an, onOpen }: { an: An; onOpen: Open }) {
  const byId = index(an);
  return <Block id="slowest" kicker="SABSE ZYADA TIME" title="Sabse dheeme 5 sawaal" note="Tap karo, solution khulega.">
    <View style={styles.list}>{an.time.slowest.map((i: string) => byId[i]).filter(Boolean).map((q: any) => <QRow key={q.id} testID={"a2-slowest-q-" + q.number} q={q} an={an} onPress={() => onOpen(q.id)} />)}</View>
  </Block>;
}

export function TimeSection({ an, onOpen }: SectionProps) {
  const t = an.time;
  if (!t.available) return <Later id="time" />;
  return <>
    <Where t={t} />
    <Subjects t={t} />
    <Blocks an={an} />
    {t.pace?.length > 1 ? <Pace an={an} /> : null}
    <Looks t={t} last={an.habits?.last} />
    <Slowest an={an} onOpen={onOpen} />
  </>;
}

const styles = StyleSheet.create({
  list: { gap: 8 },
  twin: { flexDirection: "row", alignItems: "center", gap: 8 },
  twinLabel: { width: 38 }, twinValue: { width: 46, textAlign: "right" },
});
