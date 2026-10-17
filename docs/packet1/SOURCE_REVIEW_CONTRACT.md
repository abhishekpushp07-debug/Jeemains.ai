# Source review ledger contract

`source_review.py` makes coverage claims mechanically checkable, not automatically true. The current ledger contains an agent review of PDF-05 pages 3 and 55: 38 exactly partitioned blocks and 65 hash-bound obligations. The other 3,261 blocks remain unreviewed. No work is labelled done merely by running the extractor.

## Review operation

For each original text block, record its exact source hash and an ordered, gap-free partition of Unicode codepoint offsets (end exclusive). Each partition has a fragment SHA-256 and one disposition:

- requirement: references a unique atomic obligation with owner role, repair packet, contract boundaries and acceptance cases
- context/layout: no requirement binding, with explicit rationale

Every character must be accounted for, including whitespace. Unknown, duplicated, overlapping, stale-hash, unowned or evidence-mismatched records fail validation. No original source snippets, credential examples or live secrets are emitted. Evidence must be an existing hash-matching regular file under allowed repository roots; traversal, secret/config files and symlinks are rejected.

Independent semantic review must still determine that compound obligations were split correctly and normative content was not misclassified as context. The validator cannot infer that from offsets. Therefore even complete mechanical coverage does **not** set `semantic_completeness_proven`, `operator_approval_present` or Packet 1 exit to true. Evidence-file existence is traceability, not proof of a successful test or a signature.

Current source: 177 pages / 3299 blocks. The 45 earlier selected obligations and 60 analysis names remain a useful reviewed subset, but they have not been falsely converted into exact-span reviews.

Run from any directory:

`python /app/docs/packet1/source_review.py docs/packet1/review_ledger.v1.json`

Persist the JSON output under `/app/docs/packet1/evidence/`; never rely on `/tmp` for handoff. No database, production content, role or credential is changed by validation.
