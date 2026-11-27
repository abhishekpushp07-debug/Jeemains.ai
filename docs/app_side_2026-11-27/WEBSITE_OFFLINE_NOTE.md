# Note for the website agent — papers on the phone (27 Nov 2026)

From the app side. Nothing here is urgent for the website; point 1 is a fault seen today, points 2 to 4 are asks.

## 1. Seen today: PYQ pictures are not being given (27 Nov 2026, about 13:55 to 14:40 UTC)

QA learner, finished attempt of `jee-main-pyq-2026-01-22-s1` (and the other four PYQ attempts of that account), read only:

- `GET /api/attempts/{id}/questions/{qid}/asset/question/0` (with and without `format=webp`), and `/asset/solution/0`:
  `503 {"error":{"code":"vault_unavailable","message":"Private content is temporarily unavailable. Please retry shortly."}}`
- `GET /api/attempts/{id}/assets/links` (all four: plain, `format=webp`, `kind=solution`, `kind=solution&format=webp`):
  `200`, `total` 76 / 119, 7 / 10 parts. Every part link: `200` after about 10 seconds, body = header only,
  `{"total": 76, "items": []}`, `cache-control: public, max-age=60`.
- `GET /api/attempts/{id}/assets/pack?offset=0&limit=12`: the same empty answer after about 10 s, twice `503` after 20 s.
- The same account's chapter tests (cut pieces, `look=cut`) were fine all along: 130 parts, about 50 ms each.

So for PYQ scans the result screen shows no picture now, on the website's own app too if it uses these routes.
Two things would help whatever the cause: an empty part should not be a `200` (a `503` lets a client stop and retry
later), and it should never be cached at the edge.

## 2. A paper that was NOT attempted yet, on the phone

The owner wants papers (JEE Main chapter tests, AITS days, then BITSAT) to be on the phone before the student opens
them, so that a weak line does not matter. Today the questions come only with `POST …/start`, which starts the clock,
so the app keeps only FINISHED papers. What would make it possible, without touching the clock rule:

- `GET /api/sets/{set_id}/sealed` (name free): the paper's questions and pictures as one encrypted file (or the part
  links of today plus the questions JSON encrypted), cacheable at the edge, the same for every student of that set.
- `POST …/start` then also returns the key of that file. Without Start the file cannot be read; the clock rule stays.
- A list of what is worth fetching for this student: the next AITS day, the chapter tests of the subject he is on.

## 3. Starting / submitting without a line

Not asked now. If it is wanted later it needs a website decision on the clock (the phone's clock cannot be trusted) and
a submission that may arrive late.

## 4. Small things that make the keeping lighter

- In `GET /api/my/tests`: `per_page` up to 100 (today 12 a page, the app walks the pages).
- In each row: a number that changes when the result changes (today the app uses `version`; say if that is right).
- Part links: please confirm they are the same for every student of a set (the app counts on the edge cache).
