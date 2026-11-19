# Rapid Fire — Rules (written first, June 2026)

Owner's rules (Hinglish brief, 19 Nov 2026): "1. 20 seconds. 2. 30 / 50 cards option just above or below the
subject list, above the chapter list. 3. Double the content without repeating; up to 3x where the chapter is
not covered; proper overview of what is covered and what JEE topics are not. 4. Short notes, concepts,
points, formulae — solvable without pen within 20 seconds. That is the gate. 5. Same for BITSAT English and
Logical Reasoning. Do not rush. Questions should not repeat."

## R1 — Time
- Every card gets **20 seconds** in every mode: Solo Sprint, Practice Rival, Quick Match, Friends rooms,
  Gang battles, Knockout Cup, Cup Night. The clock starts only when the card is on screen.
- Server limits follow the same number (`CARD_SECONDS = 20` in duels.py, `seconds_per_card: 20` for solo).

## R2 — Card count (30 / 50 / 100)
- The student picks **30, 50 or 100 cards** for a round.
- Where: in the Rapid Fire lobby directly **below the subject list**, and in the battleground sheet
  **between the subject tabs and the chapter list** (one shared choice, remembered on the phone).
- A count is offered only when the chosen subjects/chapters have that many unique cards; otherwise that
  pill is dimmed with "needs more cards" and the round falls back to the largest count that fits.
- Applies to Solo Sprint, Practice Rival, Quick Match (you are matched only with players who chose the same
  count) and Play Friends rooms. Knockout Cup / Cup Night stay 30 (bracket timing is fixed).

## R3 — Content volume, no repetition
- Coverage is measured against the official **NTA JEE Main 2026 syllabus**, chapter by chapter, split into
  subtopics (and the official **BITSAT 2026** syllabus for English and Logical Reasoning).
- Every JEE chapter at least **doubles (2x)**. A chapter whose subtopics are missing or thin may grow up to
  **3x**: extra = min(existing, 8 x missing subtopics + 4 x thin subtopics).
- New cards are written first for the missing and thin subtopics, then spread by subtopic weight.
- Report: `/app/memory/RAPID_FIRE_COVERAGE.md` (covered, thin, missing, targets, final counts).

## R4 — The 20-second gate (a card goes live only if ALL pass)
- **G1 Type**: formula, law, definition, short-note fact, concept statement, trend, exception,
  unit/dimension, graph shape, standard result (English: grammar rule, usage, vocabulary; LR: one-rule pattern).
- **G2 No pen**: answerable in the head. At most one trivial mental step. No substitution with non-trivial
  numbers, no multi-step algebra or calculus, no solving equations, no long case work.
- **G3 15-second read + answer** for a prepared student (5 s margin inside 20 s). Prompt ≤ 120 characters
  (English/LR ≤ 150), options ≤ 40 characters, one short explanation line.
- **G4 One right answer**: exactly one correct option; no "all of these", "none of these", "both A and B".
- **G5 Blind second solve**: a model from a different AI family solves the card without seeing the key. Its
  answer must equal the key, otherwise the card is dropped (never "fixed" silently).
- **G6 Syllabus**: inside NTA JEE Main 2026 (BITSAT 2026 for English / LR). Nothing beyond it.
- **G7 No repetition**: not the same fact asked the same way as any other card — exact fingerprint,
  near-duplicate check (same answer + ≥ 70 % same words) and a judge check against the same subtopic.

## R5 — BITSAT English and Logical Reasoning
- Same rules, same 20 s. New subjects "English" and "Logical Reasoning" (shown as BITSAT in the arena).
- Text-only by design: long reading passages and figure-based non-verbal reasoning (paper cutting, figure
  matrix, mirror images) are excluded because they cannot be fair in 20 s without pictures / long reading.

## R6 — No repeats for a student
- Inside a round: never the same card or the same prompt twice.
- Across rounds: cards the student has not seen yet are dealt first; seen cards return only after the
  unseen pool of that selection runs out.

## Pipeline (resumable; `backend/rapidfire/expand_bank.py`)
syllabus (subtopics per chapter) → map (every existing card tagged to a subtopic) → report (coverage +
targets) → author (Claude Sonnet 5.5, missing/thin subtopics first, ~1.4x over-generation) → gate
(GPT-5.6 Terra blind solve + G1–G7) → dedupe (whole chapter + same-answer cards of the subject's other chapters,
flagged = `dup2`) → merge (append to `rapidfire/cards/*.json`, subject-wide exact/near-duplicate check, cards with raw
TeX `\` or `$` skipped; live sync picks them up within 60 s) → final (after-numbers in the coverage report).
Nothing reaches students before the gate. Top-up rounds: author → gate → dedupe again (author only writes what is short).

## Result (20 Nov 2026, live)
Physics 2383 → 5292 (2.2x), Chemistry 1878 → 4492 (2.4x), Mathematics 1894 → 4046 (2.1x), English 0 → 1416,
Logical Reasoning 0 → 912. Total 6155 → 16158 cards. Backup of the bank before merge: /tmp/rf/cards_backup_before_merge
(temporary). Per-chapter numbers: `/app/memory/RAPID_FIRE_COVERAGE.md` (section "After expansion").
