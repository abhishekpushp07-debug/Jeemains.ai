#!/bin/bash
# TEST-ONLY pocket C1a: the older suites once more after C1a, strictly one at a time, and only after the C1a chain has ended.
# The list is the one the S1b re-run used (/root/p2/r2_chain.sh), plus any names given here. Each suite drops only its own disposable test DB.
cd /app/backend || exit 1
while ! grep -q "^CHAINDONE" /root/p2/c1_chain.log; do pgrep -f "c1_chain.sh" > /dev/null || break; sleep 5; done
OUT=/root/p2/c1_regress.log
: > "$OUT"
for t in $(grep -o "r2_regress.sh .*" /root/p2/r2_chain.sh | cut -d' ' -f2-) "$@"; do
  echo "=== $t $(date -u +%T)" >> "$OUT"
  timeout 420 python "tests/$t.py" > "/root/p2/c1_reg_$t.log" 2>&1
  echo "exit $? :: $(grep -E '^TOTAL [0-9]|[0-9]+/[0-9]+ passed|passed$|^RESULT|^OK|^ALL ' "/root/p2/c1_reg_$t.log" | tail -n 1)" >> "$OUT"
  grep -E '^FAIL' "/root/p2/c1_reg_$t.log" | cut -c1-600 >> "$OUT"
done
echo "REGDONE $(date -u +%T)" >> "$OUT"
