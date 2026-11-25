#!/bin/bash
# TEST-ONLY packet D regression: the older storage suites, strictly one at a time (each drops only its own disposable test DB).
cd /app/backend || exit 1
OUT=/root/p2/d_regress.log
: > "$OUT"
for t in "$@"; do
  echo "=== $t $(date -u +%T)" >> "$OUT"
  timeout 420 python "tests/$t.py" > "/root/p2/d_reg_$t.log" 2>&1
  echo "exit $? :: $(grep -E '^TOTAL' "/root/p2/d_reg_$t.log" | tail -n 1)" >> "$OUT"
  grep -E '^FAIL' "/root/p2/d_reg_$t.log" | cut -c1-600 >> "$OUT"
done
echo "REGDONE $(date -u +%T)" >> "$OUT"
