# 05 · Rank data

What the app server knows, where every number comes from, and how it stays current.

## 1. The rule: the data lives on the app server only

The website does **not** get a copy of the cut-off data, and must not make one. Every college, branch, closing rank,
seat count, fee and percentile curve reaches the website through the app server's API (`docs/03`), at the moment a
student asks.

Why:

- **One truth.** The app and the website always show the same number for the same student.
- **Renewed once.** When new cut-offs are published, the app server is updated and the website shows them the same
  minute, with no website release.
- **Nothing to maintain.** No CSV import, no database table, no yearly script on the website side.

This pack therefore ships no data files. `RANK/api_examples/` holds frozen sample answers for designing screens and
typing fields, never as a source of numbers.

If the website needs a list for its own pages (for example an SEO page per college), it calls `GET /rank/colleges`
(and the other endpoints) and caches the answer for a short time; it does not keep its own copy.

## 2. What is covered

| Exam | Coverage |
|---|---|
| JEE Main 2026 | 115 institutes: 32 NITs, 26 IIITs, 53 GFTIs, 4 JAC Delhi colleges (DTU, NSUT, IIIT-Delhi, IGDTUW) · 750 programs · 10,733 seat rows · 7 rounds (JoSAA R1–R5, CSAB Special 1–2; JAC R1–R4) |
| JEE Main 2025 (trend) | 8,425 seat rows of the JoSAA 2025 final round (R6) |
| JoSAA 2026 seat matrix | seats of 694 programs (all quotas and categories together) |
| COMEDK UGET 2026 | 151 colleges (148 with General Merit allotment) · 76 courses · 880 GM college-courses · 4 rounds · seats and yearly fee · 2025 final closing |
| BITSAT | 50 programs on Pilani (18), Goa (15), Hyderabad (17) · final cut-offs 2022–2026 |
| Percentile curves | NTA 2026 shift-wise percentile tables (19 shifts in 3 paper types) |
| Candidates | JEE Main 2026: 15,38,468 · COMEDK 2026: 1,29,000 |

JEE seat rows by quota: Home state 3,186 · Other state 3,526 · All India 2,963 · Delhi region 531 · Outside Delhi 395 ·
J&K 80 · Goa 38 · Ladakh 14.

## 3. Not covered, by design

- IITs and IISc (they admit through JEE Advanced).
- SPA (B.Arch / B.Planning) and the DASA quota.
- COMEDK's KKR (Kalyana Karnataka) quota rows.
- Categories other than the five (`GEN`, `EWS`, `OBC-NCL`, `SC`, `ST`) and PwD.

## 4. Official sources

| Data | Source |
|---|---|
| JEE Main 2026 result, category counts and cut-offs | NTA press note of 20 April 2026 |
| Shift-wise marks vs percentile | NTA 2026 shift data (one shift, 8 Apr S2, from Careers360 bands) |
| JoSAA 2026 Round 1–5 opening/closing ranks | `josaa.admissions.nic.in` → Opening & Closing Rank |
| CSAB Special 2026 Round 1–2 | `admissions.nic.in/csabspl` |
| JAC Delhi 2026 Round 1–4 | `jacdelhi.admissions.nic.in/or-cr` |
| JoSAA 2025 final round | JoSAA opening/closing rank archive |
| JoSAA 2026 seat matrix | JoSAA seat matrix |
| COMEDK 2026 Round 1–4 cut-offs, 2025 cut-offs, 2026 seat & fee matrix | `comedk.org` PDFs (every number parsed from the official PDFs) |
| COMEDK marks vs rank | three public analyses: CollegeDekho 2026, Shiksha 2026, the 2024–25 trend (PW, Careers360) |
| BITSAT cut-offs 2022–2026 | `admissions.bits-pilani.ac.in/FD/BITSAT_cutOffs.html` |

`GET /rank/meta` returns the exact source links (`sources`, `comedk.sources`) for the website's "Data" line.

## 5. What the official bodies did not publish

The server says so in plain words instead of guessing (`meta.missing`):

- JAC Delhi never published the closing ranks of its Upgradation and Spot rounds (those cells are empty, `unpublished: true`).
- IIIT-Delhi's Round 1 sheet came in a different format; its Round 1 rank is not included.
- COMEDK publishes no marks-to-rank table: marks → rank is always a range of three analyses, with a sentence saying so.
- JoSAA publishes no college fee; the compare screen says where to find it.

## 6. Checked how

When the data was last rebuilt, all 58,382 in-scope official JoSAA/CSAB rows were compared with the server's copy:
every one matched, and the rebuilt file was identical. Every numeric cell of the four COMEDK round PDFs was parsed
(R1 1,191 · R2 181 · R3 547 · R4 368 cells).

## 7. Renewal each year

Done by the app project only:

1. new official files are fetched and parsed by the app server's data builders;
2. the rebuilt data is checked row by row against the official pages;
3. the app server is redeployed.

From that minute the website shows the new numbers. Field names do not change, so the website needs no change either.
Watch `meta.note`, `meta.sources` and `y25_label`: their words follow the new year by themselves.
