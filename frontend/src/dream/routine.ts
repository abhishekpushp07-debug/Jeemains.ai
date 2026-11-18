// "Dream Unlocked": the Kohinoor Legends' 30-second routine. 64 counts at 128 BPM. Count k is beat k of the cheer track
// served at /api/rf/art/dream_cheer.m4a (made by backend/rapidfire/make_dream_cheer.py, whose SPINS are the lead's spins here).
// Eight sections of eight counts: intro, verse, verse, build, drop with spins, mirrored verse, verse, finale.
// Holders: 0 stand, 1 side kick, 2 knee lift, 3 lunge. Lead: 0 star jump, 1 high kick, 2 hip sway, 3 high-low.
export const BEAT = 60000 / 128, COUNTS = 64, ROUTINE_MS = BEAT * COUNTS;

type Section = { hold: number[]; holdHop: number[]; lead: number[]; leadHop: number[]; spin: number[] };
const INTRO: Section = {
  hold: [0, 0, 0, 0, 2, 0, 2, 0], holdHop: [0, 0.02, 0, 0.02, 0.04, 0.02, 0.04, 0.03],
  lead: [2, 2, 2, 2, 3, 2, 3, 0], leadHop: [0, 0.02, 0, 0.02, 0.03, 0.02, 0.03, 0.12], spin: [0, 0, 0, 0, 0, 0, 0, 0],
};
const VERSE: Section = {
  hold: [0, 2, 0, 1, 0, 3, 2, 1], holdHop: [0.06, 0.03, 0.06, 0.02, 0.06, 0, 0.03, 0.02],
  lead: [2, 0, 3, 1, 2, 0, 3, 1], leadHop: [0.02, 0.16, 0, 0.05, 0.02, 0.16, 0, 0.05], spin: [0, 0, 1, 0, 0, 0, 1, 0],
};
const BUILD: Section = {
  hold: [1, 0, 1, 0, 2, 1, 2, 1], holdHop: [0.03, 0.05, 0.03, 0.05, 0.05, 0.04, 0.06, 0.05],
  lead: [1, 0, 1, 0, 1, 1, 0, 0], leadHop: [0.05, 0.12, 0.05, 0.12, 0.06, 0.08, 0.16, 0.2], spin: [0, 0, 0, 0, 0, 0, 0, 0],
};
const DROP: Section = {
  hold: [0, 3, 0, 3, 0, 2, 0, 1], holdHop: [0.06, 0, 0.06, 0, 0.06, 0.03, 0.06, 0.02],
  lead: [2, 2, 2, 2, 3, 1, 3, 0], leadHop: [0.04, 0.02, 0.04, 0.02, 0.04, 0.16, 0, 0.18], spin: [1, 0, 1, 0, 1, 0, 0, 0],
};
const MIRROR: Section = {
  hold: [2, 1, 2, 1, 0, 3, 0, 3], holdHop: [0.03, 0.02, 0.03, 0.02, 0.06, 0, 0.06, 0],
  lead: [3, 1, 3, 1, 0, 2, 0, 2], leadHop: [0, 0.14, 0, 0.14, 0.12, 0.02, 0.12, 0.02], spin: [0, 0, 0, 0, 0, 1, 0, 1],
};
const FINALE: Section = {
  hold: [1, 2, 1, 2, 0, 0, 0, 0], holdHop: [0.04, 0.05, 0.04, 0.06, 0.1, 0.02, 0.06, 0],
  lead: [1, 1, 1, 1, 0, 2, 0, 0], leadHop: [0.1, 0.1, 0.12, 0.14, 0.22, 0.02, 0.18, 0], spin: [0, 0, 0, 0, 0, 1, 0, 0],
};
const SECTIONS = [INTRO, VERSE, VERSE, BUILD, DROP, MIRROR, VERSE, FINALE];
export const HOLD = SECTIONS.flatMap(s => s.hold), HOLD_HOP = SECTIONS.flatMap(s => s.holdHop);
export const LEAD = SECTIONS.flatMap(s => s.lead), LEAD_HOP = SECTIONS.flatMap(s => s.leadHop), LEAD_SPIN = SECTIONS.flatMap(s => s.spin);

/** What the squad shouts, by the count it starts on (each stays until the next one). */
export function chantsFor(name: string, college: string, over: number): [number, string][] {
  const first = (name.trim().split(/\s+/)[0] || "Champion").toUpperCase(), c = college.toUpperCase();
  return [
    [0, "READY?"], [2, "OK!"], [4, `${first}!`], [6, "LET'S GO!"],
    [8, "D"], [9, "D·R"], [10, "D·R·E"], [11, "D·R·E·A"], [12, "D·R·E·A·M"], [13, "DREAM!"],
    [16, `${c}!`], [20, "AA RAHE HAIN!"],
    [24, "1"], [25, "2"], [26, "3"], [27, "4"], [28, "TARGET…"], [30, "CROSS!"],
    [32, "WHOOO!"], [36, over > 0 ? `+${over} MARKS UPAR!` : "BILKUL TARGET PAR!"],
    [40, `GO ${first} GO!`], [44, "GO! GO! GO!"],
    [48, "YOU DID IT!"], [52, "AB AUR UPAR!"],
    [56, "FINAL…"], [57, "3"], [58, "2"], [59, "1"], [60, "DREAM UNLOCKED!"],
  ];
}
