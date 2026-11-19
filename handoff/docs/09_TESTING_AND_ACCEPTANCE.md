# 09 · Testing and acceptance

How to prove the website is connected and behaves like the app.

## 1. The connection check

```bash
python CONNECT/connect_check.py                                   # the live app server: 21 checks (Rank + Mission)
python CONNECT/connect_check.py --pdf                             # + the 7 PDFs
python CONNECT/connect_check.py https://<website>/api --website   # through the mounted connector
JEELIVE_ACCESS_COOKIE='<access_token cookie>' python CONNECT/connect_check.py https://<website>/api --website --pdf
```

Expected on the day this pack was built (live server): `ALL 21 CHECKS PASSED`, with the signed-in checks skipped.
With a real signed-in session the Mission and Dream college checks run too. Exit code 0 = pass. Python 3.8+, no packages.

## 2. Numbers: compare with the server, not with files

The website must show **what the server answers now**. To check a screen:

1. fill the form on the website;
2. send the same body with `curl` (`CONNECT/curl_examples.sh`) to the app server;
3. every number, tag and sentence on the screen must match the answer.

`RANK/api_examples/` shows the expected shape. Its numbers were right on the day of capture and match the server
until the app project renews the data; after that only the live answer counts.

## 3. Acceptance list

**Connection**

- [ ] `connect_check.py --website --pdf` passes against the website's `/api` with a signed-in session.
- [ ] No page contains a copy of cut-off data; every Rank number arrives from `/api/rank/*` at the moment it is shown.
- [ ] A slow or failing app server shows "Rank abhi load nahi hua. Retry dabao." with a Retry button, and Retry works.

**Rank**

- [ ] All six tools work; each form remembers its last values after a reload.
- [ ] JEE 180 marks, Normal, General, Bihar: the card shows the same CRL range and percentile as `POST /rank/predict` for that body.
- [ ] The list shows 25 cards, page 2 the rest; the chips show the server's `counts` and the "in reach" line `reach.all`.
- [ ] Tags read exactly Safe / Likely / Borderline in the colours of `docs/06` §9.
- [ ] Near misses show the server's `gap` sentence.
- [ ] A card opens the college sheet on the card's own path; `blocked` paths show the sentence and no green cell.
- [ ] JAC Delhi Upgrade/Spot cells say they were not published.
- [ ] BITSAT 280, COMEDK 110 marks and COMEDK rank 4500 match their answers.
- [ ] Target marks for a JEE, a COMEDK and a BITS college match their answers.
- [ ] College compare (branches and colleges) matches; a removed seat shows as missing, not as zero.
- [ ] Each PDF button downloads a PDF with the server's file name.
- [ ] Every result screen shows the estimate note.

**Mission**

- [ ] A signed-in student sees the Impact panel with the server's `helped` and `week`; a new student sees the zero state.
- [ ] The share caption ends with the student's own link.
- [ ] Opening that link in a fresh browser adds exactly one; opening it again from the same browser adds none.
- [ ] Opening it with `curl` or from a link preview adds none and still lands on `https://jeelive.ai`.
- [ ] If the website gates results: a cancelled share keeps the result locked; coming back from WhatsApp opens it.

**Dream college** (if built)

- [ ] Adding on the website appears in the app after its next sync, and the reverse.
- [ ] Removing on one device does not remove a dream added on another meanwhile.

**Everywhere**

- [ ] Works at 320 px and 390 px wide, keyboard only, and with reduced motion.
- [ ] No session cookie, pass or personal value appears in logs, analytics or the page source.

## 4. Load

The app server answered 1,000 simulated students using the app at the same time with no errors (p95 46 ms on the
server). The connector pools connections and caches the three GET lists for 10 minutes. Call on **Show**, never on
every key press.
