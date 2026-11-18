// A college's full branch list inside College compare ("Saari branches dekho"): every branch with its 2026 final closing
// and the marks it needs (normal paper; JEE for the student's category, gender, PwD and state), and a + button that adds
// it to the branch compare (the same list as "Add to Compare" on the College predictor cards).
import React, { useEffect, useState } from "react";
import { ActivityIndicator, StyleSheet, View } from "react-native";
import { buzz, ErrorBox, Press, T } from "@/src/components/ui";
import { Glyph } from "@/src/components/Glyph";
import { rankColors as colors, radius, space } from "@/src/theme";
import { fmt, JeeProfileIn, targetBitsat, targetComedk, targetJee } from "./api";
import type { CompareCollege } from "./colleges";
import { bitsatRowSaved, comedkRowSaved, jeeRowSaved, Saved, toggleSaved, useShortlist } from "./shortlist";

export const FULL: Record<CompareCollege["exam"], number> = { jee: 300, comedk: 180, bitsat: 390 };
/** ₹3,22,000 → "₹3.22 L". */
export const lakh = (fee: number) => fee >= 100000 ? `₹${(fee / 100000).toFixed(2)} L` : `₹${fmt(fee)}`;

type Row = { name: string; line: string; marks: number; saved: Saved };

async function rowsOf(c: CompareCollege, p: JeeProfileIn): Promise<Row[]> {
  if (c.exam === "jee") {
    const t = await targetJee({ inst: Number(c.key), ...p });
    return t.rows.map(r => ({ name: `${r.branch}${r.degree ? ` (${r.degree})` : ""}`, marks: r.final.marks.normal, saved: jeeRowSaved(c.title, r),
      line: [`Closing ${fmt(r.final.close)} ${r.rank_type} · ${r.final.label}`, r.seats ? `${r.seats} seats` : null].filter(Boolean).join(" · ") }));
  }
  if (c.exam === "comedk") {
    const t = await targetComedk(c.key);
    return t.rows.map(r => ({ name: r.course, marks: r.final.mid, saved: comedkRowSaved(c.key, c.title, r),
      line: [`Closing ${fmt(r.final.close)} · ${r.final.label}`, r.fee ? lakh(r.fee) : null, r.seats ? `${r.seats} GM seats` : null].filter(Boolean).join(" · ") }));
  }
  const t = await targetBitsat();
  return t.rows.filter(r => r.campus === c.key).map(r => ({ name: r.program, marks: r.cutoff, saved: bitsatRowSaved(r),
    line: [`Cutoff ${r.cutoff} · 2026`, r.history.length > 1 && r.history[r.history.length - 2] != null ? `2025: ${r.history[r.history.length - 2]}` : null].filter(Boolean).join(" · ") }));
}

export function CollegeBranches({ college, profile, testID, onBranches }: { college: CompareCollege; profile: JeeProfileIn; testID: string; onBranches: () => void }) {
  const saved = useShortlist();
  const [rows, setRows] = useState<Row[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tries, setTries] = useState(0);
  const prof = college.exam === "jee" ? `${profile.category}|${profile.female}|${profile.pwd}|${profile.state}` : "";
  useEffect(() => {
    let live = true;
    setError(null);
    rowsOf(college, profile).then(r => { if (live) setRows(r); }).catch(e => { if (live) setError(e.message); });
    return () => { live = false; };
  }, [college.id, prof, tries]); // eslint-disable-line react-hooks/exhaustive-deps

  if (error) return <View style={styles.pad}><ErrorBox error={error} retry={() => setTries(t => t + 1)} testID={`${testID}-error`} /></View>;
  if (!rows) return <ActivityIndicator testID={`${testID}-loading`} color={colors.muted} style={styles.loading} />;
  const ids = new Set(saved.map(s => s.id));
  const inCompare = rows.filter(r => ids.has(r.saved.id)).length;
  return <View testID={`${testID}-list`} style={styles.list}>
    <T size={11.5} color={colors.muted}>
      {rows.length} branches · marks = normal paper par 2026 final closing{college.exam === "jee" ? " (aapke profile ke liye)" : ""}
    </T>
    {rows.length === 0 ? <T testID={`${testID}-none`} size={12.5} color={colors.custom_softText}>Aapke profile par is college mein koi seat nahi khulti.</T> : null}
    {rows.map((r, j) => {
      const on = ids.has(r.saved.id);
      return <View key={r.saved.id} testID={`${testID}-${j}`} style={styles.row}>
        <View style={{ flex: 1, minWidth: 0, gap: 2 }}>
          <T w="bold" size={13.5} numberOfLines={2}>{r.name}</T>
          <T size={11.5} color={colors.custom_softText} numberOfLines={2}>{r.line}</T>
        </View>
        <View style={styles.marks}>
          <T testID={`${testID}-${j}-marks`} w="heavy" size={16}>{r.marks}</T>
          <T size={9.5} color={colors.muted}>/ {FULL[college.exam]}</T>
        </View>
        <Press testID={`${testID}-${j}-add`} onPress={() => { if (!on) buzz("success"); toggleSaved(r.saved); }} scaleTo={0.92}
          accessibilityRole="button" accessibilityState={{ selected: on }} accessibilityLabel={on ? `${r.name} compare se hatao` : `${r.name} compare mein jodo`}
          style={[styles.add, on && styles.addOn]}>
          <Glyph name={on ? "check" : "plus"} size={18} color={on ? colors.custom_fOn : colors.custom_fSky} stroke={2.2} />
        </Press>
      </View>;
    })}
    {inCompare ? <Press testID={`${testID}-go`} onPress={onBranches} accessibilityRole="button" scaleTo={0.98} style={styles.go}>
      <T w="heavy" size={13.5} color={colors.custom_fOn} style={{ flexShrink: 1 }}>{inCompare} branch compare mein · side by side dekho</T>
      <Glyph name="arrow-right" size={16} color={colors.custom_fOn} />
    </Press> : <T size={11.5} color={colors.muted}>Kisi bhi branch ka + dabao, wo Branches compare mein jud jayegi.</T>}
  </View>;
}

const styles = StyleSheet.create({
  pad: { padding: space.md },
  loading: { paddingVertical: space.md },
  list: { gap: 2, paddingHorizontal: space.md, paddingBottom: space.md },
  row: { flexDirection: "row", alignItems: "center", gap: space.sm, minHeight: 56, paddingVertical: space.sm, borderTopWidth: 1, borderTopColor: colors.custom_barLine },
  marks: { alignItems: "flex-end", minWidth: 44 },
  add: { width: 44, height: 44, borderRadius: 22, borderWidth: 1, borderColor: colors.custom_fSkyLine, backgroundColor: colors.custom_fSkySoft,
    alignItems: "center", justifyContent: "center" },
  addOn: { backgroundColor: colors.custom_fSky, borderColor: colors.custom_fSky },
  go: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 6, minHeight: 44, marginTop: space.sm, paddingHorizontal: space.md,
    borderRadius: radius.pill, backgroundColor: colors.custom_fSky },
});
