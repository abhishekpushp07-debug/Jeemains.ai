# Rapid Fire portrait refresh — completed 27 October 2026

## Approved scope
Executed Phase 1 of `/app/plan/plan.md`. Only Rapid Fire was redesigned and its
active question bank/testing history cleaned. Academic content, tests, website
results and the archived NEET bank were not deleted or rewritten.

## Full-bank suitability pass
Every one of the **7,045 active JEE cards** was sent with its complete prompt,
formula, all options, answer key, explanation and any diagram to a fresh
AI-assisted editorial review. The previous importance/keyword cache was NOT
used to decide suitability. Decisions are hash-bound to original card content,
validated for complete ID coverage, persisted in `backend/rapidfire/portrait_review/`.
No deletion was allowed while any review batch was missing or inconsistent.

| Outcome | Count |
| --- | ---: |
| Kept, direct quick recall | **6,155** |
| Permanently removed from active bank | **890** |
| Physics kept | 2,383 |
| Chemistry kept | 1,878 |
| Mathematics kept | 1,894 |

Rejection reasons: **442 calculation**, **226 ambiguous**, **105 incorrect**,
**85 multi-step**, **32 borderline timing**. These are editorial judgments, not
measured guarantees for every student. Kept timing estimates are at most 15 seconds.
Suitable question wording/options/keys were not bulk-rewritten. Fourteen retained
cards gained original, scientifically consistent double-slit, ellipse or charged-ring
vector diagrams. Labels remain clear on a 360px phone and render without a download.
Answer-side formula references are now hidden until feedback/review.

Fresh rounds select **30 unique prompts/IDs**, rotating across available chapters.
Sparse selections return an honest choose-mixed error instead of padding or
resurrecting rejected questions. Existing repeat-missed/revision modes remain.

## Approved permanent cleanup
Applied once with marker `rapid_portrait_2026_v1`:
- 890 newly rejected active records + 4,041 previously retired JEE RF database
  records deleted; newly rejected source seed records removed as well. No new
  rejected-question archive was created.
- **209 JEE solo sessions**, **388 JEE duels**, **255 JEE learning events** deleted.
- JEE match-derived XP, correct totals, wins and leaderboard standings reset.
- RF event bus remains a MongoDB capped collection (32 MiB, max 200,000).
- **344 profiles**, aggregate **10,257 Coins**, ownership/equipped cosmetics,
  avatars/freezes and all **399 award ledger records** preserved exactly.
- NEET card/session/duel/learning documents and NEET profile stats fingerprinted
  before/after and unchanged. Shared streaks and claimed quest flags preserved.
- Cleanup is idempotent; `--apply` must not be used for future gameplay resets.

Machine-readable evidence: `backend/rapidfire/portrait_cleanup_report.json`.
After all QA fixtures were removed, wallet/ownership hashes still matched the
pre-cleanup baseline; JEE solo/duel/learning history was empty for a fresh start.

## Experience delivered
- Original portrait energy lobby, player progression/Coins strip, Play Now modes,
  separate Challenge Friend, Join code, one-tap Friends Fight history.
- Four original managed-storage WebP artworks total **31,088 bytes**; reusable,
  disk-cached and nonblocking with local fallback. No 3D engine or video dependency.
- Scoped teal/royal-blue/purple palette, graphite solo/duel cards, scientific
  notation rendering, reduced-motion-aware entrance/feedback components.
- Historical matches are read-only; show opponent, both scores, timestamp and
  historical earned-coins labels. Viewing does not start or reward a new match.
- Confirmed coin purchases, owned-item equip, refreshed real balances, unchanged
  score/reward rates. +1 SCORE is distinguished from +2 COINS per correct answer.
- New verified companion access binds private RF HTTP/WS to canonical identity;
  client-supplied user IDs no longer authorize records. Web uses existing SID,
  native bridges the canonical access cookie in RAM; opaque grants expire in 15m.

## Verification and limitations
- TypeScript + modified JS/Python lint passed.
- Final combined backend run (serial): **19 passed, 1 skipped**, with repeated live
  canonical login deliberately deselected. Test cleanup was corrected to exact
  fixture-owned IDs; it cannot delete another worker's active QA grants.
- Iteration 42 backend: 11 passed (including positive canonical PIN integration).
- Iteration 43: 10 previous checks passed; 9 mutating checks passed, 1 skipped
  because no current sparse Physics chapter was available for that data-dependent test.
- Main phone-size UI checks then completed the initially blocked fixture flows:
  solo correct/skip/real 20s timeout/result/+2 actual Coins/fresh play-again;
  invite/join/live answer/full duel completion/participant history/read-only reopen;
  purchase confirmation/real deduction/equip/lobby refresh; native-vector diagram
  readability and four reachable options/no horizontal overflow at 360px.
- Test harness substituted authentication only for isolated local QA users and
  blocked irrelevant academic prefetch calls. All RF gameplay/wallet/history APIs
  remained real. This harness is NOT present in production application code.
- Canonical service still sometimes returns 502/503/read timeouts. Bounded failure
  states and safe GET retry are present; sign-in/signup POSTs are not blindly replayed.
- Physical Android native cookie bridge, offline typesetting/device performance,
  accessibility settings and final APK/AAB size still need device/build measurement.
  No under-20-MB guarantee or full offline multiplayer promise is made.
- Phase 2 new content/cosmetics and Phase 3 recurring competitions are NOT built.