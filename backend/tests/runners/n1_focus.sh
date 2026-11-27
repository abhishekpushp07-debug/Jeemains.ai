#!/bin/bash
# TEST-ONLY: the two focused suites of packet N1, one after the other (about 15 seconds).
# Each suite makes and drops only its own disposable tejas_isolated_* database; the app's own database is never touched.
# Use: cd /app/backend && bash /root/p2/solo.sh bash tests/runners/n1_focus.sh   -> /root/p2/n1_focus.log
cd /app/backend || exit 1
LOG=/root/p2/n1_focus.log; : > "$LOG"
for t in one_account259 catalogue262; do
  echo "=== $t $(date -u +%T)" >> "$LOG"
  timeout 600 python -u "tests/$t.py" > "/root/p2/n1_$t.log" 2>&1
  echo "exit $? :: $(grep -E '^TOTAL [0-9]' "/root/p2/n1_$t.log" | tail -n 1)" >> "$LOG"
  grep -E '^FAIL' "/root/p2/n1_$t.log" | cut -c1-700 >> "$LOG"
done
echo "FOCUSDONE $(date -u +%T)" >> "$LOG"
cat "$LOG"
