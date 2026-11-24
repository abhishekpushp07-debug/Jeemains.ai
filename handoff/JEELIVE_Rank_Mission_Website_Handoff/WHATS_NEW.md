# What is new in this pack

This pack replaces the earlier Rank + Mission pack. Three things are new, a few small things changed, nothing that
worked before was taken away from the server.

| | | Read |
|---|---|---|
| **NEW** | **Cut off**: a Rank tool. Pick a college or a branch, see every round's cut-off, then filter by your own score to Safe / Likely / Borderline. JEE Main, COMEDK, BITSAT. | `docs/11_CUT_OFF_NEW.md` |
| **NEW** | **Meri details**: the student's score and category typed once at the top of the Rank page, used as starting values by all six tools. | `docs/12_MERI_DETAILS_NEW.md` |
| **NEW** | **Scorecard rank**: every JEE Main form now also takes the All India Rank from the scorecard, beside marks and percentile. | `docs/03` §0, `docs/04` §3 |

## 1. The six tools now

| # | Tile | Was |
|---|---|---|
| 1 | RANK PREDICTOR | the same |
| 2 | **CUT OFF** — `college / branch` — NEW | PERCENTILE SE RANK |
| 3 | TARGET MARKS | the same |
| 4 | COLLEGE PREDICTOR | the same, plus a Rank (CRL) field |
| 5 | COLLEGE COMPARE | the same |
| 6 | DREAM COLLEGE | the same |

The "Percentile se rank" tile and screen are gone from the app. A student with only a percentile now types it into
Cut off's score box or the College predictor's form; both show the rank it stands for. `POST /rank/percentile` still
answers (older app versions call it), but no current screen uses it: **do not build a page for it**.

## 2. On the server

| Change | Detail |
|---|---|
| New endpoint | `GET /rank/cutoff/options`: the college and branch pickers of the three exams |
| New endpoint | `POST /rank/cutoff`: the cut-off table, with or without a score |
| New optional field | `rank` (1 … 20,00,000) in the JEE form of `POST /rank/predict`, `/rank/college` and `/rank/pdf/jee`. Most exact wins: rank, then percentile, then marks |
| New answer field | `source` (`"marks"`, `"percentile"` or `"rank"`) in the result block |
| New wordings | the result `summary` can start "Rank 7,500 · …"; a near miss `gap` can read "rank lagbhag 323 aur upar chahiye"; `check` can read "Rank aur percentile aapas mein mel nahi kha rahe, ek baar check kar lo." |
| Changed sentence | an empty JEE form now answers `422 "Marks, percentile ya rank mein se koi ek daalo."` (was "Marks ya percentile mein se koi ek daalo.") |
| PDF name | with a rank the JEE list PDF is named `JEELIVE-JEE-colleges-rank-7500.pdf` |

Everything else answers exactly as before; field names only grew.

**Live or development?** The two new endpoints and the `rank` field are on the development server today and reach the
live server with the app project's next publish. `MANIFEST.json` → `cut_off_on_live` records which it was when this pack
was built. `CONNECT/connect_check.py` prints `WAIT` (not `FAIL`) for the 8 new checks on a server that does not have
them yet, and `PASS` once it does.

## 3. In `CONNECT/`

| File | Change |
|---|---|
| `backend_fastapi/jeelive_app_connect.py` | forwards the two new paths (`cutoff/options` is cached like the other lists). **Replace your copy**, or add `"cutoff/options"` to `RANK_GET` and `"cutoff"` to `RANK_POST` |
| `frontend_web/jeeliveApp.ts` | `rank.cutoffOptions()`, `rank.cutoff()` and their types; `rank` in `FormBody`; `source` in `RankResult` |
| `frontend_web/rankProfile.ts` | **new file**: Meri details for the browser (limits of every score, save / load / clear, each tool's saved form) |
| `connect_check.py` | 29 public checks (was 21): 8 new ones for Cut off and the scorecard rank |
| `curl_examples.sh` | 10 new lines |
| `openapi_rank_mission.json` | now includes the two new paths |

## 4. Elsewhere in the pack

| Folder | Change |
|---|---|
| `docs/` | two new documents (11, 12); 01, 02, 03, 04, 06, 09 and 10 updated |
| `RANK/api_examples/` | 12 new files, `23_…` to `34_…` (Cut off for every exam, the scorecard rank, what the server refuses) |
| `RANK/screenshots/` | new `01_…` (the page top with the Meri details bar and the CUT OFF tile); 20 `NEW_cutoff_…` (19 and 20 are the additions of §6); 3 `NEW_meri_details_…`; the two "Percentile se rank" screens removed |
| `RANK/code/server_reference/` | `rank_cutoff.py` (new), `rank_predictor.py` (rank as a score), `tests/test_rank_cutoff.py` (the server's own proof) |
| `RANK/code/app_reference_ui/src_rank/` | `Cutoff.tsx`, `CutoffList.tsx`, `ProfileBar.tsx`, `profile.ts` (new); `PercentileRank.tsx` removed; `ToolGrid.tsx`, `InputCard.tsx` and the tools that read the profile updated |

## 5. If the website was already built from the earlier pack

1. Replace the connector file and the browser client; add `rankProfile.ts`.
2. Run `python CONNECT/connect_check.py https://<website>/api --website`.
3. Change the second tile to **CUT OFF** and build the tool from `docs/11`.
4. Remove the "Percentile se rank" page (or keep its address and send visitors to Cut off).
5. Add the **Rank (CRL)** field to the College predictor's JEE form, with the line under the three boxes (`docs/06` §6).
6. Add the **Meri details** bar above the tiles (`docs/12`), and make every tool read its saved form again after a save.
7. Work through the two new acceptance lists (`docs/11` §11, `docs/12` §6).

## 6. Added after the first Cut off build (23 Nov 2026, second pass)

Nothing was renamed or removed. If the website already took the first Cut off pack, these are the only differences.

| | What | Read |
|---|---|---|
| **NEW** | **Last-year arrow** on every Cut off card: each row of `POST /rank/cutoff` carries `trend` = `{dir, prev, label}` or `null` | `docs/11` §13.1, `docs/03` §13.3 |
| **NEW** | **Compare toggle** on every Cut off card: each row carries `save`, the row as one shortlist item (the same shortlist as the College predictor's bookmark) | `docs/11` §13.2 |
| **NEW** | **Cut off PDF**: `POST /rank/pdf/cutoff`, body = the body of the list on screen; "PDF WhatsApp" and a PDF button under the heading | `docs/11` §13.3, `docs/03` §12 |
| **NEW** | **Who builds what**, the app's All India series changes, and three facts to confirm | `docs/13_APP_UPDATE_AITS_AND_WHO_BUILDS_WHAT.md` |
| **NEW** | **CEO dashboard hand-off**, including the one export the website has to add (`GET /api/ceo/signups`) | `docs/14_CEO_DASHBOARD.md` |

In `CONNECT/`:

| File | Change |
|---|---|
| `backend_fastapi/jeelive_app_connect.py` | forwards `pdf/cutoff`. **Replace your copy**, or add `"pdf/cutoff"` to `RANK_PDF` |
| `frontend_web/jeeliveApp.ts` | `trend` and `save` on `CutoffRow`; types `CutoffTrend`, `SavedRow`; `toCompareItem(save)`; `rank.pdf("cutoff", body)` |
| `connect_check.py` | the college check also proves `trend` and `save`; with `--pdf` one more check draws the Cut off PDF (31 checks in all with `--pdf`) |
| `curl_examples.sh` | one more PDF line |

Elsewhere: `RANK/sample_pdfs/sample_cutoff_*.pdf` (4 files with their request bodies); the answers `24_…` to `32_…` in
`RANK/api_examples/` now show `trend` and `save`; screenshots `NEW_cutoff_19` and `NEW_cutoff_20`; all Cut off
screenshots were retaken because every card has a new foot line; `tests/test_rank_cutoff.py` grew from 25 to 33 checks.

One rule changed inside the server and is worth knowing: the JEE Main arrow compares the **last JoSAA round of 2026 with
2025's final round on the same seat path**, never a CSAB closing.

As before, all of this is on the development server today and reaches the live server with the app project's next publish.
