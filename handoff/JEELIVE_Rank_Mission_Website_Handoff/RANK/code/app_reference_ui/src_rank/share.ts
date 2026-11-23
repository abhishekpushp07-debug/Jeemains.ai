// What goes out when a Rank card is shared: the card's photo (see src/shareCard.ts) with a short caption and the student's
// own link. `fallback` is the full text, used where a photo cannot be made (an older app build, a browser without sharing).
import type { CardShare } from "@/src/shareCard";
import { BitsatOut, ComedkOut, EstimateOut, fmt, fmtPct, fmtRange, RankResult, Seat } from "./api";
import { LEVEL, TAG } from "./tones";
import type { Saved } from "./shortlist";

const ESTIMATE = "2026 ke data par estimate, guarantee nahi.";
const invite = (link: string) => `Apna rank aur college free mein dekho 👉 ${link}`;
const pctText = (r: RankResult) =>
  r.percentile[0] === r.percentile[1] ? r.percentile[0].toFixed(2) : `${r.percentile[0].toFixed(2)} – ${r.percentile[1].toFixed(2)}`;

/** Caption = headline lines + the invite; fallback = every line + the invite. */
const pack = (filename: string, head: string[], rest: string[], link: string): CardShare => ({
  filename, caption: [...head, "", invite(link)].join("\n"), fallback: [...head, ...rest, "", invite(link)].join("\n"),
});

export function shareJee(r: RankResult, seats: Seat[], link: string): CardShare {
  const rest = ["", `Expected percentile: ${pctText(r)}`];
  if (r.cat_rank) rest.push(`Expected ${r.cat_rank.label}: ${fmtRange(r.cat_rank.range)}`);
  if (r.pwd_rank) rest.push(`Expected ${r.pwd_rank.label}: ${fmtRange(r.pwd_rank.range)}`);
  if (seats.length) {
    rest.push("", "Top college-branch (2026 cutoff):");
    seats.slice(0, 5).forEach((s, i) => rest.push(`${i + 1}. ${s.college} · ${s.branch}${s.tag ? ` (${TAG[s.tag].label})` : ""}`));
  }
  rest.push("", ESTIMATE);
  return pack("JEELIVE-Rank-Card.png", ["🎯 Mera JEELIVE.AI Rank Card · JEE Main 2026", r.summary, `Expected rank (CRL): ${fmtRange(r.crl)}`], rest, link);
}

export function shareBitsat(d: BitsatOut, link: string): CardShare {
  const r = d.result;
  const rest: string[] = [];
  if (r.best) rest.push(`Best: ${r.best.college} · ${r.best.program} (cutoff ${r.best.cutoff})`);
  if (r.target) rest.push(`Agla target: ${r.target.college} · ${r.target.program}, +${r.target.gap} marks aur`);
  return pack("JEELIVE-BITSAT-Card.png", ["🎯 Mera JEELIVE.AI Rank Card · BITSAT 2026", `Score: ${r.score} / ${r.max}`,
    `2026 cutoff se ${r.cleared_all} / ${r.total_all} BITS programs clear`], rest, link);
}

export function shareComedk(d: ComedkOut, link: string): CardShare {
  const r = d.result;
  const rest: string[] = [`${r.in_reach} / ${r.total} GM college-course pahunch mein`];
  if (d.items.length) {
    rest.push("", "Top college-course (2026 closing rank):");
    d.items.slice(0, 5).forEach((s, i) => rest.push(`${i + 1}. ${s.college} · ${s.course} · ${fmt(s.close)}${s.tag ? ` (${TAG[s.tag].label})` : ""}`));
  }
  rest.push("", ESTIMATE);
  return pack("JEELIVE-COMEDK-Card.png", ["🎯 Mera JEELIVE.AI Rank Card · COMEDK 2026", r.summary,
    `${r.from_marks ? "Expected rank" : "Rank"} (GM): ${fmtRange(r.rank)}`], rest, link);
}

export function shareEstimate(d: EstimateOut, link: string): CardShare {
  if (d.exam !== "jee") return pack("JEELIVE-Rank-Predictor.png", ["🎯 Mera JEELIVE.AI Rank Predictor · COMEDK 2026", d.summary,
    `Expected rank: ${fmtRange(d.rank)}`], [`Percentile: lagbhag ${fmtPct(d.percentile)}`, "", ESTIMATE], link);
  const r = d.result;
  return pack("JEELIVE-Rank-Predictor.png", ["🎯 Mera JEELIVE.AI Rank Predictor · JEE Main 2026", r.summary, `Rank (CRL): ${fmtRange(r.crl)}`], [
    `Percentile: ${fmtPct(r.percentile)}`,
    ...(r.cat_rank ? [`${r.cat_rank.label}: ${fmtRange(r.cat_rank.range)}`] : []),
    ...(r.pwd_rank ? [`${r.pwd_rank.label}: ${fmtRange(r.pwd_rank.range)}`] : []),
    "", "Paper type ke hisaab se:",
    ...d.levels.map(l => `${LEVEL[l.level].label}: ${fmtPct(l.percentile)} percentile · rank ${fmtRange(l.crl)}`),
    "", ESTIMATE,
  ], link);
}

export function shareShortlist(list: Saved[], link: string): CardShare {
  const rest = [""];
  list.forEach((s, i) => rest.push(`${i + 1}. ${s.title} · ${s.sub}${s.tag ? ` (${TAG[s.tag].label})` : ""}`, `   ${s.line}`));
  return pack("JEELIVE-Shortlist.png", ["⭐ Meri college shortlist (JEELIVE.AI)", `${list.length} colleges, 2026 cutoff ke saath`], rest, link);
}
