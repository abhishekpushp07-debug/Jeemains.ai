#!/bin/bash
# TEST-ONLY Student Choice chain, strictly one at a time: the backend suite, the QA-cleanup suite, then the browser walk.
cd /app/backend || exit 1
OUT=/root/p2/choice_chain.log
: > "$OUT"
for t in choice_iso229 choice_adversarial_t1_232 db_audit_iso194; do
  echo "=== $t $(date -u +%T)" >> "$OUT"
  timeout 420 python -u "tests/$t.py" > "/root/p2/choice_$t.log" 2>&1
  echo "exit $? :: $(grep -E '^TOTAL [0-9]' "/root/p2/choice_$t.log" | tail -n 1)" >> "$OUT"
  grep -E '^FAIL' "/root/p2/choice_$t.log" | cut -c1-600 >> "$OUT"
done
bash /root/p2/choice_ui.sh desk mob
echo "=== ui :: $(grep -E '^TOTAL' /root/p2/ui229.log | tail -n 1)" >> "$OUT"
grep -E '^FAIL' /root/p2/ui229.log | cut -c1-600 >> "$OUT"
echo "CHAINDONE $(date -u +%T)" >> "$OUT"
