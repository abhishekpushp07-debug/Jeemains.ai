// The marks each dream seat needs, worked out when the student pins it (from the same 2026 data as Target marks):
// JEE Main: the final round's closing rank turned into marks for the student's category (normal paper; easy..tough range).
// COMEDK: the final round's closing rank turned into marks (middle of the range). BITSAT: the 2026 cutoff itself.
import { BitsatItem, Category, ComedkItem, fmt, Seat, targetComedk, targetJee } from "@/src/rank/api";
import type { Dream } from "./store";

export type JeeProfile = { category: Category; female: boolean; pwd: boolean; state: string | null };
let profile: JeeProfile = { category: "GEN", female: false, pwd: false, state: null };
/** The College predictor form's category, gender, PwD and state: the JEE dream's marks are worked out for them. */
export const setJeeProfile = (p: JeeProfile) => { profile = p; };

const MISSING = "Is seat ka target abhi nahi mila. Thodi der baad dobara try karo.";

export async function jeeDream(s: Seat): Promise<Dream> {
  const t = await targetJee({ inst: s.inst, ...profile });
  const rows = t.rows.filter(r => r.prog === s.prog);
  const row = rows.find(r => r.path === s.path) ?? rows[0];
  if (!row) throw new Error(MISSING);
  const m = row.final.marks;
  return { id: `jee-${s.prog}`, exam: "jee", college: s.college, branch: s.branch, need: m.normal,
    range: [Math.min(m.easy, m.tough), Math.max(m.easy, m.tough)], note: `${row.final.label} closing ${fmt(row.final.close)} ${row.rank_type}`, at: Date.now() };
}

export async function comedkDream(c: ComedkItem): Promise<Dream> {
  const t = await targetComedk(c.code);
  const row = t.rows.find(r => r.cc === c.cc);
  if (!row) throw new Error(MISSING);
  return { id: `comedk-${c.id}`, exam: "comedk", college: c.college, branch: c.course, need: row.final.mid,
    range: [Math.min(...row.final.marks), Math.max(...row.final.marks)], note: `${row.final.label} closing ${fmt(row.final.close)} GM`, at: Date.now() };
}

export const bitsatDream = async (b: BitsatItem): Promise<Dream> => ({
  id: `bitsat-${b.id}`, exam: "bitsat", college: b.college, branch: b.program, need: b.cutoff, note: "BITSAT 2026 cutoff", at: Date.now(),
});
