import React from "react";
import { StyleSheet, View } from "react-native";
import { Icon, IconName, T } from "@/src/components/ui";
import { colors, space } from "@/src/theme";
import { An, Drill, Open, SectionProps, TONE, r1 } from "./format";
import { B, Block, Callout, EmptyLine, LinkButton, QChips, Tile, Tiles } from "./parts";
import { Waterfall } from "./charts";

const STEP: Record<string, [string, IconName, string]> = {
  careless: ["Careless galti theek", "lightning-bolt", "Jo sawaal Par time ke aadhe se kam mein galat hue. Aaram se padhte to sahi + negative wapas."],
  guard: ["Mushkil par risk nahi", "shield-alert-outline", "Jo Tough sawaal class mein bhi 25% se kam bane aur aapse galat hue. Chhod dete to negative bachta."],
  reinvest: ["Atka time wapas", "timer-outline", "Jahan time laga par marks nahi bane, woh time chhode hue Easy sawaalon ko dete. Aapki apni accuracy se hisaab."],
};
const AT: Record<string, string> = { current: "Abhi", realistic: "Realistic target", maximum: "Maximum potential" };

function Steps({ an, p, onDrill, onOpen }: { an: An; p: any; onDrill: Drill; onOpen: Open }) {
  return <Block id="potential-steps" kicker="HAR STEP KE PEECHE KE SAWAAL" title="Kahan se kitne marks">
    {p.steps.filter((s: any) => STEP[s.key]).map((s: any) => {
      const [name, icon, about] = STEP[s.key];
      return <View key={s.key} testID={"a2-potential-step-" + s.key} style={styles.step}>
        <View style={styles.stepHead}>
          <Icon name={icon} size={19} color={TONE.warn.ink} />
          <T w="heavy" size={14.5} style={{ flex: 1 }}>{name}</T>
          <T w="mono" size={18} color={TONE.good.ink}>+{s.marks}</T>
        </View>
        <T size={12.5} color={colors.muted}>{about}{s.key === "reinvest" && s.minutes ? ` Atka time: ${s.minutes} min.` : ""}</T>
        {s.questions.length > 0 ? <>
          <QChips id={"potential-" + s.key} ids={s.questions} an={an} onOpen={onOpen} max={18} />
          <LinkButton testID={"a2-potential-questions-" + s.key} label={`${s.questions.length} sawaal ki list`} icon="arrow-right" onPress={() => onDrill(name, s.questions)} />
        </> : <EmptyLine>Is step mein koi sawaal nahi. Badhiya!</EmptyLine>}
      </View>;
    })}
  </Block>;
}

export function Potential({ an, onDrill, onOpen }: SectionProps) {
  const p = an.potential, ranked: any[] = p.at.filter((x: any) => x.rank), g = p.guess;
  return <>
    <Block id="potential" kicker="SEEDHA HISAAB · KOI ANDAAZA NAHI" title="Yahan se marks bach sakte the" note="Realistic target = Careless + Risk poora, aur atke time ka aadha. Maximum = teeno poore.">
      {!p.available ? <EmptyLine testID="a2-potential-partial">Is attempt mein time record nahi hua, isliye Careless aur Time wale step 0 hain. Agle mock se poore dikhenge.</EmptyLine> : null}
      <Tiles>
        <Tile id="potential-current" label="Abhi ka score" value={p.current} sub={`${p.paper_maximum} mein se`} />
        <Tile id="potential-realistic" label="Realistic target" value={p.realistic} sub={`+${r1(p.realistic - p.current)} marks, sirf aadatein badal kar`} tone="good" />
        <Tile id="potential-maximum" label="Maximum potential" value={p.maximum} sub={`+${r1(p.maximum - p.current)} marks`} tone="good" />
      </Tiles>
      <T size={12} color={colors.muted}>Realistic target sirf aadatein badal kar mil sakta hai, bina naya padhe.</T>
      <Waterfall p={p} />
    </Block>
    <Steps an={an} p={p} onDrill={onDrill} onOpen={onOpen} />
    {ranked.length > 0 ? <Block id="potential-rank" kicker="ISI PAPER KE STUDENTS SE" title="Itne marks par Rank lagbhag">
      <View style={{ gap: 8 }}>
        {ranked.map(x => <View key={x.key} testID={"a2-tile-at-" + x.key} style={styles.at}>
          <View style={{ flex: 1 }}>
            <T w="heavy" size={13.5}>{AT[x.key]}</T>
            <T size={12} color={colors.muted}>{x.score} marks · {x.of} mein · Percentile {x.percentile}</T>
          </View>
          <T testID={`a2-tile-at-${x.key}-value`} w="mono" size={22} color={x.key === "current" ? colors.onSurface : TONE.good.ink}>#{x.rank}</T>
        </View>)}
      </View>
    </Block> : null}
    <Callout testID="a2-guess" icon="dice-5-outline" tone="info" title="Guess ka niyam">
      <T size={13} color={colors.custom_softText}>Is paper mein sahi par <B>+{g.pos}</B> aur galat par <B>{g.neg}</B>. Jawab tabhi do jab <B>{g.break_even}% se zyada</B> yakeen ho.</T>
      <T size={13} color={colors.custom_softText}>4 option mein se ek bhi pakka hata sako to guess faydemand hai. Bilkul andhere mein chhodna behtar hai.</T>
      <T size={12.5} color={colors.muted}>Bina kisi galat jawab ke (sirf chhod kar) aapka Score <B>{p.no_negative}</B> hota.</T>
    </Callout>
  </>;
}

const styles = StyleSheet.create({
  step: { gap: 10, padding: space.md, borderRadius: 16, borderWidth: 1, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_bar },
  stepHead: { flexDirection: "row", alignItems: "center", gap: 8 },
  at: { flexDirection: "row", alignItems: "center", gap: space.md, padding: space.md, borderRadius: 16, borderWidth: 1, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_bar },
});
