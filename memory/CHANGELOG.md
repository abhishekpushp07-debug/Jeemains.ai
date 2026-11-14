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

