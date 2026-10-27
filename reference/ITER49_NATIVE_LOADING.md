# Native loading pass — iterations 48–49

## Why Redis alone was insufficient
Android uses the canonical academic API directly. The local Redis service caches RF metadata, not question-image decoding, encrypted device reads or native views. The bottlenecks addressed here are the actual frontend pipeline.

1. Every queue event previously notified every image and the entire Player/Result; path listeners now isolate invalidations. Navigation still prioritizes the current subject and downloads all allowed crops.
2. Cached reads previously joined a FIFO behind encryption writes. A priority scheduler moves reads ahead of queued writes but never across open/clear barriers. No weakened encryption or plaintext fallback.
3. Native ArrayBuffer→Blob→FileReader conversion was replaced by exact-byte, chunked yielding base64. Header dimensions stabilize layout. Only a bounded neighbouring-question window warms decoded native images, with memory-only image caching.
4. KaTeX's ~364KiB inline CSS/font source was rebuilt/reloaded as cards changed. A stable offline native WebView now receives only updated body/style, hides stale content until matching revision acknowledgement and reports layout after fonts/resize. Prompt/options are memoized; card-level remounts and 10Hz content state updates removed. The 20-second gameplay deadline and 100ms expiry checks remain.
5. JSON body reading had no deadline after headers, and caller cancellation disabled the deadline entirely. A composed abort/race now covers the full request. No automatic replay of PIN or cookie-rotating session requests.

## Verification
- 24 frontend isolated runtime checks passed across suites40/48/49. Original byte parity tested using all-byte equality and SHA on random1MiB images. Queue listener fanout16→2 in one isolated75-completion run is NOT device speed or FPS.
- RF9 backend cases passed; one sparsechapter test skipped because none exists. RealRFAPI/disposableQA UI verified answer→next,20.4s untouched-card timeout→auto-next,320px and390px layouts,finish summary. ExactQA cleanup and originalwallet/archive guard passed.
- Real PIN login and ownedcompleted-list read succeeded; latercanonical503/520 prevented completion of liveimage/zoom/parity verification. DirectPythoncanonical authtimedout; parity3SKIPPED. No canonicalacademic writes or realwallet changes.
- Offline HTML shell exercised in browser bridge harness; this does not prove Android nativeWebView/nativeAES/nativebitmap performance. Forced503session returns usablePINform; MyTests now distinguishes unavailable from emptyhistory.

## On-device acceptance checklist
1. Open an existing eligible paper; do not create/submit an attempt just for timing without user intent. Observe first question, then10questions,back/forward,subjectjump andlargeimagezoom.
2. Open an existing released result and several supplied/AI solutions. Confirm no stale formula/answer during rapid switches; source remains sharp/unchanged.
3. Account → Loadingperformance → Refresh. Capture local p50/p95 + counts; Shareexports aggregatesonly. Resetdoesnotdeleteimages/answers. Cold,cached andprefetchedsamples must be interpreted separately; imagepaint ends atdisplaycallback, not an FPS measure.
4. Reopen samepaper, then restart app and reauthenticate sameaccount to check encrypted-disk latency. Confirm logout/accountswitch neverdisplaysprevioussource or maths. Largecrops must notexhaustRAM.
5. PlayRF onphysicalphone to confirm offlineKaTeX/fontlayout,100msdeadlinecheck/20sfeedback,swipe andnativeRing animation. DevExpoGo overhead mustnotbe reportedasreleaseperformance.

## Still pending
- Upstream jeelive.ai origin intermittently returns503/520 and slowAI/image responses. Backend auth/session noretry is correct because it may rotatecookies. Avoid blanketretry/concurrencyincreases or privateRedis caching.
- Native device measurements and released-image E2E/parity retest when upstreamhealthy.
- Actual signedAndroid APK/AAB size check for<20MB target. No artifact produced; priorrawJS/asset size is not APKsize.