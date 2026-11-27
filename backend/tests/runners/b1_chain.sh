#!/bin/bash
# TEST-ONLY 27 Nov 2026, packet B1 (PYQ pictures from the kept copy when storage fails; an empty picture part answers 503):
# the two new suites, then the 54 older suites once more, strictly one at a time (the list of /root/p2/c1_regress.log).
# Each suite drops only its own disposable test DB. Use: cd /app/backend && bash tests/runners/solo.sh bash tests/runners/b1_chain.sh
cd /app/backend || exit 1
LOG=/root/p2/b1_chain.log; : > "$LOG"
for t in pyq_pictures_real263 pyq_pictures263; do
  echo "=== $t $(date -u +%T)" >> "$LOG"
  timeout 600 python -u "tests/$t.py" > "/root/p2/b1_$t.log" 2>&1
  echo "exit $? :: $(grep -E '^TOTAL [0-9]' "/root/p2/b1_$t.log" | tail -n 1)" >> "$LOG"
  grep -E '^FAIL' "/root/p2/b1_$t.log" | cut -c1-700 >> "$LOG"
done
echo "FOCUSDONE $(date -u +%T)" >> "$LOG"
OUT=/root/p2/b1_regress.log; : > "$OUT"
for t in $(grep -o "^=== [^ ]*" /root/p2/c1_regress.log | cut -d' ' -f2); do
  echo "=== $t $(date -u +%T)" >> "$OUT"
  timeout 420 python "tests/$t.py" > "/root/p2/b1_reg_$t.log" 2>&1
  echo "exit $? :: $(grep -E '^TOTAL [0-9]|[0-9]+/[0-9]+ passed|passed$|^RESULT|^OK|^ALL ' "/root/p2/b1_reg_$t.log" | tail -n 1)" >> "$OUT"
  grep -E '^FAIL' "/root/p2/b1_reg_$t.log" | cut -c1-600 >> "$OUT"
done
echo "REGDONE $(date -u +%T)" >> "$OUT"
