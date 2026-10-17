# Test isolation and evidence contract

Only `python -m pytest /app/tests/packet1` is the Packet 1 suite. Old audit scripts remain historical evidence; do not run them against the preview. They can contain weak harnesses or sensitive fixtures.

The Packet 1 harness must load a throwaway UUID database name before importing any application module, assert the name has the exact `tejas_p1_test_<32hex>` form, reject the configured pilot database, and prevent overrides from changing it after import. No test may insert QA sets into the preview database or publish real content. Cleanup may delete only its own newly created database. Fail closed on any other name. The existing MONGO_URL file is not changed.

Use the real Mongo repository with temporary fixtures for concurrency/receipt tests. External storage and parser network calls are BLOCKED or explicitly stubbed; no source upload, real cloud write, cron registration, credential/session deletion or production admin sign-in is allowed. For browser smoke tests use an ephemeral phone-only test profile with visible test metadata if necessary; prefer unauthenticated public flows and isolated ASGI login tests.

Every audit regression asserts the correct behavior, not the presence of a bug. Known defects owned by later packets use strict expected-failure markers and are listed as OPEN/red. An unexpected pass fails triage; a generic exception or unrelated timeout is not a valid known failure. Preserve the exact sequence and independent expected outcome. Use barriers, not lucky timing, for concurrent preimages. Test mocks are labelled in reports.

For tests of held functions, bypass only the in-process hold under the isolated test harness; never add an application runtime bypass. Demonstrate the default hold separately before bypassing. No monkeypatch of the function under test or its result. Storage stubs/parser output are permitted only as explicitly limited test inputs and do not certify real storage/parser integration.

Evidence includes run UUID, UTC time, code/source hashes, test node IDs, passed/failed/xfailed/skipped counts, mock inventory and before/after namespace checks. No secret values, full HTTP auth bodies, cookies, phone numbers, answer payloads, private source content or .env dumps in artifacts. Reproducing A01–A06 does not close them.

## Independent small golden ledger

`golden_practice_v1.json` defines a deliberately tiny custom-practice fixture with hand-calculated expected marks, not official JEE/BITSAT exam certification. The oracle never calls the scorer to create expected values. A real-function test passes inputs to the scorer and compares exact output fractions/summary. Full four-adapter golden matrices remain P06 work.
