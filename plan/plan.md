# jeemains.ai / Witcircle — Familiar Exams, Clear Results aur 5-Lakh Capacity Roadmap

Existing learning platform mein light-only, exam-specific test screens, clear navigation, segmented results aur useful My Tests banana—original content aur working exam rules preserve karke.
Canonical sources, fast high-clarity images aur Android-ready APIs ke saath backend ko 5 lakh simultaneous active examinations ki measurable capacity tak strengthen karna.

## Who it's for

- JEE Main, BITSAT aur COMEDK students, including mobile users on inconsistent networks.
- Owner aur authorised Content Studio users jo questions, official keys, apne solutions aur optional AI solutions manage karte hain.
- Future Android users, jinke attempts, results aur content web ke saath consistent rahenge.

## Core features and experience

### 1. Source of truth: original source, approved content aur delivered image alag hain

Cropped image ek delivery copy hai; use akela source of truth nahi maana jayega. Canonical content ka matlab hoga ek authoritative, traceable record:

- Original PDF/source master preserved rahega. Har published question aur option ko uske source document, page aur question se trace kiya ja sakega.
- Question appearance, option order, official answer key aur published test version ka verified relationship rahega.
- Owner-provided solution aur AI-generated solution alag pehchaan ke saath rahenge. AI output official answer key ko replace nahi karega.
- Ek approved question se hi Studio preview, student display, result review aur PDF report ki matching content identity niklegi.
- Published material ko silently overwrite nahi kiya jayega. Correction ek visible revision hogi; already-running exam ka paper beech mein nahi badlega.
- Existing records ko bina verification reliable canonical records declare nahi kiya jayega. Missing source links owner ko visible honge.

### 2. Original PDF look, small downloads, sharp symbols

User ka selected experience **Original PDF look everywhere** hai. OCR/text recreation ko default display nahi banaya jayega.

- Questions, options, diagrams aur mathematical notation source jaise hi rahenge; unnecessary white margins reduce kiye ja sakenge, content nahi.
- Normal reading ke liye lightweight image aur zoom ke liye sharper copy milegi. Larger copy sirf zarurat par download hogi.
- Ordinary question-plus-options ke initial readable view ka provisional budget **25–60 KB** hai. Yeh target hai, hard cap nahi: complex diagrams, long questions ya tiny symbols ke liye larger files allowed hongi.
- Subscripts, fractions, minus signs, vectors, graph labels aur option letters ko byte reduction se zyada priority milegi.
- Same device par recently opened question dobara unnecessarily download nahi hoga, browser/app cache limits ke andar.
- Image unavailable ho toh blank question ya invisible failure ke badle visible loading/retry state milegi.
- Exam traffic ke dauran PDF cropping, image conversion ya AI generation student request ka part nahi honge.

### 3. Image delivery aur exam transactions ke alag capacity goals

Proposed delivery service **private Amazon S3 storage + Amazon CloudFront CDN** hai. Paid setup, account access aur spending separate approval ke bina start nahi honge.

- Student image bytes directly nearby CDN delivery servers se aayenge; ordinary image views exam application se stream nahi hongi.
- Image access check cached copies par bhi apply hoga. Same image authorised students ke liye shared CDN cache se serve ho sakegi, bina har student ki separate image copy banaye.
- Source PDFs, answer keys, unreleased content aur owner-only files student-delivery paths mein expose nahi honge.
- Protected, short-lived image links web aur Android dono ko support karenge. Link renewal student ka timer, selected answer ya current question reset nahi karega.
- Published image copies immutable hongi. Naya approved version purani cached image ko galti se current paper mein nahi laayega.
- CDN speed login, answer saving, submissions aur results ki capacity ka proof nahi hai; unke capacity outcomes alag report honge.

Available managed-storage integration backend-proxied downloads document karta hai, direct presigned downloads nahi. Isliye usse akela 5 lakh concurrent image delivery ka established solution nahi maana gaya hai. Proposed external CDN ki account limits aur spending launch approval ka part hongi.

### 4. Light-only test screens aur exam-specific familiarity

**Entire test-taking screen light mode mein rahegi**, account theme ya device dark-mode setting kuch bhi ho. No dark question canvas, dark palette panel ya dark-mode toggle inside an exam. Original PDF images light surfaces par clear rahengi.

BITSAT, JEE Main aur COMEDK ke liye ek generic navigation shell ko sirf rename nahi kiya jayega. Har exam ki verified instructions ke hisaab se section access, question palette, review states, save/clear actions, previous/next behaviour, timer aur submission summary align honge.

**Reference policy selected by user: 2027 screens, release hone par.** Tab tak latest verified official reference use hoga, with visible reference-year/verification information. Existing papers ke marking, duration, section rules aur bonus rules UI redesign se silently change nahi honge.

Research findings and boundaries:
- **JEE Main:** NTA ka official CBT familiarity portal available hai. NTA instructions question status, saved response aur marked-for-review distinctions document karti hain. Abhyas mobile instructions ko desktop JEE interface ka exact screenshot proof nahi maana jayega.
- **COMEDK:** official mock-test page seven familiarity demos link karta hai. The linked demo login page is publicly reachable; active exam screen was not verified during this research. Official page khud kehta hai ki demo actual syllabus/pattern ka proof nahi hai.
- **BITSAT:** official brochure-based navigation and bonus rules provide a reference; current active public exam screen was not verified. FAQ mein model question paper unavailable hona interface demo ki permanent absence ka proof nahi hai.
- **2027:** kisi exam ki official active 2027 screen is research mein verify nahi hui. Unreleased/unseen layouts ko invent karke exact official replica nahi kaha jayega.

Desktop par verified screen familiarity target hogi. Mobile par same action names and meanings ke saath readable adaptation hogi; tiny desktop screenshot ko squeeze karke unusable replica nahi banaya jayega. No official logos, endorsement or affiliation claim.

### 5. Clear navigation across the product

- Normal study pages par predictable destinations: exam/practice discovery, **My Tests**, results through attempts, and Profile. Owner Studio stays separate and authorised.
- **Profile → My Tests** required entry point hoga; main student navigation se bhi direct access milega.
- Page heading, current exam/test identity, selected destination aur back destination obvious honge. Browser back, return from a result, and direct result links context preserve karenge.
- Active exam distraction-free hoga: global navigation reduced, current exam controls prominent, and accidental exit par meaningful warning. Exit/resume rules existing timer policy follow karenge.
- Empty, loading, failed and unavailable screens clear next action batayengi; broken-looking blank panels nahi honge.

### 6. Segmented, colourful results and solutions

Result hierarchy: **score summary → Analysis / Solutions / Real-exam Comparison navigation**. Default Analysis open hoga; tabs/sections active state aur position preserve karenge.

- **Analysis:** score and accuracy, subject performance, time and pacing where recorded, question outcomes, and 25 deep insights grouped into short, clearly named categories. Evidence unavailable ho toh diagnosis invent nahi hogi.
- **Feedback form:** Analysis ke graphs aur insights ke immediately baad, usi Analysis view mein. It will not precede analysis, interrupt as a popup, or require traversing all solutions first. Submission gets a visible acknowledgement and repeat taps do not create duplicate feedback.
- **Solutions:** question-number navigation, subject and correct/incorrect/skipped/review filters, previous/next, student's answer versus official key, then the matching explanation. Source question image aur selected question context visible rahenge.
- Owner-provided and **AI generated** explanations distinctly labelled; missing solutions show an honest state, not a generate-on-student-view action.
- A chart or question row can open the matching solution and return to the same analysis context. Filters and selected question are retained when moving between these views.
- Colour is meaningful: correct/incorrect/skipped/review statuses use consistent accessible colour plus labels/icons, not colour alone. Results can be colourful without making the exam screen visually busy.
- Existing PDF download remains discoverable and retains its full-attempt content; on-screen filter does not silently narrow the exported report.

### 7. My Tests inside Profile

User selected all four capabilities:

1. **Resume unfinished tests:** show eligible ongoing attempts, last saved state and remaining/deadline status. Resume original attempt, never restart the timer. Expired/submitted attempts cannot be falsely presented as resumable.
2. **Attempt history and reports:** completed attempts with exam, test, attempt date, score, status, result entry and available PDF download. Search and exam/date/status filters; retakes remain separate.
3. **Saved tests for later:** save/remove available tests without creating an attempt. Unpublished, withdrawn or expired tests show honest availability rather than broken Start buttons.
4. **Compare my attempts:** side-by-side score, accuracy, completion/time where recorded and subject changes, only for meaningfully comparable paper versions and marking rules. Cross-exam/chapter-to-full-paper comparisons do not imply equivalence.

Organisation: **In progress / Saved / Completed**, with comparison reachable from selected completed attempts. Each item has one obvious primary action and concise secondary actions; existing history is retained rather than rebuilt as empty lists.

### 8. Same-score real-exam rank comparison

Result ka **Real-exam Comparison** view user ke question ko address karega: “Agar ye marks reference real exam mein aate, toh standing kya ho sakti thi?” It is a historical scenario, not an official result or guarantee that mock performance will repeat in a real paper.

- **Platform rank** among comparable app attempts and **estimated real-exam rank** are separate, clearly named measures. App participants ko total national candidates nahi maana jayega.
- Every numeric comparison shows reference exam/year, compatible total marks and rules, source, shift/session where relevant, method limits and a range where precision is not supported.
- **JEE Main:** raw marks alone unique AIR nahi dete. Shift-wise normalization, percentile, candidate pool and ranking rules matter. Supported reference data se percentile/rank range milega; unknown shift ko silently guess nahi kiya jayega.
- **COMEDK:** same marks can map to different ranks by year, participant distribution and tie rules. Historical evidence supports a range, not an exact personal rank from total marks alone.
- **BITSAT:** merit/score practice JEE AIR ke barabar nahi hai. Published, usable rank evidence absent ho toh numeric rank unavailable rahega; any available score/cutoff context separately labelled hoga, rank ke naam par nahi.
- Chapter tests, incomplete papers, incompatible maximum marks, or different bonus rules do not get a fake national-rank conversion. Marks ko percentage se scale karke full-exam rank invent nahi hoga.
- Primary published sources preferred. A vetted nonofficial historical dataset may be used only with visible provenance, limitations and appropriate permission; coaching estimates never labelled official.
- Research confirms why normalization matters but **a complete usable marks-to-rank dataset has not yet been verified**. Until reliable evidence is approved, comparison view says “Reliable comparison unavailable” with reason; no hardcoded or AI-invented ranks.
- 2027 screen availability and 2027 ranking-data availability are separate. Earlier-year evidence remains explicitly labelled until usable 2027 data exists.

### 9. Reliable attempts, APIs aur 5 lakh concurrent examinations

- Web aur future Android app ke liye common, documented, versioned APIs: catalogue, saved tests, attempt history, start/resume, answer save, submit, results, feedback aur permitted solution viewing.
- Android ko direct database access, website scraping ya embedded cloud credentials ki zarurat nahi hogi.
- Connection drop, refresh aur repeated requests se duplicate attempts, double submission ya newer answer ka older answer se replacement nahi hoga.
- Student ko saved, saving aur offline/unsaved states clearly dikhengi. Device par pending answer ko server-saved bataya nahi jayega. Exam-specific Save/Review button meaning aur recovery drafts confusing tarah se mix nahi honge.
- Exam clock aur submission rules authoritative rahenge; device clock badalna extra exam time nahi dega.
- Database, application capacity, memory, connections, caches and report/AI workloads ke explicit capacity boundaries rahenge. “More RAM” ya “CDN added” alone scale proof nahi hai.
- Student answers durable acknowledgement ke bina saved nahi dikhengi. A cache eviction or service restart must not become the only cause of losing acknowledged work.
- Reports, analytics, historical rank comparisons and AI processing exam answers save karne ki capacity se compete nahi karenge.
- Target **500,000 simultaneously active examinations** hai, including start, navigation, saves, reconnects and finish—not idle logged-in users. Current capability ko evidence ke bina is target ke barabar present nahi kiya jayega.

### 10. Existing product commitments remain protected

- Existing brand identity: matte maroon `#5C0025`, Figtree aur Roboto Mono. Latest request authorises navigation/result redesign and mandates light-only tests; it supersedes the earlier no-redesign limitation, not the content-preservation commitment.
- Existing student phone login aur owner Content Studio access remain; replacement login system is not part of this proposal.
- Existing 94 BITSAT chapter tests ke content, marking aur duration unchanged.
- Existing 50 BITSAT full mocks: 130 main + 12 conditional bonus questions, 180-minute common timer, +3/−1/0 marking.
- Bonus sirf all 130 main answers select hone par unlock; warning ke baad main answers locked.
- Full mocks ki current visibility commitment 17 October 2027 tak retained; invalid material private aur reason Studio mein visible.
- Retakes separate attempts rahenge. Existing results, graphs, ranks where comparable data exists, 25 deep insights, AI Answer Review aur PDF reports retained and better organised.
- Official PDF key scoring authority rahegi. AI disagreement automatic correction nahi banega.
- AI **sirf owner ke explicit Solve action** par chalega, mocks aur chapterwise dono ke liye. Upload, publish, login, exam, result view, startup ya scheduled discovery se naya solving work start nahi hoga.
- Owner solutions overwrite nahi hongi. Already-saved AI solutions preserve hongi; legacy automatic work stop/pause hoga, delete nahi.

## User flow

### Owner

1. Source upload/open → original source aur question/option preview available.
2. Source mapping, crop readability aur official key completeness visible; unresolved new content publish nahi hota.
3. Owner apna solution retain/provide karta hai, ya selected test par **Solve with AI** explicitly click karta hai.
4. Solve action eligible missing solutions, existing owner solutions aur expected AI usage clearly batata hai; repeated clicks duplicate work nahi banate.
5. Approved content ek complete version ke roop mein live hota hai; half-published paper students ko nahi dikhta.
6. AI/PDF disagreements review list mein jaate hain; scoring key unchanged rehti hai jab tak existing authorised correction process se verified decision na ho.
7. Owner delivery health, feedback, content readiness aur costs dekhta hai; supported official interface references and historical-comparison evidence remain identifiable.

### Student — web aur future Android

1. Exam discover kare, test save kare, ya **Profile → My Tests** se continue/history open kare.
2. Exam instructions, source/reference year and paper rules dekhe; light-only test start/resume kare.
3. Exam-specific familiar actions se questions navigate, answers save, mark/review or clear kare. Original PDF images readable rahein.
4. Weak network par pending versus acknowledged state clear rahe; resume original timer aur existing answers retain kare.
5. Existing bonus and submission rules follow karke durable submission confirmation mile.
6. Result score summary dekhe → Analysis explore kare → uske neeche optional feedback de.
7. Solutions mein selected question review kare; Real-exam Comparison mein available evidence-backed scenario dekhe, clearly separated from app cohort rank.
8. My Tests se report download, eligible retake or comparable previous attempts open kare; context lose na ho.

## UI/UX feel

The latest request is a usability redesign, not just cosmetic recolouring. Familiar destinations, clear page hierarchy, fewer competing actions and predictable back/next behaviour are the priorities.

- Exam workspace strictly light-only with white/light-neutral surfaces and strong text/diagram contrast. Existing source images and zoom/pan remain readable without inverted colours.
- BITSAT, JEE Main and COMEDK controls derive from verified references, not decorative branding. Status colours and action semantics follow each verified exam; lack of 2027 evidence stays visible.
- Outside active exams, retain the maroon brand while using restrained colour-coded analysis sections, clear headings, accessible legends and well-spaced charts.
- Desktop exam familiarity and mobile usability have separate presentation needs. Mobile uses reachable controls and an accessible question navigator without covering the question or creating horizontal scrolling.
- Result analysis, solution reading and rank comparison have distinct destinations; all preserve current test identity and a clear route back to My Tests.
- Keyboard access, visible focus, touch targets, loading/retry states and non-colour status labels apply throughout. Feedback stays below Analysis; no interruption or compulsory form before solutions.
- No fabricated testimonials, official affiliation, rank guarantees or proven-capacity badges.

## Implementation phases

### Approval model: 3 major delivery phases, 25 owner-approved checkpoints

Roadmap ke 25 numbered checkpoints hi user ke requested **25 working phases** hain; unhe neeche 3 major delivery phases mein group kiya gaya hai.

**Sirf major Phase 1, MVP, current build scope hai. Uske andar bhi ek numbered checkpoint complete hone ke baad stop hoga, completion evidence aur limitations share hongi, aur next checkpoint ke liye explicit approval li jayegi.** Major Phases 2–3 future roadmap hain, current implementation permission nahi. Plan approval saare 25 checkpoints, paid services ya capacity expenses ko ek saath authorise nahi karta. Current action planning only hai.

### Major Phase 1 — MVP: familiar exams, clear navigation aur useful results

**01. Preservation, source baseline aur owner AI control**
- Outcome: existing content/attempts protected; source-traceability gaps visible; automatic mock/chapter AI solving band and legacy automatic work paused/cancelled without deleting saved solutions. Per-test explicit Solve control protects owner solutions.
- Completion evidence: no student/upload/publish action starts AI; owner-requested jobs alone can proceed; existing tests and source gaps have a clear status summary.

**02. Product navigation foundation**
- Outcome: consistent discovery, My Tests and Profile destinations, clear page identity and context-preserving back navigation. Profile includes the requested My Tests entry.
- Completion evidence: students can reach and return from tests/results without dead ends, losing filters or being sent to an unrelated page. Active-exam exit is deliberate.

**03. Light-only exam workspace**
- Outcome: test screen, question surface, palette and navigation remain light under all account/device theme settings; original PDF appearance and zoom remain readable.
- Completion evidence: no dark exam view, no hidden action or covered question on mobile, and a clear save-state display. Existing answers and timer behaviour are preserved.

**04. JEE Main familiarity mode**
- Outcome: section/question navigation, response-save/review meaning, palette legend, numerical entry where applicable and submission flow follow verified NTA/JEE references.
- Completion evidence: reference source/year and any adaptations are visible; mobile Abhyas is not treated as proof of desktop parity. 2027 mode is labelled pending until its actual reference can be verified and approved.

**05. BITSAT familiarity mode**
- Outcome: BITSAT navigation follows verified references; all-main-answer bonus eligibility, warning and main-question locking remain unchanged.
- Completion evidence: BITSAT is not merely the JEE screen renamed. Unverified visual details are labelled as a practice adaptation; no exact 2027-screen claim without evidence.

**06. COMEDK familiarity mode**
- Outcome: verified COMEDK controls, palette, section movement and submission instructions inform the dedicated exam experience, respecting each published paper's rules.
- Completion evidence: official familiarity demo and actual paper rules are distinguished. Active-screen parity requires an actual screen reference, not the publicly visible login page alone.

**07. Analysis, solutions aur feedback redesign**
- Outcome: score summary plus distinct Analysis, Solutions and Real-exam Comparison destinations; colourful labelled charts, grouped deep insights, question filters and linked solution navigation. Feedback sits directly below Analysis.
- Completion evidence: a student can move from an analysis question to its explanation and back without losing context; feedback never obstructs reading or downloading; AI labels and missing-data states remain honest.

**08. Complete My Tests experience**
- Outcome: In progress, Saved and Completed views include original-attempt resume, searchable/filterable history, reports, saved-for-later tests and comparable-attempt comparison.
- Completion evidence: expired attempts are not resumable, saving a test does not start it, retakes remain separate, and comparison does not mix incompatible exams or scoring rules.

**09. Same-score real-exam comparison**
- Outcome: a dedicated historical scenario view separates app cohort rank from source-backed real-exam percentile/rank estimates, using ranges and reference-year/shift context as appropriate.
- Completion evidence: eligible same-score comparisons are explainable from approved evidence; incompatible tests and missing datasets show explicit reasons. A numeric comparison is not declared ready without usable data, and 2027 estimates are never fabricated from older-year labels.

### Major Phase 2 — canonical content, efficient delivery aur exam integrity

**10. Complete canonical source and version records**
- Outcome: original source, verified question/options, official key and approved solution origins are traceable; each published paper version is consistent across Studio, exam and report.
- Completion evidence: source reconciliation exposes gaps; old attempts remain explainable from their original paper and scoring basis; no silent live-content overwrite.

**11. Crop quality and lightweight image variants**
- Outcome: clipped notation/options and answer leakage are resolved against original sources; lightweight reading and sharper zoom copies preserve PDF appearance.
- Completion evidence: actual complete-question image-size distribution and readable mobile/desktop samples are available. The 25–60 KB ordinary-view target never overrides mathematical clarity; larger exceptions are documented.

**12. Durable private storage and protected CDN delivery**
- Outcome: original sources and image copies no longer depend exclusively on runtime files; authorised students receive image bytes directly from shared CDN delivery, not through the exam application on every view.
- Completion evidence: approved asset completeness, protected origins, authorised cache access and smooth expired-link renewal; bounded prefetch and on-demand zoom avoid whole-paper download storms. Paid infrastructure requires separate prior approval.

**13. Shared web and Android API contract**
- Outcome: documented, versioned interfaces cover catalogue, My Tests, saved tests, start/resume, answers, submission, results, feedback and protected assets.
- Completion evidence: a future Android client does not need website scraping, direct database access or embedded storage credentials; existing web flows remain compatible. Building the Android app is excluded.

**14. Durable saving and weak-network recovery**
- Outcome: delayed/repeated saves cannot silently overwrite newer accepted responses; pending device drafts remain distinct from server-confirmed answers and from each exam's saved/evaluable state.
- Completion evidence: refresh/reconnect recover the correct acknowledged state; conflicting device changes are not silently accepted; cache loss does not erase the only copy of accepted work.

**15. Deadline, bonus and final-submit integrity**
- Outcome: authoritative timer, existing bonus rules, expiry and repeat-safe submission stay consistent across clients and new exam layouts.
- Completion evidence: one final outcome per attempt, no extra time through device-clock changes/reconnect, and recoverable durable submission acknowledgement even if the confirmation screen is interrupted.

**16. Complete publication and audited corrections**
- Outcome: only complete approved paper versions become available; held content has a reason; verified owner corrections and any resulting regrades are explicit.
- Completion evidence: no half-published/mixed-version exam, no AI-driven key replacement, and no unannounced scoring-basis change for a running attempt.

**17. Results integrity and heavy-work isolation**
- Outcome: PDF reports, analytics, rank comparisons, imports and manual AI jobs do not exhaust exam-saving resources; displayed marks, bonus totals and permitted report content remain consistent.
- Completion evidence: delayed report/AI work has visible status without stalling exams; cohort figures are real and comparable, rank estimates remain separately labelled, and source-matched explanations stay attached to the right questions.

### Major Phase 3 — measured 5-lakh capacity and operational safety

**18. Database, memory and connection capacity**
- Outcome: active attempt writes, history reads and analytics have explicit capacity limits; memory and connection use remain bounded as concurrency grows. Caches speed up reusable content without becoming the only durable answer store.
- Completion evidence: peak and sustained workload reports identify read/write headroom, memory growth, connection pressure and bottlenecks; accepted answers reconcile after service interruption. Database replacement or unlimited RAM is not assumed necessary.

**19. Independent scaling and start/finish rushes**
- Outcome: image delivery, exam APIs, answer storage and background workloads can expand independently; exam-start, reconnect and final-submit bursts receive dedicated capacity planning.
- Completion evidence: busy/failed components have bounded impact, delivery cache misses do not overwhelm exam services, and demonstrated capacity includes active work rather than idle sessions.

**20. Privacy and abuse protection**
- Outcome: private results, owner controls, signing credentials and answer keys stay protected; abusive traffic control does not reject legitimate shared-network exam traffic.
- Completion evidence: access boundaries hold across web/Android-compatible APIs, protected images and My Tests; no promise of screenshot-proof downloaded content. These protections apply from the MVP, not only when this deeper scale checkpoint is reached.

**21. Live exam health view**
- Outcome: owner can see active attempts, image failures, save/submission failures, capacity pressure and incident status without inspecting technical internals.
- Completion evidence: image-delivery problems, exam-service problems and delayed analytics are distinguishable, with actionable alerts rather than silent failure.

**22. Recovery and preservation commitments**
- Outcome: source/content recovery and attempt-data restoration have explicit, evidence-backed commitments; repair does not require wiping students' saved work.
- Completion evidence: recovery coverage and remaining time/data-loss limitations are documented. Absolute zero-loss or instant recovery is not claimed without evidence.

**23. Exam cost and quota guardrails**
- Outcome: per-event delivery, database, memory/compute and background-processing costs, provider quotas and approved capacity envelope are understandable.
- Completion evidence: owner can see expected 5-lakh-event cost and headroom. Budget alerts do not abruptly terminate a running exam; commitments and costly new workloads are controlled in advance. Earlier paid checkpoints still require prior approval.

**24. 500,000 active-exam capacity evidence**
- Outcome: a written capacity report covers 500,000 simultaneous examinees with same-paper start rush, image navigation, saving, reconnect, expiry and finish bursts.
- Completion evidence: declared device/network/geography, actual image sizes, latency, failures, data integrity, memory stability, service headroom and cost are reported. Any shortfall is explicit; successful CDN delivery alone is not a pass for the full examination system.

**25. Controlled production release and handover**
- Outcome: owner-approved release stays within demonstrated capacity; supported screen-reference versions, source integrity, Android API handover and incident/recovery ownership are documented.
- Completion evidence: actual capacity and remaining limitations are published honestly; 2027 interface adoption requires verified references and owner approval without changing ongoing attempts. No automatic jump to 5 lakh real students.

### Success targets — commitments to measure, not present-day claims

- **Fidelity:** approved crop mein no missing question/option content, no answer-key leakage, readable mathematical notation.
- **Image budget:** ordinary initial reading image 25–60 KB target; clarity-based exceptions permitted. Size measured per complete question-plus-options view, not a misleading single tiny sub-image.
- **Reading speed:** prefetched/cached next question near-instant; provisional p95 target under 300 ms to display on the agreed device profile. Uncached normal question provisional p95 target within 2 seconds on the agreed healthy mobile-network profile. Poor/no connectivity ke liye universal instant-load promise nahi.
- **Answer safety:** no acknowledged answer lost, no accepted older save replacing a newer answer, no duplicate final submission under the agreed workload.
- **Responsiveness:** provisional healthy-network p95 save acknowledgement under 1 second and durable submission acknowledgement under 2 seconds; full analytics/report generation can finish separately.
- **Peak service:** provisional critical-request failure rate below 0.1% under declared target conditions; expected permission/validation rejections reported separately.
- **Capacity:** 500,000 concurrent active examinees is the target. Smaller verified capacity ko 5 lakh-ready label nahi diya jayega.

A bandwidth illustration: average 50 KB per complete question view × 130 main questions × 500,000 students is approximately **3.25 TB delivered**, excluding zoom, bonus, retries and other traffic. CDN original server load reduce karta hai; student bandwidth aur delivery bill zero nahi karta. Aur 500,000 active students ka sirf ek periodic save per 30 seconds bhi about **16,667 requests/second average** hai, before answer-change and submission bursts. Yeh illustrative assumptions hain, measured product traffic nahi.

## Assumptions

1. The latest manual-only AI instruction supersedes all earlier automatic-on-upload/live requirements. Paused legacy automatic jobs will not resume without an explicit owner request. Existing saved solutions remain intact; infrastructure recovery may resume only already owner-requested unfinished work.
2. Manual solving defaults to one selected test at a time, generating only eligible missing solutions. It does not silently solve the entire library or replace owner-provided content. Existing individual-question controls, if present, remain compatible.
3. The 5 lakh target means simultaneously active exam takers, including a conservative same-paper peak—not total registered accounts. Initial delivery planning assumes India-heavy traffic because these exams primarily serve that audience; this is a planning assumption, not a claim about current users or a data-residency commitment.
4. Original PDF appearance remains authoritative for question display. No OCR replacement, retypesetting or reconstruction is introduced as the student default. Compression can change encoding, not question meaning or layout relationships.
5. The latest request explicitly permits UI/UX and navigation redesign. Existing test content, login, attempts, marking, results/report capabilities and maroon brand remain protected, but their current navigation/layout is not frozen. This is not a wholesale backend rewrite. The handoff is historical context, not independent proof of present production health.
6. Private S3 + CloudFront remains the proposed delivery integration. Research supports protected direct CDN delivery, not this application's 5 lakh capacity. Account access, final region/residency approval and spending consent are required at the relevant checkpoint; no paid setup is authorised by this plan alone.
7. Image variants are prepared before delivery. Exact encoding and target-size exceptions follow source clarity rather than choosing the smallest file at any cost.
8. Image-access links expire and renew; expiry cannot revoke bytes already downloaded by a student. Browser/device caches and screenshots prevent an absolute anti-copy guarantee.
9. Existing privacy boundaries remain. Student access does not grant source PDFs, official keys during an attempt, unreleased bonus assets or another student's private records. My Tests and comparisons are private to the authorised account.
10. An attempt remains tied to its published paper and scoring basis. Verified correction/regrading is an explicit, auditable owner action, not an AI side effect or a side effect of changing the exam-screen template.
11. Future Android API compatibility is included; building/publishing the Android app is not. Existing authentication credentials/providers are not replaced by default.
12. Full offline exams, new proctoring rules, payments, additional test libraries and new AI providers are outside scope. Existing content rights, numerical-answer support, downloads and previously approved working functionality remain protected.
13. There remain exactly 25 numbered approval checkpoints within 3 major phases. MVP is checkpoints 01–09; later phases remain roadmap only. Each numbered checkpoint ends with evidence/limitations and an explicit stop for owner approval. Approval of the plan is not permission to execute all checkpoints, launch paid capacity work or deploy automatically.
14. No application code, queue, database, running deployment or infrastructure changes during planning. The manual-only AI request and new UI changes are not represented as already implemented.
15. Light-only applies to the entire test-taking workspace irrespective of browser/device/account theme. Other product areas keep their existing theme policy unless the agreed result/navigation redesign requires light surfaces for clarity.
16. User selected 2027 exam references when released. Until verified references exist, latest verified official guidance is the baseline, labelled with its actual version and any practice adaptations. No automatic source-watching or silent update of ongoing exams is included. Mobile familiarity preserves meanings and reachability rather than claiming identical desktop geometry.
17. User selected all four My Tests features: resume, history/reports, saved tests and attempt comparison. Comparison defaults to the same paper/version and marking basis; unsupported comparisons explain why rather than fabricate improvement.
18. Feedback is optional and lives below the completed Analysis content, not at the top of results, in a blocking popup or behind solution reading. Existing feedback data is retained. Public testimonials or external messaging are not added.
19. Same-score real-exam standing is an evidence-backed historical scenario. Default reference is the latest suitable verified historical dataset, with its real year visible. Official primary data is preferred; vetted nonofficial evidence is explicitly labelled. No usable dataset means a clear unavailable state, not mocked ranks, extrapolated chapter scores or an invented 2027 prediction.
20. Exact real-exam AIR is not inferable from total mock marks alone. Reference shifts, participant distribution, tie rules, score scale and bonus treatment matter. JEE percentile, COMEDK rank range, BITSAT score/merit context and platform cohort rank are not interchangeable.
21. The latest dissatisfaction with navigation is addressed through structural changes, not just colours: consistent destinations, context-preserving back links, exam-specific controls, result segmentation and actionable My Tests entries. Existing strengths such as original content, bonus handling and formula zoom are retained.

### Research basis and verified limitations

**Exam screens and same-score comparisons**

- NTA official CBT familiarity portal: https://nta.ac.in/Quiz — JEE Main familiarity resources are present; this does not establish an official 2027 active screen.
- NTA CBT instructions: https://nta.ac.in/Download/AboutCBT.pdf — primary instruction reference identified for navigation and saved/review status behaviour; exact screen parity still needs the applicable active interface reference.
- NTA Abhyas mobile instructions: https://nta.ac.in/Abhyas/test — Save & Next, Clear, Review Later and status meanings are documented; this is not a substitute for desktop JEE screenshots.
- COMEDK official mock page: https://www.comedk.org/mock-test — seven familiarity demos are linked and the page says they do not establish actual syllabus/pattern or show a score.
- Official-linked COMEDK demo: https://www.digialm.com/OnlineAssessment/index.html?1022@@M47 — public login was retrieved, but active test-screen layout was not verified in this planning session.
- BITS official FAQ: https://www.bitsadmission.com/FD/BITSAT_FAQs.html — does not provide model question papers; this is not evidence that no interface demo can ever exist. A current active public BITSAT screen was not verified.
- NTA normalization reference: https://jeemain.nta.nic.in/document/national-testing-agencyntaprocedure-to-be-adopted-for-compilation-of-nta-scoresfor-multi-sessionpapersnormalization-procedure-based-on-percentilescore/ — raw marks alone are not a unique AIR mapping across shifts.
- No official active 2027 exam-screen reference or complete usable historical marks-to-rank dataset was verified during this planning research. These limits remain visible rather than being filled with invented facts.

**Protected image delivery**

- CloudFront signed URLs validate access policy before serving cached/origin content: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-signed-urls.html
- Private S3 origin protection: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html
- Shared delivery cache controls: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/controlling-the-cache-key.html
- Reducing repeated origin requests: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/origin-shield.html
- Service quotas are not an application concurrency guarantee: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cloudfront-limits.html
