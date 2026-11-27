// "Meri details" at the top of the Rank tab: marks, percentile, rank and category, typed once (all optional).
// Closed it is one baby pink bar ("Add details" + Click, or the saved line + Edit) with a row of lights running round it;
// open it is a small form per exam. Save fills every Rank tool with these values.
import React, { useEffect, useState } from "react";
import { StyleSheet, View } from "react-native";
import { Press, T } from "@/src/components/ui";
import { Glyph } from "@/src/components/Glyph";
import { Shine } from "@/src/analysis/Shine";
import { pinkShine } from "@/src/components/series/looks";
import { dotEdges, rankColors as colors, radius, space } from "@/src/theme";
import { Category, CutoffExam, fmt, Level, ScoreKind } from "./api";
import { CATEGORY_LABEL, LEVEL } from "./tones";
import { NumberField, Picker, RemoveButton, Strip, Switch, Toggle } from "./controls";
import { FormButton } from "./accent";
import { clearProfile, RankProfile, readScore, saveProfile, SCORE, useRankProfile } from "./profile";
import { syncProfile } from "./profileSync";

const LEVELS: Level[] = ["tough", "normal", "easy"];
const CATS: Category[] = ["GEN", "EWS", "OBC-NCL", "SC", "ST"];

/** The closed bar's line, e.g. "JEE Main: 180 marks, 97.4 percentile · OBC-NCL · Bihar  |  BITSAT: 280". */
function profileLine(p: RankProfile) {
  const j = p.jee;
  const jee = [[j.marks && `${j.marks} marks`, j.pct && `${j.pct} percentile`, j.rank && `rank ${fmt(Number(j.rank))}`].filter(Boolean).join(", ") || null,
    CATEGORY_LABEL[j.category], j.female ? "Female" : null, j.pwd ? "PwD" : null, j.state].filter(Boolean).join(" · ");
  const comedk = [p.comedk.marks && `${p.comedk.marks} marks`, p.comedk.rank && `rank ${fmt(Number(p.comedk.rank))}`].filter(Boolean).join(", ");
  return [`JEE Main: ${jee}`, comedk ? `COMEDK: ${comedk}` : null, p.bitsat.score ? `BITSAT: ${p.bitsat.score}` : null].filter(Boolean).join("  |  ");
}

/** The first wrong number, with the exam whose page shows it. */
function problemOf(p: RankProfile): { exam: CutoffExam; text: string } | null {
  const boxes: [CutoffExam, ScoreKind, string][] = [["jee", "marks", p.jee.marks], ["jee", "percentile", p.jee.pct], ["jee", "rank", p.jee.rank],
    ["comedk", "marks", p.comedk.marks], ["comedk", "rank", p.comedk.rank], ["bitsat", "marks", p.bitsat.score]];
  for (const [exam, kind, text] of boxes) {
    const v = readScore(exam, kind, text);
    if (typeof v === "string") return { exam, text: v };
  }
  return null;
}

export function ProfileBar({ states }: { states: string[] }) {
  const profile = useRankProfile();
  const [open, setOpen] = useState(false);
  const [saved, setSaved] = useState(false);
  useEffect(() => { void syncProfile(); }, []); // signed in: the account's copy on jeelive.ai (./profileSync.ts)
  if (open) return <ProfileForm start={profile} states={states} onClose={done => { setOpen(false); setSaved(done); }} />;
  const filled = profile.at > 0;
  return <Press testID="rank-profile" onPress={() => { setSaved(false); setOpen(true); }} scaleTo={0.99} style={styles.press} accessibilityRole="button"
    accessibilityLabel={filled ? `Meri details: ${profileLine(profile)}. Edit karo` : "Add details"}>
    {/* The series streak card's baby pink (gloss, a glint from corner to corner); its edge is a row of lights on the black page. */}
    <Shine {...pinkShine} radius={20} ring={6} band={64} edge={dotEdges.details} dots={colors.custom_rankBg} face={styles.bar}>
      <View style={styles.icon}><Glyph name="account-outline" size={17} color={colors.custom_tabInk} stroke={1.5} /></View>
      <View style={{ flex: 1, minWidth: 0, gap: 2 }}>
        <T testID="rank-profile-title" w="bold" size={14} color={colors.custom_tabInk}>{filled ? "Meri details" : "Add details"}</T>
        <T testID="rank-profile-summary" size={12} color={colors.custom_seriesPinkInk} numberOfLines={3}>
          {filled ? profileLine(profile) : "Marks, percentile, rank aur category. Har tool mein pehle se bhare milenge."}
        </T>
        {saved ? <T testID="rank-profile-saved" w="semibold" size={11.5} color={colors.custom_tabInk}>Save ho gaya. Har tool mein bhar diya; kisi bhi tool mein alag se badal sakte ho.</T> : null}
      </View>
      <View testID="rank-profile-edit" style={styles.edit}>
        <Glyph name={filled ? "pencil" : "plus"} size={14} color={colors.onBrandPrimary} stroke={2} />
        <T w="heavy" size={13} color={colors.onBrandPrimary}>{filled ? "Edit" : "Click"}</T>
      </View>
    </Shine>
  </Press>;
}

function ProfileForm({ start, states, onClose }: { start: RankProfile; states: string[]; onClose: (saved: boolean) => void }) {
  const [p, setP] = useState(start);
  const [exam, setExam] = useState<CutoffExam>("jee");
  const [picker, setPicker] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const jee = (x: Partial<RankProfile["jee"]>) => { setP(v => ({ ...v, jee: { ...v.jee, ...x } })); setProblem(null); };
  const comedk = (x: Partial<RankProfile["comedk"]>) => { setP(v => ({ ...v, comedk: { ...v.comedk, ...x } })); setProblem(null); };
  const save = async () => {
    const bad = problemOf(p);
    if (bad) { setExam(bad.exam); setProblem(bad.text); return; }
    setBusy(true);
    await saveProfile(p);
    void syncProfile(true);
    onClose(true);
  };
  const box = (testID: string, e: CutoffExam, kind: ScoreKind, value: string, onChange: (v: string) => void) => {
    const r = SCORE[e][kind]!;
    return <NumberField testID={testID} label={r.label} placeholder={r.hint} value={value} onChange={onChange} max={r.len} decimal={r.decimal} signed={r.signed} />;
  };
  const scores = [p.jee.marks, p.jee.pct, p.jee.rank].filter(Boolean).length;
  return <Strip title="Meri details" testID="rank-profile-form" right={<RemoveButton testID="rpf-close" label="Meri details band karo" onPress={() => onClose(false)} />}>
    <T size={12.5} color={colors.custom_softText}>Ek baar bharo, sab optional hai. Save karte hi ye har tool mein pehle se bhara milega; kisi bhi tool mein alag se badal sakte ho.</T>
    <Switch prefix="rpf-exam" value={exam} onChange={e => { setExam(e); setProblem(null); }}
      items={[{ key: "jee", label: "JEE Main" }, { key: "bitsat", label: "BITSAT" }, { key: "comedk", label: "COMEDK" }]} />
    {exam === "jee" ? <>
      <View style={styles.wrap}>
        {box("rpf-jee-marks", "jee", "marks", p.jee.marks, v => jee({ marks: v }))}
        {box("rpf-jee-percentile", "jee", "percentile", p.jee.pct, v => jee({ pct: v }))}
        {box("rpf-jee-rank", "jee", "rank", p.jee.rank, v => jee({ rank: v }))}
      </View>
      <T testID="rpf-jee-note" size={11.5} color={colors.custom_dim}>
        {scores > 1 ? "Ek se zyada bhare hain: sabse pakka number chalega. Pehle Rank, phir Percentile, phir Marks." : "Jo pata hai wahi bharo, koi ek kaafi hai."}
      </T>
      {p.jee.marks ? <View style={styles.row}>
        <T w="semibold" size={12} color={colors.muted} style={styles.rowLabel}>Paper</T>
        {LEVELS.map(l => <Toggle key={l} testID={`rpf-level-${l}`} label={LEVEL[l].label} on={p.jee.level === l} ink={LEVEL[l].ink} soft={LEVEL[l].soft} onPress={() => jee({ level: l })} />)}
      </View> : null}
      <View style={styles.wrap}>
        {CATS.map(c => <Toggle key={c} testID={`rpf-cat-${c}`} label={CATEGORY_LABEL[c]} on={p.jee.category === c} onPress={() => jee({ category: c })} />)}
      </View>
      <View style={styles.wrap}>
        <Toggle testID="rpf-female" label="Female" on={p.jee.female} onPress={() => jee({ female: !p.jee.female })} />
        <Toggle testID="rpf-pwd" label="PwD" on={p.jee.pwd} onPress={() => jee({ pwd: !p.jee.pwd })} />
        <Toggle testID="rpf-state" label={p.jee.state ?? "Home state"} on={!!p.jee.state} caret onPress={() => setPicker(true)} />
      </View>
    </> : exam === "comedk" ? <>
      <View style={styles.wrap}>
        {box("rpf-comedk-marks", "comedk", "marks", p.comedk.marks, v => comedk({ marks: v }))}
        {box("rpf-comedk-rank", "comedk", "rank", p.comedk.rank, v => comedk({ rank: v }))}
      </View>
      <T size={11.5} color={colors.custom_dim}>COMEDK mein sabki ek hi merit list hai, isliye category nahi lagti. Dono bhare ho to Rank chalegi.</T>
    </> : <>
      <View style={styles.wrap}>
        {box("rpf-bitsat-score", "bitsat", "marks", p.bitsat.score, v => { setP(x => ({ ...x, bitsat: { score: v } })); setProblem(null); })}
      </View>
      <T size={11.5} color={colors.custom_dim}>BITSAT mein sirf score chalta hai: percentile, rank aur category nahi lagte.</T>
    </>}
    {problem ? <T testID="rpf-error" w="semibold" size={13} color={colors.error}>{problem}</T> : null}
    <FormButton testID="rpf-save" label="Save karo" busy={busy} onPress={save} />
    {start.at ? <Press testID="rpf-clear" onPress={async () => { await clearProfile(); void syncProfile(true); onClose(false); }} style={styles.link} accessibilityRole="button">
      <T w="bold" size={13} color={colors.custom_softText}>Meri details hatao</T>
    </Press> : null}
    <Picker visible={picker} title="Home state" options={states} value={p.jee.state ? [p.jee.state] : []} allLabel="No home state"
      onChange={v => jee({ state: v[0] ?? null })} onClose={() => setPicker(false)} testID="rpf-state-picker" />
  </Strip>;
}

const styles = StyleSheet.create({
  press: { borderRadius: 20 },
  bar: { flexDirection: "row", alignItems: "center", gap: space.md, minHeight: 56, paddingVertical: space.sm, paddingHorizontal: 10 },
  icon: { width: 34, height: 34, borderRadius: 17, backgroundColor: colors.custom_tabChip, alignItems: "center", justifyContent: "center" },
  // Black on the pink, as the pink Rank card's Share button.
  edit: { flexDirection: "row", alignItems: "center", gap: 5, minHeight: 44, paddingHorizontal: 14, borderRadius: radius.pill, backgroundColor: colors.custom_tabInk },
  wrap: { flexDirection: "row", flexWrap: "wrap", gap: space.sm },
  row: { flexDirection: "row", alignItems: "center", gap: space.sm, flexWrap: "wrap" },
  rowLabel: { width: 44 },
  link: { minHeight: 44, alignItems: "center", justifyContent: "center" },
});
