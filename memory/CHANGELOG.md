## 2026-11-23 (night) — Upload PDF dialog: visible "PDF chuniye" button (preview only, needs deploy)
- Owner on jeelive.ai: picker often did not open. UploadDialog PdfBox now has a real button (data-testid upload-main-pick / upload-key-pick / upload-solutions-pick) that clicks a visually hidden input (.master-pdf-input); label tap also opens it; button says "Badlo" after a pick. Dialog close X is 44x44 in admin dialogs.
- Tests: tests/ui_upload_repro223.py 12/12 (bridge 181); testing agent iteration_215: all requested flows pass.
- Production facts (deployer, 23 Nov): upload backend healthy (82-part upload 200 at 17:45 UTC, book eed94a04 reading). Owner deleted ~222 tests + 7 uploads incl. Rapid Fire from Library at 17:38 UTC (permanent Mongo delete). Supabase files untouched (no storage delete exists in code). 30 verified JEE Main PYQ intact. Emergent support says production Mongo has 7-day point-in-time recovery via support@emergent.sh (unverified).

## 2026-11-23 — Super Admin Phase 1 finished: Block/Unblock, machine panel, re-read progress, Hinglish, 44 px / 390 px, noindex, 409 lock (preview only)
- Screens: AdminStudents (Band karo / Chalu karo), MachinePanel in StorageBadge, MockList/MasterType/MasterHome/FixList re-read lines, Hinglish copy, master.css touch + mobile rules, useNoIndex in AdminWorkspace + Auth, robots.txt.
- Server: master.mock_status refuses Live/Schedule while re-reading; book_worker.step 409 -> job waits (jobs.BUSY_WAITS=90); Hinglish upload messages; book_view filename guard; Supabase not-set message Hinglish.
- Tests: tests/phase1_iso221.py 17/17; stale 50-day series expectations fixed in master_iso181, structure_iso173, library_aits_iso180, fresh_start_iso183; forgot_pin_iso184 updated; testing agent iteration_214.

## 2026-11-21 — PDF Engine 2.0 Phase 1 recovered after the rollback + options always stacked (preview only)
- Recovered exact lost code: tejas/book_cutter.py (printed boxes first, a/A separation, cut_boxes checks), book_cuts.py (frames), book_imports.cut_view (frames), book_pdf_worker (off-page pictures), book_reader (READER_VERSION 5: top-margin "Question N", chapter called Solutions, bookmark key tables), chapter_reader (bare flag); CutTool.js + cut-tool.css (full-page fix tool). Sources listed in memory/RECOVERY_2026-11-21.md; copies in memory/recovered/.
- QuestionPieces PieceOptions always `is-stack` / data-layout="stack"; App.css .answer-options one column; .piece-stem scroll-margin-top under sticky tabs.
- Tests: cut_cases210 41/41, scan compare (tests/cut_compare_restore211.py) 0 differences on 5,900 questions, chapters_iso182 58/58, typed_delete_iso185 54/54, ui_cut210 (updated for stacked options) 232/232, testing agent iteration_205 113/113 (tests/ui_verify211.py).


## 2026-11-18 — Picture questions send no machine text; CDN probe
- User: "on app i see that pic of question is also there and aaai written words also. Is that problem there on website too jeelive.ai bitsat chapter wise probably or pyq jee mains". Website (preview and live bundle checked) shows only the pictures + a closed "Read accessible text"; the app showed `text`. The player sent the accessible-text sentence as `text`, and results sent the raw machine/OCR text (BITSAT and JEE Main chapter-wise).
- attempts.delivered + results: `render_mode: source` with pictures → `text: ""` (accessible_text kept as the screen-reader label); source without pictures → accessible_text in both (never raw machine text). APP_INTEGRATION.md step 4 rule for the app. Testing agent iteration_197: backend 16/16 bridge + 33/33 iso, frontend player/results 1920 + 390 pass (tests/picture_text_bridge200.py).
- media.py: public GET /api/media/probe.bin (fixed bytes, public cache, X-Media-CDN) to confirm CDN HITs. media_cdn_iso198 now 33/33; get_ready_iso188 47/47.
- MEDIA_CDN_URL secret slot exists (separate test/live); live slot to be filled by the owner via the secure card, then deploy.


## 2026-11-18 — Question pictures via CDN-cacheable signed links
- New tejas/media.py: /api/attempts/{id}/assets/links + public /api/media/pack/... (signed, day-bucket expiry, public immutable cache headers, ACAO *, per-process cache + coalescing, never caches a part with a broken picture). /assets/pack reuses media.picture_refs/assemble (unchanged output).
- server.py Protections: /api/media keeps its own Cache-Control (else private, no-store). origins.py: CORS middleware skips /api/media. admission/runtime: 'media' lane 32, wait 3 s. route_contracts: attempts.asset_links, media.media_pack.
- Frontend privateResources.preloadPaper: CDN links first (credentials omit), quick retry, then private pack, then single pictures; skips links for papers without pictures.
- backend/.env MEDIA_CDN_URL= (empty → links on the same server). docs/CDN_SETUP.md, APP_INTEGRATION.md §15, CAPACITY_REPORT update. tools/load_live.py LOAD_MEDIA=1.
- Tests: tests/media_cdn_iso198.py 29/29, get_ready_iso188 47/47, iso189 15/15, iteration_196 (tests/media_cdn_bridge199.py 10/10, browser flows pass). Load A/B logs test_reports/load198_*. Load accounts +91600198 removed (703 accounts, 664 attempts); phone-limit rows expire by TTL.


## 2026-11-16 — Chapter-wise PDFs: solutions at the end of each chapter are read
- Live RCA (book a05c49f7 'bitsat maths final', 640 pages): 435 pages 'unresolved', 0 solutions, all 34 chapter mocks held (~6,513 issues). Cause: the reader did not know headings like 'Answer key – <chapter name>' / '<chapter name> – Solutions', paired key-table cells '1' with '11' when keys print as '(B)', and took '…Differentiability)' inside working as a new chapter.
- chapter_reader: named_role() (role heading naming a known chapter, digit-led titles like '3D Geometry' allowed), name_heading() rejects brackets, bookmark_plan() adds key/solution starts from child bookmarks.
- book_reader (READER_VERSION 4): key table + solutions on one page are both read; '(B)' key cells; group labels '(Q16–Q30)' not flagged; under a plan only the current chapter's printed key/solution headings are used.
- book_worker: use_bookmark_parts() reads by the PDF's bookmarks when they mark every chapter's key/solutions (owner plan wins); on the v4 re-read, never-released old-label mocks are deleted and kept pages are relabelled by page range.
- Result on the owner's PDF: 32 chapters × 50 questions + 50 worked solutions + key, no conflicts; only Mathematical Induction Q37/Q38 (page 183, tall matrix) held for a crop fix.
- Tests: iteration_190 (all requested passed), iteration_191 + self-run tests/maths_bookmarks_iso190.py 36/39 — the 3 failures are a synthetic case (published old-label mock owning part of a chapter), impossible on the live book (0 published mocks). Regressions 178/182/key_table_split190 pass. NOT deployed.
- Known stale suites: book_publishing_iso170, book_publishing_rules_iso170, book_capture_iso170 (uploads lack section_id).


## 2026-11-16 — Owner editing power (preview only, NOT deployed)
- Edit questions on every Draft PDF mock: answer buttons A–E, type options the picture cuts off (students see them under the picture), change the answer; filter "Fewer than 4 options".
- PDF upload: 8 retries with backoff and 90 s per part, waits while offline, resumes a half-sent copy even after it was moved to the Library.
- Library: Delete / Delete all / Delete selected beside Restore (tests and uploads); students keep score lines only.
- Master: visible Live/Off switch on every mock row, status menu labelled STATUS; AITS day papers get a Live/Off switch.
- Body limits: library.restore/delete 128 KB, book_imports.fix_question 64 KB.
- Tests: iteration_185, iteration_186 (tests/typed_delete_iso185.py, retest_iso186.py).


## 2026-11-15 (newest) — Simple PIN, One Account, Exam-Day Readiness (preview only, NOT deployed)
- Forgot PIN: POST /api/auth/pin/reset {phone,new_pin,confirm_pin}; /forgot-pin screen; 'Forgot PIN?' link on /login; "There is no public PIN reset" removed from login and privacy page.
- Change PIN in Profile verified working (shared replace_pin helper).
- Student PIN hash bcrypt cost 12 → 8 (re-hash on next sign-in); staff passwords unchanged.
- Stale tab after deploy reloads itself once; source line refreshes exam/section names on every route; a read PDF restored from the Library shows again in Master Uploads.
- docs/APP_INTEGRATION.md (Forgot PIN for the app), docs/SERVER_SIZE_REQUEST.md (10–12 vCPU, DB for ~1,400 saves/s).
- Tests: iteration_184 all pass; tests/forgot_pin_iso184.py 53/53.


## 2026-11-15 (latest) — Clean source line, fresh start, Library redesign (preview only, NOT deployed)
Students and the app now read where a test sits ("BITSAT · Chapter-wise Tests · Physics", "JEE Main · PYQ Papers · 2025") instead of file names or back-office text. One-time fresh start: only JEE Main PYQ stays for students; all other tests, All India series papers (dates kept) and uploads move to the Library; Rapid Fire untouched; student attempts untouched. Library redesigned as a plain recycle bin: stats, guide with next upload steps, exam tabs, type chips, search, exam › type groups with subject sub-headers, select + sticky restore, restore dialog in plain words; series papers return to their day when free.
Tests: fresh_start_iso183 38/38; regressions library_aits_iso180 125/125, master_iso181 124/124, structure_iso173 133/133, chapters_iso182 58/58; testing agent iteration_183 passed after 3 small fixes.


## 2026-11-15 (later) — Chapter PDF reader + Draft preview (preview only, NOT deployed)
Chapter-wise PDFs of any layout are split into one Draft test per chapter by themselves: printed headings ("Chapter 3: Kinematics", "CHAPTER 03 — KINEMATICS", "Ch-2 Gravitation", "Unit 4 …", a bare syllabus name, "Answer Key – Chapter 3", keys at the back), else the PDF's own bookmarks, else the owner marks chapter starts on page pictures ("Q1 here" hints). Subject order: chosen by you > chosen at upload > printed in the PDF > cover/file name > chapter name; unclear subjects are asked and block Live. Chapters page: rename, subject, change starts, read again (with confirm). Uploads list keeps chapter uploads with a Chapters button. Draft preview: "Try as student" on every Draft with questions (Master list and Fix page) builds a private copy exactly as publishing would and opens the full student flow (preflight, player, submit, results) for owner and reviewers; students never see it. No AI used.
Also: page pictures use the asset lane and load 3 at a time with retry (they hit the 503 busy guard otherwise); mock_solutions skips qa_only sets.
Tests: chapters_iso182 58/58, master_iso181 124/124, structure_iso173 133/133, structure_imports_iso174 51/51; testing agent iteration_182 7/7 flows.


## 2026-11-15 — "Ek Master" Phase 1 (preview only, NOT deployed)
Built: Master screen (exam › mock type › mock) with a Today line (to fix, ready for Live, student reports, nightly data-check note); mock types with default time and marks; Upload PDF (main + optional key + optional solutions PDFs joined in the browser with pdf-lib, then the existing resumable book upload); Write editor (one question, paste whole paper, Excel rows, photos for question, options and solution); one status endpoint for Live / Scheduled / Off / Library on one or many mocks, with the Live exam switch; test series for any exam (dates, days, open and last-start time, give a day, Fill days in order, free days, Show on Home); student series cards on Home and the opening page and a series page; reviewer view limited to mocks to fix and student reports.
Removed from the screen: AdminOverview, AdminContent, AdminUpload, UploadWizard, AdminReview, AdminSchedule, ContentTools, DataHealth, WaitingList, AiReviewPanel, JeeTransferPanel, MockBookPanel, SeriesSchedulePanel, SeriesBookPanel, BookUpload, BookAllowances, StudioEditor, studioContracts. Their backend routes are unchanged. No content, attempt or score was deleted.
Engine changes (no AI): a heading-less PDF becomes one mock; type defaults fill missing printed rules; key-only mocks no longer need a per-question tick unless the book prints or promises worked solutions; unreadable PDFs show a plain reason instead of reading forever.
Authorization: owner for everything; reviewer may read and fix only book mocks in the to-fix state and written drafts that still have marked questions (404 otherwise), cannot add, delete, paste, change status or see series; verified PYQ papers refuse rename, move, schedule and Library.
Mistake during this session, fully undone: a stray `git rm --cached -r .` staged the removal of frontend/src from the git index; it was reverted with `git restore --staged` before any checkpoint, no file was lost.
Also during this session the preview backend was down for about 50 minutes (a lost line break in master.py, fixed). Evidence: tests/master_iso181.py 124/124, tests/master_jee_series_iso181.py 17/17, library_aits_iso180.py 125/125, structure_iso173.py 133/133 (isolated DBs, storage + AI mocked). Testing-agent report: /app/test_reports/iteration_181.json (no bugs in the flows reached; it did not reach the series panel with papers, the Fix screen, photos, Excel or the chapter and PYQ dialogs, which the main agent then checked on the bridge).


## 2026-11-14 — Super Admin: Library, replace by upload, Ready desk, Held fixer, All India Test Series uploads (preview only, NOT deployed)
User asked for: a book/paper upload into the All India Test Series (AITS, 62 days); replace or remove one, some or all mocks and chapters (AITS too); a clickable Ready status that publishes; a way to fix held papers. Also, once on the next deploy, move BITSAT mock-wise + chapter-wise and JEE Main chapter-wise content into a private Library you can restore. PYQ is never touched. Choices: AITS needs both ways to schedule (pick a day for each mock, or auto-fill); students keep old scores; private restorable Library; the cleanup runs once on the next deploy.
Built: tejas/library.py (GET /api/admin/library with tests + set-less uploads; POST archive {ids}|{section_id}; POST restore {ids, uploads}; GET export ZIP with test JSON + original PDFs + manifest; cleanup_once() at startup, idempotent through the tejas_migrations doc 'library-2026-11-bitsat-and-jee-main-chapters'; PYQ refused by test_kind and by pyq section). Replace by upload: books (replace_ids/replace_all), papers/Excel and chapter books (form field 'replace'). Old tests stay live, marked "being replaced", until the new upload is published, then they move to the Library in the same catalog slot. Ready desk: GET /api/admin/catalog/waiting, POST /api/admin/publish-ready (book mocks, books, chapter books; now or at a chosen time). Held fixer: GET .../mocks/{mid}/problems and POST .../fix (owner checks the answer type, options and key; optional key-only; native recheck, no AI). AITS: the wizard offers "All India Test Series"; GET /studio/all-india-jee lists AITS books and mocks; assign kind book_mock (+replace); fill (auto days in printed order); clear (all future days); DELETE book-mocks/{id}; the worker builds each mock privately for its day.
UI: Library page + nav, Section select + bulk Replace / Move to Library, Replace all / Move all, AITS row on Exams & Content, ReadyAction popover on Ready chips (Review > Ready tab, Upload lists, student preview), HeldFixer on the book page (?fix=), SeriesBookPanel for AITS books, rewritten Schedule AITS panel.
Preview: the one-time cleanup already ran on preview restart: 50 BITSAT mocks, 94 BITSAT chapters, 78 JEE Main chapters are now in the Library; PYQ untouched.
Tests: QA iteration_178. Isolated harness tests/library_aits_iso180.py found 2 AITS bugs (refill after clear, replace freeing the day before validation). Both fixed, rerun 125/125. Preview UI non-destructive checks passed. Minor items also fixed: set-less archived uploads restorable, PYQ section guard, trimmed replace ids, chapter-book exam on the queued view, PYQ hidden from wizard replace.


## 2026-11-14 — Live exam 15-minute start window + instant score; production deploy dispatched
User: "Start Window: Let each live exam have a 15-minute start window, so a student who gets in late doesn't lose time" + "Whoever enters late will get proper 3 hrs from their time but result for timely student will also be immediate after submission." Defaults (user said stop asking): new starts refused after 15 min; upcoming already-scheduled live exams get the window; All India series unchanged.
Built: tejas/live_window.py (window, guard, score_sealed, apply_to_upcoming at startup). Regular live exams: last_start_at = start + 15 min, end_at = last_start_at + duration, each student's deadline = own start + full duration. Score (summary) shown right after submission (results 'embargoed' + score_released + summary); answers, solutions, ranks, reports, retries stay locked until end_at. Competitions API adds last_start_at/can_start (status unchanged). UI: competition cards/detail, EmbargoedResult score card, Studio schedule summary. App guide section 13 (docs + public download, SHA256SUMS updated).
Tests: test_start_window177_isolated 26/26, QA iteration_176 128/128 backend across 5 suites + 21/21 edge suite, frontend flows mocked 100%. Then the user said "Go Live"; deploy dispatched with the integrity + speed work.


## 2026-11-14 — 1-lakh capacity audit, data integrity auto-repair (preview only, NOT deployed; waiting for user go-ahead)
Production read-only audit (deployer): 48 attempts all consistent with their frozen score records, no wrong scores, no duplicates, no expired open attempts. Found 13 ranking entries for missing attempts, 7 leftover score records, 1 failed report job.
Built: tejas/integrity.py (owner-only GET /api/admin/integrity, POST /api/admin/integrity/run; 19 checks, counts only; safe repairs archive before delete into tejas_integrity_archive; ledger is source of truth; report-only checks never modify). It runs from maintenance on the first run after deploy and then nightly 2–5 AM IST. Super Admin Overview has a Data health panel (DataHealth.js) with retry on error.
Speed: per-process sealed paper cache (tejas/papers.py) for preflight/start (CPU per preflight 8.4→3.4 ms, start 16.2→8.5 ms); student session check cache 10 s with logout/PIN change/owner reset eviction; leaderboard shared 10 s cache + index (p50 203→54 ms at 4,000); maintenance drains mass-submit grading backlog in batches; security middleware rewritten as pure ASGI (save CPU 3.98→3.32 ms) and unhandled 500s now keep the {data,error,meta} envelope and headers.
Tests (isolated DBs, dropped): test_integrity176_isolated 32/32, test_iter177_t1_isolated 44/44 (QA iteration_175 found the waiting_for_score requeue bug, fixed), test_iter145_load 5/5, 4,000-student bench (all started, submitted and graded). Stale old tests test_iter118_auth_cors_isolated (2) and test_iter119_denied_headers (1) send phone without PIN; unrelated.
Preview cron already ran the integrity check on preview: found 0, fixed 0.


## 2026-11-14 — Organised Super Admin Phase 1 (preview only, not deployed)
Built: 7-part Super Admin; Exams & Content (create custom exams hidden until Show on Home, custom sections, reorder sections/tests, rename, Live/Unlive switch, move within exam, unplaced list, advanced tools); destination-first upload wizard (book / paper / Excel / chapter book by section layout) with student preview; book detail with "Publish all ready" (now or scheduled) and per-mock switches; Review (held reasons, reports, solutions, mock-book checks); Schedule & Live; Students; Team (reviewer list/grant/remove). Student Home/exam hub/section pages now read the structure from /api/catalog/*. Hidden exams blocked for students on list, detail, preflight and start. Auto-publish removed (legacy 'publish' action no longer enables it). App guide section 12 added (docs + public download copy).
Fixed after QA: scheduled per-mock release shown as published; legacy publish re-enabling auto-publish; resume_mock state; PDF paper into chapters section; chapter-book destination validated before dedupe; empty file 422; '1 test' plural; import page shows destination.
Tests: structure_iso173 133/133, structure_imports_iso174 51/51 (isolated DBs, storage + AI mocked).


## 2026-11-13 22:05–22:16 UTC — maintenance switched on in preview, deploy dispatched (outcome pending)
User approved both the deploy and the maintenance job after seeing its production effects (13 expired attempts closed, 12 submitted attempts graded, 1 report job re-dispatched).
Added WEBHOOK_CRON_SECRET to preview backend/.env (generated, never printed) and restarted the backend. No app code changed.
Preview check: platform dispatch script 200, scheduled 22:15Z run 200, endpoint checks 7/7. Maintenance closed and graded 2 preview attempts that had been expired since 2026-10-26.
Deploy dispatched about 22:13Z (code-only, same production DB and secrets, plus the new key). At 22:16:30Z live still served the old build. Not verified: deploy result, cron on production, a real book upload on production.



## 2026-11-13 late night (fork) — diagnosis only, no app code changed
Found: the book-processing stall fix is not on production because no deploy ran after it was written (deployer: newest run afd285f5 completed 10:25:43Z; fix saved 19:48–20:33Z). Confirmed from outside that the live bundle lacks the fix's strings. Fix files are still uncommitted in git.
Re-ran the book suites in isolated DBs (storage + AI MOCKED): 270/270. Frontend production build compiles.
Maintenance cron left off: its first production run would close 13 expired attempts, grade 12 submitted ones and re-dispatch 1 report job; the user has not agreed to that. A new key in preview backend/.env reaches production on the next redeploy.
Slowness not reproduced; stalls measured from the preview pod fell in a window in which unrelated hosts stalled too. Showed one error-page mechanism on live (old tab after a deploy), not fixed.
Not run: real-storage 100 MB probe, cron secret, any deploy.



# Performance work — dated implementation and measurement history

## 2026-11-13 night — large-book stall fixed (preview only, not deployed)
Cause: jobs.drain_lane quantum (16) ended a book's batch chain after 17 batches (340 pages); cron recovery is dead because WEBHOOK_CRON_SECRET is missing. Repro in isolated DB: 421-page book stuck at 340/421 with 1 queued job for 50 s. Fix: book_step lane continues in a fresh task. Also fixed a retry storm (failed or late publications were retried every batch) with BookMock.publish_hold kept across rebuilds and cleared by owner-requested runs. BookUpload retries a failed part 3 times; Pause works mid-retry. Added "Upload Book" entry points in the account menu and Content Studio.
Tests (isolated DBs, storage + AI MOCKED): 270/270 across iso170, rules170, ext170, scale171 (new groups: chain, holds), large, pages. Browser smoke without a job pump via tests/book_bridge172.py: 421 pages / 30 mocks published by itself; injected 520 retried; desktop + mobile, no overflow. Not tested with a real publisher PDF or on production.
Not changed: cron secret (needs user decision), production (needs redeploy).


## 2026-11-13 evening — post-deploy outside checks, deck numbers, no app code change
User kept the 100 MB-only limit; plan/deck.md updated to match. Re-ran tests/book_scale_iso171.py size key3: 11/11 (isolated DB, storage + AI MOCKED).
Live https://jeelive.ai, unauthenticated GET only: /api/health 26/26 200, same 136 API paths as preview (23 book routes), bundle carries the new upload copy, anon admin 401, owner-login renders desktop + mobile. Nothing behind login was tested on production. Read-only deployer diagnosis (its report): run afd285f5 live since 10:25Z, 2 pods healthy with 0 restarts, zero 5xx/tracebacks, 1 owner, ADMIN_* present, 0 books on production; no fault confirmed; pod memory under a 100 MB upload, 520 recurrence and authenticated flows remain unconfirmed. Owner-login seeding behaviour documented in PRD status.


## 2026-11-13 — Limits: only 100 MB per PDF (tested in preview; user deployed later the same day)
User: "1000 page ka limit hta do bas mb ka limit rkho 100 mb"; chose "Mock limit bhi hata do". Page and mock caps removed; 3-digit mock headings ("Mock Test 120", "Answer Key - Mock Test 100"). Scale: sandboxed worker batch API with hard-linked cached original (/tmp/jeelive-book-originals, sha-verified, newest 6), 20 pages per step, max 5 mocks published per step with lease renewal, upload parts deleted after original stored, resume no longer capped at 100 parts.
QA171 (isolated DBs, storage+AI MOCKED, real parser): exactly 100 MiB/200 parts accepted, +1 byte 422; 1,501 pages/150 mocks read in 75 steps (127s, ~215MB RSS) and all published; 100 MiB file peak ~580MB RSS; browser 54.7MB/110-part pause+resume. Found endless loop (auto_publish off, >5 ready mocks) + ROLE 2-digit headings → fixed; retests key3 11/11, pages 23/23. Real phone [number not stored] checked: login works, but it is a student account → Super Admin API 403 by design (owner uses email/password /owner-login). Session logged out; no role changes.


## 2026-11-13 — Phase 1 book publishing (preview only, not deployed)
Super Admin → Uploads: combined PDF (50MB/1000 pages/50 mocks), resumable SHA-256-verified 512KB parts, PDF+edition dedupe, background batched reading, book map, page review desk (crop drag + coordinates, region identity, continuations, shared passages), range mapping, printed-rule desk (JEE Main/BITSAT/COMEDK/Custom, per-section marking, BITSAT 12-bonus), automatic per-mock publication with isolated holds, schedule/missed-release decision, competitive embargo, pause/resume/remove (access removal only), corrected versions preserving old attempts, separate bounded AI reading and two-pass explanation allowances, student /book-series.
QA169 found 3 HIGH (later mocks held, global unmapped holds, series crash) → fixed. QA170 203/206; remaining instruction-sentence role bug fixed; targeted ext170 rolewords+worked 21/21. Synthetic labelled PDFs only; storage + AI MOCKED in tests; real sealed parser. Customer DB: 0 test books/sets/users; isolated DBs dropped.


## 2026-10-27 — verified performance release queued
Final168: 23/23backendtests incl400pixel-exactoriginalcrops; Jan24S1coldpreflight4667→1163ms,Apr08S2 9126→354ms,warm6–7ms; Janimages58.28→53.26MB(-8.6%), renderCPU10.76→9.12s(-15%vs164), median156→137ms; sourcefanout7→1. Yieldresolvedmeasuredco-locatedseries1028→135ms,healthp9542.5→1ms. Aproutputbyteidentical, one400.6msmaxoutlierremainsunproven,p95122ms. ServerbenchmarkusesMOCKEDstorageboundarywithactualoriginalPDFs; notproductionRTT/global4G/500kqualification. 167frontend9races+21Node/buildpass, desktop/mobilefinalsmoke168renders/nooverflow; mainviewedfinaloriginalPNGquestion+solution. TestDBsremoved, realdata/credentials/academicrecordsuntouched, noappintegrationsmocked.
Deployment accepted/QUEUED job/client_ref bcd75d41-4661-4f5a-bead-654e0ffe34d2. Latestmaincode29895fe plusnonappreports/docs; do NOTredispatch/poll/wait(toolinstruction:deploymentpanel/systemnotificationwillreport). Noactualpublishedstatusyet. ExistingDBbinding/secretsmustremain,nohistoricalreset/import/PINmutation/noRedisinfra/costchange. LIVECloudflare520remainsunresolvedplatformtransportfailure; don'tclaimcachefixorincidentticketopened. NoRedisprovisioned/sharedcacheenabled. Operationaldocupdatedactualmeasuredruntime vsreferencearchitecture.


## 2026-10-27 — QA166/167 complete; final CPU/fairness refinement
166passed100backendcorrectness+2xbenchmark:19papersallrefgeometry/pagecount,400RGBpixelidentical; wholepagepreflightJan~1.13s/Apr.33s vs4.69/9.13. 167frontend9races+21Nodetests+prodBuildpass; lateAactive/completedcannotoverwrite/redirectB, correctBPUT/drafts,StrictModeno5sstall, bothwidthsoverflow0. Noappchangesbytesters,allisolatedDBsremoved. Mainviewedfullrealquestion+solutioncrops, noformula/colorchange.
166foundPNG6CPUregression+31%/coldJanimage for19%bytecut,April90/199imageslarger; replacedwithmeasuredfasterPNGlevel1ONLYreviewedlargepagewidth>1600pt fullres, ordinary/AprilnativeMuPDFencoderretained. Added1msworkerthreadyieldaftereachwholepageraster (max26ms/paper) topreventbacktobackGILstarvingAPI; notprocesspool/notbackgroundscheduler. Rendercachev5. Need168narrowbeforeafter+pixelcorrectness/fairness checkbeforepublish. MuPDFbothold/newwarnsbutacceptstruncatedJPEG; canonicalhash/sourceauditunchanged, notnewcorruptionrejectionclaim. Nonintrefsaretrustedcuratedschema, preexistingtypeerrorsnotexpandedscope. LiveCF520stillrequiresplatform intervention.


## 2026-10-27 — 164 evidence and 165 diagnosis; second implementation
164 correctness passed: 400 original crops RGB-identical, isolated PYQ25/load5/pixel12, browser production-build complete start/save/reload/submit/originalsolutions desktop/mobile. Source GET fanout7→1; no duplicate question revisit/zoom or start GET, 4asset/3studio bounds, RAM isolation and one401refresh tests passed. Cold4.7/9.1s and imagebytes unchanged; doNOTclaim improvements there. Report164reconstructed165fromrawXML/JSON afteragenttime limit. AllisolatedDBs/temporarycredentialsremoved; live520stillunresolved. Q2Jan24S1ref0 visuallyverifiedcomplete; ref1surplusMATICSheader, notmissingcontent; noacademicmappingchange.
165 profilingproved85–99%validationtimeinsideMuPDFper-clipimage decode/downscale; DisplayListbuildonly5–9ms. Prototypewholepagerasteronce gives1.36/.36s butlowrespixelsdiffer, so NEVERuseforstudentdelivery. Implementedvalidate_crop_pages ONLYdiscardedpreflightvalidation: shared_geometrychecksEVERYref, page/rect/omit/pixelarea, fullpage.3renderonceperreferencedpage, noPNGencode/cachepagebitmap. SHA/file/auth/fullrefproof remains. Deliveredcropstilloriginalcliprender; PillowPNGlevel6 lossless sameformat toreduceJanpayload(~19%prototype), potentialCPUtradeoffmustmeasure166. NoWebP/lossy/resolutionchange/nativecontractbreak. Proof/rendercacheversionbumped.
165reviewflag Playerroute race ACTUALLYREPRODUCEDmainread-onlyMOCKEDbrowser: URL/attempts/B, onlyGETA, titleFixtureattemptA afterdelay. Firstreprofixturequestionreportswrongobjectcrashed, correctedactual[]; secondconfirmedrace. FixedPlayerRoute keyeduser+attempt, abortpendingloadcleanup, ignoreabortedresponse beforedrafts/navigation, retainStrictModefreshload andstartoneusehandoff. Needs166targetedrace/build/wholepageguards/pixelfidelity/baselineafter+mobile; no appsuccessclaimbeforetests. No productionchangesyet.


## 2026-10-27 — first performance implementation batch (verification not yet run)
Backend: per-validation2-pageboundedDisplayListcache sortedbyPDFpage; preservefullall-refvalidation/permissions, explicitowned-documentfinallyclose. SmallerPNG usesGRAY ONLYwhenR==G==Bpixelwise; coloredpixelsremainRGB, needpixel-equivalenceQA. Derivativescallrawrendereronce(no2ndSHA/corecachecopy),versionrender3. Sourcecache64MiB+32stripedlockscoalescecoldGETandPUTinvalidate, originalSHAchecksremain. NoRedisinstalled/configuredbecauseunavailableandnotcurrentDBbottleneck.
Frontend: commonfetchWithSession401onlysingle-flight+staggeredresponseversionhandling forJSON/images/download; privateResources12MiB RAM-onlyblobLRUplusactiveleases,4inflight,epoch/abort/logoutclear; no-cacheHTTPunchanged. SourceImageusesblobURLandlazyvisibility, zoomreusesbytes. Nextquestionprefetchmax2(skipSaveData), startviewRAMoneuse5sTTLsameuser/attempt(nohistory/privatepayloadstorage), existingfullreloadstillcanonicalGET. RemovedunusedGoogleInterCSS,latinfontsubsetimports+buildonlyactualcompiledFigtree400/700preload; mainminheightavoidslazyfooterCLS. Allnewfilesexportssettled; no testsrunmidcoding.
Deployercriticalfollowupconfirmedlive520outsidepods, no toolingtofixplatformnetwork. Sent actualplatformsupportescalationrequest; doNOTclaimincidentopenedunlessconfirmed. Separateprobe/health404latenthardenonlynot520cause; currentlyno unprefixedrouteadded dueAPIprefixrules. Nativecontracts/canonicalwritesunchanged. Baseline163q2headerfragmentneedinspectallrefsread-onlybeforeclaimcontentmissing. Next actualrendererPNGpixel/viewverification thenonesmoke+testing164 fullaftercomparisons/privacy/staleauth/sourcefidelity/isolatedload. No realcustomerlogin or testwrites.



## 2026-10-27 — user-approved performance project, baseline captured
Original user request: “Testing kiya world best ke hisab se 40% hi hai 1. Speed of api fetching 2. Speed of loading of tests and website 3. Use of world best practices of coding ..redis , caching canonical forms databases and all ye sab boht weak hai . Make it the world best”. User chose “b. Tests ke baad live bhi karo”; added “World best yaar. Yhi mera future hai”. No paid infrastructure authorised. Preserve all IDs/accounts/papers/attempts/results and native API compatibility; Rapid Fire untouched.

Baseline163 is real evidence, not marketing: live low-rate9/46GETs hung30s thenCF520, including trivialhealth0.5ms; preview0/15. Healthy2fixedreplicas1vCPUeach/2Gi request4Gi limit, no Redis, no HPA; backend logs miss edge-generated failures. Deployer RCA402afcbe correlated network/ingress, follow-up critical escalation queued. Do not claim solved until repeated live health/API end-to-end checks pass. No customer test writes/live logins.

Cold original-source preflight Jan4.67s/Apr9.13s, warm7ms. About200refs reparsed same PDF pages; DisplayList reuse microprofile0.85s/0.09s. Jan81questionPNGs58.3MB; color fidelity must remain original, so grayscale allowed ONLY if RGB channels are exactly equal. RGB→lossyJPEG or blanketgray is NOT approved. Core crop cache32MiB + derivative48MiB duplicate data; source32MiB, no request coalescing:10concurrent images caused7fullPDFdownloads128.7MB. Need byte-bound single-flight source reads, one crop cache, document close, per-validation bounded display lists. Do not share mutable PyMuPDF documents across threads.

JSONAPI/DB healthy in isolation: commonreads~2–7ms, allIXSCAN, no grounds for broadDBrewrite. User-state PYQ aggregation maychoose popularity-shapedindex; require larger synthetic fanout evidence beforelocalhint. Canonical Mongo majority/journal answer ACK/idempotence, deadline/ledger correctness remain untouched. Redis secrets/service absent; no fake Redis claims/provision; first fix provenCPU/network. Read Redis integration playbook, optionalfuturemanagedRedis requirescredentials/costapproval; not essential forcurrentfastmetadatareads.

Frontendbaseline: coldhomepage~1.0sLCP andwarm160–252ms fromUSdatacenterunthrottled(NOTIndia4G), mainJS170KBgzip,CSS60KBgzip, latefonts+unusedInterGoogleCSS, authlazyfooterCLS0.14–0.37. Start alreadyreturns53KBattempt butPlayerfetchesagain. Images no-store(revisitrefetch) andeveryimageerrorPOSTrefreshes, notjust401; sharedrefreshpromise unused. Planper-user MEMORY-ONLY byte-bounded blobs/coalescing with authgeneration/logout clear, no persistentprivateHTTPcache, authbeforecache/releasegateunchanged; nextquestionprefetchbounded. Reuseone-usefreshstartresponseinRAM, neverhistory/localStorage. Fontpreloadstaticcompilation, removeunusedInter, reservemainloadingheight.

QA baseline files: tests/iso_harness_perf163.py,bench_iter163_perf_baseline.py,iso_bridge_perf163.py,compare_perf163.py; reportsiteration163 +iter163_perf_baseline.json +iter163_live_frontend_baseline.json. All original PDFs via localstorageboundary; realnetworkstorage latency NOT measured. Repeat exactafterharness, comparecold/warm/CPU/payload/RSS/error/receipts; full privacy/render pixel fidelity required. No implementation or new dependencies installed yet as of this entry.

Earlier project history is preserved, unchanged, in PRD.md; new detailed entries continue here to prevent that file exceeding700lines.

## 2026-11-14 — Section phone preview link + production deploy dispatched
- Owner-only GET/POST/DELETE /api/admin/catalog/sections/{sid}/preview-link: create (rotates old link), status, turn off. 7-day expiry, 192-bit token, only sha256(token) stored in tejas_section_previews, audited.
- Public GET /api/preview/sections/{token}: read-only titles/order/status (live, draft, paused, unlive, scheduled, ended) plus combined-book mocks waiting to publish (ready/held/publishing/scheduled, falls back to book-level release_at, shows the book title). No question content, ids or answers. Hidden exams/sections still preview but stay unreachable for students.
- UI: "Phone preview link" button in Super Admin › Exams & Content › section panel (copy/share/open, make new, turn off). Public page /preview/s/:token, mobile-first, subject groups only for chapter layout plus a "Waiting to publish" group.
- QA174: isolated DB 67/67 (tests/section_preview_iso175.py), frontend passed; the 3 minor QA items were fixed and the isolated suite re-ran 67/67. Customer preview DB: QA created and then turned off links on jee-main:mocks and bitsat:chapters (revoked rows + audit only).
- Production deploy of the whole organised Super Admin + preview link dispatched (job bcd75d41-4661-4f5a-bead-654e0ffe34d2); live confirmation pending.

## 2026-11-14 — Native mock-book reader fix (no AI): answer keys, solutions, crops, safe re-read
- Root cause on live (4,481-page JEE book, 50 mocks all held, ~25,000 issues): "Answer key" / "Detailed solutions" pages were read as instructions, so no mock had keys or solutions. Source PDF was fine; it was the reader.
- tejas/book_reader.py: explicit key/solution page roles bound to the current "Mock N" + subject; key cells parsed natively; no false anchors from formulas, solution steps, wrapped lines, "Q2 = 1", stray "511."; header/footer labels ignored; crop cuts follow the printed row (tall glyphs, big brackets ⎛⎜⎝ / private-use pieces, 2x2/3x3 matrices, integral limits) and never cut inside a header. READER_VERSION bumped.
- tejas/book_publish.py: continuation issues name the page the question starts on ("starts on the previous page"); unused imports removed.
- tejas/book_worker.py: books read by an older reader are re-read automatically on recover(); owner repairs, AI-approved pages and pages of published mocks are never touched; no duplicate mocks; no AI allowance is ever created by native reading.
- Results (in memory, no DB writes, no AI): BITSAT 1,284 pages 50/50 ready, 0 issues. JEE 4,481 pages 35 ready / 15 held, 38 issues = 19 questions (Q20/Q45/Q70 at section ends) whose type/options cannot be confirmed from the print plus their follow-on checks; these stay held on purpose for owner review. Synthetic 3-mock book 2 ready / 1 held (deliberately broken mock stays held). Crop edge audit: only 2 physically overlapping rows left (cosmetic).
- Tests: tests/book_reader_regressions178.py (all pass), tests/reread_iso179.py 15/15 (isolated DB), tests/repro_book_rebuild.py, tests/boundary_slice179.py, tests/audit_crops.py; testing agent iteration_177. Test PDFs live in /tmp/book (lost on pod restart; not committed).
- NOT deployed. Production book not reprocessed yet; waits for the user's go-ahead.


## 2026-11-16 — Clickable PDF counts, JEE AITS 9 Dec–27 Jan, owner early access, series inside its exam
- User (Hinglish): dashboard numbers clickable (Held → all held); JEE AITS 9 Dec 2026 – 27 Jan 2027 (50 days); papers whose day falls outside lose it ("Unka din hata do, main dobara dunga"); BITSAT AITS only inside BITSAT, no separate card; super admin abhishek@billpe.com takes AITS from today "Asli student jaisa, rank mein gine".
- BookPublishing.js: Detected / Complete / Held / Published / Scheduled are buttons that filter the Book map (book-filter-*, book-filter-note, book-filter-clear); count numbers now 30px (CSS scoped to direct label span).
- live_series.py FIRST 2026-12-09, TOTAL 50, LAST 2027-01-27; series_streak cups end at 50; one-time jee_dates_job (tejas_migrations 'jee-series-2026-12-09-50-days', via library.run_cleanups) moves the series doc and removes days outside the range (papers stay published as "without a day"; pending book mocks lose their day). Preview: done, moved 0.
- Owner early access: owner role sees future given-day papers (early true) on /series/all-india-jee and /series/<sid>/schedule, can open and start them as a real series_live ranked attempt (content.permitted + attempts.guard_start early). Students unchanged. "EARLY · ONLY YOU" section on the hub.
- SeriesCards removed from Home/Landing; catalog exam returns the AITS section with series_path, ExamHub links to it. Master toggle is "Open to students".
- "Give a day" waits up to 30 s (one budget per request) for a busy PDF instead of the instant "book changed / processing" 409.
- Tests: testing agent iteration_187 (47/47 new + 124/124 regression in isolated DBs, frontend all flows); follow-up fixes: schedule_data uses stored series_window, single wait budget, metric styling. NOT deployed.



## 2026-11-16 — Simple Start test, 60 s get-ready with whole-paper loading, AITS score + solutions on submit
- Live RCA (deployer): "Check my device" hung >2 min because POST /sets/{id}/preflight validated ~150 crops one by one (Cloudflare 100 s timeout), and the check repeated every minute per pod.
- User (Hinglish): keep it simple for every test; Start test → 60 s counter with fun rules, "Begin now" allowed; whole paper must load at once and keep loading; AITS marks + solutions right after submit, rank after the day closes.
- SetDetail.js rewritten: facts, marking, 3 steps, one "Start test" (no integer box, device check or checkbox). Start sends get_ready:true; start no longer needs preflight; preflight no longer validates sources (papers.needs_check removed).
- attempts.start: ready_until = start + up to 60 s (shortened only so a live window never cuts solving time); deadline = ready_until + duration. POST /attempts/{id}/begin ends it early (deadline = now + duration). Answers and visits rejected while ready_until is in the future. GET /attempts/{id}/assets/pack returns 12 pictures per request (binary header + PNGs, skips a bad crop).
- Frontend: GetReady.js (ring countdown, 6 rules, load bar, Begin now enabled at 100%, opens by itself at 0), preloadPaper in privateResources.js (2 workers, retries forever, falls back to single pictures, pins images in memory), useAttempt computes ready synchronously.
- live_window.answers_sealed replaces score_sealed: All India series show score, answers, solutions, reviews, retry, report right after submit; regular live competitions unchanged. New GET /attempts/{id}/series-rank (sealed until the day closes, then rank among the day's live attempts; owner's early attempt counts as asked). SeriesRankCard on results. "Result sealed" status/filter removed. Texts updated (hub, banner, player, SeriesPage). docs/APP_INTEGRATION.md updated.
- Tests: iteration_188 (backend 47/47 + 47/47 regression; 2 frontend bugs fixed), iteration_189 (109/109 backend, all retest items pass; last CSS band fixed and checked by screenshot). NOT deployed.


## 2026-11-18 — Analysis 2.0 tested and polished, wrong-PIN-only sign-in limit with real student IP, preview load test + 1–2 lakh capacity report
- User order (Roman Hinglish): Backend fix → 8 sections → PDF → testing → rate limiter → scale test. Choices: "Haan, isi order mein karo"; "10 galat PIN, phir 15 min rok"; "Preview pe asli load test + hisaab se report"; "Analysis ko pehle perfect karo. Make everything perfect, elegant, and powerful."
- Hydration warnings ('<span> inside <tbody>/<tr>') came from the dev-only visual-edits babel plugin (frontend/plugins/visual-edits/babel-metadata-plugin.js wraps every {expr} child in a display:contents span). Fixed there: no wrapping inside table/thead/tbody/tfoot/tr/colgroup/select/optgroup/datalist/html/head. Production build never loads the plugin. 0 console errors on all 16 views afterwards.
- Analysis polish: topper time 0 → '—' (analysis.class_view topper_time `or None`, QsByQs, SolutionInsight, compare column + phone card); Qs-by-Qs headers '<label> · time' and 'Class topper'; waterfall Abhi → Careless → Risk → Time → Max with a dashed 'Target' line; '1 mark' singular; Time chart y-axis unit (m / %); AnalysisWorkspace set() uses the functional setParams (no stale mode=compare); Solutions filter jumps to the first subject that has a match.
- Testing agent iteration_195: backend 58/58 after its fix of analysis_api.load() (student's own name was overwritten by the name of the student ranked above → wrong name on analysis, PDF and scorecard); frontend all flows pass at 1920 and 390. tests/ui197_check.py: nav, fast Personal → Qs, compare and the Solutions filter jump pass.
- Sign-in limit (tejas/phone.py): client_ip() = the X-Forwarded-For hop just left of the last Cloudflare hop (Cloudflare v4/v6 ranges); typed leftmost entries ignored; None when it cannot be told (no Cloudflare hop / private) → only the per-number limit. Measured preview chain: '<typed>, student, Cloudflare edge, 136.110.214.0 (LB)'; peer is the private ingress 10.x; CF-Connecting-IP is not forwarded. Sign-in counts ONLY wrong PINs: 10 per number within 15 min of the first → 15-min wait (429 + Retry-After, PIN not checked), 100 per address → same wait for that address; 401 message says tries left; a correct PIN clears the number's count. Old 5-attempts-per-window and 20-per-hour budget removed for sign-in. Signup / Forgot PIN / Change PIN keep limit_pin (5 per number, 60 per real address per 15 min). docs/APP_INTEGRATION.md updated. tests/wrong_pin_iso197.py 32/32 (isolated DB). tests/test_iter156_pin_hour_budget_isolated.py now describes the removed hourly budget (obsolete).
- Load test on preview (backend/tools/load_live.py + new tools/load_accounts.py seed/remove): 9,000 seeded +91600197xxxx accounts, JEE Main PYQ 08 Apr 2026 S2. Public URL: 200 together 0 failures; ~500 from one IP → Cloudflare 429 "Just a moment…" challenge. Same server direct: 500 and 1,000 (30 s ramp) 0 failed sign-in/start/save, 2,000 → pod CPU 2.0/2.0 and auto-stop. Per student 3-hour paper ≈ 1.2 backend CPU-s + 0.43 Mongo CPU-s; 1 lakh ≈ 11 vCPU average / ~45 at start (pictures 7.4 MB per student); 2 lakh ≈ 22 / ~90. Report: docs/CAPACITY_REPORT_2026-11-18.md; docs/SERVER_SIZE_REQUEST.md updated. All load data removed via qa_cleanup (9,000 accounts, 3,889 attempts, …); preview back to 2 profiles / 8 attempts, 0 orphans.
- NOT deployed.



## 2026-11-18 — App team update packet (Analysis 2.0 and everything since 26 Oct)
- User (Hindi): one deep file for the app team listing everything the app must build after the earlier package, so nothing is missed.
- docs/app_packet/APP_UPDATE_2026-11-18.md: P0/P1/P2 checklist; picture questions (text ""), start + get-ready + /assets/links; PIN and busy/limit messages; time capture spec (v/a/m events, sid, n, server clock, timeline on answer saves/submit, /timeline, limits); Analysis 2.0 API, gates, class.state, every response field, 8 screens with Hinglish copy, comparative mode, leaderboard, learnings, PDF, share PNG, retry, Solutions insight line; exam structure, live window, series, typed options, bonus, display name; acceptance checks.
- backend/tools/export_app_analysis_samples.py: reads real responses from the isolated analysis bridge (synthetic students) into docs/app_packet/samples (14 files); analysis_rulebook.json from the server rules and copy.
- docs/APP_INTEGRATION.md: date, series-as-section bullet corrected (kind aits + series_path), new §16 pointer. Public copies in frontend/public/downloads/app-update-2026-11-18/ + jeelive-app-update-2026-11-18.zip (SHA256SUMS checked; zip downloads 200 from the preview URL).
- Found: the website has no screen to set the display name (API only), so leaderboards show "Learner xxxx" until a name is set.


## 2026-11-18 — Leaderboard name on the website Profile
- User: "Add a name field on the website Profile so leaderboards and compare show students' real names".
- frontend/src/components/DisplayName.js (new): row "Leaderboard name: X / Not set" + Set name / Change → dialog (max 20, counter, Save name, Remove name, server error as is, 3 per day note); setUser keeps display_name. Profile.js shows it for phone students and uses display_name in the identity box. CSS .display-name-row (learning-workspace.css).
- backend/tejas/names.py clean(): first character must be a letter/digit; combining marks (Unicode M*) allowed, so "राहुल शर्मा" is accepted (was 422 before).
- Checked on tests/analysis_bridge196.py (disposable DB): Hindi name 200; phone-like, symbols and leading mark 422; UI save → "Priya 2026" in the profile box and on the hero's leaderboard; analysis student name intact; 390 px no overflow. App packet §8.6 updated. NOT deployed.


## 2026-11-18 — Whole-site app theme (light default) + app navigation
- User (Hindi): whole website in the app theme (white/maroon/red/black), light default with a dark switch, phone = app bottom tab bar, laptop = top header, Home like the app, exam screen black-maroon bar + white question. Then: build Rank, My Tests, Mission; Rapid Fire as a picture only (not clickable) until the Play Store link comes.
- New: src/app-theme.css (light tokens, .feature-dark featured card, header pill nav, bottom tabs, home, rank/mission, My Tests chips/tabs, player, results, analysis, streak light fixes), lib/theme.js (light default, localStorage 'jeelive-theme'), components/BottomTabs.js, components/home/HomeParts.js, features/Rank.js + Mission.js (coming-soon), public/brand/rapid-fire.png + jeelive-vector-light.svg.
- Changed: index.html early theme script, ThemeToggle, Shared.js (HeaderNav + light/dark logo), App.js (/rank, /mission, body.has-tabs), Home.js, Landing.js, Profile.js (filter chips), TestCards.js (Solutions button), Player.js (dark header, testid), GetReady, Results.js score card, analysis Overview score block.
- Tested iteration_198 (frontend, disposable bridge): ~95% → tester fixed sticky player header, Get Ready title colour (--navy in .feature-dark), light streak text. Main agent then fixed: Rapid Fire gem no longer covers the analysis bar (bars sit 98px up, gem pointer-events none), phone signed-out header shows Log in, chip row fade, profile box full width, bigger ring score text; 390 px no overflow on / and /login. NOT deployed.



## 2026-11-18 — Rank 6 tools, Mission share gate, result sparkle, Dream college (from the App branch)
- User (Hindi): read the app codebase, build Rank's 6 tools, Mission like the app, result sparkle; whole site like the app except Rapid Fire. Choices: share-gated Mission, sparkle at own best or 40%+, light Rank page with jewel tiles, Rank public.
- Backend: rank_predictor/rank_tools/rank_bitsat/rank_comedk/rank_pdf (app logic + data, reportlab), dreams.py (5 dreams per exam, released full mocks, celebration), mission.py (personal link, friends counted once per real browser, bots ignored).
- Frontend: /rank public (Rank predictor, Percentile se rank, Target marks, College predictor JEE/BITSAT/COMEDK with college sheets + round ladders, College compare colleges/branches, Dream college), PDFs + WhatsApp share; /mission (impact panel, maker's card, share buttons); share gate on results after each fresh submit (useAttempt → lockResult); ResultSparkle banner + confetti once per attempt + Dream College Meter; Home Dream college section.
- Preview quirk found: the preview editor wraps dynamic children in display:contents spans, so CSS '>' selectors were replaced by classes/descendants.
- Tested: iteration_199 (backend 23/23 in tests/test_rank_mission_dream199.py; frontend fixes: real reachable counts, word-wise college search + aliases, compare auto-tick, pager scroll, result gate keyed by id) and iteration_200 retest passed; then fixed DOST medal contrast and BMS/PES aliases (checked).


## 2026-11-19 — Rank and Mission matched to the app's design notes
- User: match Rank (design_guidelines_rank_royal.md + _v2) and Mission (design_guidelines_mission_stats.md) to the app, "most powerful, elegant, and perfect"; Rapid Fire stays a Play Store entry only (no link supplied yet, still non-clickable).
- Rank (frontend only): app hero (red dash eyebrow, serif title, cutoff line, 'Free · bina login ke'); six black-metal jewel tiles with brilliant-cut diamond, NEW badges, live value lines (compare/dream counts), solid blood College tile, selected glow in the tool colour; form panels with the tool's colour band (Rank yellow, Percentile teal, Target lime, College red, Compare sky, Dream violet); summary row with 'Doosra number dekhna hai?' + Edit pill (College: purple shining bar); metal Rank Card (diamond watermark, chrome serif number, twinkling stars, red rule, № serial); medal coins on every row (4+ dark coin), top-3 wash; app tag colours. Mobile footer stacks; dark card edge.
- Mission: impact count-up 1.2 s; quiet 'Aapka impact card par dikhega' under the gate card when friends were helped.
- Tested iteration_201 (frontend, signed out, desktop + 390 px, light + dark): all passed, no console errors; then fixed 2 cosmetic notes (mobile card footer wrap, dark card edge) and checked by screenshot.



## 2026-11-19 — App hand-off pack (JEELIVE_Rank_Mission_Website_Handoff.zip) applied
- User uploaded the app team's Rank/Mission pack ("See"). Pack rule: the website keeps no college data or algorithms; all answers come from the app server word for word.
- Backend: new tejas/app_connect.py (allow-listed /api/rank/* proxy with a 16 KB body limit, /api/mission/me, /api/dream read/save/mocks/cheered as the signed-in student via /rf/access grants, /api/j/{code} redirect); app-server errors and refused sessions → 503 'Abhi load nahi hua…' (never 401). Released website full mocks are sent to the app server (checked at most every 30 s, re-sent after 10 min). Deleted rank_predictor/rank_tools/rank_bitsat/rank_comedk/rank_pdf/mission.py and rank_data/. dreams.py keeps only /api/dream/celebration/{id}. Env: JEELIVE_APP_API, JEELIVE_SITE_URL.
- Frontend: app DreamMeter + ProgressChart ported (Rank Dream tool, Home compact meter, Results); app college/COMEDK/BITSAT card stat boxes (CLOSING/ROUND/2025 SE, CUTOFF/AAPKA, FEE / SAAL), BITSAT AAPKA bug fixed, 5-year history bars scale to cutoffs; server filenames on PDFs; Mission share link from the server.
- Preview quirk: dynamic SVG children are hidden by the editor's wrapper spans, so the Gem and the chart are drawn from fixed markup; no bare 'span' selectors in these components.
- Tested iteration_202 (backend 18/18 + pack connect_check 22/22; frontend all flows with route mocks, no DB writes). Then fixed BITSAT history bar heights, the Dream exam switch at 320 px and missing-key guards in mission_me/_grant (iteration_203).


## 2026-11-19 — Analysis 2.0 Phase 1 finished (preview only, NOT deployed)
- User: build everything in plan/plan.md without asking, show it together.
- frontend/src/analysis2.css: styles for everything that had none ((i) popover, on/off chips, Painful by chapter, journey folds + result mark, Qs grid tag dot + class strip, leaderboard name box, Solutions four cards + question journey, Advanced link). Removed `>` child selectors that the preview's visual-edit span broke (score ring digits were stacking, tiles lost their width) and added a reset for that span.
- charts.js / parts.js: one LEGEND setting (legend order = bar order), Waterfall has Target and Max as bars (no overlapping dashed label), +0 steps draw a thin bar, pace "Sab jawab" line uses the ink colour.
- Journey.js: tag icon on each visit chip when tag colours are on. CompareBody.js: "{n} students ka hisaab" only for groups above 1. SolutionNavigator.js: tag key moved under the strip. DisplayName.js: all copy in Hinglish.
- backend/tejas/analysis_pdf.py: Question Journey drawn as visit boxes per time block; sections share a page when the previous one is short (no near-empty pages); rank table drops duplicate scores.
- tests/analysis_iso195.py: PDF check now also needs contents, journey, tags and pace. 60/60.
- docs/app_packet: APP_UPDATE_2026-11-19.md addendum, explain.js, samples re-exported at analysis_version 3 + 12_explain_texts.json, rulebook version 3, README. Public copy + zip: frontend/public/downloads/app-update-2026-11-19/ and jeelive-app-update-2026-11-19.zip (SHA256SUMS checked, 200 from the preview URL).
- Checked in a browser (isolated bridge, synthetic class of 14): all 8 sections personal + comparative at 1920 and 390, light and dark; attempt without time record; name box save; report and scorecard downloads.
- Testing agent run (test_reports/iteration_204.json): no defects, no app code changed by it. Added tests/ui_analysis2_flows206.py (18/18) for the flows its scripts skipped.
- Found while checking the PDF: a display name or note in Hindi printed as "?????" (the name rule allows Hindi since 18 Nov). Fixed in backend/tejas/analysis_pdf.py: text the built-in font cannot print goes through MuPDF's htmlbox (right font, letters joined correctly), fonts are subset; the scorecard PNG does the same. Checked through the real routes with a Hindi name. tests/analysis_iso195.py now 62/62.
- Left alone: isolated test database tejas_isolated_book170_436fa878 from an earlier session (see ROADMAP).
- tests/ui_analysis2_flows206.py now imports its helpers from ui_analysis2_walk204.py (which only runs its walk when started directly). Re-run after the change: 18/18, 390 px dark walk clean.
- Seen in the test setup only: the Results page's Dream meter call (/api/dream, relayed to the app server) answers 503 for the synthetic test students, because they do not exist on the app side. Signed out on the preview it answers 401. Not checked with a real signed-in student (already pending as "Live Authenticated Validation").
