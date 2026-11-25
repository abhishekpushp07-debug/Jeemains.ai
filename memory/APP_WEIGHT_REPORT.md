# JEELIVE app — what makes it heavy, measured (24 Nov 2026, night)

Owner's question: "I have built almost a dozen small features. Are they making the app heavy or slow? Is there a way
(smaller packets, caches, Redis…) so new things never become a liability?" Owner's choice: **measure, then show me a list.**

Everything below was measured on the app as it is tonight (Android release JS bundle made with `expo export`, bytecode
off). What could NOT be measured here: the final APK / Play Store download size and speed on a real phone (no Android
build can be made on this machine). Sizes are raw file sizes; the store compresses them further.

## 1. The short answer
- **The small features are not what makes the app heavy.** All of them together are about **195 KB of 5,058 KB** of the
  app's code (3.8 %). The lightest costs 2.7 KB, the heaviest 29 KB. Removing every one of them would not be felt.
- **Where the weight really is:** the libraries the app stands on (66 % of the code), the maths fonts (7 %), one icon
  font (1.3 MB), the pictures (1.7 MB, mostly Rapid Fire's arena, squads and avatars) and Rapid Fire's sounds (0.4 MB).
- **Tonight the app got lighter, not heavier:** the code went from 5,255,333 to 5,179,835 bytes (−75 KB) although three
  AITS additions (+21 KB) were added, because a 95 KB website export that was carried inside the app for three colours
  is no longer carried.
- **Redis is NOT in the app today** (corrected 24 Nov, late night: an earlier version of this report said it was). It
  was added on the server on 27 Oct for public Rapid Fire lists and taken out again on 14 Nov during a deploy health
  check (commit `923c12c`); the server now keeps those lists in its own memory for a short time
  (`backend/metadata_cache.py`), which needs no extra service. Redis would add nothing to the phone and cannot make the
  APK smaller, so it is not being put back. The phone has its own small cache (2 MB limit, 64 answers, cleared when
  the account changes). No change needed there.

## 2. What the phone carries (measured)
| Part | Size | Share |
|---|---:|---:|
| **Code (JS) in total** | **5,058 KB** | 100 % |
| Libraries + runtime (React Native 672, Reanimated 639, Expo Router 503, KaTeX 266, gesture handler 193, icon name list 182, SVG 123, worklets 105, keyboard 102 …) | 3,326 KB | 65.7 % |
| The app's own code | 1,733 KB | 34.3 % |
| – maths fonts for offline solutions (`katexCss.ts`, already the smallest format) | 361 KB | 7.1 % |
| – all screens (`app/`) | 325 KB | 6.4 % |
| – Rapid Fire (`src/rapid`) | 289 KB | 5.7 % |
| – Rank tab (`src/rank`) | 192 KB | 3.8 % |
| – Analysis (`src/analysis`) | 119 KB | 2.3 % |
| – AITS series parts (`src/components/series`) | 68 KB | 1.3 % |
| – Dream College 50 · Misfire 34 · Mission 23 | 107 KB | 2.1 % |
| **Files packed into the app** | **3,604 KB** in 139 files | |
| Pictures (80, all already WebP) — Rapid Fire arena 1,017 KB (48), Cheer Squad 353 KB (12), avatars 338 KB (18), other 30 KB (2) | 1,737 KB | |
| Fonts (8) — **icon font 1,277 KB**, Figtree ×5 and Roboto Mono ×2 about 23 KB each | 1,441 KB | |
| Sounds (25, Rapid Fire) | 404 KB | |
| PNG (24, app icon / splash sizes) | 22 KB | |

Requests (web preview, QA learner): Home after sign-in **15** (3 of them are the sign-in itself); opening the series
page **4**; opening the AITS Leaderboard **5**; the Rank graph the first time **1 per released day** (8 with the
stand-in days), **0** on reopening; the "Aap vs" sheet **0**.

## 3. The list: every small feature, what it weighs, what I recommend
Code size = the feature's own files in the release bundle. "Runs when" = when it costs the phone anything.

| # | Feature | Code | Own pictures / sounds | Runs when | Recommendation |
|---|---|---:|---|---|---|
| 1 | Champions Wall (Rapid Fire) | 6.2 KB | none | its tab is open | Keep |
| 2 | Cheer Squad | 28.7 KB | 353 KB pictures | squads screen / a cheer arrives | Keep. Its pictures are its real weight; do not add more squads' art without need |
| 3 | Crown share + celebration | 15.0 KB | none | after a crown | Keep |
| 4 | Cup Night + reminder | 15.8 KB | none | cup screens | Keep |
| 5 | WhatsApp match links | 6.6 KB | none | on share / on opening a link | Keep |
| 6 | Mission "Creator's Letter" card | 23.0 KB | none | Mission tab | Keep |
| 7 | Dream progress chart | 7.5 KB | none | Dream section | Keep |
| 8 | Dream Unlocked celebration | 16.0 KB | none | once, when a dream is crossed | Keep |
| 9 | Dream share card | 3.1 KB | none | on share | Keep |
| 10 | College / Branch compare | 19.3 KB | none | Rank tab tool | Keep |
| 11 | Cut off tool + "Meri details" | 26.4 KB | none | Rank tab tool | Keep |
| 12 | Once-a-day scenes and sounds, Daily share | 21.6 KB | uses Rapid Fire's 404 KB of sounds | Rapid Fire lobby / result | Keep |
| 13 | AITS Leaderboard | 22.3 KB | none | its screen | Keep |
| 14 | Naam badlo | 2.7 KB | none | sheet open | Keep |
| 15 | Rank share + Streak share (one shared screen) | 15.8 KB | none (drawn in code) | share screen | Keep |
| 16 | Rank journey graph (new) | 5.9 KB | none | only when "Rank" is tapped | Keep |
| 17 | "Aap vs" sheet (new), with "Har din mein yahi naam dhoondo" | 3.2 KB | none | sheet open, no request | Keep |
| 18 | Shine (gloss, running edge, glint) + Smooth Mode | 8.6 KB | none | wherever a shiny card is on screen | Keep. It is the one feature that costs the phone while it is on screen; Smooth Mode calms it on a slow phone and only cards on screen move |
| | **All of the above** | **≈ 247 KB (4.9 %)** | | | |

(Rows 1–11 and 14–17, the "extras", are the 195 KB / 3.8 % quoted above; Misfire, 34 KB, is a study tool and not counted as a small extra.)

**So: nothing on this list needs removing for weight.** If the owner wants fewer things on screen for the *student's*
sake, that is a product choice, not a size one; say which and they go.

## 4. The real savings, in order of size
| What | Saving | Risk | Status |
|---|---:|---|---|
| Website export no longer carried inside the app (it was read at every start for 3 colours) | **−95 KB code** | none: the 3 values are word-for-word the same; a script checks them against the export (`tests/tools/website_tokens.py`) | **Done tonight** |
| Icon font: the app ships all 7,448 Material icons (1,277 KB; the icon package's own build files also copy the font into Android and iPhone builds, which would be a second copy — read in its build files, not seen in a built APK) but uses about 250 names | about **−1.2 MB per copy** and −180 KB code | **Not safe to do blind.** (a) It changes how every icon in the app is loaded and cannot be checked without a real Android build; (b) the Rapid Fire store takes icon names from the server (`backend/shop.py`), so a cut-down font would show an empty box for any icon added on the server later | **Not done. Owner's decision, with a build in hand** |
| Maths fonts (20 KaTeX faces, 340 KB) | up to −120 KB by dropping rare faces | a solution that uses `\mathcal`, `\mathfrak`, sans or typewriter letters would look wrong | Not done; not recommended |
| Pictures (1.74 MB) and sounds (0.4 MB) | — | already WebP / m4a; the owner asked that card artwork is never replaced. Only the 48 arena pictures the app uses are packed (the folder holds more) | Leave |
| Series data is asked again each time a series screen opens (3 small requests) | fewer requests | a short "still fresh" window could show an old state right after a paper is handed in | Not done; low value |
| `frontend/public/jeelive_handoff.zip` (2.6 MB) | — | it is NOT in the phone app (`.easignore` leaves it out); it only sits in the web export | Leave; owner's file |
| `frontend/package-lock.json` beside `yarn.lock` | — | owner's word needed (earlier note) | Left |

No package was found that only adds weight: of the eleven with no direct import in the app's code, ten are needed by
Expo Router, Reanimated, the web preview or the build (`expo-asset`, `expo-linking`, `react-native-screens`,
`react-native-worklets`, `react-dom`, `react-native-web`, …).
`expo-web-browser` has no import in the app's code; it is small and listed as a build plugin, so it was left.

## 5. The rules every new feature now follows (so the app stays light and nothing breaks)
1. **No new package** unless nothing already installed can do the job. A native package is carried by every phone for
   ever. (Tonight's three additions: none.)
2. **No new picture or sound files for decoration.** Cards, flames, graphs and share pictures are drawn in code
   (gradients, SVG, the icon font) — the Streak picture is 5.8 KB of code and no image.
3. **Inside what is already there**, and **asleep until opened**: a feature asks the website only when the student
   opens it, and keeps what it got (the Rank graph: one request per day once, then at most two).
4. **The website's numbers are the only numbers.** Nothing is added up or guessed on the phone (no invented overall
   Rank, no matching of students by name).
5. **Weigh after every change:** `python3 /app/tests/tools/weight.py build` prints this report's numbers and stops with
   an error if the code grew more than 2 % or the files more than 3 % over the kept numbers
   (`tests/tools/weight_baseline.json`, saved tonight: code 5,179,835 bytes, files 3,690,544 bytes).
6. **Walk the whole app after every change:** `tests/smoke_all.py` opens 22 screens as the QA learner (read only) at
   390 and 320 wide and reports any screen that does not come up, shows the red error screen, throws, or scrolls
   sideways. Tonight: 22 of 22 fine at both widths.
7. **TypeScript and ESLint clean** before anything is called done; the testing agent for anything larger than a tweak.
8. **One small pocket at a time**, each one checked before the next begins.
