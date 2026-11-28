// Cut off (Rank tab tile): pick ONE thing, a college or a branch, and read every round's 2026 cut-off.
// College -> all its branches. Branch -> its 100 most wanted college-branches. JEE Main, BITSAT and COMEDK.
// A score is optional: with it only the rows the student can reach stay, tagged Safe, Likely or Borderline.
// The server does all the working out (POST /api/rank/cutoff), so the app and the website always agree.
import React, { useEffect, useState } from "react";
import { ActivityIndicator, StyleSheet, View } from "react-native";
import { ErrorBox, T } from "@/src/components/ui";
import { rankColors as colors, space } from "@/src/theme";
import { storage } from "@/src/utils/storage";
import { Category, cutoff, CutoffBy, CutoffExam, CutoffIn, cutoffOptions, CutoffScore, Level, ScoreKind } from "./api";
import { CATEGORY_LABEL } from "./tones";
import { Picker, Strip, Switch, Toggle } from "./controls";
import { CollegeSearch } from "./CollegeSearch";
import { Chooser, useOnce, useTarget } from "./TargetMarks";
import { CutoffList } from "./CutoffList";
import { SAVED, useProfileSaves } from "./profile";
import { track } from "@/src/jlTracker";

const CATS: Category[] = ["GEN", "EWS", "OBC-NCL", "SC", "ST"];
/** One exam's choice. `text` is what is typed in the score box; `score` is the one the list is filtered by (null = show all). */
export type Pick = { by: CutoffBy; college: string | null; branch: string | null; kind: ScoreKind; text: string; score: CutoffScore | null };
type State = { exam: CutoffExam; level: Level; category: Category; female: boolean; pwd: boolean; state: string | null } & Record<CutoffExam, Pick>;
const PICK: Pick = { by: "college", college: null, branch: null, kind: "marks", text: "", score: null };
const DEFAULT: State = { exam: "jee", level: "normal", category: "GEN", female: false, pwd: false, state: null, jee: PICK, comedk: PICK, bitsat: PICK };

type Words = { tab: string; pick: string; hint: string; none: string };
const COLLEGE: Words = { tab: "College se", pick: "College chuno", hint: "College ka naam ya shehar likho", none: "Koi college nahi mila. Naam thoda chhota likh kar dekho." };
const BRANCH: Words = { tab: "Branch se", pick: "Branch chuno", hint: "Branch likho, jaise CSE ya Mechanical", none: "Koi branch nahi mili. Naam thoda chhota likh kar dekho." };
const WORDS: Record<CutoffExam, Record<CutoffBy, Words>> = {
  jee: { college: COLLEGE, branch: BRANCH }, comedk: { college: COLLEGE, branch: BRANCH },
  bitsat: {
    college: { tab: "Campus se", pick: "Campus chuno", hint: "Pilani, Goa ya Hyderabad", none: "Koi campus nahi mila." },
    branch: { tab: "Program se", pick: "Program chuno", hint: "Program likho, jaise Computer Science", none: "Koi program nahi mila. Naam thoda chhota likh kar dekho." },
  },
};
const ABOUT: Record<CutoffExam, string> = {
  jee: "Category, gender aur home state se seat ka raasta badalta hai, isliye cutoff bhi. Home state se NIT ki Home-state seat aur JAC Delhi ki Delhi seat khulti hai.",
  comedk: "Sirf GM (All India) seats. COMEDK mein category se cutoff nahi badalta.",
  bitsat: "BITS round-wise cutoff publish nahi karta, isliye 2022 se 2026 tak ke final cutoff score dikhenge. Category se cutoff nahi badalta.",
};

export function Cutoff({ states }: { states: string[] }) {
  const [st, setSt] = useState<State>(DEFAULT);
  const [picker, setPicker] = useState<"key" | "state" | null>(null);
  const saves = useProfileSaves();
  useEffect(() => {
    storage.getItem<string | null>(SAVED.cutoff, null).then(raw => {
      if (!raw) return;
      try {
        const v = JSON.parse(raw);
        setSt({ ...DEFAULT, ...v, jee: { ...PICK, ...v.jee }, comedk: { ...PICK, ...v.comedk }, bitsat: { ...PICK, ...v.bitsat } });
      } catch { /* keep defaults */ }
    });
  }, [saves]);
  const patch = (x: Partial<State>) => setSt(prev => { const next = { ...prev, ...x }; storage.setItem(SAVED.cutoff, JSON.stringify(next)); return next; });
  const exam = st.exam, p = st[exam], w = WORDS[exam];
  const pick = (x: Partial<Pick>) => patch({ [exam]: { ...p, ...x } });

  const lists = useOnce(cutoffOptions);
  const options = lists.data?.[exam][p.by === "college" ? "colleges" : "branches"] ?? [];
  const chosen = options.find(o => o.key === (p.by === "college" ? p.college : p.branch));
  const q: CutoffIn | null = chosen ? {
    exam, by: p.by, key: chosen.key, ...p.score,
    ...(exam === "jee" ? { level: st.level, category: st.category, female: st.female, pwd: st.pwd, state: st.state } : {}),
  } : null;
  const t = useTarget(q, cutoff);
  // While the next list loads, the old one is another exam's or another college's: never show it under this choice.
  const data = t.data && q && t.data.exam === exam && t.data.by === p.by && t.data.key === q.key ? t.data : null;
  // One event for each answer shown (a new exam, college or branch), not for every score typed under it.
  const shown = data ? `${data.exam}|${data.by}|${data.key}` : "";
  useEffect(() => { if (shown && data) track("cutoff_search_completed", { exam: data.exam, by: data.by, rows: data.rows.length }); }, [shown]); // eslint-disable-line react-hooks/exhaustive-deps

  return <>
    <Switch prefix="cut-exam" value={exam} onChange={e => patch({ exam: e })} items={[{ key: "jee", label: "JEE Main" }, { key: "bitsat", label: "BITSAT" }, { key: "comedk", label: "COMEDK" }]} />
    <ErrorBox error={lists.error ?? undefined} retry={lists.retry} testID="cut-options-error" />
    <Strip form title="Kiska cut off dekhna hai?" testID="cut-form">
      <Switch prefix="cut-by" value={p.by} onChange={by => pick({ by })} items={[{ key: "college", label: w.college.tab }, { key: "branch", label: w.branch.tab }]} />
      <Chooser testID="cut-pick" label={chosen?.title ?? null} empty={w[p.by].pick} onPress={() => setPicker("key")} />
      {exam === "jee" ? <>
        <View style={styles.wrap}>
          {CATS.map(c => <Toggle key={c} testID={`cut-cat-${c}`} label={CATEGORY_LABEL[c]} on={st.category === c} onPress={() => patch({ category: c })} />)}
        </View>
        <View style={styles.wrap}>
          <Toggle testID="cut-female" label="Female" on={st.female} onPress={() => patch({ female: !st.female })} />
          <Toggle testID="cut-pwd" label="PwD" on={st.pwd} onPress={() => patch({ pwd: !st.pwd })} />
          <Toggle testID="cut-state" label={st.state ?? "Home state"} on={!!st.state} caret onPress={() => setPicker("state")} />
        </View>
      </> : null}
      <T size={11.5} color={colors.custom_dim}>{ABOUT[exam]}</T>
    </Strip>
    <ErrorBox error={t.error ?? undefined} retry={t.retry} testID="cut-error" />
    {data && lists.data ? <CutoffList key={`${exam}-${p.by}-${data.key}`} data={data} busy={t.busy} pick={p} onPick={pick} kinds={lists.data[exam].score}
        level={st.level} onLevel={level => patch({ level })} query={q!} />
      : q ? (t.error ? null : <ActivityIndicator testID="cut-loading" color={colors.muted} />)
      : <T testID="cut-hint" size={13} color={colors.muted}>
        {p.by === "college" ? `${w.college.pick}: uski har branch ka har round ka cut off dikhega.` : `${w.branch.pick}: us branch ke top 100 college, har round ke cut off ke saath dikhenge.`}
        {" Phir apna score daal kar sirf wahi dekh sakte ho jahan aap eligible ho."}
      </T>}
    <Picker visible={picker === "state"} title="Home state" options={states} value={st.state ? [st.state] : []} allLabel="No home state"
      onChange={v => patch({ state: v[0] ?? null })} onClose={() => setPicker(null)} testID="cut-state-picker" />
    <CollegeSearch key={`${exam}-${p.by}`} visible={picker === "key"} title={w[p.by].pick} options={options} hint={w[p.by].hint} none={w[p.by].none}
      onPick={k => pick(p.by === "college" ? { college: k } : { branch: k })} onClose={() => setPicker(null)} testID="cut-pick-sheet" />
  </>;
}

const styles = StyleSheet.create({
  wrap: { flexDirection: "row", flexWrap: "wrap", gap: space.sm },
});
