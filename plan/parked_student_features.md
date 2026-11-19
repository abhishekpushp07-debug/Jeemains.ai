# Parked: three student features

**Status: not started.** No code was written for these features. They were parked at the owner's request when the Super Admin PDF engine work began.

**Owner's instruction:** save this work for the future, work on super admin first, and **remind the owner about these three features when the super admin work is done.**

First build step after plan approval: copy this file to `/app/memory/PARKED_STUDENT_FEATURES.md` and add a pointer to it in `/app/memory/PRD.md`. (It sits in `/app/plan` only because plan mode allowed writes nowhere else.)

## Part A. From the handoff summary (reliable)

What the owner asked for:
1. **Galti Notebook**: an error notebook collecting all wrong questions for re-practice, segmented Subject -> Chapter -> filter.
2. **Subject Rank**: on each paper, a separate Rank and Percentile for Physics, Chemistry and Maths.
3. **Seekh Reminder**: the student's top 3 learnings shown right before the next mock starts.
4. The app team's packet updated for all three.

Quality bar: visually stunning, perfect and elegant. The owner also said not to keep asking questions.

Decisions taken because the owner did not answer the earlier questions (all can be changed):
- The notebook holds wrong answers only, not skipped questions.
- A question leaves the notebook when the student later solves it correctly, or marks it "Got it" by hand.
- Rapid Fire is left out for now.
- The app team guide is updated together with the features.
- Student copy in Roman Hinglish, in the Analysis 2.0 design language.

Starting points named in the handoff:
- Backend: `backend/tejas/attempts.py`, `backend/tejas/class_stats.py`, `backend/tejas/analysis_api.py`, `scoring.py`.
- Seekh Reminder goes into `frontend/src/components/player/GetReady.js`.
- Galti Notebook entry point: possibly `frontend/src/features/Home.js` or a new route.
- Subject Rank: the background job in `class_stats.py` works out rank and percentile for the overall score only; it needs the same per subject, then the Analysis 2.0 screens show it.

## Part B. Technical leads NOT checked in this session

These notes were written at the start of the planning session. The reading they came from cannot be traced in this session, so none of them was confirmed against the code. Treat every line as a lead to check, not as a fact.

**Seekh Reminder**
- Seekh may be stored per attempt in `tejas_learnings` (`_id` = attempt id, `user_id`, `items` up to 3 of up to 140 characters, `submitted_at`, `title`, `exam`), with a `notes_for()` helper in `analysis_api.py` that finds the seekh of the previous mock.
- The get-ready screen may be switched on by `features/SetDetail.js` sending `get_ready: true` to `/sets/{id}/start`, with a 60-second countdown.
- Likely need: one small read call for "my latest non-empty seekh" and a card on the get-ready screen; nothing shown when the student has never written any.

**Subject Rank**
- Class statistics may be built in `class_stats.refresh()` over `tejas_class_entries`, with per-question short codes on each entry and `subject`, `pos`, `neg` per question on the class frame, which would let each student's subject score be worked out in the same pass.
- Overall rank may come from a sorted score histogram through `rank_at()`; the same histogram per subject would give rank, class size and percentile per subject.
- Classes built before the change would have no subject histogram and need a rebuild marker. The analysis cache may be keyed on an `ANALYSIS_VERSION` that needs raising.
- Places to show it: Overview, the Performance table, and the PDF report.

**Galti Notebook**
- A wrong answer may be a scored row with `outcome == 'incorrect'`. Attempts may carry `test_kind`, `mode`, `exam`, `set_id`, `pack_id`.
- Question pictures are served per attempt (`/attempts/{id}/questions/{qid}/asset/...`; this path was seen in `Player.js` in this session), so a notebook entry needs to remember an attempt it can be opened through.
- Points to settle in code: nothing enters before a live exam's answers are released; deleted papers drop out; preview and staff attempts are excluded.
- An existing "retry" mode (untimed revision; the label was seen in `Player.js` in this session) may be reusable for re-practice across attempts.
- New API routes may need an entry in `backend/tejas/route_contracts.py` and a request model.

**Loose ends, also unchecked**
- The app team files `docs/app_packet/APP_UPDATE_2026-11-19.md` and `README.md` may still say "preview only, not on jeelive.ai", while the handoff says the owner has deployed to production. Check and correct with the next change.
- A leftover test database on the preview MongoDB was noted earlier (name recorded as `tejas_isolated_book170_436fa878`). Check that it exists and ask the owner before dropping anything.

## Analysis 2.0 plan

`/app/plan/plan.md` held the Analysis 2.0 plan until the Super Admin PDF engine plan replaced it. A full copy of the old text is saved as `/app/plan/analysis2_plan.md`. If `/app/memory/PRD.md` points to `plan.md` for the Analysis plan, update that pointer.

Still pending from it, Phase 2 (needs its own approval):
- Sign-in rate limiter fix: read the student's real IP and count only wrong PINs.
- Mock-to-mock trend over the last 5 mocks.
- Owner sets Difficulty and chapter tag per question in Master.
- Subject-wise Rank and Percentile (one of the three parked features above).
- Galti notebook (one of the three parked features above).

Phase 3 (needs its own approval):
- Load test for 1 to 2 lakh students at the same time.
- Owner paper report: most-failed question, most-picked wrong option.
- Target Score for the next mock and its follow-up.

## The work that pushed these aside

The owner asked for a stronger PDF engine in Super Admin: the question area shows only the question and each option button shows that option's content cut from the book, with no AI. Its plan is `/app/plan/plan.md`. When its Phase 1 is accepted, remind the owner about the three parked features.
