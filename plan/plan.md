# JEELIVE.AI Native Android App — Detailed Product Mission

JEELIVE.AI ka proper native Android app JEE Main, BITSAT aur COMEDK students ko structured practice, reliable exam attempts, clear solutions aur useful progress guidance dega.
Pehla version existing website ke saare student features aur naya 20-second Rapid Fire card mode lekar aayega; distribution sirf private pilot tak limited rahegi.

## Who it's for

### Primary users
- JEE Main aspirants jo full mocks aur chapter-wise practice dono karte hain.
- BITSAT aspirants jinhe exam practice ke saath applicable branch guidance chahiye.
- COMEDK aspirants jinhe practice, result history aur eligible approximate rank guidance chahiye.
- Students jo har din chhota revision session karna chahte hain, lekin har baar full-length test dene ka time nahi hota.
- Students jo sirf score dekhne ke bajay galti ka reason samajhna, original solution padhna aur weak concepts revise karna chahte hain.

### First-version audience
- Pehla version approved private-pilot participants ke liye hoga.
- Existing unverified phone-entry flow hi rahega; ise OTP-verified ya secure proof of phone ownership nahi kaha jayega.
- Pilot mein real private student records, actual personal phone identities aur sensitive learner information use nahi hogi.
- Private distribution ko verified authentication ka substitute nahi maana jayega.
- Owner/reviewer ka protected Content Studio student app ka part nahi hoga. Content-management access students ko nahi milega.

### Product mission
App ka objective website ko phone ke andar khol dena nahi hai. Objective ek focused mobile learning experience dena hai jahan student:
1. Apne goal ke hisaab se relevant practice choose kare.
2. Bina answers lose hone ke test complete kare.
3. Result se turant samjhe ki kya sahi hua aur kya revise karna hai.
4. Desired subject aur question ki solution tak minimum taps mein pahunch sake.
5. Formulae aur short concepts ko Rapid Fire ke through frequently recall kare.
6. Apni progress samjhe, bina fake ranks, guaranteed scores ya misleading AI claims ke.

## Core features and experience

### 1. Entry, account aur pilot boundary

**Entry experience**
- Opening screen par JEELIVE.AI identity aur clear learning purpose dikhna chahiye.
- Returning participant ko unnecessarily har launch par sign in nahi karna pade.
- Existing phone-entry experience par clear indication rahe ki phone ownership verify nahi hui hai.
- Publicly available information aur personal activity ke beech clear distinction rahe.
- Sign-in expire hone par saved work lost hone ka impression nahi diya jayega. Re-entry ke baad same profile ka work recover ho sakega.

**Account separation**
- Ek participant ke drafts, saved tests, results, reflections aur Rapid Fire history doosre profile mein nahi dikhne chahiye.
- Account switch aur signout par unsynced work ho toh Keep drafts, Discard drafts aur Stay signed in ke clear choices rahenge.
- Local pending work ko submitted ya officially saved result nahi dikhaya jayega.
- APK ya app screen mein owner credentials, server secrets ya private source access expose nahi hoga.

**Release boundary**
- Phase 1 mein public launch nahi hoga.
- Existing number-only entry ko silently OTP login mein convert nahi kiya jayega.
- Verified identity aur real private student data ka use baad ke separately approved release phase ka part hoga.

### 2. Home: next useful action clear hona chahiye

Home screen ka kaam sirf promotional text dikhana nahi, student ko next action tak pahunchana hai.

**Primary destinations**
- JEE Main.
- BITSAT.
- COMEDK.
- Rapid Fire.
- My Tests.
- All India JEE Main Test Series.

**Home priorities**
- In-progress attempt ho toh usse continue karne ka clear action.
- New practice start karne ka clear action.
- Short revision ke liye Rapid Fire ka distinct entry point.
- Series availability aur streak sirf applicable state mein dikhna.
- Same banner mein multiple repeated marketing paragraphs nahi honge.
- Content unavailable ho toh honest empty state; fake active papers ya fabricated student activity nahi.

**Brand identity**
- Platform name JEELIVE.AI hi rahega.
- Supplied logo aur uski identity preserve hogi.
- AI Astra creator attribution requested series surfaces par clear hogi, lekin har screen ko repeated slogans se fill nahi kiya jayega.

### 3. Exam hubs aur practice discovery

Har exam ke andar clear destinations rahenge:
- Mock tests.
- Chapter-wise practice.
- Previous results/history.

**Catalogue experience**
- Relevant subject choose karna.
- Chapter ya test search karna.
- Available papers ko manageable list mein browse karna.
- Title, subject, question count, duration, availability aur attempt state samajhna.
- In-progress test par Resume, completed attempt par Result aur available new paper par Start jaisa context-specific action.
- Unavailable ya restricted paper ko clickable working test ki tarah present nahi karna.
- Back jaane par selected exam, subject, search aur list position unnecessarily reset nahi honi chahiye.

**Rule visibility**
- Attempt start karne se pehle marks, negative marking, duration aur special section rules clear rahenge.
- Existing JEE chapter content ke liye Physics 90 minutes, Mathematics 120 minutes aur Chemistry 70 minutes; marking +4, −1, 0 preserve rahegi.
- Ye timings har future paper par blindly apply nahi hongi. Har selected paper ke actual rules authoritative rahenge.
- Student ko practice chapter aur full exam simulation mein difference samajh aana chahiye.

### 4. Test instructions aur start experience

Start screen par student ko ye clear hona chahiye:
- Kaunsa paper start hone wala hai.
- Kitne questions hain.
- Kitna time milega.
- Marking aur negative marking kya hai.
- Special bonus/section restrictions kya hain.
- Internet interruption mein kya safe rahega aur kya pending reh sakta hai.
- Start karne ke baad timer kab se count karega.

Repeated tap, slow response ya temporary connection interruption se duplicate attempts create hone ka experience nahi hona chahiye. Existing resumable attempt ho toh usi attempt par wapas aana chahiye.

### 5. Reliable native test player

**Question presentation**
- Ek main question reading area.
- Typed questions aur original source-image questions dono supported.
- Supplied diagrams, equations aur source images readable rahenge; zoom available hoga jahan needed ho.
- Source image ko inaccurate extracted text ya invented AI wording se replace nahi kiya jayega.
- MCQ options aur integer response fields question type ke hisaab se dikhengi.
- Optional confidence control answer dene mein obstruction nahi banega.

**Navigation**
- Subject navigation.
- Question-number palette.
- Current, visited, answered, marked, answered-and-marked aur pending-save states mein clear difference.
- Colour ke saath icon, outline ya label bhi rahega.
- Mark for review, clear response aur normal next-question navigation available rahenge.
- Back action accidental submission nahi karega.

**Saving experience**
- Answer select hona aur server par acknowledged save hona alag states hain.
- Pending, Saving, Saved, Offline aur Conflict states understandable language mein dikhengi.
- Network loss par local work quietly discard nahi hoga.
- Purana acknowledgement naye answer ko erase nahi karega.
- Do devices par conflicting edits hon toh latest work ko silently overwrite nahi kiya jayega.
- Student ko clear choice milegi: authoritative saved answer dekhna, apna pending draft inspect karna, ya deliberately discard karna.

**Timer**
- Exam timer app background, phone rotation ya device clock change se extra time nahi dega.
- Screen par remaining time readable rahega.
- Deadline ke baad late draft ko accepted scored answer nahi dikhaya jayega.
- App reopen hone par actual attempt state restore hogi, fresh timer nahi.

**Submission**
- Submit se pehle answer/save status clear hoga.
- Unsynced answers ko hide karke success receipt nahi dikhayi jayegi.
- Submission accepted aur result prepared hone ko separate states maana jayega.
- Grading pending ho toh student ko receipt aur safe return path milega.
- Grading fail ho toh permitted Retry grading action ho; submitted answers ko change ya re-submit-as-new nahi kiya jayega.

### 6. BITSAT-specific behavior

- Applicable paper mein main questions aur bonus section ka difference clear hoga.
- Bonus entry sirf eligibility complete hone par offer hogi.
- Entry se pehle main answers lock hone ki consequence explicit hogi.
- Bonus enter karne ke baad main answers edit karne ka misleading control nahi rahega.
- BITSAT result par fabricated AIR nahi dikhaya jayega.
- Applicable result par top distinct branch matches aur available campus/programme context diya jayega.
- Guidance ke saath score basis, eligibility aur admission-not-guaranteed qualification preserve rahegi.

### 7. Results: score ke baad useful next step

Existing student result sections phase 1 mein rahenge:
- Analysis.
- Progress.
- Confidence.
- Rank/guidance.
- Solutions.

**Result states**
- Submitted and grading.
- Grading needs retry.
- Submitted but results embargoed.
- Released result.
- Revised score version available.

**Analysis**
- Correct, incorrect, skipped aur other applicable outcomes.
- Subject-wise performance.
- Meaningful accuracy/progress context.
- Current attempt aur comparable previous performance ka useful comparison.
- Score, maximum aur rules ke context ke bina raw number ko official rank mein convert nahi karna.

**Score versions**
- Original aur available revised versions clearly distinguishable rahengi.
- Version change par selected subject, question aur result section retain rahega jahan possible ho.
- Revised result ko silently original result replace karne ki tarah present nahi kiya jayega.

**Guidance**
- JEE Main aur COMEDK rank ranges approximate aur non-official rahengi.
- Sirf eligible full-paper context mein available guidance dikhayi jayegi.
- Chapter score ko full-exam score scale karke guessed AIR nahi banega.
- BITSAT ke liye branch guidance, invented rank nahi.
- Insufficient evidence par clear Unavailable state; made-up confidence nahi.

### 8. Focused Solutions — agreed navigation

Required layout:
1. Small subject tabs.
2. Selected subject ke question numbers ki ek horizontal scroll row.
3. Sirf selected question aur uski released solution.

**Behavior**
- Subject tap karne par usi subject ka question navigation dikhna chahiye.
- Question number tap karne par wahi question open ho.
- Original paper question numbers preserve honge; filtering ke baad renumber nahi honge.
- Long question rows mein last question easily reachable rahega.
- Selected question visible aur clearly highlighted rahega.
- Incorrect, correct, skipped, marked aur other relevant filters preserve rahenge.
- Empty filter result par honest empty state aur alternate filter action.
- Dropdown, Previous/Next strip aur saari solutions ki expanded long list wapas nahi aayegi.

**Solution integrity**
- Original supplied solution primary source hogi.
- Active test ya embargo period mein hidden solutions expose nahi hongi.
- Existing saved supplementary explanation ho toh uski nature clear rahegi.
- Paused AI generation ko working Generate solution button ki tarah present nahi karna.
- Solution open karne aur AI se solution generate karne ko same operation nahi maana jayega.

**Reflection and reporting**
- Student apni mistake category aur short note record kar sakega.
- Review steps explicitly complete kiye ja sakenge.
- Review completed ka matlab actions recorded hai, mastery proved nahi.
- Question, answer key, solution ya display problem report ki ja sakegi.
- Report submit hona instant key correction ya score change ka promise nahi hoga.

### 9. My Tests aur continuation

Three main views:
- In progress.
- Saved.
- Completed.

**Required actions**
- Exact in-progress attempt resume karna.
- Test save/unsave karna.
- Past result open karna.
- Applicable filters/search/date context retain karna.
- Eligible attempts compare karna.
- Unavailable saved paper ko honest unavailable state mein show karna.
- Completed, expired, grading aur embargoed attempts ko distinguish karna.

Student ko paper browse karte waqt progress lose hone ya back jaane par starting screen se dobara search karne ki zarurat nahi honi chahiye.

### 10. All India series aur consistency

**Series experience**
- Existing 62-day series ka clear hub.
- Today's availability.
- Upcoming/scheduled papers.
- Archive/practice access jahan applicable ho.
- Series results aur analysis.
- Server-confirmed daily completion streak.

**Availability**
- Prelaunch, live, start-window closed aur ended/archive states clearly distinguish honge.
- Countdown, start eligibility aur result release actual series rules follow karenge.
- Missing paper ke slot mein fake Start action nahi hoga.
- Historical dates aur future schedules ko promotional copy se override nahi kiya jayega.

**Streak**
- Current streak, best streak aur relevant completion milestones.
- Cup/trophy/running animation restrained aur optional-motion friendly hogi.
- Sirf eligible confirmed series completion streak advance karegi.
- Rapid Fire session complete karna automatically All India daily test complete nahi maana jayega.

**Compact banner**
- Deep blue visual identity.
- Created by AI Astra credit.
- Main All India / JEE Mains Test Series title.
- Proper diagonal 45-degree top-right 100% AI ribbon, horizontal pill nahi.
- Ek pale block mein burgundy Score 200+ with AI aur compact bold AI analysed PYQ based test series descriptor.
- Compact dates, duration/test-count context, availability aur actions.
- Repeated aspiration paragraphs aur separate promotional lines se clutter nahi hoga.
- AI claims, world-best aspiration aur score-goal qualifications explainer mein clear rahengi; verified superiority ya guaranteed score imply nahi hoga.

### 11. New feature: Rapid Fire formula/concept cards

#### Purpose
Rapid Fire fast recall aur recognition ke liye hoga, full mock ka chhota version nahi.

Student ko short card par formula, rule, definition, relationship ya single concept identify karna hoga. Time-consuming numerical solving, long reasoning chains aur lengthy reading passages is mode ka part nahi honge.

#### Entry and session setup
- Home par distinct Rapid Fire entry.
- MVP focus: Physics, Chemistry aur Mathematics.
- Student subject choose kar sakega.
- Available content ke hisaab se chapter-specific ya selected subject ka mixed session choose ho sakega.
- Default session: 10 eligible cards.
- Har card ke liye maximum 20 seconds.
- Iska maximum active-question time approximately 3 minutes 20 seconds hoga; feedback aur end-review time is limit mein include nahi hoga.
- Approved cards kam hon toh actual available count dikhaya jayega; same session fill karne ke liye repeated questions nahi thope jayenge.
- Cards unavailable hon toh clear empty state. Numerical questions ko force-fit karke mode populate nahi kiya jayega.

#### Card design
- Center mein ek prominent card.
- Peechhe next-card ka subtle stack indication, Tinder-inspired feel.
- One short prompt, readable formula if needed, aur short answer choices.
- Preferably one or two short lines of prompt; no long paragraphs.
- Clear subject/chapter label, current card number aur 20-second indicator.
- Answer choices text-heavy ya multi-step nahi hongi.
- Correctness sirf colour se communicate nahi hogi.

#### Allowed content
- Formula recognition.
- Law/principle identification.
- Meaning of a short symbol or relationship.
- Unit/dimension recognition where no calculation is required.
- Direct conceptual distinction.
- One-step true/false recognition with clearly written options where appropriate.

#### Excluded content
- Numerical substitution.
- Arithmetic calculations.
- Multi-step algebra or derivations.
- Long logical puzzles.
- Large passages.
- Dense diagrams requiring prolonged analysis.
- Ambiguous trick wording jiska main challenge reading confusion ho.
- Unreviewed automatically generated cards.

Short symbolic formula dikhana allowed hai; values substitute karke answer calculate karwana allowed nahi.

#### Answer and gesture rules
- Answer select karne ka authoritative action option tap hoga.
- Swipe ko guess/correctness ka implicit signal nahi maana jayega.
- Answer tap hote hi lock hoga; double tap se score change nahi hoga.
- Answer ke baad short Correct/Incorrect feedback aur ek-line concept explanation dikh sakti hai.
- Answer ke baad right swipe ya Next button next card par le jayega.
- Answer se pehle left swipe ya Skip button current card skip karega.
- Gesture ke equivalent visible buttons rahenge, taaki swipe difficult hone par bhi feature usable ho.
- Previous card par jaakar locked answer change nahi kiya ja sakega; full review session ke end par milega.

#### 20-second behavior
- Timer tab start hoga jab card readable form mein saamne aa jaye.
- Earlier answer dene par remaining 20 seconds wait karna compulsory nahi hoga.
- Answer lock hone ke baad us card ka answer timer stop hoga.
- Bina answer ke 20 seconds complete hone par card Timed out record hoga aur next card par transition hoga.
- Timeout ko answered ya correct nahi maana jayega.
- App background hone se active card ko extra answer time nahi milega.
- Background mein session ke baaki cards silently consume nahi honge. Return par expired current card reconcile hoga; next card ka timer uske visible hone par start hoga.
- Session se bahar nikalne par accidental loss avoid karne ke liye clear exit choice hogi.

#### Rapid Fire scoring
- Correct: 1 point.
- Incorrect: 0 points.
- Skipped: 0 points.
- Timed out: 0 points, separate count.
- No negative marking in Rapid Fire.
- Answered accuracy = correct / answered cards; skipped aur timed-out cards separately visible rahenge.
- Session score total correct out of total session cards ke context mein dikhaya jayega.
- Rapid Fire score ko JEE marks, official AIR, BITSAT branch eligibility ya full-test performance equivalent nahi banaya jayega.

#### Session completion
End screen par:
- Cards completed.
- Correct, incorrect, skipped aur timed-out counts.
- Answered accuracy.
- Total correct score.
- Topics needing revision based on this session, without claiming a definitive ability diagnosis.
- Review missed cards.
- Repeat missed cards as a fresh practice session.
- Start another session.

Missed-card review mein original prompt, student's selection or timeout state, correct answer aur short approved explanation milegi. Review untimed hoga.

#### Content and progress separation
- Rapid Fire ek naya dedicated mode hai; existing full-length numerical paper ko 20-second timer dekar rename nahi kiya jayega.
- Is mode ke liye reviewed formula/concept cards chahiye.
- Existing source questions ya supplied solutions ko silently rewrite nahi kiya jayega.
- New paid AI generation service is feature ka part nahi hai.
- Rapid Fire activity same pilot profile ke under separately recognizable rahegi.
- Existing mock-test marks, sealed attempts, series ranking aur 62-day streak rules par iska effect nahi hoga.

### 12. Resilience and honest states

Har important journey mein appropriate Loading, Empty, Offline, Pending, Error, Retry aur Unavailable states honge.

- Loading ko fake progress percentage se fill nahi karna.
- Error ko blank screen mein hide nahi karna.
- Network recover hone par duplicate submission ya duplicate session create nahi karna.
- Long list ya horizontal rail ke last items reachable rahenge.
- Account/session problem aur content unavailable problem ko distinguish karna.
- App ko repeatedly open karne par selected context aur safe pending work preserve rehna chahiye.
- Existing protected content restrictions aur deliberate safety holds bypass nahi hongi.

## User flow

### Flow A — first private-pilot visit
1. App opens with JEELIVE.AI branding.
2. Private-pilot boundary aur unverified phone-entry limitation clear hoti hai.
3. Participant existing permitted pilot entry complete karta hai.
4. Home par exams, Rapid Fire, My Tests aur series destinations milte hain.
5. Selected profile ka hi progress/context dikhaya jata hai.

### Flow B — chapter practice
1. Exam select.
2. Chapter practice select.
3. Subject/chapter choose.
4. Paper details aur rules read.
5. Readiness confirmation.
6. Start or resume the appropriate attempt.
7. Answer, mark, navigate and monitor saving state.
8. Pending saves resolve karke submit.
9. Receipt/grading state.
10. Result and focused Solutions.
11. Mistake reflection or relevant next practice.

### Flow C — interrupted full mock
1. Ongoing attempt mein connection/app interruption hoti hai.
2. Pending work safely distinguished rehta hai; timer ko extra time nahi milta.
3. App reopen/reconnect par same attempt recover hota hai.
4. Accepted answers aur pending drafts reconcile hote hain.
5. Conflict/deadline ho toh clear explanation milti hai.
6. Student allowed state se continue karta hai ya sealed result par jata hai.

### Flow D — focused solution revision
1. Completed result open.
2. Solutions tab select.
3. Subject tab choose.
4. Horizontal row se desired original question number select.
5. One question and released solution read.
6. Mistake category/note or content report record.
7. Filter/subject/question change without losing result context.

### Flow E — 3-minute Rapid Fire burst
1. Home → Rapid Fire.
2. Physics/Chemistry/Mathematics choose.
3. Chapter-specific or available mixed set choose.
4. Session count and 20-second rule visible.
5. First card appears; timer begins.
6. Option tap locks answer; short feedback appears.
7. Right swipe/Next advances; unanswered left swipe/Skip records skip.
8. Timeout automatically records timed-out card and advances.
9. End summary shows correct, incorrect, skipped and timed-out separately.
10. Student reviews missed concepts or starts another session.

### Flow F — daily series
1. Series banner/hub open.
2. Current availability and start eligibility visible.
3. Eligible paper start/resume.
4. Complete and submit under its existing rules.
5. Eligible confirmed completion updates series streak.
6. Results become available only when release rules allow.
7. Archive and personal series history remain accessible where permitted.

## UI/UX feel

### Overall personality
- Elegant, attractive, energetic and trustworthy.
- Not dead/minimal to the point that every action looks the same.
- Not loud, cluttered or full of competing gradients, slogans and animations.
- Native navigation and gestures; website wrapper nahi.
- Clear hierarchy: main action, supporting information, optional details.

### Existing colours to preserve
- JEE Main: glossy blood red identity.
- BITSAT: saffron/orange identity.
- COMEDK: premium black identity.
- All India series: deep shining blue identity.
- Score tagline and diagonal AI ribbon: supplied logo ke burgundy-red colour family.
- Subject tabs: distinct but coordinated accents.

### Reading and accessibility
- Question and solution reading surfaces white/light aur high contrast rahengi, including original source images.
- Dark/light shell choice reading clarity ko harm nahi karegi.
- Comfortable touch targets, scalable text aur readable formulas.
- Selected tabs, active question, chosen answer aur save state clearly visible rahenge.
- Accessibility labels and non-colour status cues.
- Reduced motion preference respected.
- Card swipe, trophy and ribbon styling useful hierarchy support karegi; exam reading distract nahi karegi.

### Rapid Fire feel
- Strong single-card focus.
- Smooth but brief swipe transition.
- Visible countdown without aggressive flashing.
- Correct/incorrect feedback concise.
- No loud casino-style rewards, penalty lives, distracting confetti loops or public racing leaderboard in the MVP.
- Small-card experience aesthetically distinct hoga, lekin JEELIVE.AI branding se disconnected nahi lagega.

## Implementation phases

### Phase 1 — Complete student-feature private pilot: MVP

**Sirf ye phase ab approve hone ke baad build hoga.**

Included:
- Proper native Android student experience.
- Existing phone entry with explicit unverified/private-pilot limitation.
- All current website student features: exam discovery, mocks, chapters, test player, save/resume, My Tests, comparisons, results, focused solutions, reflection/reports, applicable rank/branch guidance, All India series and streak.
- New Rapid Fire mode with 10-card default sessions, maximum 20 seconds per card, formula/concept-only content, native card gestures, simple scoring and missed-card review.
- Supplied branding and the latest compact diagonal-ribbon banner treatment.
- Clear pending/offline/error/empty/release states.
- Existing content, scoring, timing and source-solution integrity preserved.

Not included:
- Public release.
- OTP upgrade.
- Real private student data.
- Native owner/reviewer administration.
- New AI generation, social feed, subscriptions, payments, push campaigns or proctoring.
- Full offline download library or unrestricted copying of private PDFs.
- Restoring a result-PDF download control that is intentionally hidden in the current student experience.

### Phase 2 — Verified learner identity and wider-use readiness

This phase is not part of the current build approval.

- Verified student identity and appropriate account recovery.
- Clear account privacy and deletion experience before wider real-user use.
- Refinement of confusing journeys identified during the private pilot.
- Expansion of reviewed Rapid Fire formula/concept coverage.
- Clear separation of real learner information from pilot-only activity.

All core student features and the initial Rapid Fire experience already belong in phase 1; phase 2 is not a reason to postpone them.

### Phase 3 — Controlled public Android release

This phase is not part of the current build approval.

- Public availability only after verified identity and privacy requirements are resolved.
- Clear store-facing descriptions, support path and release expectations.
- Gradual wider availability rather than a claim of unlimited capacity.
- Existing student progress/content integrity maintained during the transition.
- Additional integrations or feature families require their own explicit scope; they are not silently bundled into public release.

## Assumptions: choices made without further questions

1. Native means an actual Android app experience, not a website opened inside a wrapper.
2. The existing JEELIVE.AI platform and approved content remain the source of truth; there is no replacement student platform or production data migration.
3. Phase 1 includes all current student features, as selected, not merely tests and solutions.
4. Existing unverified phone entry is retained only for the selected private-pilot use. No public release or real private learner information is allowed in that phase.
5. Native staff/admin tooling is excluded; existing protected web staff workflows remain separate.
6. Rapid Fire starts with Physics, Chemistry and Mathematics. Other subject families are not promised for this new mode in MVP, while their existing normal-test support remains intact.
7. A default Rapid Fire session contains 10 eligible cards; fewer available cards are shown honestly.
8. Twenty seconds is a maximum answer window per card, not a forced wait after an early answer.
9. Option tapping selects an answer; right swipe after answering advances, left swipe before answering skips. Equivalent buttons are always available.
10. Rapid Fire awards 1 point for correct, 0 for incorrect/skipped/timeout, with no negative marking. This never changes the JEE/BITSAT/COMEDK normal-test scoring rules.
11. Rapid Fire timeout advances the active card, but backgrounding the app does not silently consume unseen future cards.
12. Rapid Fire uses reviewed, short formula/concept content. Automatic paid AI generation and converting lengthy numericals into timed cards are excluded.
13. Rapid Fire has separate practice history/summary and does not advance the official series streak or create an official rank.
14. Rank/branch guidance remains approximate, evidence-dependent and unavailable where the current result is not eligible.
15. Score200+ is a preparation goal; AI Astra/100%AI are the creator's stated series branding. Neither becomes a guaranteed result, proof of AI authorship for every supplied solution, or verified world-best claim.
16. Existing paused generation and protected content restrictions remain respected.
17. Only phase 1 is the current proposal for building. Verified identity and public release are later phases, not assumed completed capabilities.
