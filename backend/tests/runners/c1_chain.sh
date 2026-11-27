#!/bin/bash
# TEST-ONLY pocket C1a ("Jod") + the S1b full-size run again: strictly one suite at a time, and only after the S1b chain has ended.
# Each suite drops only its own disposable test database.
cd /app/backend || exit 1
LOG=/root/p2/c1_chain.log
: > "$LOG"
while ! grep -q "^CHAINDONE" /root/p2/r2_chain.log; do pgrep -f "r2_chain.sh" > /dev/null || break; sleep 5; done
one() {
  name=$1; secs=$2; shift 2
  echo "=== $name $(date -u +%T)" >> "$LOG"
  timeout "$secs" "$@" > "/root/p2/c1_$name.log" 2>&1
  echo "exit $? :: $(grep -E '^TOTAL [0-9]' "/root/p2/c1_$name.log" | tail -n 1)" >> "$LOG"
  grep -E '^FAIL' "/root/p2/c1_$name.log" | cut -c1-700 >> "$LOG"
}
for t in "$@"; do
  case "$t" in
    iso254) one question_records_iso254 1500 python -u tests/question_records_iso254.py ;;
    full251) one source_repaint_full251 5400 python -u tests/source_repaint_full251.py ;;
    aits_a) one aits_real247_a 3300 python -u tests/aits_real247.py /root/pdfengine/aits/a.pdf a ;;
    build253) one question_records_build253 900 python -u tests/question_records_build253.py ;;
    unit252) one question_link_unit252 900 python -u tests/question_link_unit252.py ;;
  esac
done
echo "CHAINDONE $(date -u +%T)" >> "$LOG"
