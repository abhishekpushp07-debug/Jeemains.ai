# 04 · Rank algorithms

How the app server turns a student's numbers into ranks, tags and targets. Every rule below runs **only on the app
server**. This document exists so the website team understands the answers and can explain them to students; it is not
a recipe to rebuild them. The website calls the server and shows what comes back (one source = the app and the website
never disagree).

The reference code is in `RANK/code/server_reference/` (read-only). Worked numbers below come from the server on the
day this pack was built.

## 1. JEE Main: marks → percentile

NTA publishes, for every 2026 shift, the marks that reached certain percentiles. The 19 shifts are grouped into three
paper types by how many marks the same percentile took:

| Paper type | Shifts |
|---|---|
| Tough | 22 Jan S2, 21 Jan S1, 23 Jan S2, 8 Apr S2, 6 Apr S1, 2 Apr S2 |
| Normal | 23 Jan S1, 21 Jan S2, 24 Jan S1, 4 Apr S2, 2 Apr S1, 4 Apr S1, 5 Apr S2 |
| Easy | 24 Jan S2, 28 Jan S2, 6 Apr S2, 22 Jan S1, 28 Jan S1, 5 Apr S1 |

Each type becomes one marks → percentile curve. A student's marks are placed on the curve by straight-line
interpolation between its two neighbouring points, clamped to 0…100.

180 marks → Tough 99.3667, Normal 99.1154, Easy 98.7692.

The student chooses the type ("How was your paper?"). There is deliberately **no shift picker**: next year's shifts will
not match 2026 dates.

## 2. Percentile → All India rank (CRL)

The plain formula `rank = (100 − p) / 100 × N` (N = 15,38,468 candidates) overshoots: NTA's own count at the General
cut-off (93.4123549 percentile → CRL 96,873) is 4.4 % below it. The server corrects with a factor `k` that is exactly
1 at the top, exactly 0.95584 at the General cut-off, and moves in straight lines between and below:

```
x = 100 − p                       x0 = 100 − 93.4123549
k = 1 − (1 − K) · x / x0          when x ≤ x0
k = K + (1 − K) · (x − x0) / 93.4123549   otherwise         (K = 96873 / (x0/100 · N) = 0.95584)
CRL = round(k · x / 100 · N), clamped to 1…N
```

99 percentile → k 0.99330 → CRL 15,282.

Percentile from a rank is the reverse, found by bisection (50 steps).

## 3. The student's range

A rank from marks is never one number: ties and the paper's difficulty move it. The server makes a band around the
middle rank `r`:

```
width w = min(cap(r), max(4, round(r × 10 %)))      from marks
width w = min(cap(r), max(4, round(r × 2 %)))       from a percentile (NTA's number is exact; only ties move it)
cap(r)  = 200 below rank 2,000 · 500 below 10,000 · 1,000 above
best = max(1, r − w/2)      worst = best + w
```

180 marks, normal → r 13,529, w 1,000 → CRL **13,029 – 14,029**, percentile 99.08 – 99.15 (the percentile range is kept
at most 0.5 wide). The `spread` sentence adds the tough and easy ranks for the same marks (9,702 and 18,779).

## 4. Category and PwD rank

NTA publishes each category's total and how many of it passed its own cut-off, but no table of category ranks. The
server spreads each category along the CRL in three bands:

| Band (CRL) | Share of that category per CRL position |
|---|---|
| 1 – 96,873 (above the General cut-off) | a typical share: EWS 13 %, OBC-NCL 27 %, SC 4.5 %, ST 1.3 % (estimate) |
| 96,873 – the category's own cut-off CRL | NTA's count of that category above its cut-off ÷ the band's width |
| beyond | the rest of the category ÷ the rest of the list |

Category cut-off CRLs: EWS 2,59,977 · OBC-NCL 2,82,261 · SC 5,38,346 · ST 7,20,042.
Category rank = sum of (width × share) up to the student's CRL. CRL 20,000 → OBC-NCL rank 5,400.
PwD rank = rank × 0.312 % (PwD candidates ÷ N). Every category and PwD number is labelled an estimate.

## 5. Which seats the student may take

A seat row is (program, quota, category, PwD, female-only). The student may take it when **all** hold:

- category is OPEN, or the student's own category;
- PwD seat only with `pwd`, female-only seat only with `female`;
- quota: `AI` All India always · `HS` home state = the institute's state · `OS` other state = any other state ·
  `DL` Delhi region only for state Delhi · `OD` outside Delhi only for other states · `GO` / `JK` / `LA` only for Goa,
  Jammu & Kashmir, Ladakh.

For each program the server keeps the student's **easiest** open path (largest closing rank relative to the student's
rank), and names it (`path`). The college sheet can show other paths too; a path the student cannot take comes with a
`blocked` sentence and no green cell.

## 6. Tags: Safe, Likely, Borderline

Against a seat's closing rank `c` (on the right rank type: CRL, category rank or PwD rank) and the student's
`best ≤ mid ≤ worst`:

```
c < best                       → out of reach (no tag)
c ≥ worst  and  c ≥ 1.15 × mid → Safe
c ≥ worst                      → Likely
best ≤ c < worst               → Borderline
```

With best 9,000, mid 10,000, worst 10,500: 8,999 none · 9,000 Borderline · 10,499 Borderline · 10,500 Likely ·
11,499 Likely · 11,500 Safe.

- **Which closing rank:** the largest over JoSAA R1–R5 (JAC: R1–R4). CSAB Special rounds count too, but because they
  fill leftover seats on CRL, a CSAB-only chance is at most Borderline.
- **The list of 50:** all seats in reach sorted by demand (how early in the counselling they fill); then up to 20
  Borderline, 15 Likely and 15 Safe are taken, so every student sees dream, fair and safe picks together; free places are
  filled in demand order. Each filter chip makes its own 50.
- **Near misses:** seats closing within 10 % above the student's best rank. The 5 most wanted are shown with what it would
  take: marks needed for that closing rank − the student's marks (at least +1), or the percentile difference.

## 7. Round ladder (college sheet)

For each round: inside = `close ≥ the student's best`. The sheet's sentence uses one rule everywhere:

- first round where `close ≥ worst` → "aapki rank R3 se andar aati hai";
- else first round where `close ≥ best` → "R4 se borderline, aapki range ke andar par pakka nahi";
- else → "aapki rank kisi round ki closing rank tak nahi pahunchi".

CSAB cells always compare against the CRL. JAC Delhi's Upgrade and Spot rounds were never published and show as such.

## 8. Target marks

For each branch: take the closing rank of the student's easiest open path, turn it into the CRL it needs (category and
PwD ranks converted back with §4), into a percentile (§2), and into marks on each paper type (§1), rounded up. CSAB and
JAC close on CRL directly. NIT Rourkela, Computer Science, Bihar, General → 217+ marks on a normal paper.

## 9. COMEDK

- **Marks → rank.** COMEDK publishes no marks–rank table. Three public analyses are each interpolated in log(rank).
  The student's range is the lowest to the highest of the three; the middle estimate is their median.
  110 marks → 850 / 2,300 / 3,200 → **850 – 3,200**, mid 2,300.
- **From a rank card rank** `r`: exact; a small band `r … r + max(50, 5 % of r)` only marks seats closing just behind it as
  Borderline.
- **Seats:** General Merit (All India) only. Closing rank of a seat = the largest over R1–R4; demand = the smallest.
- **Tags:** the same rule as §6 with best/mid/worst from above. List of 50 and near misses as JEE (near = within 15 %).
- **Marks needed** for a closing rank: the fewest marks whose middle estimate reaches it.

## 10. BITSAT

No category quota; one cut-off per program decides everything. With `d = score − 2026 cut-off`:
`d ≥ 10` Safe · `d ≥ 0` Likely · `−5 ≤ d < 0` Borderline · else no tag (`near` when at most 20 short).
Safe target = cut-off + 10, because cut-offs move 10–20 marks a year.

## 11. College vs college

For each college: the number of branches, the easiest branch (fewest marks needed, normal paper), the toughest, the
Computer Science branch needing the most marks, seats (JoSAA seat matrix, all quotas; COMEDK GM) and the fee range
(COMEDK only; JoSAA publishes no college fee). JEE marks use the student's own easiest seat path (§8).

## 12. Speed

All data is held in memory; a JEE list touches about 10,700 seat rows in a few milliseconds. The last 512 different
forms are remembered, so a page change or a filter tap is almost free.
