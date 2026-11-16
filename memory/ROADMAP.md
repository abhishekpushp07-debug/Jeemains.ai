# Owner editing power (2026-11-16)
- P0: Deploy only when the user says "deploy" (edit questions, typed options, upload resume, Library Delete, Live/Off switches).
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
