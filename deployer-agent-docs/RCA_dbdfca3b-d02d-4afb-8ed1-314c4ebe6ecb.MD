# jeelive.ai — Read-Only Production DB Integrity Audit

- Deployment: campus-search-debug (jeelive.ai) · active run `dbdfca3b-d02d-4afb-8ed1-314c4ebe6ecb`
- Database (resolved server-side): `campus-search-debug-test_database`
- Mode: READ-ONLY (find/count/distinct/list_collections/list_indexes only). No writes, no secret changes.
- Time anchor **NOW = 1794673813** (epoch s) — taken from `tejas_operations.maintenance.last_run` (1794673812.96), the production server's own clock at the most recent cron tick. Used for all deadline/lease "< now" checks.

## 1) Collection counts (exact count())
| collection | count |
|---|---|
| tejas_users | 1 |
| tejas_phone_profiles | 14 |
| tejas_sessions | 9 |
| tejas_sets | 252 |
| tejas_attempts | 48 |
| tejas_ledgers | 55 |
| tejas_jobs | 289 |
| tejas_cohort_entries | 57 |
| tejas_packs | 34 |
| tejas_files | 164 |
| tejas_score_versions | 0 |
| tejas_question_reports | 0 |
| tejas_reviews | 0 |
| tejas_saved_tests | 0 |
| tejas_preflight | 52 |
| tejas_audits | 424 |
| tejas_cron_receipts | 73 → 74 (incremented mid-audit) |

## 2) Indexes (name — unique/partial flags)
**tejas_attempts** (15): `_id_`; `user_id_1_start_request_keys_1` (unique, partial: start_request_keys exists); `user_id_1_set_id_1_mode_1` (unique, partial: status="active"); `status_1_deadline_1`; `set_id_1_version_1_status_1_mode_1_cohort_indexed_1_submitted_at_1_id_1`; `set_id_1_mode_1_competition_ranked_1_summary.score_-1`; `id_1` (unique); `user_id_1_started_at_-1`; `user_id_1_start_key_1` (unique); `chapter_attempt_latest`; `exam_attempt_history`; `set_id_1_status_1_version_1`; `status_1_grading_status_1_submitted_at_1`; `user_id_1_series_id_1_started_at_-1`; `user_id_1_exam_1_mode_1_status_1_submitted_at_-1`.
**tejas_phone_profiles** (3): `_id_`; `id_1` (unique); `phone_1` (unique).
**tejas_users** (3): `_id_`; `email_1` (unique); `id_1` (unique).
**tejas_sessions** (3): `_id_`; `id_1` (unique); `expires_at_1` (TTL, expireAfterSeconds=0 — requires BSON date values).
**tejas_ledgers** (2): `_id_`; `id_1` (unique).
**tejas_cohort_entries** (4): `_id_`; `id_1` (unique); `cohort_id_1_user_id_1` (unique); `cohort_id_1_score_-1`.
**tejas_sets** (9): `_id_`; `chapter_book_id_1_chapter_number_1`; `id_1` (unique); `status_1_exam_1`; `status_1_audience_1_exam_1_created_at_-1`; `series_date_1` (unique, sparse); `pyq_date_catalogue`; `book_import_id_1_mock_number_1`; `catalog_section_id_1` (sparse).

## 3) tejas_attempts by {status, grading_status, mode}
- {completed, ready, practice}: **48** — this is the ONLY group. All 48 attempts are completed / ready / practice.

## 4) Active attempts with deadline>0 AND deadline<now
- **0** (there are 0 attempts with status="active" at all).

## 5) Completed attempts with grading_status issues
- grading_status NOT in [ready, failed]: **0**
- grading_status = "failed": **0**

## 6) Completed+ready attempts with NO ledger (attempts.id → ledgers.id)
- **0** — every one of the 48 attempts has a matching ledger.

## 7) Completed attempts with a ledger but summary.score_exact mismatch (or summary missing)
- **0** — all 48 attempt score_exact values equal their ledger score_exact. No missing summaries.

## 8) Attempts with pack_id set but no matching tejas_packs._id
- **0** — all 48 pack_id values resolve to a packs doc.

## 9) Attempts with set_id but no matching tejas_sets.id
- **0** — all 48 set_id values resolve to a sets doc.

## 10) Attempts whose user_id matches neither phone_profiles.id nor users.id
- **0** — all 48 resolve (47 to phone_profiles, 1 group to the single users doc).

## 11) Duplicate groups (groups with >1 doc)
- phone_profiles by phone: **0**
- users by email: **0**
- attempts (competition_end exists) by (user_id,set_id): **0** — 0 attempts have a competition_end field.
- attempts status="active" by (user_id,set_id,mode): **0** — 0 active attempts.
- cohort_entries by (cohort_id,user_id): **0** (protected by unique index).
- ledgers by id: **0** (protected by unique index).

## 12) tejas_jobs by {kind, status}; running with lease_until<now
- book_step / done: **225**
- grade / done: **48**
- cohort / done: **15**
- report / failed: **1**
- Distinct statuses present: done, failed only. status="running": **0**; running with lease_until<now: **0**.
- NOTE: 1 failed job — kind=report, lease_until 1794611712.887 (status "failed"). The only non-done job in the system.

## 13) Sessions integrity
- user_id matching neither phone_profiles.id nor users.id: **0** (all 9 resolve).
- expires_at NOT a BSON date: **0** (all 9 are valid BSON dates — consistent with the TTL index requirement).

## 14) cohort_entries referential checks
- attempt_id with NO matching attempt: **13** of 57. Breakdown: 7 point to ids that exist only as tejas_ledgers docs (6fa7173d, 89739b0a, b54f67d2, dd3ad893, b78e13c0, 1067390e, f5093625); 6 point to ids that exist in NEITHER attempts nor ledgers (aaba8b6c, 2b7b7b07, f060a812, b74aec6c, 5c37c9bd, 50e3a853).
- score_exact != ledger summary.score_exact (for the 44 entries whose attempt_id resolves to a ledger): **0 mismatches**. The remaining 6 orphan entries (neither attempt nor ledger) have no ledger to compare against (unresolvable), overlapping the set above.

## 15) Timestamp sanity
- submitted_at < started_at: **0**
- deadline>0 AND submitted_at > deadline+5: **0** (auto-submits land exactly at deadline; manual submits land before it).

## 16) Operations & cron
- tejas_operations id="maintenance": last_run=1794673812.9641807, expired=0, outbox_checked=0, recovered_jobs=0.
- 5 newest tejas_cron_receipts "at": 1794673812.936, 1794672912.860, 1794672012.902, 1794671112.679, 1794670212.904 — exactly 900 s (15 min) apart. Cron receipt count rose 73→74 during the audit. **The 15-minute production cron is firing normally.**

## Server / infra facts
- MongoDB version & replica-set status: **NOT retrievable** through the available read-only query interface (only find/count/distinct/list_collections/list_indexes are exposed — no buildInfo/hello/replSetGetStatus). The app DB is platform-managed MongoDB Atlas (one cluster per app), which runs as a replica set by design; the TTL index (expireAfterSeconds) and partial indexes in use confirm a modern (3.6+) server. Exact version string is UNVERIFIED from this interface.
- Production backend (tier_2 "Grow"): replicas **2** (max 2, HPA disabled, VPA enabled); CPU request **500m**, limit **1000m**; memory request **2Gi**, limit **4Gi**; ephemeral-storage **5Gi**.

## Summary of anomalies (everything else is clean)
1. **Orphaned cohort_entries (13/57)** and **orphaned ledgers (7: 55 ledgers vs 48 attempts)** — scoring/cohort records survive for attempts no longer present in tejas_attempts. No unique/FK constraint ties cohort_entries.attempt_id or ledgers.id back to an attempt, so pruned/deleted attempts leave these behind. Could be intentional retention, but it IS a referential gap.
2. **1 failed `report` job** (lease_until 1794611712) sitting in status="failed" — will not retry on its own.
3. No scoring drift, no stuck/expired active attempts, no duplicates, all pack/set/user FKs resolve, sessions valid, cron healthy.
