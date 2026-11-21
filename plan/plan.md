# JEELIVE.AI: Fix the live PYQ tests and make the selected option green, then the 8-level backend plan

First, the PYQ tests that are broken in the live app are fixed, and in every test the selected option turns green in place of red. Both go live together.
After that, the backend is rebuilt in 8 small, safe levels until it is fast, strong and ready for 50,000 students at once.

## Who it's for
- **Students:**
  - they can take JEE Main PYQ papers without errors
  - answers are never lost and question pictures load
  - the option they choose is clearly marked in green
- **Owner (Abhishek):** the live app works again. Afterwards an **App Health** page shows speed and errors. There is no manual work in between: one Publish for Phase 1, and one Publish at the end of all the levels.

## Core features and experience

### 1. Problem found in the live app (from the screenshots)
- The PYQ paper list shows "The origin web server sent a response that Cloudflare could not parse…" and pressing Retry gives the same error again and again.
- During a paper, an answer stays stuck at "1 pending" and does not save.
- A question picture shows "The original image could not load".
- The student sees raw technical English text.
- The jeelive.ai website was working fine in the browser at the same time. So the fault is not in the student's internet. It is on the path between our live server and the website, or in our live server itself.

### 2. What changes after the fix
- The PYQ list, answer saving and pictures work without errors.
- **Answers are never lost.** If a save cannot reach the website for a moment, the answer stays safe on the phone, a plain message shows, and it is sent again automatically when the line comes back.
- **Submit waits until every pending answer has been sent.** A paper is never submitted with answers missing.
- **Students never see technical text.** In its place they see one plain line, for example: "The website is not answering right now. Your answer is safe on this phone. We are trying again."
- If a picture fails to load, it is tried again automatically a few times, a little later each time.

### 3. The selected option turns green (every test)
- **Today:** in PYQ papers (options cut from the paper's picture), the selected option gets a red border, and the number circle and tick circle also turn red, because red is the app's main colour.
- **New:** the selected option gets a **light green border**, the **number circle and the tick circle turn green**, a white tick sits inside, and the card gets a very faint green wash.
- **Same everywhere:** this applies to mock tests, PYQ papers, All India tests and every other test, and to all three kinds of options:
  - options cut from a picture
  - typed options
  - big number tiles for scanned papers

  Those other two kinds currently mark the choice in black; they become green too.
- **No change to:** the solutions screen after a test (green = correct, red = wrong stays as it is), the question palette colours, and Rapid Fire's own game colours.
- **Before any code is written, a picture of the new look is shown** (today's red option next to the new green one). Code starts only after that.

### 4. The 8-level backend plan (as approved before)
- No screen or button changes for students.
- The same server addresses, so old builds of the app keep working.
- A new **App Health** page in the owner panel (same login as the deletion panel). It shows how many students are on, the speed, the errors, the jeelive.ai website's health and the background jobs. It shows counts only, never a student's name or number.
- Every step is checked against the previous correct answers. Every new fast path has a fallback to the old one.

### Why small steps (the straight answer)
- After every step, everything is checked. If something breaks, only that one step is undone.
- Speed is measured part by part, and future work gets faster.
- **The honest truth:** splitting files alone does not make the app faster. The real speed comes from Levels 4–7. Splitting is needed so that the speed work can be done without anything breaking.

## User flow
**Owner**
1. Approves the plan.
2. A picture of the new green option look arrives first, and the owner sees it.
3. The PYQ fix and the green option are built and checked on the preview.
4. One message arrives: "Phase 1 is ready". The owner presses **Publish** once and opens one paper to check it.
5. Levels 1–8 are built one after another on the preview, with nothing for the owner to do.
6. At the end, one message arrives: "Everything is ready". The owner presses **Publish** once more, and the App Health page shows the live app's speed.

**Student**
- Opens JEE Main → PYQ papers (or any mock test) and picks a paper.
- Taps an option: the border turns light green, and the number circle and tick turn green.
- Answers are saved quietly. If the network drops for a moment, the answer stays safe and is sent on its own.
- Submits and sees the result. Pictures load as normal.

## UI/UX feel
- Apart from the option colour, the test screen looks exactly as it does now.
- **Selected option:**
  - light green border, slightly thicker than an unselected card
  - green number circle and green tick circle with a white tick
  - a very faint green wash on the card
- **Unselected options** stay as they are: white card, grey border.
- The error box shows a short, plain line in place of the technical English text. Next to "1 pending" it shows "Safe on phone · sending".
- The App Health page uses the dark style of the owner panel, with big green / amber / red numbers, plain words, and a refresh every 30 seconds.

## Implementation phases

**Phase 1: Live PYQ fix + green option (built now)**
- **Green option, picture first:**
  - Show the before/after picture.
  - Then change all three kinds of options in every test to the light green border and green circles.
  - Check it on the phone screen size on the preview.
- **Find the cause** of the PYQ errors from the live server's records:
  - who sent the error: our live server or the jeelive.ai website
  - which tasks failed (paper list, answer save, pictures)
  - since when: whether it started after the last Publish
- **Reproduce** the same path on the preview, on a test account, without submitting any paper.
- **Fix the real cause.** If our server is at fault, it is fixed. If the website is rejecting our server, the app keeps answers safe, shows a clear message and keeps trying again; an exact note for the website team is also written.
- **Answers:** safe saving on the phone, automatic resending, and Submit waits for every pending answer.
- **Pictures:** automatic retries, a little later each time.
- Plain messages in place of technical text.
- **Done when** the preview check shows two things:
  - the full PYQ path (list → paper → answers → pictures → saving) with no errors
  - a green selected option in every kind of test

  Then one Publish.

**Phase 2: Strong foundation (Levels 1–4)**
- **Level 1, safety net:** record the right answer for every server address, merge the scattered tests into one full check, measure today's speed and crowd limit, and re-check All India Daily on a clean test account.
- **Level 2, tidy the house:** sort the 40+ server files into clear parts, put settings in one place, and remove code that never runs. The NEET archive stays safe.
- **Level 3, split the big main file:** addresses and answers stay exactly the same.
- **Level 4, faster database:** the right index for every lookup, read only the fields needed, and old temporary data clears itself. Target: every Rapid Fire database task within 20 ms (95% of the time).

**Phase 3: Power and proof (Levels 5–8)**
- **Level 5, speed engine:** keep decks, leaderboards and profiles ready in advance, reuse the website connection, compress answers, and do non-urgent work in the background. Coins and answers are always saved at once. Target: Rapid Fire answers within 100 ms (95% of the time).
- **Level 6, live match engine for 50,000:** many server copies can run side by side, background jobs run on only one copy, a match carries on if a copy restarts, and every reward is paid exactly once.
- **Level 7, shields and eyes:**
  - If jeelive.ai is slow or down, the server stops calling it again and again, and Rapid Fire keeps working.
  - Limits per player.
  - In a big crowd, important work comes first.
  - PINs and passwords never appear in any record.
  - The **App Health page** is built here.
- **Level 8, proof of 50,000:**
  - Increase the crowd step by step: 1k → 5k → 10k → 25k → 50k simulated players.
  - Show that adding copies grows capacity in a straight line.
  - Run tests lasting hours, plus fake website-down and website-slow tests.
  - Compare with the baseline and rehearse the release, then one Publish.

## Assumptions
- **Green covers every test kind and all three option styles,** not just PYQ papers, so every test feels the same.
- **During a test, green only means "your choice".** No right or wrong is shown during a test. On the solutions screen afterwards, green still means correct and red still means wrong. That screen is not changed.
- The green is the same green already used for "Answered" in the question palette, so the colours match. The border is a lighter shade of it.
- Rapid Fire's game colours (its own world) do not change.
- **The PYQ fix and the green option go live together in one Publish, before the 8 levels,** because students cannot take tests right now. The 8 levels still go live together, once, at the end. Only the owner can press Publish.
- No paper is submitted on any real student's account during testing. The test account's PIN is never used to delete anything.
- If the cause turns out to be on the jeelive.ai website (for example, the website rejecting our server), it cannot be fixed fully from the app side. In that case the app keeps answers safe, keeps trying again, shows plain messages, and an exact note is given for the website team.
- **The 50,000 target covers what runs on our server:** Rapid Fire, matches, leaderboards, Cup Night and All India. The speed and capacity of login, tests and results are in the website's hands. The plan builds shields for them.
- The preview cannot bring in a real crowd of 50,000. The proof comes from one copy's capacity plus the straight-line growth as copies are added. How many copies run in production is decided by the hosting.
- Nothing in the live database is deleted or moved. The only change is new indexes, which build on the live app without stopping it.
- No new paid outside service is used.
- Play Store / App Store readiness is not part of this plan. It will be done separately later.
- All technical decisions are taken during the build. Nothing is left for the owner to decide.
