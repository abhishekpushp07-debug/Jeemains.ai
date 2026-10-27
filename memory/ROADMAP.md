# Active roadmap

## P0 — approved 2026-10-27 performance work
1. Resolve live30-secondedge520 stalls with platform/deployer, capture correlated responseheaders/timings; no blindcachefix or falsehealthy claim. No paidinfra changes without approval.
2. Optimise originalPDFvalidation/imagepath: per-page parsing reuse, coalescedsource reads, no duplicatecropcache, guaranteedowned-documentclose, pixel-identical smallergrayPNG onlywhenallRGBchannelsidentical.
3. Improve browserquestiondelivery safely: per-userRAM-onlyblobs with boundedbytes/authgeneration/logoutclearing, single-flightrefreshONLY401, boundednext-questionprefetch, zero solution/pre-release or cross-accountleaks.
4. Remove redundant start→GET viaone-usefreshRAMhandoff, preservecanonicalanswer/draft/deadline/receipt behavior. RemoveunusedfontCSS,preloadactualcriticalbundledfonts,fixauthlazyCLS.
5. Repeat163baselineexactly +safeisolatedload/retry/concurrency/auth/sourcepixel checks, record honestbefore/after. Testactualmobile390x844/desktop1920x800. Publish afterverifiedpass; productionwritesnotusedforQA. LiveSLOsnotcertifiedfromlocalASGI.

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
