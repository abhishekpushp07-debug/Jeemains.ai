# Player/navigation performance pass — iteration39

## User's decisions
- Paper subjects as tabs plus a question grid, also in solutions.
- Ready as soon as checks complete; **no fixed30-second delay**.
- Download original paper images in the background ASAP; warm released solutions while viewing/processing results; preserve canonical content/history, RF and originalHomeartwork.

## Verified current boundary
- Canonical academic source stays `https://jeelive.ai/api`; native requests go directly there; browser preview adds the existing `/api/jl` authenticated cookie proxy.
- `POST /sets/{id}/preflight` is a storage/connection/readability-readiness contract, **not a published image manifest or preparation token**. Current learner image API requires an attempt: `/attempts/{id}/questions/{qid}/asset/{kind}/{index}`. Staff `/studio` routes are never used.
- `/start` controls the original deadline. Its `start_key` is the existing generated UUID/idempotency key, **NEVER the user's PIN**. PIN is used only for login. No canonical timer/state/data changes in this pass.
- Therefore a truthful ready screen checks storage+connection **before start**, offers immediate Start now, and does not claim the paper is downloaded yet. All permitted images start preloading once attempt question metadata arrives. Never waste30seconds of exam time behind a fakecountdown.
- Entire-paper-before-clock readiness would require owner-side canonical prepare/activate support with explicit permissions, TTL, idempotency and start semantics. It cannot be safely invented in the app; this remains an optional canonicalAPI follow-up, not an implemented guarantee.

## Actual bottlenecks found in app source
- Previously prefetched only the next question's **first** crop, loaded other crops on demand, and repeated concurrent fetches for the same asset.
- Results waited until the Solutions view/question to fetch crops; no paper-wide warming while Analysis was open.
- Every browser asset was converted to a base64dataURI, adding conversion/copy overhead; imagecache was unbounded and lacked pending-request logout cancellation.
- Subject selection returned to firstquestion, Next traversed globalpaper, palette mixedsubjects and fixed6columns couldoverflow narrowphones. No timing proof of canonicalserverslowdown was obtained; earlier testcredentials401 mean do not claim measuredlive latency improvement yet.

## Implementation
- Shared priority queue: in-flight deduplication,4total parallelrequests withone slot reserved for visiblequestion, selectedsubject/visiblecrop priority, wholeauthorizedpaper scheduling, source croporder unchanged.
-48MiB memory budget; pause bulkadmission nearbudget, evictunneeded LRUentries, pinvisiblecrops, showmemory-safe mode ratherthan promiseallfilesheld onsmallphones. Largepapers continueon-demand.
- Browser BlobURLs avoidbase64copying; native RAMdataURIs staycompatible. ExpoImage `cachePolicy=memory`, noquestion/solution diskcache/publicupload. Clear+abort/revoke onaccountswitch/logout; nooldgenerationcommit, nohiddenroute restart afterlogout. Sameverifieduser revalidation no longerwipeswarmimages.
-25second fullrequest/body/decodeabort; failedsource retry UI, honor429Retry-After/cooldown; noautologinretry. Statusreports actualresidentready images, not elapsedtime/fakeprogress. Failure ofbackgroundimages doesnotblocknavigation; visiblemissingimages blockansweringuntilrendered.
- Subjectlabels comeonlyfrom actual `question.subject`, originalorder/IDs retained. Missingmetadata is honestly Uncategorised; neverinfer Physics/Chemistry/Maths byquestionposition. Subjecttabs rememberlastquestion;Next staysinsubject, explicitNextsubject atboundary; responsive44pxgrid and subjectpositionlabel.
- Solutions preloadonlyafterreleased200summary metadata. No sealed202/embargoedsolutions/lockedbonuspreload, no fabricatedconsultation events. Original/revisedscore_version partofcachekey/path. Realconsult event stillonlywhenuseropensactualsolution.
- Preflight readySheet reused forPYQnew/re-attempt andgenericmocks/chapters/series; Continue preservesexistingattempt/originaltimer.

## Verification requirements
- Unit/isolatedtestscope: queue dedup/priority/concurrency/cancel/budget/429/retry, metadataorder/subjectgroups/lockedbonus+sealedsolutiongates andstartUUIDnotPIN; labelledsyntheticfixturesonly (noappdemoAPI).
- Livecanontests need workingPINthroughsecurecard; currentlystoredpairpreviously401anduserpromisedupdatedPINlater. Don'tguess/reset/createlearner orkeepretestingbadkeys. Measurefirstpaint, fullpaperready/revisitrequestcount and sourcehashes afterlegitimateauth.
- No productionnewattempt/account/PINchange withoutapproval; preferexistingauthorizedactivepilot ifowneragreesvisits. PhysicalAndroid/iOS cache-memory/zoom/cookierestart stillneedsdeviceQA.