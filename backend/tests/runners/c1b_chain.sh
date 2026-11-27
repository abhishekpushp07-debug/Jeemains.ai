#!/bin/bash
# TEST-ONLY pocket C1b (chapter names in the AITS analysis). Start it ONLY as: bash /root/p2/solo.sh bash /root/p2/c1b_chain.sh [extra suites]
# (solo.sh holds the one-at-a-time lock). Strictly one suite or bridge at a time; then the older suites once more (c1_after.sh).
# Each suite or bridge drops only its own disposable test database. Never stop this shell while a suite is running: stop the suite (INT) first.
cd /app/backend || exit 1
LOG=/root/p2/c1b_chain.log
: > "$LOG"
one() {
  name=$1; secs=$2; shift 2
  echo "=== $name $(date -u +%T)" >> "$LOG"
  timeout "$secs" "$@" > "/root/p2/c1b_$name.log" 2>&1
  echo "exit $? :: $(grep -E '^TOTAL [0-9]|[0-9]+/[0-9]+ passed' "/root/p2/c1b_$name.log" | tail -n 1)" >> "$LOG"
  grep -E '^FAIL' "/root/p2/c1b_$name.log" | cut -c1-700 >> "$LOG"
}
walk() {
  name=$1; runner=$2; log=$3
  echo "=== $name $(date -u +%T)" >> "$LOG"
  bash "$runner"
  echo "exit :: $(grep -E '^TOTAL' "$log" | tail -n 1)" >> "$LOG"
  grep -E '^FAIL|BRIDGE NOT READY' "$log" | cut -c1-600 >> "$LOG"
}
one question_names256 1500 python -u tests/question_names256.py
walk ui_links255 /root/p2/links_ui.sh /root/p2/ui255.log
walk ui_names257 /root/p2/names_ui.sh /root/p2/ui257.log
echo "CHAINDONE $(date -u +%T)" >> "$LOG"
bash /root/p2/c1_after.sh "$@"
