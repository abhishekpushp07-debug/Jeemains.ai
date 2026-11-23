# 12 · Meri details (the shared Rank profile)  —  NEW

> **New in this pack.** A bar at the top of the Rank page where the student types their score and category **once**.
> Those values then start every one of the six Rank tools. It is a page feature only: there is no endpoint, nothing is
> sent to a server, and it works signed out. A ready web version of its logic is in
> `CONNECT/frontend_web/rankProfile.ts`; the app's own files are `profile.ts` and `ProfileBar.tsx` in
> `RANK/code/app_reference_ui/src_rank/`.

## 1. The one rule

**The profile gives starting values. It is not a live link.**

1. **Save** on Meri details writes the profile's values into every tool's saved form.
2. After that, each tool is edited on its own. An edit inside a tool is saved for that tool only. It does **not**
   change the profile and does **not** change any other tool.
3. Saving Meri details again fills the tools again.

Everything is optional. A student who never opens the bar loses nothing: each tool works exactly as before.

## 2. What the student can give

| Exam | Fields | Limits |
|---|---|---|
| JEE Main | Marks / 300 · Percentile · Rank (CRL) · Paper (Tough / Normal / Easy, shown once marks are typed) · Category (**General at the start**, changed with chips: General, EWS, OBC-NCL, SC, ST) · Female · PwD · Home state | marks −75 … 300 (whole) · percentile 0 … 100 · rank 1 … 20,00,000 (whole) |
| COMEDK | Marks / 180 · COMEDK rank | marks 0 … 180 · rank 1 … 2,00,000 (both whole) |
| BITSAT | Score / 390 | −130 … 390 (whole) |

The labels, placeholders, limits and the sentence for a wrong number are in `SCORE` (`rankProfile.ts`), the same ones
every tool uses. `problemOf(profile)` returns the first wrong box and the exam page that shows it.

When a student gives more than one JEE Main number, the most exact one is used: **Rank, then Percentile, then Marks**.
The form says so as soon as two boxes are filled (§5).

## 3. What Save writes into each tool

| Tool | From the profile | Not touched |
|---|---|---|
| Rank predictor | JEE marks, COMEDK marks, paper type, category, PwD | the exam on screen |
| **Cut off** | category, Female, PwD, home state, paper type; per exam the most exact score **typed into the score box, not yet applied** (JEE: rank, else percentile, else marks; COMEDK: rank, else marks; BITSAT: score) | the exam on screen, College / Branch side, the chosen college and branch |
| Target marks | category, Female, PwD, home state | the exam and the chosen college |
| College predictor · JEE Main | marks, percentile and rank (all three boxes, see below), paper type, category, Female, PwD, home state | the branch filter |
| College predictor · COMEDK | marks and rank (both boxes) | the course filter |
| College predictor · BITSAT | score | campus and degree filters |
| College compare | uses the College predictor's category, Female, PwD and home state | the chosen colleges, the shortlist |
| Dream college | uses the same four for the marks a JEE dream needs | the dreams |

Two details that keep it honest:

- **An empty profile score never wipes a tool's score.** If the profile has no COMEDK number, the COMEDK form keeps
  what the student typed there. Category, Female, PwD, home state and paper type are always written (they always have a
  value).
- **When the profile has any JEE score, the College predictor's three JEE boxes are all replaced**, including the empty
  ones. Otherwise an old rank left in the form would silently win over the new marks.

After Save, every tool that is open reads its form again and shows it **open** (not collapsed), with the new values in
it. Answers already on screen are not recalculated by themselves: the student taps **Show** (Cut off: **Eligible
dikhao**). In Cut off the list goes back to the full table with the score waiting in the box.

## 4. Where it is kept

In the browser only (the app: phone storage). Keys and shapes, identical in `rankProfile.ts`:

| Key | Holds | Shape |
|---|---|---|
| `rank.profile.v1` | Meri details | `RankProfile`: `{ at, jee: { marks, pct, rank, level, category, female, pwd, state }, comedk: { marks, rank }, bitsat: { score } }` |
| `rank.estimate.v1` | Rank predictor | `EstimateForm` |
| `rank.cutoff.v1` | Cut off | `CutoffForm` |
| `rank.target.v1` | Target marks | `TargetForm` |
| `rank.form.v1` | College predictor · JEE Main | `CollegeForm` |
| `rank.comedk.v1` | College predictor · COMEDK | `ComedkForm` |
| `rank.bitsat.v1` | College predictor · BITSAT | plain text, the typed score |

- Numbers are kept as the text the student typed (`""` = not given). `at` = time of the last save, `0` = never.
- A tool reads its form as `{ ...toolDefaults, ...saved }`, so a form written before a new field existed still opens.
- Not synced between devices and not tied to the account. A student signed in on two devices has two profiles.
  (Dream college is the only Rank part stored on the account.)
- Do not send these values to analytics.

```ts
import { loadProfile, saveProfile, clearProfile, problemOf, profileLine, readForm, writeForm, SAVED } from "./rankProfile";

const profile = loadProfile();                           // EMPTY_PROFILE (category "GEN") when never saved
const next = { ...profile, jee: { ...profile.jee, marks: "200", rank: "7500" }, bitsat: { score: "280" } };
const bad = problemOf(next);                             // { exam, text } or null
if (!bad) saveProfile(next);                             // fills every tool's saved form
profileLine(loadProfile());                              // "JEE Main: 200 marks, rank 7,500 · General  |  BITSAT: 280"

const form = { ...CUTOFF_DEFAULTS, ...readForm(SAVED.cutoff) };   // a tool opening
writeForm(SAVED.cutoff, { ...form, category: "SC" });             // a tool saving its own edit: the profile stays as it was
```

`rankProfile.ts` was run against 19 checks of exactly these rules before it went into the pack.

## 5. The screen (`RANK/screenshots/01_…`, `NEW_meri_details_01` to `03`)

**Where.** Between the page header and the six tiles. Always visible on the Rank page, whichever tool is open.

**Closed, never saved** (`01_rank_tab_meri_details_bar_and_six_tools.jpg`): a one-row card with a person icon, the
title **"Apni details ek baar daalo"**, the line "Marks, percentile, rank aur category. Har tool mein pehle se bhare
milenge." and a light pill **+ Bharo**. The whole card is the button.

**Closed, saved** (`NEW_meri_details_03`): title **"Meri details"**, then the profile in one line (up to three lines
on a phone), e.g. `JEE Main: 200 marks, rank 7,500 · General  |  COMEDK: rank 30,000  |  BITSAT: 280`, and a pill
**✎ Edit**. Right after a save a green line stays until the bar is opened again:
"Save ho gaya. Har tool mein bhar diya; kisi bhi tool mein alag se badal sakte ho."

**Open** (`NEW_meri_details_01`, `02`): the card becomes a panel `MERI DETAILS` with a close button (closing without
Save changes nothing).

1. "Ek baar bharo, sab optional hai. Save karte hi ye har tool mein pehle se bhara milega; kisi bhi tool mein alag se
   badal sakte ho."
2. Switch **JEE Main · BITSAT · COMEDK** (it only changes which fields are on screen; Save saves all three).
3. The fields of that exam (§2), with one small line under them:

| Exam | The small line |
|---|---|
| JEE Main, one box or none filled | Jo pata hai wahi bharo, koi ek kaafi hai. |
| JEE Main, two or three filled | Ek se zyada bhare hain: sabse pakka number chalega. Pehle Rank, phir Percentile, phir Marks. |
| COMEDK | COMEDK mein sabki ek hi merit list hai, isliye category nahi lagti. Dono bhare ho to Rank chalegi. |
| BITSAT | BITSAT mein sirf score chalta hai: percentile, rank aur category nahi lagte. |

4. A wrong number: its sentence in the error colour, and the switch jumps to that exam. Nothing is saved.
5. Main button **Save karo**.
6. Only when a profile was saved before: the text link **"Meri details hatao"**. It forgets the profile; the tools
   keep whatever they hold.

The panel is neutral (a silver line on the black page; a chosen chip is white), not one of the six tool colours,
because it belongs to all of them. The Save button is the brand crimson `#B3172F` with white text.

## 6. Acceptance list

- [ ] The bar is on the Rank page above the tiles, for every tool, signed in or not.
- [ ] Every field is optional; Save with nothing typed still saves category, Female, PwD and home state.
- [ ] JEE Main category shows **General** until the student changes it with a chip.
- [ ] After Save, each of the six tools opens with the values of §3 and nothing else changed.
- [ ] Editing a value inside one tool does not change the bar's line, and does not change another tool.
- [ ] Saving the bar again overwrites the tools' values again.
- [ ] A profile with no COMEDK (or BITSAT, or JEE) score leaves that tool's own score in place.
- [ ] With marks and rank both given: the College predictor's card reads "Rank 7,500 …" and Cut off starts on the Rank chip.
- [ ] A wrong number shows its sentence and saves nothing.
- [ ] "Meri details hatao" empties the bar; the tools keep their values.
- [ ] The profile survives a reload; it is never sent to a server.

## 7. Questions that will come up

**Why not keep the tools tied to the profile all the time?** Students compare: "what if I get 220?", "what if I count
as OBC-NCL in my home state?". A live link would rewrite their profile every time they try a number. Starting values
give the convenience without that surprise.

**Why does Cut off not filter straight away after Save?** The student asked to see a college's cut-offs; the score is
optional there. It waits in the box, one tap away.

**Should it be stored on the account?** Not today. If the website wants that later, tell the app project so both sides
store it the same way.
