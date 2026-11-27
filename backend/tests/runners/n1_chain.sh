#!/bin/bash
# TEST-ONLY 27 Nov 2026, after three small additions for the app (display_name always in a student's answer; per_page on the catalogue;
# the app server's Cut off doors let through /api/rank): the two focused suites, the two older PIN suites, then the 54 older suites once
# more, strictly one at a time (the list is the one of /root/p2/c1_regress.log). Each suite drops only its own disposable test DB.
# Use: cd /app/backend && bash /root/p2/solo.sh bash /app/backend/tests/runners/n1_chain.sh
cd /app/backend || exit 1
LOG=/root/p2/n1_chain.log; : > "$LOG"
for t in one_account259 catalogue262; do
  echo "=== $t $(date -u +%T)" >> "$LOG"
  timeout 600 python -u "tests/$t.py" > "/root/p2/n1_$t.log" 2>&1
  echo "exit $? :: $(grep -E '^TOTAL [0-9]' "/root/p2/n1_$t.log" | tail -n 1)" >> "$LOG"
  grep -E '^FAIL' "/root/p2/n1_$t.log" | cut -c1-700 >> "$LOG"
done
for t in test_iter154_pin_auth_isolated test_iter155_pin_retest_isolated; do
  echo "=== $t $(date -u +%T)" >> "$LOG"
  (cd tests && timeout 900 python -m pytest "$t.py" -p no:cacheprovider -q > "/root/p2/n1_$t.log" 2>&1)
  echo "exit $? :: $(tail -n 1 "/root/p2/n1_$t.log")" >> "$LOG"
  grep -E '^(FAILED|ERROR)' "/root/p2/n1_$t.log" | cut -c1-400 >> "$LOG"
done
echo "FOCUSDONE $(date -u +%T)" >> "$LOG"
OUT=/root/p2/n1_regress.log; : > "$OUT"
for t in $(grep -o "^=== [^ ]*" /root/p2/c1_regress.log | cut -d' ' -f2); do
  echo "=== $t $(date -u +%T)" >> "$OUT"
  timeout 420 python "tests/$t.py" > "/root/p2/n1_reg_$t.log" 2>&1
  echo "exit $? :: $(grep -E '^TOTAL [0-9]|[0-9]+/[0-9]+ passed|passed$|^RESULT|^OK|^ALL ' "/root/p2/n1_reg_$t.log" | tail -n 1)" >> "$OUT"
  grep -E '^FAIL' "/root/p2/n1_reg_$t.log" | cut -c1-600 >> "$OUT"
done
echo "REGDONE $(date -u +%T)" >> "$OUT"
