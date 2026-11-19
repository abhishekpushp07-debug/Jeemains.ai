import React from "react";
import { StyleSheet, View } from "react-native";
import { T } from "@/src/components/ui";
import { colors } from "@/src/theme";
import { shortSubject } from "@/src/components/player/PlayerParts";
import { An, Drill, SectionProps, TONE, Tone, pick } from "./format";
import { Block, ChipButton, Fold, Grid, Key, Later, QChips, TagChip, Tile, Tiles } from "./parts";
import { Bars, SpeedMap } from "./charts";

const HEAD = ["perfect", "wasted", "overtime", "confused", "concept_gap"];
const HEAD_TONE: Record<string, Tone> = { perfect: "good", wasted: "bad", overtime: "warn", confused: "warn", concept_gap: "bad" };
const BARS: [string, Tone][] = [["Perfect", "good"], ["Careless", "bad"], ["Overtime", "warn"], ["Confused", "info"], ["Concept gap", "mute"]];
const ORDER = ["perfect", "slow_correct", "wasted", "concept_gap", "costly_overtime", "confused", "smart_skip", "not_seen"];
const OVER = ["slow_correct", "costly_overtime"];

function Headline({ an, onDrill }: { an: An; onDrill: Drill }) {
  const q = an.quality, t = an.copy.tags;
  const ids = (k: string) => pick(an, x => (k === "overtime" ? OVER.includes(x.tag) : x.tag === k));
  const name = (k: string) => (k === "overtime" ? "Overtime" : t[k][0]);
  const about = (k: string) => (k === "overtime" ? "Par time se kaafi zyada laga." : t[k][1]);
  const from = q.par_from || {};
  const rest = [...OVER, "smart_skip", "not_seen", "no_score"].filter(k => q.counts[k] > 0);
  return <Block id="quality" kicker="HAR SAWAAL KO EK HI TAG" title="Aapke attempts kaise rahe"
    note={`${an.copy.time_label} Par time: ${from.solvers ? from.solvers + " sawaal students ke data se, " : ""}${from.standard || 0} sawaal paper standard se.`}>
    <Tiles>{HEAD.map(k => <Tile key={k} id={"quality-" + k} label={name(k)} value={q.headline[k]} sub={about(k)} tone={HEAD_TONE[k]} ids={ids(k)} onDrill={onDrill} />)}</Tiles>
    {rest.length ? <View testID="a2-quality-rest" style={styles.wrap}>
      {rest.map(k => <ChipButton key={k} testID={"a2-quality-rest-" + k} label={`${t[k][0]}: ${q.counts[k]}. Sawaal dekho`} onPress={() => onDrill(t[k][0], ids(k))}>
        <TagChip tag={k} copy={an.copy} /><T w="heavy" size={13}>{q.counts[k]}</T>
      </ChipButton>)}
    </View> : null}
  </Block>;
}

function BySubject({ an }: { an: An }) {
  const rows: { name: string; values: number[] }[] = an.quality.by_subject.map((s: any) => ({
    name: s.name, values: [s.counts.perfect, s.counts.wasted, s.counts.slow_correct + s.counts.costly_overtime, s.counts.confused, s.counts.concept_gap],
  }));
  return <Block id="quality-subjects" kicker="SUBJECT × TAG" title="Kis subject mein kaisi galti">
    <Key items={BARS} />
    <Grid testID="a2-quality-table" first={2.2} head={["Subject", ...BARS.map(([name, tone]) => <View key={name} accessibilityLabel={name} style={[styles.swatch, { backgroundColor: TONE[tone].fill }]} />)]}
      rows={rows.map(r => ({ key: r.name, cells: [shortSubject(r.name), ...r.values] }))} />
    <Bars testID="a2-quality-chart" height={210} data={rows.map(r => ({ label: shortSubject(r.name), values: r.values }))} series={BARS.map(([name, tone]) => ({ name, tone }))} />
  </Block>;
}

export function Quality({ an, onDrill, onOpen }: SectionProps) {
  const q = an.quality, t = an.copy.tags;
  if (!q.available) return <Later id="quality" />;
  return <>
    <Headline an={an} onDrill={onDrill} />
    <Block id="speed-map" kicker="SPEED-ACCURACY MAP" title="Jaldbaazi ya der: galti kahan se aayi" note="Har dot ek sawaal hai. Baayein = jaldi, daayein = der. Beech ki line Par (ideal) time hai. Dot par tap karo, solution khulega.">
      <SpeedMap an={an} onOpen={onOpen} />
    </Block>
    {q.painful.length > 0 ? <Block id="painful" kicker="DOHRA NUKSAAN" title="Painful sawaal" note="Galat bhi hue aur Par time se zyada bhi khaaya. Inka concept sabse pehle dekho.">
      <QChips id="painful" ids={q.painful} an={an} onOpen={onOpen} />
    </Block> : null}
    {q.lucky.length > 0 ? <Block id="lucky" kicker="JALDI-SAHI" title="Kahin tukka to nahi tha?" note="Par ke 25% se bhi kam time mein sahi. Tukka tha to concept ek baar dekh lo.">
      <QChips id="lucky" ids={q.lucky} an={an} onOpen={onOpen} />
    </Block> : null}
    <BySubject an={an} />
    <Fold id="quality-defs" title="Tags ke matlab (rulebook)">
      {ORDER.map(k => <View key={k} style={styles.def}><TagChip tag={k} copy={an.copy} /><T size={12.5} color={colors.custom_softText}>{t[k][1]}</T></View>)}
    </Fold>
  </>;
}

const styles = StyleSheet.create({
  wrap: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  def: { gap: 4 },
  swatch: { width: 12, height: 12, borderRadius: 4 },
});
