import React, { useState } from "react";
import { StyleSheet, View } from "react-native";
import { Icon, Press, T } from "@/src/components/ui";
import { colors, space } from "@/src/theme";
import { An, Open, SectionProps, TAG, TONE, Tone, index, mmss } from "./format";
import { B, Block, ChipButton, Foot, Key, Later, QChips, Tile, Tiles } from "./parts";

const nth = (n: number) => (n === 2 ? "2nd" : n === 3 ? "3rd" : n + "th");
const CHANGE: [string, string, Tone][] = [["w2r", "Galat se sahi", "good"], ["r2w", "Sahi se galat", "bad"], ["w2w", "Galat se galat", "warn"], ["cleared", "Jawab hataya", "mute"]];

function Changes({ an, onOpen }: { an: An; onOpen: Open }) {
  const c = an.habits?.changes;
  if (!c?.total) return null;
  const g: Record<string, string[]> = { ...c.groups, cleared: [...(c.groups.r2s || []), ...(c.groups.w2s || [])] };
  return <Block id="changes" kicker="JAWAB BADALNA" title={`${c.total} baar jawab badla`}
    note={`Is badlav se net ${c.marks > 0 ? "+" : ""}${c.marks} marks. ${c.marks < 0 ? "Pehla jawab zyada sahi tha: bina pakke kaaran ke mat badlo." : c.marks > 0 ? "Dobara check karna kaam aaya." : ""}`}>
    <View testID="a2-answer-changes" style={{ gap: 8 }}>
      {CHANGE.map(([k, label, tone]) => (g[k]?.length ? <View key={k} style={[styles.change, { borderLeftColor: TONE[tone].fill }]}>
        <T size={13} w="bold" color={colors.custom_softText}>{label} <T w="heavy" size={13} color={tone === "mute" ? colors.onSurface : TONE[tone].ink}>{g[k].length}</T></T>
        <QChips id={"change-" + k} ids={g[k]} an={an} onOpen={onOpen} max={12} />
      </View> : null))}
    </View>
  </Block>;
}

function Chips({ an, onOpen }: { an: An; onOpen: Open }) {
  const j = an.journey, byId = index(an), groups: Record<number, any[]> = {};
  const [tags, setTags] = useState(true);
  j.visits.forEach((v: any) => { const i = Math.floor(v.a / j.block); (groups[i] = groups[i] || []).push(v); });
  return <Block id="journey-chips" kicker="AAPKA RAASTA" title="Har visit, time ke hisaab se" note="Ek chip = ek baar sawaal khola. Chhota number = kaun si baar. Teer ke baad = us visit mein diya jawab."
    action={<ChipButton testID="a2-journey-tags-toggle" on={tags} onPress={() => setTags(!tags)}><T size={12} w="bold">{tags ? "Tag chhupao" : "Tag dikhao"}</T></ChipButton>}>
    <Key items={[["Perfect", "good"], ["Galti", "bad"], ["Overtime / Confused", "warn"], ["Smart skip", "info"]]} />
    {Object.keys(groups).map(Number).sort((a, b) => a - b).map(i => <View key={i} testID={"a2-block-journey-" + i} style={{ gap: 8 }}>
      <T w="heavy" size={13}>{Math.round((i * j.block) / 60)}–{Math.round(((i + 1) * j.block) / 60)} min <T size={11.5} color={colors.muted}>{groups[i].length} visits</T></T>
      <View style={styles.journey}>
        {groups[i].map((v, k) => {
          const q = byId[v.q], tagged = tags && q?.tag && TAG[q.tag], tone: Tone = tagged ? TAG[q.tag][0] : "plain", t = TONE[tone];
          return <Press key={k} testID={`a2-visit-${i}-${k}`} onPress={() => onOpen(v.q)} haptic={false} scaleTo={0.95}
            accessibilityLabel={`Q${v.n}${v.v > 1 ? ", " + nth(v.v) + " baar" : ""}, ${mmss(v.d)}${q?.tag ? ", " + an.copy.tags[q.tag][0] : ""}. Solution kholo`}
            style={[styles.visit, { borderColor: tone === "plain" ? colors.custom_cardLineStrong : t.fill }]}>
            {tagged ? <Icon name={TAG[q.tag][1]} size={12} color={t.ink} /> : null}
            <T w="heavy" size={12.5}>Q{v.n}</T>
            {v.v > 1 ? <T w="heavy" size={9.5} color={tone === "plain" ? colors.custom_softText : t.ink}>{nth(v.v)}</T> : null}
            <T size={11} color={colors.muted}>{mmss(v.d)}</T>
            {v.mark ? <Icon name="flag" size={11} color={TONE.warn.fill} /> : null}
            {v.set ? <T w="heavy" size={11} color={TONE.info.ink}>→ {v.set}</T> : null}
          </Press>;
        })}
      </View>
    </View>)}
  </Block>;
}

export function Journey({ an, onOpen }: SectionProps) {
  const j = an.journey, h = an.habits || {};
  if (!j.available) return <><Later id="journey" /><Changes an={an} onOpen={onOpen} /></>;
  const s = j.summary, first = j.first_block;
  return <>
    <Block id="journey" kicker="QUESTION JOURNEY" title="Aap paper mein kaise chale">
      <T testID="a2-journey-summary" w="bold" size={14.5}>{s.total} mein se {s.visited} sawaal dekhe, {s.revisits} baar wapas gaye, {s.thrice} sawaal 3 ya zyada baar dekhe.</T>
      <Tiles>
        <Tile id="j-visited" label="Sawaal dekhe" value={`${s.visited} / ${s.total}`} tone="info" />
        <Tile id="j-revisits" label="Wapas gaye" value={s.revisits} />
        <Tile id="j-streak" label="Lagaataar sahi" value={h.streaks?.correct ?? "—"} sub="sabse lambi streak" tone="good" />
        <Tile id="j-wstreak" label="Lagaataar galat" value={h.streaks?.incorrect ?? "—"} sub="sabse lambi streak" tone="bad" />
      </Tiles>
      <Foot testID="a2-journey-order">Subject order: <B>{j.order.join(" → ") || "—"}</B>.{first ? ` Pehle ${first.minutes} min mein ${first.answered} jawab (${first.correct} sahi, ${first.incorrect} galat).` : ""}</Foot>
    </Block>
    <Changes an={an} onOpen={onOpen} />
    <Chips an={an} onOpen={onOpen} />
  </>;
}

const styles = StyleSheet.create({
  change: { gap: 8, padding: space.md, borderRadius: 14, borderWidth: 1, borderLeftWidth: 4, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_bar },
  journey: { flexDirection: "row", flexWrap: "wrap", gap: 7 },
  visit: { flexDirection: "row", alignItems: "center", gap: 5, minHeight: 44, paddingHorizontal: 10, borderRadius: 12, borderWidth: 1.5, backgroundColor: colors.custom_bar },
});
