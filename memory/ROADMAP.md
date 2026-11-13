# Active roadmap

## Book publishing (2026-11-13)
- P0: Validate with one real owner-supplied publisher PDF in preview before deploy; deploy only on explicit request.
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
