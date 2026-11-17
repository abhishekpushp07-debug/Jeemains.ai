// WhatsApp text for the Rank Card, the BITSAT card and the shortlist (plain text, so it reaches any phone instantly).
import { sendWhatsApp } from "@/src/rapid/social";
import { BitsatOut, ComedkOut, fmt, fmtRange, RankResult, Seat } from "./api";
import { TAG } from "./tones";
import type { Saved } from "./shortlist";

const SIGN = "JEELIVE.AI app ke Rank tab par apna rank aur college dekho.";
const pctText = (r: RankResult) =>
  r.percentile[0] === r.percentile[1] ? r.percentile[0].toFixed(2) : `${r.percentile[0].toFixed(2)} – ${r.percentile[1].toFixed(2)}`;

export function shareJee(r: RankResult, seats: Seat[]) {
  const lines = ["🎯 Mera JEELIVE.AI Rank Card · JEE Main 2026", r.summary, "",
    `Expected percentile: ${pctText(r)}`, `Expected rank (CRL): ${fmtRange(r.crl)}`];
  if (r.cat_rank) lines.push(`Expected ${r.cat_rank.label}: ${fmtRange(r.cat_rank.range)}`);
  if (r.pwd_rank) lines.push(`Expected ${r.pwd_rank.label}: ${fmtRange(r.pwd_rank.range)}`);
  if (seats.length) {
    lines.push("", "Top college-branch (2026 cutoff):");
    seats.slice(0, 5).forEach((s, i) => lines.push(`${i + 1}. ${s.college} · ${s.branch}${s.tag ? ` (${TAG[s.tag].label})` : ""}`));
  }
  lines.push("", "2026 ke data par estimate, guarantee nahi.", SIGN);
  return sendWhatsApp(lines.join("\n"));
}

export function shareBitsat(d: BitsatOut) {
  const r = d.result;
  const lines = ["🎯 Mera JEELIVE.AI Rank Card · BITSAT 2026", `Score: ${r.score} / ${r.max}`,
    `2026 cutoff se ${r.cleared_all} / ${r.total_all} BITS programs clear`];
  if (r.best) lines.push(`Best: ${r.best.college} · ${r.best.program} (cutoff ${r.best.cutoff})`);
  if (r.target) lines.push(`Agla target: ${r.target.college} · ${r.target.program}, +${r.target.gap} marks aur`);
  lines.push("", SIGN);
  return sendWhatsApp(lines.join("\n"));
}

export function shareComedk(d: ComedkOut) {
  const r = d.result;
  const lines = ["🎯 Mera JEELIVE.AI Rank Card · COMEDK 2026", r.summary, "",
    `${r.from_marks ? "Expected rank" : "Rank"} (GM): ${fmtRange(r.rank)}`, `${r.in_reach} / ${r.total} GM college-course pahunch mein`];
  if (d.items.length) {
    lines.push("", "Top college-course (2026 closing rank):");
    d.items.slice(0, 5).forEach((s, i) => lines.push(`${i + 1}. ${s.college} · ${s.course} · ${fmt(s.close)}${s.tag ? ` (${TAG[s.tag].label})` : ""}`));
  }
  lines.push("", "2026 ke data par estimate, guarantee nahi.", SIGN);
  return sendWhatsApp(lines.join("\n"));
}

export function shareShortlist(list: Saved[]) {
  const lines = ["⭐ Meri college shortlist (JEELIVE.AI)", ""];
  list.forEach((s, i) => lines.push(`${i + 1}. ${s.title} · ${s.sub}${s.tag ? ` (${TAG[s.tag].label})` : ""}`, `   ${s.line}`));
  lines.push("", SIGN);
  return sendWhatsApp(lines.join("\n"));
}
