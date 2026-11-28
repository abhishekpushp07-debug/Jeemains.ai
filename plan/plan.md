# JEE MAIN · 2027 JAN ATTEMPT: date-wise shift mocks on Home

On Home, COMEDK's tile gives its place to "JEE MAIN · 2027 JAN ATTEMPT". Every shift of the January 2027 session becomes its own mock: memory-based first (even if only partly recalled), then replaced by NTA's official paper when it is released.
Each mock is a normal paper (timer, autosave, result, analysis), plus an All India rank among everyone who took that shift's mock, and a Rank Card in Analysis.

## Who it's for
- **Students:** JEE Main students who want to sit the real January shifts as mocks, including those preparing for the April session.
- **Owner:** decides when the tile and papers go live.
- **Website team:** makes the papers, ranks and data. The app tells them exactly what to send.

## Core features and experience
**1. Home tile, in COMEDK's place**
- **Name:** "JEE MAIN · 2027 JAN ATTEMPT". Home's tile names are set in a single line, so on small phones it may read "2027 JAN ATTEMPT" with "JEE MAIN" above it in small caps.
- **Before the first paper:** a bold red diagonal ribbon runs corner to corner across the tile, saying "COMING SOON". The line under the name reads "20 Jan se".
- **Once the first paper is out:** the ribbon goes, and the line shows how many shift papers are ready (for example "5 shift papers"). A small "NEW" badge appears on a day a new paper arrives.
- **COMEDK:** still reachable from Explore ("comedk mocks") and its exam page. Only its Home tile moves.
- **Switch:** the owner's switch on the website decides whether the tile shows. Off means Home is exactly as today, with COMEDK back.

**2. 2027 Jan Attempt screen**
- **Top:** "JEE Main · 2027 Jan Attempt". Before 20 Jan it shows a countdown ("20 Jan tak 52 din").
- **Date-wise list:** 20, 21, 22, 23, 24 and 28 Jan. Each date has two cards: Shift 1 (9 AM–12 noon) and Shift 2 (3–6 PM). Today's date is highlighted.
- **Each shift card says where it is:**
  - "Paper shift ke baad aayega" (no paper yet).
  - "Memory based · 62/75 sawaal" (partial) or "Memory based · 75 sawaal".
  - "NTA official".
  - The student's own state: Start / Resume / Result, their score, and their All India rank in that mock.
- **Opening a paper:** goes to the usual paper page, timer, autosave, result and analysis, as every paper works today.

**3. Memory-based → NTA official**
- When NTA releases a shift's paper, the official one takes that shift's place and the memory-based one leaves the list.
- Results of the memory-based attempt stay in My Tests and stay readable, labelled "Memory based".
- If NTA changes the answer key (provisional → final), the website re-scores. The result shows the existing "revised scoring" note.

**4. All India rank of each shift mock**
- **In the result:** the result's Rank tab shows that mock's leaderboard among everyone who took it, with the number of students so far. It updates as more students take it.
- **On the shift card and in My Tests:** a rank chip, for example "#123 / 4,560".

**5. Rank Card in Analysis**
- **On a 2027 Jan Attempt mock's Analysis:** a Rank Card in the Rank tab's card style. It shows the All India rank in that mock, the top percentage, and the score.
- **For a complete 75-question paper:** it also shows expected JEE Main percentile and rank from that score, using the app's own Rank predictor (the same as the Rank tab).
- **For a partial paper:** only the mock rank, because an expected rank from a partial paper would mislead.
- **Sharing:** the card can be sent on WhatsApp, like Rank tab cards.

**6. My Tests**
- These papers are labelled "JEE Main · 2027 Jan Attempt", with "Memory based" or "NTA official".

## What the website must send (note for the website team)
- **Switch:** "jan_attempt" On/Off, in Super Admin.
- **Schedule:** the exam dates and shifts (date, shift number, time). The owner can edit it if NTA changes a date.
- **For each shift, its current paper (if any):**
  - The paper's id.
  - Memory-based or NTA official.
  - Questions in it and out of how many (62 of 75).
  - Minutes and maximum marks.
  - When it was published.
- **For the signed-in student, per paper:** their attempt (state, resume, result), score, and their rank in that mock. This works the same way as the PYQ list today.
- **When the official paper comes:** the memory-based paper stops appearing in the list. Its old attempts and results stay readable.
- **Results of these papers:**
  - Marked as a 2027 Jan Attempt paper, memory-based or official.
  - The student's rank: rank, out of how many, and percentile among takers.
  - A leaderboard for each of these papers, in the same way the result's Rank tab already reads leaderboards.
- **Rank rule:** only a student's first attempt counts in a mock's rank. Re-attempts never change it.

## User flow
1. Student opens Home and sees "JEE MAIN · 2027 JAN ATTEMPT" with the red "COMING SOON" ribbon. They tap it and see the dates, shifts and countdown.
2. On an exam day, the evening's memory-based paper appears on that shift's card. The student starts it, gives the mock, then sees the result, analysis, Rank Card and All India rank.
3. Later, NTA's official paper replaces it on that card. The earlier result stays in My Tests.

## UI/UX feel
- **Home tile:** the same look as its neighbours, so the grid stays calm. The one bold touch is the red diagonal "COMING SOON" ribbon, with white tracked capitals.
- **2027 Jan Attempt screen:** a clean date timeline. Shift cards look like today's PYQ cards. JEE Main red accents, today glowing softly.
- **Rank Card:** the same family as the Rank tab's cards. It will later take on the ruby-gold look with them, in the colour-cards task, asked about separately.

## Implementation phases
**Phase 1 (now, MVP), one pocket at a time, each finished and tested before the next:**
- **Pocket 0:** the website note above, ready to send. Nothing in the app changes.
- **Pocket 1:** the Home tile with the "COMING SOON" ribbon, behind the website's switch. Switch off means Home is as today.
- **Pocket 2:** the 2027 Jan Attempt screen: dates, shifts, countdown, every card state, and memory → official replacement. Tested with the website's answers played in the browser, since the website is not built yet.
- **Pocket 3:** All India rank: the rank chip and the result's Rank tab for these papers.
- **Pocket 4:** the Rank Card in Analysis, with expected JEE Main rank for complete papers, and WhatsApp share.

The switch stays off for students until the website is built.

**Phase 2, once the website has built it:**
- Live end-to-end test on TEST accounts: memory paper, partial paper, official replacement, re-scoring, ranks.
- Then the owner turns the switch on.
- Each shift card also links to Matched when that shift has matched questions.

**Phase 3:**
- The same pipeline for the April session (2–7 Apr 2027), by switching the session.
- The ruby-gold look for this Rank Card together with the other Rank Cards.

## Assumptions
- **Dates:** 20, 21, 22, 23, 24 and 28 Jan 2027, two shifts a day, as per NTA's notice of 24 Oct 2026. The website's schedule is what the app shows.
- **Paper:** only Paper 1 (B.E./B.Tech); B.Arch and B.Planning are left out.
- **Ribbon:** "COMING SOON" stays until the first paper of the session is published.
- **Partial papers:** the website sets their minutes and marks for the questions they have. The app shows them as sent.
- **Marking:** as JEE Main (+4 / −1), set by the website.
- **Names on leaderboards:** the student's chosen name, or "Learner".
- **Dream College meter:** only complete NTA official papers count, like PYQ. Memory-based papers do not.
- **Cost:** free for all students. No push notifications.
- **Untouched:** the start screen, the Rank tab, and the colour-cards task.
