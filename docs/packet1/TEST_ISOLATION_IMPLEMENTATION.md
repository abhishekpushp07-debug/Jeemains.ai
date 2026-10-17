# Test isolation implementation — corrected baseline

Run only `python -m pytest /app/tests/packet1` in a fresh process. Do not combine it with old unsafe audit scripts or modules that import the application before isolation.

`conftest.py` generates an exact `tejas_p1_test_<32hex>` database name BEFORE importing `tejas.db` or `server`. Runtime env changes are process-local, never written to .env. Only the supplied MONGO_URL is reused; DB_NAME, JWT secret, bootstrap staff password/email and disabled AI key are synthetic. No real staff login is used.

Motor `get_database`, indexing, `drop_database` and direct `AsyncIOMotorDatabase` construction reject every name except this run's exact UUID name. They also reject later DB_NAME drift. Application collections are therefore backed by real isolated Mongo. This is an application-test boundary, not protection against malicious arbitrary code creating unrelated low-level sockets/clients.

All async fixtures and test bodies share one session loop. Indexes are created once per run. DB-using cases delete documents inside that namespace; session teardown drops only the run's own database. Cleanup errors fail the suite. Do not revert to per-test drop/create-index churn or per-test Motor loops.

Requests/urllib/httpx network transports are blocked. In-process ASGI transport remains available for real API/auth tests. A06 explicitly MOCKS source bytes and parser results; other concurrency controls forward to real code/repositories. Publication holds are bypassed only in the isolated A02/A06 tests and restored by monkeypatch teardown.

Six known audit invariants use `xfail(strict=True, raises=OpenInvariant)`. They assert the CORRECT behavior, which the current code violates. Only that explicitly named final invariant may xfail. Setup failures, timeouts and unrelated exceptions fail the run. Unexpected passes require investigation, never silent removal. A01 belongs to P06, A02–A04 to P05, A05–A06 to P04; those are packet owners, not severity scores.

Evidence must retain counts/node IDs/code hashes/mock inventory without secret values, phones, cookies, real database names or .env dumps. Initial reports did not capture exact per-run UUID identities externally; the guard generates them internally. Final evidence bundle IDs must not be misrepresented as original test-run IDs.
