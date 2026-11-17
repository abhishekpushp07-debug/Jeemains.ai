// The input part of the Rank tab: marks / percentile, paper level and the optional chips. Shrinks to one line after Show.
import React, { useState } from "react";
import { StyleSheet, TextInput, View } from "react-native";
import { T } from "@/src/components/ui";
import { Pill } from "@/src/components/design";
import { rankColors as colors, fonts, noOutline, space } from "@/src/theme";
import type { Category, FormBody, Level } from "./api";
import { CATEGORY_LABEL, LEVEL } from "./tones";
import { Picker, Strip, Summary, Toggle } from "./controls";

export type FormState = { marks: string; pct: string; level: Level; category: Category; female: boolean; pwd: boolean; state: string | null; branches: string[] };
export const DEFAULT_FORM: FormState = { marks: "", pct: "", level: "normal", category: "GEN", female: false, pwd: false, state: null, branches: [] };
const LEVELS: Level[] = ["tough", "normal", "easy"];
const CATS: Category[] = ["GEN", "EWS", "OBC-NCL", "SC", "ST"];

/** Form -> request body, or a short message saying what to fix. */
export function toBody(f: FormState): FormBody | string {
  const m = f.marks.trim(), p = f.pct.trim();
  if (!m && !p) return "Marks ya percentile mein se koi ek daalo.";
  const body: FormBody = { level: f.level, category: f.category, female: f.female, pwd: f.pwd, state: f.state, branches: f.branches };
  if (m) {
    const n = Number(m);
    if (!Number.isInteger(n) || n < -75 || n > 300) return "Marks −75 se 300 ke beech poore ank mein daalo.";
    body.marks = n;
  }
  if (p) {
    const n = Number(p);
    if (!Number.isFinite(n) || n < 0 || n > 100) return "Percentile 0 se 100 ke beech daalo.";
    body.percentile = n;
  }
  return body;
}

export function branchLabel(b: string[]) {
  return b.length === 0 ? "All branches" : b.length === 1 ? b[0] : `${b.length} branches`;
}

export function InputCard({ form, onChange, states, branches, open, summary, onShow, onEdit, busy }: {
  form: FormState; onChange: (patch: Partial<FormState>) => void; states: string[]; branches: string[];
  open: boolean; summary: string; onShow: (body: FormBody) => void; onEdit: () => void; busy: boolean;
}) {
  const [problem, setProblem] = useState<string | null>(null);
  const [picker, setPicker] = useState<"state" | "branch" | null>(null);
  if (!open) return <Summary testID="rank-input-collapsed" text={summary} onEdit={onEdit} />;
  const show = () => {
    const body = toBody(form);
    if (typeof body === "string") { setProblem(body); return; }
    setProblem(null);
    onShow(body);
  };
  const clean = (v: string, decimals: boolean) => v.replace(decimals ? /[^0-9.]/g : /[^0-9-]/g, "").slice(0, decimals ? 10 : 4);
  return <Strip title="Your score" testID="rank-input">
    <View style={styles.inputs}>
      <View style={{ flex: 1, gap: 4 }}>
        <T w="semibold" size={12} color={colors.muted}>Marks (out of 300)</T>
        <TextInput testID="rank-marks-input" value={form.marks} onChangeText={v => onChange({ marks: clean(v, false) })} keyboardType="numbers-and-punctuation"
          placeholder="e.g. 180" placeholderTextColor={colors.custom_dim} style={styles.input} keyboardAppearance="dark" selectionColor={colors.custom_rankBloodInk} returnKeyType="done" maxLength={4} accessibilityLabel="Marks out of 300" />
      </View>
      <View style={{ flex: 1, gap: 4 }}>
        <T w="semibold" size={12} color={colors.muted}>Percentile</T>
        <TextInput testID="rank-percentile-input" value={form.pct} onChangeText={v => onChange({ pct: clean(v, true) })} keyboardType="decimal-pad"
          placeholder="e.g. 97.4" placeholderTextColor={colors.custom_dim} style={styles.input} keyboardAppearance="dark" selectionColor={colors.custom_rankBloodInk} returnKeyType="done" maxLength={10} accessibilityLabel="Percentile" />
      </View>
    </View>
    <View style={styles.row}>
      <T w="semibold" size={12} color={colors.muted} style={styles.rowLabel}>Paper</T>
      {LEVELS.map(l => <Toggle key={l} testID={`rank-level-${l}`} label={LEVEL[l].label} on={form.level === l} ink={LEVEL[l].ink} soft={LEVEL[l].soft} onPress={() => onChange({ level: l })} />)}
    </View>
    <View style={styles.wrap}>
      {CATS.map(c => <Toggle key={c} testID={`rank-cat-${c}`} label={CATEGORY_LABEL[c]} on={form.category === c} onPress={() => onChange({ category: c })} />)}
    </View>
    <View style={styles.wrap}>
      <Toggle testID="rank-female" label="Female" on={form.female} onPress={() => onChange({ female: !form.female })} />
      <Toggle testID="rank-pwd" label="PwD" on={form.pwd} onPress={() => onChange({ pwd: !form.pwd })} />
      <Toggle testID="rank-state" label={form.state ?? "Home state"} on={!!form.state} caret onPress={() => setPicker("state")} />
      <Toggle testID="rank-branch" label={branchLabel(form.branches)} on={form.branches.length > 0} caret onPress={() => setPicker("branch")} />
    </View>
    {problem ? <T testID="rank-input-error" w="semibold" size={13} color={colors.error}>{problem}</T> : null}
    <Pill testID="rank-show" size="lg" label="Show" iconRight="arrow-right" busy={busy} onPress={show} bg={colors.brandPrimary} ink={colors.onBrandPrimary} />
    <Picker visible={picker === "state"} title="Home state" options={states} value={form.state ? [form.state] : []} allLabel="No home state"
      onChange={v => onChange({ state: v[0] ?? null })} onClose={() => setPicker(null)} testID="rank-state-picker" />
    <Picker visible={picker === "branch"} title="Branch" options={branches} value={form.branches} multi allLabel="All branches"
      onChange={v => onChange({ branches: v })} onClose={() => setPicker(null)} testID="rank-branch-picker" />
  </Strip>;
}

const styles = StyleSheet.create({
  inputs: { flexDirection: "row", gap: space.md },
  input: { height: 52, borderRadius: 14, borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_cardRaised, paddingHorizontal: space.md, fontFamily: fonts.bold, fontSize: 18, color: colors.onSurface, ...noOutline },
  row: { flexDirection: "row", alignItems: "center", gap: space.sm, flexWrap: "wrap" },
  rowLabel: { width: 44 },
  wrap: { flexDirection: "row", flexWrap: "wrap", gap: space.sm },
});
