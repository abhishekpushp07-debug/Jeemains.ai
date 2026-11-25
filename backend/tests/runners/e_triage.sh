#!/bin/bash
# TEST-ONLY: the four suites that failed after Packet E step 2, first on the code BEFORE Packet E (a copy of the last commit), then the two adapted suites on today's code. One at a time.
OUT=/root/p2/e_triage.log
: > "$OUT"
cd /tmp/base_e/backend || exit 1
for t in publish_fail_iso211 media_warm_iso217 get_ready_iso188 get_ready_iso189; do
  echo "=== BASE $t $(date -u +%T)" >> "$OUT"
  timeout 420 python "tests/$t.py" > "/root/p2/base_$t.log" 2>&1
  echo "exit $? :: $(grep -E '^TOTAL' "/root/p2/base_$t.log" | tail -n 1)" >> "$OUT"
  grep -E '^FAIL' "/root/p2/base_$t.log" | cut -c1-300 >> "$OUT"
done
cd /app/backend || exit 1
for t in storage_wait224 step_guard233; do
  echo "=== NOW $t $(date -u +%T)" >> "$OUT"
  timeout 420 python "tests/$t.py" > "/root/p2/now_$t.log" 2>&1
  echo "exit $? :: $(grep -E '^TOTAL' "/root/p2/now_$t.log" | tail -n 1)" >> "$OUT"
  grep -E '^FAIL' "/root/p2/now_$t.log" | cut -c1-300 >> "$OUT"
done
echo "TRIAGEDONE $(date -u +%T)" >> "$OUT"
