## 2026-11-26, evening: FOURTH and current version of plan/phase_HI_guide.md (guide only, no code, nothing deployed). Read this block first; it overrides every block below where they differ.
- Owner's fourth message (26 Nov): (1) use Emergent's Sol 6.1 / 6.2 as the fallback rung; (2) he made the AITS first, then had ChatGPT rearrange the SAME questions chapter-wise into new PDFs; the AITS must be read once and the chapter-wise linked without AI (he asked whether plain search can do it); only the level has to carry over; cost must not double; he has held back the AITS upload for this; AITS, chapter-wise and Matched are one question database in different PDFs; (3) build it universal: a second app (transcribed "Niche Life", probably NEET Live; ASKED, not confirmed) will be a copy of this code with another theme, exam, papers and content; its Super Admin must already have all of this and its content is read again.
- CORRECTION of the third version: its linking numbers were measured on the OLD library bank (78 tests / 3,900 q). That bank is NOT the AITS question set (old chemistry 1,150 vs new chemistry 1,250: 0 identical, best likeness 0.36). The owner was told.
- FOUND 26 Nov (read only):
  - Two chapter-wise books of the AITS collection are on this pod: /root/pdfengine/chemistry_chapterwise.pdf (2,527 pages, 24 chapters, 1,250 q = 1,000 MCQ + 250 integer; also in the preview DB as one Draft book, 24 chapter mocks, all ready, 0 issues, new look, question piece `q` on 1,250 of 1,250) and /root/pdfengine/aits_maths.pdf (title page says "CHAPTER-WISE MATHEMATICS, SPACED EDITION"; 2,530 pages, 27 chapters, 1,250 q). Physics and the 50-paper AITS PDF itself were NOT seen.
  - Every question prints three lines: "Question N", "Source: AITS Mock 04 / Q68", "CH 01 / chapter name". Addresses: chemistry 1,250 distinct, mocks 1–50, 25 each, numbers 51–75 (51–70 MCQ, 71–75 integer); maths 1,250 distinct, mocks 1–50, 25 each, numbers 1–25 each exactly once. The solution page prints the same Source line. The reader stores these typed words per question at upload (`tejas_book_mocks.questions.text`; `book_publish.SOURCE` already parses the line) and the typed worked solution per page region (`tejas_book_pages.regions.text`, sections Concept / Given / steps / Check / Answer / Insight / shortcut / mistakes).
  - Universal key model list (GET {proxy}/llm/models, list only, no question sent): 100 names; has gpt-6-sol, gpt-5.6-sol, gpt-6-astra, gpt-6-luna, claude-opus-5-5; has NO gpt-6.1-sol / gpt-6.2-sol (exactly 100 names came back; limit / page / after parameters returned the same 100; no call was made to those names). The earlier playbook consult did not list them either.
  - Word-search simulation (5-letter shingles of the question words, Jaccard >= 0.30, 0.12 clear of the runner-up, same type, same answer VALUE, one-to-one; a damaged second copy linked back): old bank 3,900: 3% damage 99.9% auto, 6% 99.5%, 10% 95.0%, 15% 56.1%; new chemistry 1,250: 98.9 / 98.6 / 94.1 / 54.2%; wrong links 0 in every run; 156 held-out questions with no twin: 0 wrongly linked. Synthetic damage, not two real PDFs. New chemistry has 9 questions (4 groups, "Match List-I with List-II") that share an identical lead-in; their whole text differs (my test cut the question part at the first "(A)", which in these questions is the List-I item, so the real linker must use the whole words). In the test the search sends them to the owner list; the printed address links them cleanly. The 71 "CH line touches a question piece" hits in /tmp/link/leak2.log are FALSE positives of that check (its case-insensitive search for "CH " also hit words such as "Which" in the first line of the question; checked on one example, chapter 1 Q43, whose piece starts at y 0.0898 while the CH line ends at 0.0741 and whose rendered piece shows only the question); the Source line touches 0 pieces.
  - Source-line exposure (owner told; his decision pending): solution crops contain the Source line 1,250 / 1,250; whole-question crops (`q_refs`, still built for every question) 1,250 / 1,250; website pieces (`c_refs`) 0 / 1,250; `accessible_text` (= the typed words incl. the Source line) is in the student test payload for book-published tests (ran attempts.delivered on a draft question shaped as publish shapes it; no Live new-look test exists in preview). The app packet documents only the whole-picture route, so the app may show the line inside the question (not verifiable here).
- DESIGN in the fourth guide:
  - One record per question, three faces (AITS paper, chapter test, Matched). Link keys in order: printed address (series + printed mock number + printed question number) -> locks (same type, same answer value, words alike) -> word search when no address -> owner list ("Wahi hai / Alag hai") -> "Khud jodo". Works from Draft and in any upload order; a chapter-wise book uploaded first creates records under the printed AITS addresses. Record keeps its own copy of words and solution, survives Library / delete; re-upload re-links without AI; changed words or answer go to a "badla hua" list.
  - AI reads each record once, tags (9 of 10 slots; chapter comes from the chapter book) + level, from picture + words + PRINTED solution; it does not write a solution for AITS-collection questions. Optional switch "AI se key bhi jaanchwao", Off. Chapter-wise costs 0 calls. Estimate (assumed 2,500 in / 1,000 out + second opinion 2,500 / 800; not measured): about $0.04 per question, about $150 for 3,750 (third version said $400). Real January papers unchanged ($400–700, AI writes solutions).
  - Ladder: rung 1 own OpenAI gpt-6.2-sol, rung 2 own OpenAI gpt-6.1-sol, rung 3 own Anthropic claude-opus-5-5, rung 4 universal key trying gpt-6.2-sol, gpt-6.1-sol, gpt-6-sol in that order (first one the key lists; today gpt-6-sol). The whole job can run with no owner key: gpt-6-sol + claude-opus-5-5 on the universal key.
  - Universal (golden rule 17): new code names no exam; subjects, counts, minutes, dates, tag-slot names, tag list, match threshold, real-paper structure labels, Student Choice minutes per question and maximum all come from per-exam / per-series settings; every screen sits inside the exam; routes use {exam}; every pocket's tests also run a made-up second exam. Old JEE-bound code is left alone and listed at handoff time (grep counts: built-in series id in 8 server + 12 website files; "JEE Main" in 30 + 21; brand name in 14 + 33).
  - Section numbers changed: 4 record, 5 link, 6 Matched, 7 Student Choice, 8 Source-line decision, 9 universal, 10 what stays safe, 11 pockets, 12 dates, 13 risks, 14 all remaining work, 15 app, 16 needs.
  - Pocket order now: S1 (only if he chooses "hide": strip the Source line from student pictures and words; touches book_publish.py in two places) -> C1 (records + link + "Jod" screen + chapter names for AITS; no AI) -> H0 trial (<= 150 calls, can run on the universal key) -> H1 -> H2 -> H3 -> C2 -> H4–H6 -> I0–I5 -> H7–H8.
- Notes for whoever builds C1 (not yet verified against a real AITS paper PDF, which was never seen): today's mock-heading pattern (`book_reader.MOCK`, used with `.match`) reads "Mock 04" / "Test 4" / "JEE Main Mock 04" but NOT a heading that starts with "AITS Mock 04"; a published set keeps `mock_number` = the mock's ORDER in the book, not the printed number; by the code (book_publish.py line 348) `original_number` is not removed at publish while `coverage_key`, `cut` and `source_regions` are, but no set published by the current engine exists in preview to confirm it (the existing sets carry no `original_number`); so the AITS-side address must be taken from the Draft mock (label + `original_number`) or the heading pattern must be widened. The link must compare the WHOLE typed words (minus the three header lines), not the part before the first "(A)". Scratch scripts and logs of the 26 Nov measurements are in /tmp/link (may not survive a restart).
- Waiting for the owner: approval of the guide; the Source-line decision (hide / keep chapter-wise Draft until the AITS ends / leave); ONE AITS paper PDF (the chapter-wise PDF is no longer needed; Physics welcome); permission for the 150-call trial; the real name and exam of the second app; the app's showcase screenshots and files; a memory-based paper if he has one. His own OpenAI / Claude key is optional now.


## 2026-11-26, later: THIRD and current version of plan/phase_HI_guide.md (guide only, no code). Read this block first; it overrides the Phase H / I block below where they differ.
- Owner's new decisions (third message of 26 Nov):
  - AI key is a setting with a fallback ladder: first ChatGPT Sol 6.2 or 6.1, then Claude Opus 5.5, then Emergent itself. Guide section 3: rung 1 own OpenAI key `gpt-6.2-sol`, rung 2 own OpenAI key `gpt-6.1-sol`, rung 3 own Anthropic key `claude-opus-5-5`, rung 4 Emergent universal key `gpt-6-astra` (builder's choice: the model already proven in this app). Names and order editable on a new Super Admin screen "AI ki setting". Permanent trouble (key rejected, balance over, model missing) closes a rung and work moves down; temporary trouble retries 3 times on the same rung. Second opinion always from the other company's model. Every record keeps the model that read it. Keys only through the secure secrets card, never in chat.
  - The 3,750 AITS questions are the same questions as in the JEE Main chapter-wise tests. He asked that the chapter-wise tests get the same card (chapter, level, all 10 tags) without a second AI call, and that the chapter-wise Analysis shows them. Guide sections 4.4 and 5: the AI record belongs to the question, not the paper; identity = fingerprint of the typed words the PDF reader already extracts (letters and digits, printed number removed; same idea as duplicates.fingerprint); exact match links by itself in both directions, a near match goes to an owner list (one tap), no match gets a card only on the owner's press "Inhe bhi padhao"; a differing answer key between the two places is flagged. Analysis overlay at build time behind its own switch (paper never written to; score and rank unchanged; kept analyses rebuild once): Qs by Qs gets chapter, topic, level, 10 tags; Difficulty gets the AI estimate labelled as such until 50 students replace it; the weak list groups by topic and subtopic.
  - He asked for one final guide holding everything discussed and all remaining work: section 12 of the guide.
- Pockets renumbered: H0 trial (preview only, at most 150 AI calls: each rung once, 20 questions by both models, 10 made-up twin / opposite pairs, fingerprint check on one AITS PDF + one chapter PDF if supplied), H1 AI route + "AI ki setting", H2 tag list, H3 AI reading + "AI ki padhai" screen, first deploy; C1 chapter-wise linking, C2 tags in Analysis (chapter-wise and AITS) + app packet; H4 real-paper upload, H5 matching, H6 approval screen, second deploy before 20 Jan; H7 student page / card / API (needs the app's showcase files), third deploy before 28 Jan; H8 NTA switch and April; I0–I5 Student Choice unchanged.
- Facts gathered on 26 Nov for this version (read only):
  - Model ids and prices read on the providers' own pages: `gpt-6.2-sol` text + image in, structured output, $2 / $10 per 1M tokens, Batch 50%; `claude-opus-5-5` $4 / $20 per 1M, image input. `gpt-6.1-sol` only from a web search. The Emergent playbook's universal-key list has `gpt-6-astra`, `gpt-6-sol`, `claude-opus-5-5` and does NOT list `gpt-6.1-sol` / `gpt-6.2-sol`, so Sol 6.2 most likely needs the owner's own OpenAI key; H0 tries one call. emergentintegrations LlmChat sends a non-Emergent key straight to the provider via litellm (`provider/model`) and sends pictures the same way for every provider (code read, not run). The app has only EMERGENT_LLM_KEY today.
  - Rough cost given to the owner as an estimate, not a measurement (assumed 4,000 tokens in + 4,000 out per reading call, 4,000 + 2,000 for the second opinion): about $0.10 per question, about $400 for all 3,750 AITS questions, $400–700 for the January real papers. Universal-key rate unknown.
  - Preview chapter bank per subject: Physics 29 tests / 1,450 q (1,218 MCQ + 232 numerical), Chemistry 23 / 1,150 (1,029 + 121), Maths 26 / 1,300 (1,151 + 149). An AITS needs 1,000 MCQ + 250 numerical per subject over 50 days, so the preview bank cannot be the same set as an AITS (numerical too few, Chemistry 1,150 < 1,250). Live bank not seen. The owner was told.
  - Fingerprint of the typed words over those 3,900 questions: 3,900 distinct, no two alike; question part only (options cut off): 3,898 distinct, 2 too short. Sample of 60: likeness to the nearest different question in the same subject: middle 0.43, 90th percentile 0.77, highest 0.92. Hence near matches are never linked automatically. An AITS PDF and a chapter PDF of the same question were never compared (none in preview).
  - Live, public: /api/series/all-india-jee shows 50 days 9 Dec–27 Jan, all upcoming, none with a paper showing ready. /api/admin/master/pictures/x/retry is 404 on live (Packet E part 2 not deployed); /api/admin/storage/health and /api/ceo/v1/summary answer 401 (exist).
  - Analysis: level comes from student results at 50 attempts (65%+ Easy, under 35% Tough), then the paper's own tag or a hint (class_stats.hints_for), then an early level at 10; analyses are cached 14 days with a mark (analysis_api.load) that will need the card version added.
- Still needed from the owner: approval of the guide; permission for the 150-call trial; his OpenAI key (and Anthropic key if he wants) through the secure card; one AITS paper PDF + one chapter-wise PDF holding some of the same questions; the app's showcase screenshots and files (before H7 and I4 only); a memory-based paper PDF if he has one.
- One consequence the owner was told (risk 12 in the guide; his call, the machine blocks nothing): AITS questions are already open in the chapter-wise tests, so a student who did chapter-wise has seen them before the AITS day.



## Owner's Phase H "Matched" and Phase I "Student Choice" (2026-11-26, talk only; nothing built; guide written; the owner's decisions of 26 Nov are in the next lines)
- GUIDE (read first): plan/phase_HI_guide.md. Guide only, no code. Next: the owner sends screenshots and files of the app's two showcase screens; the guide is then re-edited so website and app use one API contract; build only after his approval.
- Owner decided on 26 Nov (these replace the "undecided" list below where they differ). H: a match needs the same chapter, topic and mix of subtopics, the same formula and the same solution path ("soul"); the full question and full solution of every question are stored, not only a card; every shift is matched against all 50 days; an approval screen with pass one / pass selected / pass all; two upload places per shift, memory-based first and then NTA; he will add his own ChatGPT or Claude key if needed. I: the pick list shows the full question without options or solution; time = 80 min per 25 Maths, 60 per 25 Physics, 40 per 25 Chemistry questions; no rank but the normal mock analysis; at most 75 questions, no other limit.
- Memory items are named Phase J–N in the guide: J parked student features (Galti Notebook exists as Misfire since 21 Nov and is missing from the app packet; Subject Rank and the Seekh Reminder on the get-ready screen are not built), K chapter and level tags + mock-to-mock trend, L storage (rest of E, F, G), M PDF Engine 2.0 Phase 2/3, N load test, CDN and owner-side items.
- FINAL GUIDE (second version, 26 Nov) replaces the first one in the same file; its sections are 0–11. The first version's 22 open questions are closed: the owner answered some and told the builder to decide the rest himself (marked "Maine rakha" in the guide).
- Owner decided in his second message of 26 Nov (these override anything older below):
  - Match rule: every question gets at least 10 tags; a real-paper question matches an AITS question when 7 or 8 of the 10 tags match. Guide: 10 fixed tag slots (chapter, topic, main subtopic, second idea, main formula, supporting formula, solution path, deciding step, what is asked, set-up); threshold is a setting, default 7. Matched shows the count and the matched tag names.
  - A match from an AITS day that came after the shift still counts and is shown like any other. No extra line.
  - Subject Rank and Seekh Reminder are NOT to be built. Phase J is closed.
  - AI is the priority. The owner is holding back the AITS papers until the Super Admin AI section exists, so that the AI reads each paper at upload: full question, full solution, 10 tags, level. AITS Day 1 is 9 Dec 2026. Pockets H0 (trial, at most 150 AI calls, preview only), H1 (tag list), H2 (AI reading + screen) come first, then the first deploy. He was told: if the section is not live in time, upload anyway; older papers are read later.
  - Student Choice list shows only the question piece that the new-look cutter already makes (part `q` of `c_refs`), one picture per question, no option pictures. Builder's choice for old-look tests: numerical questions show their picture, MCQ show the typed question words with the options cut off.
- Design rules written into the guide for "one thing must not break another": new files and new collections; every new feature has its own switch, Off by default; existing files touched only at a named short list (server.py, route_contracts.py, db.py, one guarded line in jobs.maintain, MasterType.js, HomeParts.js, ExamHub.js, one analysis file); Student Choice mocks are kept outside tejas_sets and start through their own route; pocket I0 is read-only (the 25 lines in 14 files that work from an attempt's set_id). A deploy ships the whole preview, so the first deploy also carries Packet E.
- Misfire and the app (checked 26 Nov): live jeelive.ai answers 401 on /api/my/misfire and /api/my/chapters (the routes exist) and the live bundle has the /misfire page. The app packet in docs/ never mentions Misfire and the app server publishes no API list, so whether the app's Misfire reads the website's route is NOT verified. The owner was given a one-minute test.
- Still needed from the owner: approval of the guide, permission for the 150-call trial, the app's showcase screenshots and files (needed before H6 and I4 only), and a memory-based paper PDF if he has one.
Naming: these are the owner's product phases, not sections H / I of the storage plan in plan/plan.md. Phase H takes over the "Phase G: AI reading of the question bank" talk further below.
- Phase H as the owner said it: (1) the day after the All India series ends (28 Jan 2027) the dashboard series card turns into "Matched"; the app team has already built a showcase screen. (2) In Super Admin an AI reads every All India series question with its options, answer and solution (50 days x 75 = 3,750), and what it learns is kept in the database, because an agent session ends. (3) Under the series, a place to upload the real JEE Main 2027 papers by attempt and by shift. (4) The AI reads each paper and writes detailed solutions. (5) Question-wise matching of each shift's 75 questions against the 3,750; shown on the website and supplied to the app.
- Phase I as the owner said it: from the JEE Main chapter-wise bank only, a student picks chapters (any mix of subjects), a count per chapter or one total, sees the chapter-wise question list on the next page, ticks questions himself or presses "Select Random", and builds his own mock. The app has a showcase; Super Admin needs its side.
- Found by reading on 26 Nov (preview only; live unknown): the chapter bank is 78 JEE Main chapter tests x 50 = 3,900 questions (Physics 29, Chemistry 23, Maths 26 chapters), each with a picture, typed words, options, answer, worked solution and `topic` = chapter name; no level on any; all 78 sit in the Library in preview. No series paper exists in preview, so a real series paper was not looked at. AI: one gateway (`astra.py`, 300 calls a day unless a limit is set), a two-pass solve-and-check exists, automatic solving is switched off in code since 22 Oct (`AI_SOLVING_PAUSED`), and nothing compares questions by meaning (`duplicates.py` matches exact words inside one section and subject). An attempt copies its questions when it starts, so a personal mock would not change under a student.
- Raised with the owner, undecided: what counts as a match (same question with new numbers / same concept and method / same chapter only; the last would make every shift 75 of 75); owner approval of every match; JEE Main 2027 session 1 is 20-24 and 28 Jan with two shifts for Paper 1 (read on 26 Nov in NTA's public notice of 24 Oct 2026; the Paper 1 days, the session 2 dates and the answer-key date are not in that notice) while the series runs to 27 Jan, so only series days before a shift should count and a day that has not opened must never be shown; where the papers come from, when, and with or without the key; AI cost not measured, trial on one paper first; for Student Choice: how much of a question the pick list shows, time and marking, no rank, repeats, limits, which chapters are in the pool.
- Asked the owner for: screenshots of the app's two showcase screens (they decide which fields the API must give).


## Super Admin storage machine: what is left (2026-11-26; plan/plan.md, memory/HANDOFF_2026-11-25_SUPER_ADMIN_STORAGE.md)
- Live since 25 Nov: Packets A–D. Preview only, NOT deployed: Packet E steps 1–4 (picture proof for a PDF mock, a written mock, and a built test switched on again).
- Backlog only, by the owner's word on 26 Nov ("old data is not needed"): copy of old Emergent pictures to Supabase before Live. What he was told: an old test whose pictures are split between the two stores stays Live if it is Live, but cannot be switched on again once it is switched Off, sent to the Library or taken off its day; the badge's "Purani files › copy" may make it whole (untested, and it also copies PYQ files); new tests cannot split while Supabase stays set up; the number of split tests on live is unknown.
- P1: "Pictures ki poori jaanch" button (full read + fingerprint in the background; reports only, never switches a Live mock Off).
- P1, owner to decide: for a written Draft going Live, keep the reason on the row with Dobara chalao (today a 12-second note).
- P1: one run of the proof against real Supabase for a written photo and for a test switched on again (so far only the PDF path was run on real Supabase).
- P2: the older doors (paper import, chapter book, book "resume mock", automatic import) refuse with the reason but keep no row line and no retry.
- P2: `tests/master_jee_series_iso181.py` still asks for 1 and 5 Dec (the JEE series starts 9 Dec): 3/10 since the dates changed; the test needs new dates, not the app.
- Then Packet F (per-mock fallback to Emergent after 5 minutes or on the owner's press, never a split mock) and Packet G (owner-controlled Emergent → Supabase move with byte + hash check).
- Deploy only when the owner writes exactly `deploy`.



## Owner's "Phase G": AI reading of the question bank (2026-11-25, talk only; nothing built; needs approval)
Not the storage plan's Packet G (owner-controlled Emergent → Supabase move). The owner named this work "phase g" and asked to do Packet E first.
- What was found by reading the code and the preview database (not reproduced on a live student screen):
  - Chapter-wise PDFs: the chapter name is read (printed heading or PDF bookmarks) and saved on the test (`chapter_title`, `chapter_subject`), but `book_publish` never writes `topic` on the questions. Analysis groups by each question's `topic`, so students see the subject and no chapter.
  - Levels: `analysis_rules.difficulty_for` uses student results (50 attempts; 65%+ correct Easy, under 35% Tough), then the paper's own tag, else "Not rated". `book_ai.py` saves a fixed `'difficulty': 'Moderate'` for AI-written solutions, which then shows as the paper's own level.
  - The PDF reader uses no AI (preview: 2,527 pages read, 0 by AI). The duplicate alert (`duplicates.py`) matches exact words only.
- P1, no AI: copy the chapter name of a chapter-wise test onto its questions (`topic`), new and already-built tests; Analysis then shows the chapter. Full mocks stay without chapters.
- P1, no AI: remove the fixed "Moderate" (store no level there) so it is not shown as the paper's level.
- P1, AI, needs approval + cost trial on ONE chapter first: one reading pass over every question (picture + words) saving a card per question: chapter, concepts, type of calculation, level estimate. Levels shown as an estimate until student data replaces them.
- P1, after the real JEE Main paper is supplied (owner said: session on 25 Jan, paper a few days later): AI reads each real question, shortlists from the cards, compares the top few, the owner approves each match, then students see "we had this question".
- Owner can also set level and chapter by hand in Master (already listed under Analysis 2.0 Phase 2).
- Open questions for the owner: a screenshot of the Analysis screen that shows the wrong thing; whether the books print "Level 1 / Level 2" headings; approval of the one-chapter trial.


## PDF Engine 2.0 — next (2026-11-21)
- P1 Phase 2 (needs owner approval): "chipke hue" options (5 held questions in the unboxed books), app guide + PDF format guide, diagram beside options / option on next page / two-column pages, scanned PDFs without AI, plain-word options as real text, "dobara padho" for old Drafts, solution pictures trimmed the same way, JEE Main PYQ in the new look.
- P1 Readability on phones: wide question pictures start small at 390 px (zoom button fixes it); consider a bigger starting zoom or a hint.
- P2 Speed: boxed 2,527-page book scan ~7 min (old engine without boxes ~5.5 min); measure upload → Draft time inside the app on preview.
- Stale suite expectations to refresh: master_iso181 (JEE series 50 days, AITS type on the exam page), structure_iso173 (AITS student section).


# Analysis 2.0 Phase 1 (2026-11-19)
- DONE (preview): website 8 sections + Comparative + Leaderboard + Solutions cards + (i) texts styled and browser-checked; PDF report with cover/contents/charts/journey; app packet addendum /downloads/jeelive-app-update-2026-11-19.zip.
- P0: deploy when the owner says "deploy". After deploy, tell the app team the 19 Nov addendum is live (it says "preview only").
- P1 (Phase 2, needs approval): mock-to-mock trend (last 5), owner sets Difficulty/chapter tags in Master, subject-wise Rank and Percentile, Galti notebook.
- P1 (Phase 3, needs approval): 1 to 2 lakh load test, owner paper report, target score follow-up.
- OPEN (owner's call): an isolated test database from an earlier session is still on the preview MongoDB: tejas_isolated_book170_436fa878 (14 synthetic TEST_ students, written 13:38–13:42 UTC on 19 Nov, nothing running against it, not the app database). This session did not create it, so it was not removed. Drop it only if the owner agrees.
- P2: analysis.py still has an unused old build_analysis (analysis_build.py is the live one).

# Rank 6 tools + Mission share gate + result sparkle + Dream college (2026-11-18)
- DONE (preview, iteration_199/200): public /rank with 6 jewel tools (Rank predictor, Percentile se rank, Target marks, College predictor JEE/BITSAT/COMEDK, College compare, Dream college), PDFs, WhatsApp share; Mission page + share gate after every fresh submission; result sparkle (40%+ or own best); Dream College Meter on Rank, Results (full mocks) and Home.
- DONE 2026-11-19 (preview, iteration_201): Rank restyled to the app's look and design notes (black-metal jewel tiles, tool-colour form bands, purple College summary, metal Rank Card, numbered medal coins); Mission count-up 1.2 s + 'Aapka impact card par dikhega' note.
- DONE 2026-11-19 (preview, iteration_202/203): app hand-off pack applied. Rank/Mission/Dream come live from the app server via backend/tejas/app_connect.py (local data deleted, pack connect_check 22/22). App Dream College Meter + chart, app card stat boxes, the app's 'Dream unlocked' WhatsApp picture card for a crossed dream (Dost ko dikhao).
- P0 after deploy: on live jeelive.ai, sign in as a student and check Mission (/api/mission/me) and Dream (/api/dream) load from the app server (cannot be checked in preview).
- P1: deploy when the owner asks. P2: signed-out visitors see no bottom tabs/Rapid Fire mark (tabs show only when signed in). P2: share gate is per browser (localStorage) like the app's per-phone lock; BITS seat cell in compare shows a dash (no seat data).
- WAITING on owner: Rapid Fire Play Store link (then make the gem/tab/card open it). Rapid Fire stays a non-clickable picture until then.

# App theme + navigation (2026-11-18)
- DONE (preview, iteration_198): light default + dark switch, phone bottom tabs, Home like the app, My Tests chips, player/results/analysis re-themed.
- P1: deploy when the owner asks. P2: light-mode polish of admin/Super Admin screens (not re-themed by hand).

# Analysis 2.0 + sign-in limit + capacity (2026-11-18)
- DONE 2026-11-18: jeelive.ai serves the new code (/api/media/probe.bin 200). Still check on live: sign-in counts only wrong PINs and the 401 message shows tries left.
- P0 (app team): build from /downloads/jeelive-app-update-2026-11-18.zip (docs/app_packet/APP_UPDATE_2026-11-18.md), P0 items first: picture text, time capture, Analysis 2.0.
- DONE 2026-11-18 (preview): Leaderboard name field on My Tests profile box. P1: deploy; consider a "Set your name" link in the leaderboard/analysis when the student has no name.
- P0 (platform support, owner sends docs/SERVER_SIZE_REQUEST.md): Cloudflare must not challenge /api calls from shared IPs; ~24 workers + 8 vCPU DB for 1 lakh, ~48 + 16 for 2 lakh; ask how many workers run per pod.
- P0 (owner action): CDN links are built (preview). Set up a pull CDN for https://jeelive.ai/api/media/* (docs/CDN_SETUP.md), save its address in the MEDIA_CDN_URL live slot (secure card opened 2026-11-18), then deploy; after deploy `curl -I <cdn>/api/media/probe.bin` twice must show a HIT and `x-media-cdn` = the CDN address. Without it pictures still come from the server.
- P0 (deploy): picture questions now send `text: ""` (player + results) so the app stops showing machine text under the picture; confirm on the app after deploy.
- P1: RedOS app should switch from /assets/pack to /assets/links (APP_INTEGRATION.md §15). Results-page review pictures still load privately one by one (lazy, not the start rush).
- P1: TEJAS_INFLIGHT_AUTH (4) caps sign-in at ~50–60/s per process; size with cores. Read lane 16 gives 'busy' in pack/result bursts (website retries).
- P1: class_stats rebuild is O(finishers) (~5 ms each, ~8 min at 1 lakh); make it incremental.
- P2: tests/test_iter156_pin_hour_budget_isolated.py tests the removed hourly budget; replace with tests/wrong_pin_iso197.py. analysis.py still has an unused old build_analysis (analysis_build.py is the live one).
- P2: Comparative waterfall '+0' step has no label; sticky result tabs cover a block title while scrolling (cosmetic).


# Owner editing power (2026-11-16)
- P0: User said "Deploy" on 2026-11-16; deploy queued (deployer job bcd75d41-4661-4f5a-bead-654e0ffe34d2), outcome not yet confirmed. Carries edit questions, typed options, upload resume, Library Delete, Live/Off switches.
- P0 after deploy: owner re-uploads the 33 MB AITS PDF; if it stops, note the part number shown.
- P1: Editing a question of a paper that is already Live / has a day (built set) still needs a corrected version; not built.
- P2: Platform file storage cannot delete file bytes (DELETE 405); Library Delete removes database records only.


# Simple PIN (2026-11-15)
- P0: User said "Deploy" on 2026-11-15; deploy queued (deployer job bcd75d41-4661-4f5a-bead-654e0ffe34d2), outcome not yet confirmed. Carries Forgot PIN, fresh start migration and Library work. After deploy: check /api/auth/pin/reset is in the live openapi, Library on live, JEE Main PYQ still shows its papers, and the app agent switches its Forgot Password screen to it.
- P0 (owner action): send docs/SERVER_SIZE_REQUEST.md to platform support.
- Live read-only report (2026-11-15, deployer): healthy. Last 5 deploys succeeded, serving dded31fd (12:29Z). 2 pods, 0 restarts/OOM, tier_4 Elite, CPU req 2/limit 4, mem 8/16 Gi per pod (earlier "2×1 vCPU" note was wrong). Cron maintenance 200s, 189 runs in 7 d, first nightly repair done. 24 h: one 503 on a studio asset, no 500/502/504. Largest collections: book_pages 8,962, question_solutions 7,100, files 5,564. 14 student profiles (1 new in 7 d). Not visible to the deployer: per-pod CPU use, slow requests/520s (no latency in logs), app-vs-web User-Agent, DB byte size, slow queries, backups (ask platform support/Atlas).
- P1 (open choice): no guard stops an outside PIN reset during a student's running live paper; add one if the owner asks.
- P2: Archiving single tests by id does not move their source PDF to the Library (only section/fresh start do), so such a PDF never shows "Back from the Library".
- P2: Existing students pay the old 196 ms PIN check once on their first sign-in after deploy.
- Phase 2 (separate approval): staged load test, overload waiting line, 100 MB streaming upload, faster large PDFs, decimal answers, open browser checks, history lookups at 1 lakh.


# Master Phase 1 (2026-11-15)
- P0: Wait for the user's go-ahead before deploying Master to jeelive.ai. On deploy the sets index series_date_1 is replaced by series_day_unique (done at startup by db.indexes()). The same deploy runs the one-time fresh start on production (only JEE Main PYQ stays; every other test, the 62-day JEE series papers and uploads go to the Library; series dates kept). After deploy: check the Library on live and that JEE Main PYQ still shows 30 papers.
- P0 after deploy: owner makes one real PDF upload and one written mock on live; ask for a screenshot if anything fails.
- P1: Not yet seen in a real browser (backend suite only): replacing mocks with a new PDF end to end, Library restore, a series day while it is open, and photo / Excel file bytes sent by a real browser.
- DONE 2026-11-15 (preview): general chapter reader (headings, bookmarks, owner-marked starts, subjects) and Draft preview (Try as student). Deploy only with the Master go-ahead.
- P1: Results page after a private preview links back to the exam, not to Master (cosmetic). The student-facing source line of PDF tests shows the upload file name; ask the user whether to hide it.
- P1: The mobile app must read GET /api/series to show series cards for new exams (docs/APP_INTEGRATION.md section 14).
- Phase 2 (needs approval): next year's series and archive of the old one; add or change a written question inside a PDF mock; copy a mock or move it to another exam; search and filters; drag to reorder; confirm many numerical questions at once.
- Phase 3 (needs approval): scanned and two-language PDFs; a reviewer per exam; per-mock report; change history.


# Active roadmap


## Chapter-wise solutions reader (2026-11-16)
- P0: Deploy when the user says "Deploy". After deploy every unpublished PDF is re-read automatically by reader v4 (published papers and owner repairs kept); 'bitsat maths final' should show 31 ready chapters + Mathematical Induction held for Q37/Q38 crop.
- P2: a published old-label mock that owns only part of a bookmark chapter leaves that chapter held after a plan switch (not the case on the live book).

## Simple start + get-ready + AITS results (2026-11-16)
- P0: Deploy when the user says "Deploy" — the live site still has the slow "Check my device" until then.
- Note: AITS solutions now open during the live day (owner's choice); a student who finishes early can share them with later starters.

## AITS dates + owner early access (2026-11-16)
- P0: Deploy only when the user says "Deploy". On deploy, the one-time JEE dates job runs on live: series becomes 9 Dec 2026 – 27 Jan 2027; live papers on 1–8 Dec (or after 27 Jan) lose their day and show under "without a day" for the owner to give again.
- Known minor: anonymous GET /api/sets/{id} still 404s for owner early papers (UI uses /api/my/sets/{id}, so no effect).

## Super Admin content management (2026-11-14)
- P0: The user asked to deploy on 2026-11-14. The deploy was dispatched (job bcd75d41-4661-4f5a-bead-654e0ffe34d2); the outcome is not confirmed yet. On the first production start, cleanup_once() moves BITSAT mocks + chapter-wise and JEE Main chapter-wise into the Library (PYQ untouched). After the deploy, check /super-admin/library on live and that the BITSAT/JEE Main PYQ sections still show their papers.
- P1: In AITS books whose numerical questions have no "Numerical/Section B" heading, every numerical question is held. Each one then needs one Held-fixer save. Option: a bulk "these are numerical, keys as printed" confirm for each mock.
- P2 (cosmetic): ReadyAction uses the native date-time input; the shadcn date and time picker could replace it.
- Waiting for content: new BITSAT mocks, chapter-wise and PYQ, and new JEE Main chapter-wise (the user will supply them).


## Native mock-book reader (2026-11-14)
- P0: Deploy the reader fix only on the user's go-ahead. After deploy, the live 4,481-page JEE book re-reads by itself (READER_VERSION changed; recover() picks it up). Owner repairs and published-mock pages are kept; no AI is used. Then check on live: expected ~35/50 mocks ready and ~19 questions held for review.
- P1: The 19 held JEE questions (mostly Q20/Q45/Q70, last question of a section) need the owner's quick check in Attention Needed: the print does not show their options/answer type clearly enough to publish safely.
- P2 (cosmetic): 2 crop pairs (Mock 7 p543, Mock 49 p4305) where a tall bracket physically overlaps the line above; a straight cut cannot separate them.


## 1-lakh simultaneous exam (2026-11-14)
- P0: Deploy (integrity + speed + 15-min start window) dispatched 2026-11-14 on the user's "Go Live". Confirm live build, then that the first maintenance run fixed 13 orphan ranking entries, 7 orphan score records and retried 1 report job (Super Admin › Overview › Data health).
- P2: Instant score means a student who submits early can learn whether single answers were right while late starters are still writing (inherent to the user's choice). Option: hide the topic breakdown until the end.
- P2 (cosmetic): make the live score number larger on the results card.
- P0 (infra, needs platform/Emergent support, not code): measured CPU per student over a 3-hour JEE paper is about 0.9–1.25 CPU-seconds (150 saves, 75 visits, start, submit, grade, results). 1 lakh students need about 10–12 vCPU of backend on average and ~10 vCPU to admit everyone within 2 minutes, plus a MongoDB tier for ~1,400 answer writes/s. Production today is 2 pods x 1 vCPU limit: about 10,000 starts per minute and roughly 16–22k students sitting the exam at the same time. Ask platform support for more replicas/CPU (or autoscaling) and a larger DB tier, then run one staged load test on that setup before a 1-lakh event.
- P0 (infra): Cloudflare 520 / 30 s hangs on live remain an edge issue outside the app.
- P1: For fixed-end live exams, open a start window (e.g. 15 min) so starts spread out; a student delayed at start loses time because deadline = min(start + duration, exam end).
- P1: Admission control rejects (503 + retry) rather than queueing; under overload a few saves can retry for 30+ s (client keeps local drafts). Consider a short bounded wait queue.
- P2: Session cache eviction is per pod; another pod may accept an old session for up to 10 s after logout/PIN change.


## Organised Super Admin (2026-11-14)
- P0: Production deploy dispatched 2026-11-14 (user-approved; job bcd75d41-4661-4f5a-bead-654e0ffe34d2), outcome not yet confirmed. After it is live, check /super-admin on live, built-in exams/sections seed (3 exams, 7 sections) and one phone preview link (then turn it off).
- P0 (carried): confirm on production that a real combined-book upload reads and processes (stall fix deploy outcome was pending).
- P1: Toasts at top centre briefly cover the admin breadcrumb (cosmetic). Import schedule form uses native date inputs.
- P1: Visibility cache is per process (5 s TTL, refreshed on structure/start/detail/list calls); multi-pod hide/show may lag a few seconds on list endpoints.
- P1: Obsolete old suites (book_publishing_iso170, rules170, scale171, bridges 170/171) assume auto-publish; replace with structure_iso173 / structure_imports_iso174.
- P2 (from QA174, optional): QR code in the phone preview dialog so the owner can scan instead of copy.
- Phase 2 (separate approval): tags/filters, bulk move, multi-book queue, section scheduling, hard scans/bilingual, layout profiles, All India direct upload. Phase 3: per-exam reviewer assignment, quality/usage reports, bulk scheduling.


## Book publishing (2026-11-13)
- UPDATE 2026-11-13 late night (overrides the lines below where they differ):
  - P0: The stall fix has never been deployed. No deploy run of any status exists after 10:25:43Z on 2026-11-13 (deployer); the fix was saved 19:48–20:33Z. The user approved the deploy at 22:05Z and it was dispatched about 22:13Z; outcome pending. Then confirm the live bundle contains "Connection problem on part".
  - P0: The fix files are uncommitted in git (HEAD e602cf1 is older). Make sure a checkpoint exists before any deploy.
  - P0: No signed-in session has called /api/admin/books* on production and there are 0 books there. Get one real upload done by the owner (/owner-login, email + password) and a screenshot with the time if it fails.
  - P0: maintenance cron approved by the user (22:05Z); WEBHOOK_CRON_SECRET added in preview and verified there (dispatcher 200, 2 expired preview attempts closed and graded, endpoint checks 7/7). After the deploy, confirm on production that the key exists and that POST /api/cron/maintenance arrives with 200. Expected first-run effects: 13 expired attempts closed (11 with no answers), 12 submitted attempts graded, 1 old report job re-dispatched. Unknown until then whether a production dispatcher is scheduled at all.
  - P1: Stale-tab error page. The edge returns the HTML page (200) for a missing /static/js file, so a tab opened before a deploy shows "We couldn't open this screen" on its next screen change. Possible fix: reload once automatically when a screen file fails to load. Not confirmed as the page the user saw; not approved yet.
  - P1: Slowness not reproduced. All stalls measured from the preview pod fell in one two-minute window in which unrelated hosts stalled too (17 of 20 in the same second), so the pod cannot be used to judge the site. Needs a screenshot with the time from the user, or edge analytics from platform support.
  - P1: 100 MB PUT to real object storage unproven. Storage has no delete API; ask before running a probe that writes there.

- P0: User deployed on 2026-11-13; live serves the new build (routes + bundle checked from outside, no login). No real publisher PDF has been run in preview (0 books) or on production (deployer reports 0 books). Validate with one real owner-supplied PDF; pod memory headroom for a 100 MB upload on production is unmeasured (preview peak ~580 MB RSS vs 4Gi limit).
- P0: Redeploy needed. Production still has the stall: any book over 340 pages stops reading until the owner presses "Retry saved work" (each press gives 340 more pages). Fix is in preview, tested 270/270 in isolated DBs. Deploy only on the user's word.
- P0: WEBHOOK_CRON_SECRET missing in preview and production, so scheduled maintenance never runs (expired attempts are only closed when someone opens them; interrupted jobs are not recovered after a pod restart). Needs the user's go-ahead because it changes production behaviour. Follow the scheduled-recurring-tasks skill.
- P0: Unknown whether the production container permits the PDF sandbox (chroot + seccomp as root). Watch the first real upload there.
- P1: User's "site slow / error page" not reproduced. Ask for a screenshot with the time; edge analytics need platform support.
- P1: receive() joins all parts in memory and put_object sends up to 100 MB in one request with a 120 s timeout; real object storage has only been proven with files up to ~18 MB. Test one large real file in preview.
- P2: /health on live returns the SPA HTML with 200, not a health check; the real probe is /api/health.
- P1: Owner login is email/password (/owner-login); phone+PIN accounts are students. Phone-based owner login would need explicit approval.
- P2 perf: incremental rebuild (each matching step re-scans all pages, ~4.7s at 1,500 pages/150 mocks); stream upload parts to disk instead of in-memory join (~580MB peak at 100 MB).
- P1: Two-column worked-solution continuation coverage; browser check of BookUpload resume-after-pause and BITSAT bonus UI.
- P2 (cosmetic): round coordinate display, hide response-format for non-question regions, cleaner instruction-page listing, larger series breadcrumb.
- Phases 2/3 (layout profiles, bilingual, delegated editors) need separate approval.


## P0 — release and production reliability (2026-10-27)
1. Code-only live redeploy QUEUED/accepted (job bcd75d41-4661-4f5a-bead-654e0ffe34d2) after passing backend168/frontend167. Publication NOT confirmed; tool says do not redispatch/poll/wait, deployment panel and system notification report outcome. Preserve production DB/secrets/accounts/attempts/academic data; no historical reset/import operation.
2. LIVE30-secondCloudflare520transportfault remains unresolved. Deployer confirmed hung requests never reach healthy backend pods; platform intervention required, outside available repo/preview tools. Support says support@emergent.sh; no actual incident ticket opened. Support's returned Job ID was malformed: authoritative deployment04241398-cdb1-4ca5-8232-874011d24cc3; RCA402afcbe-cbe8-4eb7-aa1b-491fa5beb602.MD. Do not repeat malformed ID. Verify bounded public health/catalogue and served final assets after rollout; do not do production-load tests or customer test writes.
3. Completed app increment: all-ref geometry + once-per-page low-res validation, losslessPNG1largepages, source singleflight64MiB, no duplicatecropcache; private per-user12MiB RAMblobcache/4requests/logoutclear,401singleflight, boundednextquestionprefetch, one-usefresh5sstartpayload, compiledfontpreloads/loginCLS, attempt-routeabort/keyfix. Measured final168Jan1163ms/Apr354ms cold vs4667/9126; warm6–7ms; 400RGBpixelidentical; sourceGET7→1; Janpayload-8.6% andrenderCPU-15%vs164; co-locatedseriesmax135ms/healthp951ms. TeststorageMOCKEDlocaloriginalPDFbytes; no productionRTT/500kclaim. Frontend167productionbuild+9race/21Nodepassed; broader164loadpassed100logical/30concurrency.
4. Remaining observed latency limitation: one April image max400.6ms in168, p95122ms and unchangedbytes; not independently reproduced, do not label definitively environmental. Global4G/realobjectstore latency/capacity remain unqualified.

## P1 — decisions only if evidence requires
- ExistinggoodDBindexesnotrewrite; expandisolateduserattemptfanoutandcheckqueryplannerbeforetargetedindexhint/additiveindex.
- ManagedRediscurrentlyNOTprovisioned/no credentials. Do not installpretendlocalRedis or silentlybuyservice. Consider onlymeasuredsharedpublicimmutablemetadata workload, behindfeatureflag withcanonicalfallback andseparatecost/credentials approval.
- A process-renderworker onlyifDisplayListcostreductiondoesnotresolveeventloopstarvation; no unboundedprocess/queue growth.

## Existing constraints / open items
- No newOTP/payments/RapidFirebackend or studenthistoryreset.
- Canonical liveAPI https://jeelive.ai/api; nativeaccount/attempt identity preserved. OldhandoffZIPsdatedsnapshots; futureexportsneedlatestUIcontracts.
- Oneincomplete23Jan2025S1 source excluded(no inventedQ48–50).
- Original30verifiedPYQ2250Qs preserved. Baseline163notedQ2headerfragment onJan24S1; inspectALLitsrefs beforedeclaringcontentmissing; do not alteracademicmappingforperformance.
- PrivateingressclientIPlimitneedsoperatortrustedproxyconfiguration. Four-digitPINtemporarylockouttrade-off documented. Owner/studentcredentials alreadyrequestedreset completed; never repeat.
- No500kconcurrency claim. Horizontalfleet, MongoHA, externalcache, recovery/workerfleet qualification needseparateproduction-scaleevidence/approval.

## Added 2026-11-23
- P1: AITS hub redesign is in preview only. Owner to check it, then publish.
- DONE in preview: website side of the CEO dashboard (brief section 9). P0: keys are saved; publish, then check /api/ceo/v1/summary on jeelive.ai with the key and the page_open counts once on live.
- DONE in preview: AITS all-days analysis (subject trend, you vs average vs topper, accuracy/time, weak list) + normal result buttons on the day page. P1: chapter tags for AITS questions (owner's choice how) so "bar-bar galat chapter" shows real chapters; check the analysis once with real students after 9 Dec.
- P1: owner to name the CEO "enhancer" if it is not the /alerts endpoint. P2: more events (test_start, analysis_open, solution_open…) and nightly daily facts only if the dashboard needs them.

