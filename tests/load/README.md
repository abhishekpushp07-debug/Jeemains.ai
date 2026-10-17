# Safe catalogue smoke and metadata measurement

Run from repository root:

```
python tests/load/catalog_smoke.py
python tests/load/bson_bytes_benchmark.py
```

The HTTP script reads REACT_APP_BACKEND_URL from frontend/.env. Optional MAX_REQUESTS (1..100), MAX_WORKERS (1..4), MAX_RPS (finite1..5). Uses only declared public catalogue GET endpoints. No login or data creation; do not extend it into shared-preview load generation. Outputs raw samples and summary in test_reports/capacity_catalog_smoke.json, returns failure for incomplete run or any failed request.

BSON script reads backend environment privately, reads at most100 live published non-QA chapter records and the matching metadata projection. It writes only a local metrics report. It never modifies database content. Compare document counts before accepting measurements;94ownerchapters were present at this release.

These scripts do **not** qualify concurrent students, answer-write durability or500kcapacity. The full campaign still needs dedicated representative infrastructure and stateful generators.

Test-data writes belong only in tests/packet1 under its guarded ephemeral database fixtures. Never import and call fixture helpers manually against backend/.env's application database.
