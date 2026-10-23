# Native screen and behavior map

Keep existing data and backend behavior. All test counts, availability, dates and scores come from APIs; do not hardcode screenshots as live data.

| Native screen | Required behavior | API family |
|---|---|---|
| Entry/account | Guest browsing where public; honest phone convenience entry; staff access only if separately approved; remember current session | `/auth/session`, `/auth/phone`, `/auth/me`, `/auth/refresh`, `/auth/logout` |
| Home | JEELIVE.AI logo, existing exam choices, compact AI Astra series banner; meaningful loading/empty/error states | `/exam-navigation/...`, `/series/all-india-jee` |
| Exam hub | JEE Main, BITSAT, COMEDK; mocks, chapter practice, results destinations | slugs `jee-main`, `bitsat`, `comedk` |
| Catalogue | Paged mocks/chapters, subject, search; original title/count/rules/availability; no fake published papers | `/{slug}/catalogue`, `/my/sets/{id}` |
| Instructions | Read returned rules, marks, duration, source availability; preflight/device check before start | `/sets/{id}/preflight`, `/sets/{id}/start` |
| Player | Typed or source-image question, MCQ/integer controls, optional confidence, mark/clear/next, subject palette, reliable save state, timer, submit confirmation | `/attempts/{id}`, `/answers/{qid}`, `/visit`, `/submit`, `/bonus` |
| My Tests | Saved, in progress, completed, filters, continue exact attempt, meaningful comparison | `/my/tests`, `/my/tests/saved/{id}`, `/my/tests/compare` |
| Results | Analysis, Progress, Confidence, Rank, Solutions; server score version selection; grading/embargo states | `/attempts/{id}/results`, `/journey`, `/cohort`, `/historical-rank` |
| Focused Solutions | Subject tabs; horizontal question rail; one question and released supplied solution; filters; report wrong content; reflection after solution | `/asset/{kind}/{index}`, `/solution-open`, `/reviews/{qid}`, `/report-wrong` |
| All India series | Existing schedule, today's availability/start cutoff, archive, results, analysis; creator branding and accurate disclaimers | `/series/all-india-jee`, `/history`, `/streak` |
| Account/drafts | Keep/discard pending drafts on signout; draft recovery for same account; no cross-account leakage | local per-account store + existing session APIs |

## Navigation preservation
Deep links/internal navigation state must retain attempt ID, selected subject, question ID, filter, score version, return location and relevant list filters. Canonical web-shaped routes are a reference, not permission to register Android App Links without domain association. Do not invent assetlinks.json or signing fingerprints.

The latest Solutions behavior is mandatory: no dropdown/previous-next strip and no all-questions-expanded list. Subject changes show only matching question numbers. Empty filters get a clear empty state. Preserve the **original question number**, not a reindexed filtered count. A valid selected question determines its subject if the two route fields conflict. Question/subject selection must survive a score-version switch when the question exists.

## Rules and guidance
- Current imported JEE chapters: 50 questions each; Physics90 minutes, Mathematics120, Chemistry70; +4 correct, -1 wrong, 0 skipped. Treat this as current content context, not a hardcoded universal rule. Use each attempt's frozen rules.
- Supplied solutions are the source of truth. Android never generates replacement solutions or embeds an AI provider key.
- JEE Main and COMEDK approximate rank ranges are historical, non-official guidance only when the backend reports compatibility. Do not estimate AIR from a chapter score or convert a 200-mark chapter to a 300-mark full exam by guesswork.
- BITSAT shows top distinct B.E. branch guidance from server cutoff evidence, not an invented rank. Preserve unavailable states, source maximum, bonus treatment, campus/programme filtering and non-guarantee disclaimer.
- BITSAT bonus entry is explicit/irreversible for main answers after server acceptance. Read the attempt's `bonus_rule`; don't infer eligibility from the exam name alone.
- Series deadlines and result release are server-controlled. Never reveal solutions during an active/embargoed exam or let Android time manipulation extend a deadline.
- Streak/trophy animation respects reduced motion and battery/lifecycle constraints; count only server-confirmed completion.

Owner/reviewer studio, content imports, safety holds, secret management and production migration are not student navigation items. Keep those in the existing protected web tools unless the owner explicitly requests native staff tooling.
