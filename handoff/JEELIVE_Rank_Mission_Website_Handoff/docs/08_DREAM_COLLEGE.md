# 08 · Dream college

The sixth Rank tool: up to five dream seats per exam, measured against the student's own mock scores, the same on
every phone and the website. Screenshot: `RANK/screenshots/25_dream_college_meter.jpg`. Code:
`RANK/code/app_reference_ui/src_dream/`, `RANK/code/server_reference/dream.py`.

## 1. What the student sees

- **Add** from any college card's **🎯 Dream college** button in the College predictor; the Dream tile shows the count.
- **Dream College Meter** (`DreamMeter.tsx`): header `DREAM COLLEGE METER · JEE MAIN`, title **"Kitne marks door?"**,
  `2/5`; purple outside (header band, border, glow), deep black inside; the latest mock score with the change since the
  one before; rows alternate royal blue and teal, each with a diamond; per dream: college, branch, marks needed
  ("need"), the easy–tough range, and how many marks the latest mock is away.
- Empty state: "Apne 5 dream college + branch chuno" / "College predictor mein kisi bhi college card par 🎯 Dream college
  dabao. Har mock ke baad yahan dikhega kitne marks door ho." and a **Dream college chuno** button.
- Foot: "Marks normal paper ke hisaab se, 2026 cutoff par estimate. Guarantee nahi."
- **Progress chart** (`ProgressChart.tsx`): the student's recent mock scores against each dream's line (up to 5 lines:
  `#9DB6FF`, `#5EF0D6`, `#FFC94D`, `#FF8FC7`, `#C6F36B`).
- Share (`DreamShare.tsx`) as a picture with the student's Mission link.

The app also plays a short "Dream Unlocked" celebration when a mock first reaches a dream. It uses the game's art and
is **not part of this pack**; the website can show a simple message instead. The `cheered` list (§3) still tells every
device that the moment has been marked, so it is not repeated.

## 2. How "need" is worked out (when the dream is pinned)

From the same server answers as Target marks (`need.ts`):

| Exam | need | range |
|---|---|---|
| JEE Main | marks on a normal paper for the seat's round closing, for the student's category, gender, PwD and state (`POST /rank/target/jee`, the row matching the card's `path`) | [easy, tough] marks |
| COMEDK | middle marks for the final round's GM closing (`POST /rank/target/comedk`) | [low, high] |
| BITSAT | the 2026 cut-off itself | none |

`note` records what it was based on: `"R5 closing 13,994 CRL"`, `"R4 closing 2,310 GM"`, `"BITSAT 2026 cutoff"`.

## 3. API (signed-in; through the connector)

| Website route | App server | Body | Answer |
|---|---|---|---|
| `GET /api/dream` | `GET /rf/dream` | | `{dreams, mocks, cheered}` |
| `PUT /api/dream/dreams` | `PUT /rf/dream/dreams` | `{dreams: Dream[], base: string[]}` | `{dreams}` (the account's list after merging) |
| `POST /api/dream/mocks` | `POST /rf/dream/mocks` | `{mocks: Mock[1..30]}` | `{ok: true}` |
| `POST /api/dream/cheered` | `POST /rf/dream/cheered` | `{ids: string[1..15]}` | `{ok: true}` |

Shapes:

```ts
Dream = { id: "jee-230" | "comedk-E095|CY" | "bitsat-Pilani-cs", exam: "jee"|"bitsat"|"comedk",
          college: string /*≤160*/, branch: string /*≤200*/, need: number /*−100…400*/, range?: [number, number],
          note: string /*≤200*/, at: number /*ms*/ }
Mock  = { id: string /*≤64*/, exam, score: number, max: number, raw: number, rawMax: number, title: string, at: number }
```

Rules: at most 5 dreams per exam; an id twice → `400 "Ek college do baar hai."`; more than 5 for an exam →
`400 "Har exam ke 5 dream college hi ho sakte hain."`; the newest 30 mocks are kept, a mock sent again replaces its copy.

## 4. The merge rule (two devices never wipe each other)

A device sends its list **and** `base` = the ids of the account list it last saw. The server applies only that
device's changes to the account's current list:

- a dream in `base` but not in the device's list → removed (the student removed it here);
- a dream not in `base` → added, while that exam has a free slot;
- dreams added elsewhere meanwhile → kept;
- `base: []` (never synced) → the device's dreams are only added, never removed.

Two saves at the same moment retry on the latest revision (up to 10 times), else
`503 "Abhi bahut badlav ek saath aa rahe hain. Thodi der mein phir try hoga."` — retry later.

## 5. Website flow

1. On sign-in, `GET /api/dream`; keep the list in the page and in local storage for offline viewing.
2. On add/remove, update locally at once, then `PUT /api/dream/dreams` with `base`; replace the local list with the answer.
3. When the website shows a released full mock result, `POST /api/dream/mocks` with it (scores on the exam's scale).
4. Signed out: the Dream tile shows a sign-in prompt; nothing is stored on the server.
