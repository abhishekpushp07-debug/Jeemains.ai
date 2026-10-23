# Completeness reconciliation — revision1.1, 2026-10-23

The first ZIP was rechecked against the actual web client call sites and mounted backend handlers. Two omissions were found and corrected; this is an explicit correction, not a claim that the earlier package was perfect.

## Corrections
1. Added guest public catalogue/details: GET `/api/sets`, GET `/api/sets/{id}`. The web SetDetail uses the public route when no user exists; the authenticated route remains `/api/my/sets/{id}`.
2. Added grading/job recovery: GET `/api/jobs/{id}`, POST `/api/jobs/{id}/retry`; also completed the already-listed optional report contract with GET `/api/jobs/{id}/download`. Web Results already uses job retry when grading fails. The server checks ownership/state; job-status GET can dispatch work and is not a safe production probe.
3. Marked legacy POST `/api/attempts/{id}/solutions/{qid}` unavailable: it returns410 because AI generation is paused. Source questions/supplied solutions remain authoritative. Consultation uses the DIFFERENT `/questions/{qid}/solution-open` route.

## Core feature coverage
| Feature | Contract included | Reference checked |
|---|---|---|
| Entry, restore, refresh, signout | auth cookie routes | server auth handlers; API client |
| Public set preview | public sets/detail | SetDetail.js; content handlers |
| Signed-in catalogue/chapters | exam-navigation + my/sets | ExamSection.js; SetDetail.js |
| Start/preflight/resume | preflight/start/attempt read | SetDetail.js; useAttempt.js |
| Autosave, visits, bonus, submit | answer/visit/bonus/submit | useAttempt.js; attempts/answers handlers |
| Pending/failed grading | results + job status/retry | Results.js pending branch; jobs handlers |
| Released original images/solutions | binary asset + consultation | Results.js; private asset handlers |
| Optional saved AI supplement | existing reads, generation410 warning | useResultExtras.js; legacy solution handlers |
| Reflection and wrong-content reports | reviews/reports | reflection/report components |
| My Tests/save/compare | my/tests families | Profile.js; My Tests handlers |
| Journey/cohort/rank/branches | corresponding learner routes | results learning/branch components |
| Series/history/streak | public/owned series routes | LiveSeries.js; banner/streak components |
| Optional report capability | report/job/download, rights gated | jobs/attempt report handlers; UI remains hidden |

## Still intentionally NOT complete
- Native project, APK, actual Android HTTP/cookie/image/device tests: Android agent must build/test them.
- Verified phone ownership/OTP: backend gap, not solved by a document.
- Play Store signing, publisher details, approved privacy/deletion policy and application ID: release inputs, not guessed.
- Optional push, subscriptions, verified app links, proctoring or full offline content: not existing promised integrations.
- Native owner/reviewer administration: not the student app; protected web tooling stays separate, with existing safety holds.
- Live/preview deployment parity and workload capacity: require separate evidence.

This reconciliation increases handoff coverage. It is not an exhaustive security audit or a native release certification. The user can give this updated ZIP to the Android agent to start implementation with the documented boundaries.
