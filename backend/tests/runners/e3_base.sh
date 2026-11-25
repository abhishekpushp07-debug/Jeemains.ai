#!/bin/bash
# TEST-ONLY: the two old suites that failed after Packet E step 3, run on a copy of the last commit (the code BEFORE step 3). One at a time.
OUT=/root/p2/e3_base.log
: > "$OUT"
cd /tmp/base_e3/backend || exit 1
for t in book_publishing_rules_iso170 book_scale_iso171; do
  echo "=== BASE $t $(date -u +%T)" >> "$OUT"
  timeout 420 python "tests/$t.py" > "/root/p2/base3_$t.log" 2>&1
  echo "exit $? :: $(grep -E '^TOTAL' "/root/p2/base3_$t.log" | tail -n 1)" >> "$OUT"
  grep -E '^FAIL' "/root/p2/base3_$t.log" | cut -c1-260 >> "$OUT"
done
echo "BASEDONE $(date -u +%T)" >> "$OUT"
