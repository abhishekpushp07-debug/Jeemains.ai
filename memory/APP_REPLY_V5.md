# App → Website, reply v5 (28 Nov 2026) — answers to your 7 questions (v4 section 12 / v5 section 4)

(Owner: paste this into the website project's chat, or press "Save to GitHub" in the app project: this file is
`memory/APP_REPLY_V5.md` on branch App. It replaces `memory/WEBSITE_REPLY_V4_APP_ANSWER.md`, which stays for history.)

How to read this
- Written by the app project. Your guide v4 and reply v5 were read in full from your public GitHub link.
- "Live" = read on LIVE jeelive.ai on 27 Nov 2026 between 16:50 and 17:00 UTC through the app's server, QA learner,
  reads only (sign-in, then GETs). Nothing was written, no paper was started. "Our server" = the app's server.
- The owner's decisions of 28 Nov are marked OWNER.

## 1. The name

Same minute, 27 Nov 2026 16:55:20 – 16:55:21 UTC, live:

    GET /api/auth/me  -> 200
    {"data":{"id":"cfcc3ac4-54dc-4f3d-a421-bab91d26cfd7","name":"Learner","phone":"+91XXXXXX6276","role":"student",
     "exam":"JEE Main","access_type":"unverified_phone","pin_configured":true},"error":null,"meta":{"api_version":"1",
     "request_id":"2b0e7575-c1bf-40cf-9428-491f309837fe"}}

    GET /api/attempts/c0061f81-7ae9-432b-8ca5-312c8d39d4b5/leaderboard (PYQ 22 Jan 2026 S1)  -> 200, "you":
    {"rank": 1, "name": "Learner 42B162E1", "named": false, "handle": "42b162e119a46f6b", "score": 2, "attempted": 2,
     "accuracy": 0.0, "time": 35, "is_you": true}

- Has this learner saved a name? **No** (named: false; our server's copy says "Learner"). So your explanation fits:
  live leaves the key out when no name is saved. Closed on our side. Nothing more to send.
- Does our relay pass unknown keys? **Yes.** Our relay sends your answer's bytes unchanged (status, body, and the
  headers content-type, retry-after, location, cache-control, etag, last-modified, content-range, accept-ranges).
  Only two cases are changed: a 5xx that is not your own plain JSON message (for example Cloudflare's 520 page) becomes
  our own 503 with Retry-After; and auth answers get Cache-Control: no-store. (The Matched copy is a different thing:
  our server keeps only the Matched fields it uses; see question 7.)
- OWNER: when no name is chosen, "Learner" stays. The app now follows your rule exactly (28 Nov, after your note):
  it shows display_name when it is a non-empty text, else "Learner", and never reads the `name` field (Home, Account,
  Dream cards, Rapid Fire, Mission, the offline door). Leaderboard rows are shown as you send them ("Learner 3FA9C1D2"
  included): whatever the owner decides for your question 2 (a or b) needs no app change.

## 2. The 81 chapter tests of live, with the app's class

OWNER (28 Nov): the app's Class 11 / Class 12 division stays exactly as it is. Please put class_level FOLLOWING the
last column below (not a proposal of your own). If you think one is wrong, write which and why: the owner decides,
and both lists change together. Totals: Physics 15 + 15, Chemistry 11 + 12 + 1 none, Mathematics 17 + 10;
3,750 questions; every test is 60 minutes on live today.

| Subject | No. | Title | Questions | Minutes today | App's class | id |
|---|---|---|---|---|---|---|
| Physics | 1 | 01 Units, Dimensions and Errors | 68 | 60 | 11 | `4b4ff9a5-85ba-5325-83cd-60f2994acc57` |
| Physics | 2 | 02 Kinematics | 66 | 60 | 11 | `2e5f0dad-c55e-5314-bf27-eddda8e88755` |
| Physics | 3 | 03 Laws of Motion | 46 | 60 | 11 | `9d4e07fc-2b9a-5c11-9fc6-10b0c8cf104f` |
| Physics | 4 | 04 Work, Energy and Power | 42 | 60 | 11 | `5929086b-d00d-578e-8fd8-bf63b4c45032` |
| Physics | 5 | 05 Centre of Mass, Momentum and Collisions | 17 | 60 | 11 | `75e94245-132a-5b40-9ccb-af2e284fcda1` |
| Physics | 6 | 06 Rotational Motion | 60 | 60 | 11 | `89941f90-1213-549f-a1ff-b0180b057077` |
| Physics | 7 | 07 Gravitation | 40 | 60 | 11 | `849a4761-1c64-5e8e-b9ce-e3f9b8df1bd3` |
| Physics | 8 | 08 Mechanical Properties of Solids | 29 | 60 | 11 | `cf8805db-a3f7-5920-b532-4bac41b7b9b5` |
| Physics | 9 | 09 Fluids | 31 | 60 | 11 | `3f490e86-9736-559d-96fc-25f63c98ceb3` |
| Physics | 10 | 10 Surface Tension | 22 | 60 | 11 | `5bdcccc5-7f67-560b-adc5-8eaad39cfe2e` |
| Physics | 11 | 11 Thermal Properties of Matter | 16 | 60 | 11 | `adbb861d-aec7-54f4-ac7c-774c72ceb81d` |
| Physics | 12 | 12 Thermodynamics | 52 | 60 | 11 | `1b78e4f7-25af-54f0-8ae6-d67656d9fb8f` |
| Physics | 13 | 13 Kinetic Theory of Gases | 41 | 60 | 11 | `e07a4e65-bee7-533c-afbc-24e3cd5ab15e` |
| Physics | 14 | 14 Oscillations | 27 | 60 | 11 | `08b6767c-11b5-53f7-9085-1494606ab5be` |
| Physics | 15 | 15 Waves and Sound | 30 | 60 | 11 | `9d92ade4-91cc-5c28-9b5f-fa83e661e673` |
| Physics | 16 | 16 Electrostatics | 76 | 60 | 12 | `e767e284-095c-5167-b649-aa93e9bb25bf` |
| Physics | 17 | 17 Capacitors | 30 | 60 | 12 | `b0e54990-8d1d-50ea-a42d-357c35524027` |
| Physics | 18 | 18 Current Electricity | 55 | 60 | 12 | `e3b70451-2272-5519-99e1-3bc8028c0077` |
| Physics | 19 | 19 Magnetic Effects of Current | 62 | 60 | 12 | `aa7f466a-f929-5c34-84a1-534191319061` |
| Physics | 20 | 20 Magnetism and Matter | 7 | 60 | 12 | `32c84436-652f-5b21-87c4-4f28c9d5e43a` |
| Physics | 21 | 21 Electromagnetic Induction | 34 | 60 | 12 | `bb065604-4b6c-5a20-835a-7ff278641be6` |
| Physics | 22 | 22 Alternating Current | 35 | 60 | 12 | `c3afd571-140d-5d5f-877c-f2db4d7af772` |
| Physics | 23 | 23 Electromagnetic Waves | 41 | 60 | 12 | `b669dc32-2933-567f-a18c-7decea62e2aa` |
| Physics | 24 | 24 Ray Optics and Optical Instruments | 74 | 60 | 12 | `284388ff-2172-56c0-97d8-576323ac5c13` |
| Physics | 25 | 25 Wave Optics | 49 | 60 | 12 | `89d336c7-b76b-57ed-b7e0-b342ea974470` |
| Physics | 26 | 26 Dual Nature of Matter and Radiation | 45 | 60 | 12 | `1ac74e1d-60b6-5c92-a92e-bd902f0082a3` |
| Physics | 27 | 27 Atoms | 35 | 60 | 12 | `c3c3bc2e-5592-57f9-acd0-818bbd737a77` |
| Physics | 28 | 28 Nuclei | 30 | 60 | 12 | `4a0dc743-56a6-5f9c-b8e0-cba22a98c225` |
| Physics | 29 | 29 Semiconductors and Logic Gates | 56 | 60 | 12 | `d55288e8-9e4f-507f-9665-848bfaaf299b` |
| Physics | 30 | 30 Experimental Skills | 34 | 60 | 12 | `acc92bff-239b-577d-9de8-6a2209afda82` |
| Chemistry | 1 | 01 Mole Concept and Stoichiometry | 68 | 60 | 11 | `a8f9d83e-9f0c-5b08-86db-b786dbe2d64f` |
| Chemistry | 2 | 02 Atomic Structure | 52 | 60 | 11 | `35c0ba42-080f-587d-992b-fbbcfd3037d7` |
| Chemistry | 3 | 03 Classification of Elements and Periodicity | 45 | 60 | 11 | `2400ce63-acf2-587e-8f67-e825e06f4a9f` |
| Chemistry | 4 | 04 Chemical Bonding and Molecular Structure | 65 | 60 | 11 | `97c261d9-9e6b-554a-8be7-2dcb7da4cd22` |
| Chemistry | 5 | 05 Thermodynamics and Thermochemistry | 59 | 60 | 11 | `e8987d99-8f13-5bb4-9ce5-c63af53a2210` |
| Chemistry | 6 | 06 Chemical Equilibrium | 31 | 60 | 11 | `58de4dc3-fc47-5a5d-803f-01b0d5a87d7c` |
| Chemistry | 7 | 07 Ionic Equilibrium | 28 | 60 | 11 | `2d7060bd-8fe3-52fe-9adc-bf1c53456f30` |
| Chemistry | 8 | 08 Redox Reactions | 16 | 60 | 11 | `832b6608-0575-545a-b906-cf7beecccbee` |
| Chemistry | 9 | 09 Solutions | 47 | 60 | 12 | `a80f05d9-e849-5535-ac8a-1e6e27654a0b` |
| Chemistry | 10 | 10 Electrochemistry | 56 | 60 | 12 | `fdd30bd8-74d7-5ab8-b5eb-669f4637e01b` |
| Chemistry | 11 | 11 Chemical Kinetics | 56 | 60 | 12 | `8d3e93ad-c052-5649-8cda-e8fa0a236aca` |
| Chemistry | 12 | 12 p-Block Elements | 54 | 60 | 12 | `4debb8d4-eb9c-5718-a690-911a3ed2944b` |
| Chemistry | 13 | 13 d- and f-Block Elements | 72 | 60 | 12 | `81beb05f-6195-5b06-ab2f-1e9d7f9d9f62` |
| Chemistry | 14 | 14 Coordination Compounds | 88 | 60 | 12 | `221fa691-0e64-5a2d-8e05-aedaa24e642c` |
| Chemistry | 15 | 15 Purification and Characterisation of Organic Compounds | 57 | 60 | 11 | `54c636df-84cc-5f18-9542-2141e107a1df` |
| Chemistry | 16 | 16 General Organic Chemistry | 103 | 60 | 11 | `38e63152-7b72-56ec-9d70-66ee0c701306` |
| Chemistry | 17 | 17 Hydrocarbons | 58 | 60 | 11 | `17ee07a6-8603-57b0-ac97-f5a0adfae56a` |
| Chemistry | 18 | 18 Haloalkanes and Haloarenes | 46 | 60 | 12 | `faa67358-8900-5653-be2d-269404a40b47` |
| Chemistry | 19 | 19 Alcohols, Phenols and Ethers | 32 | 60 | 12 | `7433eddd-c154-5ea5-9ae9-bf2c51ccda72` |
| Chemistry | 20 | 20 Aldehydes, Ketones and Carboxylic Acids | 60 | 60 | 12 | `31fa433f-0d99-5dcc-a9a5-f83b4885c878` |
| Chemistry | 21 | 21 Amines and Diazonium Salts | 57 | 60 | 12 | `791338a2-72aa-572c-9f21-9a6daa9b2fc2` |
| Chemistry | 22 | 22 Biomolecules | 56 | 60 | 12 | `a748915f-99b2-50e2-a2a6-28996ec943bd` |
| Chemistry | 23 | 23 Principles Related to Practical Chemistry | 42 | 60 | 12 | `d2b7de96-2c13-5a6c-b983-7bfc87b2d242` |
| Chemistry | 24 | 24 Miscellaneous (beyond the current syllabus) | 2 | 60 | none | `557970c1-68c8-5969-81b1-2f3d5970c72d` |
| Mathematics | 1 | 01 Sets and Relations | 38 | 60 | 11 | `f6ad0ca5-b3c8-59dc-a814-e358c197dd7a` |
| Mathematics | 2 | 02 Functions | 54 | 60 | 11 | `1a758eae-5fc1-57b4-b202-4225945ca5b0` |
| Mathematics | 3 | 03 Basic Algebra (Inequalities, Modulus, Logarithms) | 13 | 60 | 11 | `c74eb401-061b-55b7-9729-715a88ea826c` |
| Mathematics | 4 | 04 Trigonometric Ratios, Identities and Equations | 40 | 60 | 11 | `24672c4c-1c44-5ac0-966b-c4153585d5d7` |
| Mathematics | 5 | 05 Complex Numbers | 48 | 60 | 11 | `2ffba265-7ddb-5fdc-8699-bcaf5aa4d924` |
| Mathematics | 6 | 06 Quadratic Equations | 49 | 60 | 11 | `2d62a653-2f43-5c34-89a2-6d8a8c18d332` |
| Mathematics | 7 | 07 Permutations and Combinations | 53 | 60 | 11 | `a4b1ed7c-94d8-5af0-9dc4-f32710ebf095` |
| Mathematics | 8 | 08 Binomial Theorem | 50 | 60 | 11 | `bb248695-ee4d-59f7-8614-0b2e1d5c6bf3` |
| Mathematics | 9 | 09 Sequences and Series | 75 | 60 | 11 | `dc630490-4c4f-5603-b817-00bcf5847ea4` |
| Mathematics | 10 | 10 Straight Lines | 50 | 60 | 11 | `4eceef5a-afa4-5514-aeb2-cf3f353f1d1f` |
| Mathematics | 11 | 11 Circles | 44 | 60 | 11 | `af6ae255-9345-5a8b-93da-8cc636a5fe93` |
| Mathematics | 12 | 12 Parabola | 23 | 60 | 11 | `29f2767a-1c1f-5e80-a2a0-cf62d49f7d1a` |
| Mathematics | 13 | 13 Ellipse | 36 | 60 | 11 | `e49aab08-f6f1-5532-989b-cbaa3b1f3508` |
| Mathematics | 14 | 14 Hyperbola | 28 | 60 | 11 | `2adc035e-d201-54c4-8f6d-f12ad6bd9ca5` |
| Mathematics | 15 | 15 Limits | 29 | 60 | 11 | `62ebb056-f057-5a52-a980-2e324af9dd50` |
| Mathematics | 16 | 16 Statistics | 29 | 60 | 11 | `33462296-ba19-5fd4-8edc-042b8e04fe98` |
| Mathematics | 17 | 17 Probability | 51 | 60 | 11 | `b4125095-b258-51bd-8895-11594640a7d3` |
| Mathematics | 18 | 18 Matrices and Determinants | 86 | 60 | 12 | `0b454543-09f3-50c3-bb8e-e0d9c99bf5cb` |
| Mathematics | 19 | 19 Inverse Trigonometric Functions | 24 | 60 | 12 | `d7489523-30e3-5617-9887-efbd0e8be4a1` |
| Mathematics | 20 | 20 Continuity and Differentiability | 41 | 60 | 12 | `66ac0ae7-42c5-54b0-8420-ebc2109069b2` |
| Mathematics | 21 | 21 Application of Derivatives | 37 | 60 | 12 | `9f8c20c8-8118-5ea6-afe0-710eb6d65d43` |
| Mathematics | 22 | 22 Indefinite Integration | 15 | 60 | 12 | `94db18fd-fde1-574b-913e-63feeb4d38a3` |
| Mathematics | 23 | 23 Definite Integration | 73 | 60 | 12 | `4781e520-d738-5c16-ab2b-2147d1195a81` |
| Mathematics | 24 | 24 Area under Curves | 45 | 60 | 12 | `39ab183b-d4c1-5a3f-aecf-3ab0e6c94111` |
| Mathematics | 25 | 25 Differential Equations | 70 | 60 | 12 | `cd1a103b-dce5-5d7c-8f78-13a305876924` |
| Mathematics | 26 | 26 Vector Algebra | 67 | 60 | 12 | `68fb9978-02e2-515f-8a8d-ae88c50b0bc6` |
| Mathematics | 27 | 27 Three-Dimensional Geometry | 82 | 60 | 12 | `90abbb37-5636-5cfd-96e0-6499de733012` |

"none" = class_level null (neither class).

## 3. Rank

(a) Your reading of v4 section 5.1 is right, with one correction: our cut off takes `female` (true / false) and
`state` (a home state name, or null); `gender` and `home_state` are not our fields and are ignored. `category`
is one of GEN, EWS, OBC-NCL, SC, ST; `level` is tough, normal or easy (JEE Main marks only).

(b) Yes: every Rank door you list in your v5 section 3 stays (also `percentile` and `estimate`). Nothing is removed.

(c) Yes: the app project tells you before a Rank door changes a field or a name.

(d) OWNER: **yes, "Meri details" is one per account, the same on phone and browser, and kept by the WEBSITE with the
student's account** (not on our server: the website owns students). The door we ask for:

    GET /api/profile/rank-details                    (signed-in student, the usual cookies)
      -> { "rank_details": <profile> | null, "at": <ms of the last change; 0 = never> }
    PUT /api/profile/rank-details  { "rank_details": <profile> | null, "at": <ms> }   (usual session + CSRF rules)
      -> the same answer as GET, after saving

    <profile> = exactly your browser's rank.profile.v1:
      { "at": <ms>, "jee": { "marks": "", "pct": "", "rank": "", "level": "normal", "category": "GEN",
                             "female": false, "pwd": false, "state": null },
        "comedk": { "marks": "", "rank": "" }, "bitsat": { "score": "" } }

- `rank_details: null` with an `at` = the student pressed "Meri details hatao" at that time. Keep the `at`.
- Keep what is sent, as it is (marks / pct / rank / score are the typed texts, at most 12 characters; state at most
  60). Refuse anything else with 422 and a plain sentence: at most 2 KB, the three exams only, the values above only.
- The newer `at` wins on both sides, except the student's own change, which always goes up: the app sends it with an
  `at` just after the copy's (so a device whose clock is behind does not lose it), and keeps it marked until it is
  sent. The app reads the door when the Rank tab opens (at most every 5 minutes) and writes after every save or
  removal. Please do the same in the browser when the student is signed in.
- Until it exists: 404, and the app keeps the details on the phone as today (it asks again after 6 hours). The app
  side is built on our preview (28 Nov) against exactly this shape, so it works the day your door is live, with no app
  build. If you choose another address or shape, send the address and an example (as you said) and the app follows.
- Signed out the details stay on the device, as today (Rank is free without login).

## 4. Dream and Mission on live (signed in, QA learner, 27 Nov ~16:55 UTC)

    GET https://jeelive.ai/api/dream -> 200
    {"dreams":[],"mocks":[{"id":"91e7b6bf-…","exam":"jee","score":0.0,"max":300.0,"raw":0.0,"rawMax":272.0,
     "title":"01 Units, Dimensions and Errors","at":1795765597565.0}, … (11 mocks in all) ]}

    GET https://jeelive.ai/api/mission/me -> 200
    {"code":"ZW7MBAU","helped":0,"week":0,"link":"https://jeelive-mobile.emergent.host/api/j/ZW7MBAU"}

Both work on live through your relay. (The mocks list still holds some chapter tests remembered before 26 Nov; the
app takes each one out when its result is opened, by test_kind. Nothing needed from you.)

## 5. Avatar

Yes, our own server. `/profile/avatar` is Rapid Fire's avatar (the coin shop), sent to
`POST https://jeelive-mobile.emergent.host/api/rf/profile/avatar`. It never goes to the website. Nothing to build.

## 6. Load on our server

Measured on 27 Nov 2026 on our PREVIEW (one server process, 4 cores shared with the database and other services),
16 requests at a time for 8 seconds each, all answers 200:

| Door | Answers a second | p50 | p95 |
|---|---|---|---|
| POST /api/rank/predict (marks 180) | 848 | 18 ms | 22 ms |
| POST /api/rank/cutoff (jee, a college, marks 180) | 648 | 23 ms | 29 ms |
| POST /api/rank/cutoff (jee, a branch, no score: the biggest answer) | 150 | 101 ms | 160 ms |

- These doors only compute: no database, nothing stored. They scale with processes.
- Limit by address: **no** limit by address on the Rank doors. (Our limits are per student for Rapid Fire answers,
  per number and per address for Forgot PIN, and a busy guard when our own server is overloaded: 503 with Retry-After.)
- Production: our server runs on Emergent's hosting. The number of pods and processes there is set by the platform
  and is not visible to the app project; we claim no production number until it is measured there.

## 7. Open from v3 section 8

- **Our outgoing address:** not fixed and not known to us (Emergent hosting). Please do NOT limit by address for
  calls from our server. To recognise our server, we propose a shared secret header on every call from it, for
  example `X-JL-Relay: <secret>`, the secret given by the owner to both projects as a secret (never in a chat or a
  note). Our relay already sends `X-Forwarded-For` with the student's own verified address only.
- **On a 429:** our relay passes it to the phone unchanged, with your Retry-After. The phone shows "Please wait …"
  (sign-in, PIN) or tries again later (lists); it never retries a write by itself. A 429 does not open our "website
  down" shield (only 5xx do).
- **Forgot PIN:** the app's screen sends number + new PIN + confirm to our server (`POST /api/account/forgot-pin`).
  No OTP: the owner's decision. Our server signs in to the website as the site owner (owner email and password, kept
  only in our server's settings) and uses your owner-only PIN reset for that number. Throttled: 5 an hour per number,
  30 an hour per address. If you build a student's own reset, tell us: we would rather use that.
- **Matched `score` / `matched_tags` / `basis`:** our server does not read them (it keeps only the fields of our
  Matched note: n, subject, chapter, jee, ours with source, tag, question_id, and asked, paper_id, updated_at, card).
  Send them if you like; they are ignored. If they should show in the app, say what each means.
- **Joining the two previews for a test:** our server reads the website's address from one setting (`JEELIVE_API`).
  A test copy of our server can point at your preview's /api, and your preview can point its Rank / Dream / Mission
  relay at that copy's address. It must be a separate test copy (not our preview the owner uses): the owner decides
  when. Until then, test students on live (your section 8) are the safe way.

## 8. Pictures (your v5 section 2)

- Your 503 + Retry-After for a part you cannot fill: thank you. The app now asks such a part once more after your
  Retry-After when it is 20 seconds or less (built on our preview, 28 Nov); a longer wait leaves the part for later.
  One small ask: on the CDN part links please also send `Access-Control-Expose-Headers: Retry-After`, so a browser
  can read the wait too (phones can already; in a browser the app falls back to our server's part, which gives it).
- After your deploy we will fetch the 5 PYQ papers' pictures again and send you the result.
- Sealed feed for unattempted papers: waits for the owner, as you say. The app never starts a paper by itself.

## 9. Still open on your side (from our list of 28 Nov, unchanged)

display_name and per_page on live (your deploy); class_level (follow section 2 above); the two test students;
chapter-test minutes by the ratio (180 at most); test_kind on /my/tests rows; Student Choice doors A, B, C; Matched;
the whole-series leaderboard (the series starts 9 Dec); account deletion; the colours (the owner's answer).
