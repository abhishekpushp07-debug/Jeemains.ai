// College vs college in College compare: a search sheet (JEE Main / COMEDK / BITSAT) adds whole colleges; tick 2–3 to read
// them side by side (entry marks, Computer Science, toughest branch, branches, seats, fee). Each college opens its full
// branch list ("Saari branches dekho"), where any branch can join the branch compare.
import React, { useEffect, useMemo, useRef, useState } from "react";
import { ActivityIndicator, StyleSheet, useWindowDimensions, View } from "react-native";
import { ErrorBox, Press, T } from "@/src/components/ui";
import { Glyph } from "@/src/components/Glyph";
import { rankColors as colors, radius, space } from "@/src/theme";
import { CATEGORY_LABEL, EXAM, KIND, TAG } from "./tones";
import { CollegeCol, CollegeSide, compareColleges, fmt, getColleges, JeeProfileIn } from "./api";
import { track } from "@/src/jlTracker";
import { RemoveButton, Strip, Switch, Tag } from "./controls";
import { useAccent } from "./accent";
import { CollegeSearch, Option } from "./CollegeSearch";
import { CompareCollege, toggleCollege, useCompareColleges } from "./colleges";
import { CollegeBranches, FULL, lakh } from "./CollegeBranches";
import { Dash, TableRow, tableStyles } from "./compareKit";

const MAX = 3;
type Exam = CompareCollege["exam"];
type Opt = Option & { c: CompareCollege };

/** The search sheet's colleges, loaded once per app run. */
let cached: Record<Exam, Opt[]> | null = null;
async function loadOptions() {
  if (cached) return cached;
  const d = await getColleges();
  const opt = (c: CompareCollege, find?: string): Opt => ({ key: c.id, title: c.title, sub: c.sub, find, c });
  cached = {
    jee: d.jee.map(c => opt({ id: `jee-${c.inst}`, exam: "jee", key: String(c.inst), title: c.short, sub: `${KIND[c.type]?.label ?? c.type} · ${c.city}, ${c.state}` }, c.name)),
    comedk: d.comedk.map(c => opt({ id: `comedk-${c.code}`, exam: "comedk", key: c.code, title: c.short, sub: `COMEDK · ${c.city}` }, `${c.name} ${c.code}`)),
    bitsat: (d.bitsat ?? []).map(c => opt({ id: `bitsat-${c.campus}`, exam: "bitsat", key: c.campus, title: c.name, sub: `${c.programs} programs · BITSAT` })),
  };
  return cached;
}

const profileText = (p: JeeProfileIn) => [CATEGORY_LABEL[p.category], p.pwd ? "PwD" : null, p.female ? "Female" : null,
  p.state ? `Home state ${p.state}` : "Home state nahi chuna"].filter(Boolean).join(" · ");

export function CollegeCompare({ profile, onBranches }: { profile: JeeProfileIn; onBranches: () => void }) {
  const list = useCompareColleges();
  const a = useAccent();
  const [pick, setPick] = useState<string[]>([]);
  const touched = useRef(false);
  const [hint, setHint] = useState<string | null>(null);
  const [sheet, setSheet] = useState(false);
  const [exam, setExam] = useState<Exam>("jee");
  const [opts, setOpts] = useState(cached);
  const [optError, setOptError] = useState<string | null>(null);
  const [open, setOpen] = useState<string | null>(null);
  const [data, setData] = useState<{ items: CollegeCol[]; notes: string[] } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tries, setTries] = useState(0);

  // Until the student ticks something, the newest colleges (up to 3) stay ticked, so a compare shows straight away.
  useEffect(() => { if (!touched.current) setPick(list.slice(0, MAX).map(c => c.id)); }, [list]);
  const chosen = pick.map(id => list.find(c => c.id === id)).filter((c): c is CompareCollege => !!c);
  // JEE marks depend on the student's category, gender, PwD and state: a change there asks again.
  const prof = `${profile.category}|${profile.female}|${profile.pwd}|${profile.state}`;
  const key = chosen.map(c => c.id).join(",") + (chosen.some(c => c.exam === "jee") ? `#${prof}` : "");
  useEffect(() => {
    if (chosen.length < 2) { setData(null); return; }
    let live = true;
    setBusy(true); setError(null);
    compareColleges(chosen.map(c => ({ exam: c.exam, id: c.key })), profile).then(d => { if (live) { setData(d); track("college_compare_used", { kind: "colleges", count: chosen.length }); } })
      .catch(e => { if (live) setError(e.message); }).finally(() => { if (live) setBusy(false); });
    return () => { live = false; setBusy(false); };
  }, [key, tries]); // eslint-disable-line react-hooks/exhaustive-deps

  const fetchOptions = () => { setOptError(null); loadOptions().then(setOpts).catch(e => setOptError(e.message)); };
  const openSheet = () => { setSheet(true); if (!opts) fetchOptions(); };
  const toggle = (id: string) => {
    touched.current = true;
    if (pick.includes(id)) { setPick(pick.filter(x => x !== id)); setHint(null); return; }
    if (pick.length >= MAX) { setHint("Ek baar mein 3 colleges tak. Pehle kisi ek ka tick hatao."); return; }
    setPick([...pick, id]); setHint(null);
  };
  const add = (optKey: string) => {
    const o = opts?.[exam].find(x => x.key === optKey);
    if (!o) return;
    const there = list.some(c => c.id === o.c.id);
    toggleCollege(o.c);
    if (there) setPick(p => p.filter(x => x !== o.c.id));
    else if (touched.current && pick.length < MAX) setPick(p => [...p, o.c.id]); // untouched: the newest 3 are ticked anyway
  };
  const remove = (c: CompareCollege) => {
    touched.current = true;
    setPick(p => p.filter(x => x !== c.id));
    if (open === c.id) setOpen(null);
    toggleCollege(c);
  };
  const added = useMemo(() => new Set(list.map(c => c.id)), [list]);

  return <>
    <Strip form title="Colleges compare" testID="cmp-colleges" right={<T w="bold" size={12} color={a ? a.on : colors.muted}>{pick.length} / {MAX} chune</T>}>
      <Press testID="cmp-add-college" onPress={openSheet} accessibilityRole="button" accessibilityLabel="College dhoondo aur compare mein jodo"
        scaleTo={0.98} style={[styles.add, a && { borderColor: a.line, backgroundColor: a.soft }]}>
        <View style={[styles.addIcon, { backgroundColor: a?.ink ?? colors.brandPrimary }]}><Glyph name="magnify" size={18} color={a?.on ?? colors.onBrandPrimary} /></View>
        <View style={{ flex: 1, gap: 1 }}>
          <T w="heavy" size={14.5}>College dhoondo aur jodo</T>
          <T size={12} color={colors.custom_softText} numberOfLines={1}>JEE Main · COMEDK · BITSAT, koi bhi college</T>
        </View>
        <Glyph name="plus" size={20} color={a?.text ?? colors.onSurface} stroke={2.2} />
      </Press>
      {list.length === 0 ? <T testID="cmp-colleges-empty" size={13} color={colors.custom_softText}>
        2–3 college jodo aur side by side dekho: entry ke liye kitne marks, Computer Science kitne par, seats aur fee. Har college ke andar uski saari branches bhi.
      </T> : null}
      {list.map((c, i) => <CollegeItem key={c.id} c={c} i={i} on={pick.includes(c.id)} open={open === c.id} profile={profile}
        onTick={() => toggle(c.id)} onRemove={() => remove(c)} onOpen={() => setOpen(open === c.id ? null : c.id)} onBranches={onBranches} />)}
      {hint ? <T testID="cmp-college-hint" w="semibold" size={12.5} color={colors.custom_flame}>{hint}</T> : null}
      {list.length > 0 && pick.length < 2 ? <T testID="cmp-college-need" size={12.5} color={colors.muted}>Side by side ke liye kam se kam 2 college chuno.</T> : null}
      {list.some(c => c.exam === "jee") ? <T testID="cmp-profile" size={11.5} color={colors.muted}>
        JEE marks aapke liye: {profileText(profile)}. Badalna ho to College predictor form mein badlo.
      </T> : null}
    </Strip>
    <ErrorBox error={error ?? undefined} retry={() => setTries(t => t + 1)} testID="cmp-college-error" />
    {busy && !data ? <ActivityIndicator testID="cmp-college-loading" color={colors.muted} /> : null}
    {data && chosen.length >= 2 ? <CollegeTable cols={data.items} notes={data.notes} /> : null}
    <CollegeSearch visible={sheet} title="College jodo" testID="cmp-college-sheet" onClose={() => setSheet(false)} onPick={add}
      options={opts?.[exam] ?? []} picked={added}
      header={<View style={{ gap: space.sm }}>
        <Switch prefix="cmp-sheet-exam" value={exam} onChange={setExam}
          items={[{ key: "jee", label: "JEE Main" }, { key: "comedk", label: "COMEDK" }, { key: "bitsat", label: "BITSAT" }]} />
        {optError ? <ErrorBox error={optError} retry={fetchOptions} testID="cmp-college-sheet-error" />
          : !opts ? <ActivityIndicator testID="cmp-college-sheet-loading" color={colors.muted} /> : null}
      </View>} />
  </>;
}

function CollegeItem({ c, i, on, open, profile, onTick, onRemove, onOpen, onBranches }: {
  c: CompareCollege; i: number; on: boolean; open: boolean; profile: JeeProfileIn;
  onTick: () => void; onRemove: () => void; onOpen: () => void; onBranches: () => void;
}) {
  const a = useAccent();
  const ex = EXAM[c.exam], ink = a?.text ?? colors.onSurface;
  return <View testID={`cmp-college-${i}`} style={[styles.card, on && a && { borderColor: a.line }]}>
    <View style={styles.cardTop}>
      <Press testID={`cmp-college-${i}-tick`} onPress={onTick} accessibilityRole="checkbox" accessibilityState={{ checked: on }}
        accessibilityLabel={`${c.title}, ${c.sub}`} scaleTo={0.99} style={styles.cardMain}>
        <View style={[tableStyles.check, a && { borderColor: a.line }, on && a && { backgroundColor: a.ink, borderColor: a.ink }]}>
          {on ? <Glyph name="check" size={14} color={a ? a.on : colors.onBrandPrimary} stroke={2.4} /> : null}
        </View>
        <View style={{ flex: 1, gap: 3 }}>
          <View style={styles.line}>
            <Tag label={ex.label} ink={ex.ink} soft={ex.soft} />
            <T w="bold" size={14.5} numberOfLines={1} style={{ flexShrink: 1 }}>{c.title}</T>
          </View>
          <T size={12} color={colors.custom_softText} numberOfLines={1}>{c.sub}</T>
        </View>
      </Press>
      <RemoveButton testID={`cmp-college-${i}-remove`} label={`${c.title} compare se hatao`} onPress={onRemove} />
    </View>
    <Press testID={`cmp-college-${i}-branches`} onPress={onOpen} accessibilityRole="button" accessibilityState={{ expanded: open }}
      accessibilityLabel={open ? `${c.title} ki branches band karo` : `${c.title} ki saari branches dekho`} scaleTo={0.98}
      style={[styles.see, a && { borderColor: a.line }]}>
      <Glyph name="format-list-bulleted" size={16} color={ink} />
      <T w="bold" size={13} color={ink} style={{ flex: 1 }}>{open ? "Branches band karo" : "Saari branches dekho"}</T>
      <Glyph name={open ? "chevron-up" : "chevron-down"} size={18} color={ink} />
    </Press>
    {open ? <CollegeBranches college={c} profile={profile} testID={`cmp-college-${i}-branch`} onBranches={onBranches} /> : null}
  </View>;
}

function CollegeTable({ cols, notes }: { cols: CollegeCol[]; notes: string[] }) {
  const tight = useWindowDimensions().width < 360 && cols.length === 3;
  // "Sabse aasaan entry" only between colleges of one exam (marks out of the same total).
  const same = cols.every(c => c.exam === cols[0].exam && !c.missing && c.easiest);
  const entry = cols.map(c => c.easiest?.marks ?? Infinity);
  const best = same ? entry.indexOf(Math.min(...entry)) : -1;
  const feeNotes = [...new Set(cols.filter(c => !c.missing && !c.fee && c.fee_note).map(c => c.fee_note!))];
  const row = (key: string, label: string | null, cell: (c: CollegeCol, i: number) => React.ReactNode) =>
    <TableRow key={key} id={`cmp-college-row-${key}`} label={label} count={cols.length} tight={tight} best={best}
      cell={i => cols[i].missing && key !== "head" ? <Dash /> : cell(cols[i], i)} />;
  // Three columns on a small phone: a size smaller, so long words like "Biotechnology" fit a cell without breaking.
  const small = tight ? 10 : 11.5;
  const side = (s: CollegeSide | null | undefined, exam: Exam, testID: string) => s ? <View style={{ gap: 1 }}>
    <View style={styles.marks}>
      <T testID={testID} color={colors.custom_rankSilver} style={tableStyles.serif}>{s.marks}</T>
      <T size={10.5} color={colors.muted}> / {FULL[exam]}</T>
    </View>
    <T size={small} color={colors.custom_softText} numberOfLines={4}>{s.branch}</T>
    <T size={tight ? 9.5 : 10.5} color={colors.muted} numberOfLines={3}>{exam === "bitsat" ? `Cutoff ${s.close}` : `Closing ${fmt(s.close)} ${s.rank_label}`} · {s.label}</T>
  </View> : <Dash />;
  return <Strip title="College vs college" testID="cmp-college-table">
    <View style={tableStyles.table}>
      {row("head", null, (c, i) => <View testID={`cmp-college-col-${i}`} style={{ gap: 3 }}>
        <Tag label={EXAM[c.exam].label} ink={EXAM[c.exam].ink} soft={EXAM[c.exam].soft} />
        {c.missing ? <T size={12} color={colors.error}>Ye college 2026 ke data mein nahi mila.</T> : <>
          <T w="bold" size={tight ? 12 : 13.5} numberOfLines={4}>{c.title ?? "—"}</T>
          <T size={small} color={colors.custom_softText} numberOfLines={2}>{c.place ?? ""}</T>
        </>}
      </View>)}
      {row("entry", "Entry: sabse kam marks", (c, i) => c.easiest ? <View style={{ gap: 2 }}>
        {side(c.easiest, c.exam, `cmp-college-entry-${i}`)}
        {i === best ? <T testID={`cmp-college-best-${i}`} w="semibold" size={11} color={TAG.safe.ink}>sabse aasaan entry</T> : null}
      </View> : <T size={11.5} color={colors.muted}>Aapke profile par koi seat nahi</T>)}
      {row("cs", "Computer Science", (c, i) => side(c.cs, c.exam, `cmp-college-cs-${i}`))}
      {row("top", "Sabse mushkil branch", (c, i) => side(c.toughest, c.exam, `cmp-college-top-${i}`))}
      {row("count", "Branches", c => <View>
        <T w="bold" size={13.5}>{c.branches ?? 0}</T>
        {c.cs_count ? <T size={10.5} color={colors.muted}>{c.cs_count} Computer Science</T> : null}
      </View>)}
      {row("seats", "Seats", c => c.seats ? <View>
        <T w="bold" size={13.5}>{fmt(c.seats)}</T>
        {c.seats_label ? <T size={10.5} color={colors.muted}>{c.seats_label}</T> : null}
      </View> : <Dash />)}
      {row("fee", "Fee / saal", c => c.fee ? <T w="bold" size={13}>{c.fee[0] === c.fee[1] ? lakh(c.fee[0]) : `${lakh(c.fee[0])} – ${lakh(c.fee[1])}`}</T>
        : <T size={11} color={colors.custom_dim}>website par *</T>)}
    </View>
    {feeNotes.map(n => <T key={n} size={11.5} color={colors.custom_dim}>* {n}</T>)}
    {notes.map(n => <T key={n} size={11.5} color={colors.custom_dim}>{n}</T>)}
  </Strip>;
}

const styles = StyleSheet.create({
  add: { flexDirection: "row", alignItems: "center", gap: space.md, minHeight: 64, padding: space.md, borderRadius: 16, borderWidth: 1.5,
    borderStyle: "dashed", borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_cardRaised },
  addIcon: { width: 38, height: 38, borderRadius: 19, alignItems: "center", justifyContent: "center" },
  card: { borderRadius: 16, borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_cardRaised, overflow: "hidden" },
  cardTop: { flexDirection: "row", alignItems: "center", paddingLeft: space.md, paddingRight: 2 },
  cardMain: { flex: 1, flexDirection: "row", alignItems: "center", gap: space.md, minHeight: 60, paddingVertical: space.sm },
  line: { flexDirection: "row", alignItems: "center", gap: space.sm },
  see: { flexDirection: "row", alignItems: "center", gap: space.sm, minHeight: 44, marginHorizontal: space.md, marginBottom: space.md, paddingHorizontal: space.md,
    borderRadius: radius.pill, borderWidth: 1, borderColor: colors.custom_cardLineStrong },
  marks: { flexDirection: "row", alignItems: "baseline" },
});
