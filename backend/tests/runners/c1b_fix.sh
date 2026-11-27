#!/bin/bash
# TEST-ONLY pocket C1b, after the switch learned to write nothing for a press that changes nothing. Start it ONLY as:
#   bash /root/p2/solo.sh bash /root/p2/c1b_fix.sh
# One suite or bridge at a time, each in its own disposable test database (each drops only its own).
cd /app/backend || exit 1
LOG=/root/p2/c1b_fix.log
: > "$LOG"
one() {
  name=$1; secs=$2; shift 2
  echo "=== $name $(date -u +%T)" >> "$LOG"
  timeout "$secs" "$@" > "/root/p2/c1b_fix_$name.log" 2>&1
  echo "exit $? :: $(grep -E '^TOTAL [0-9]|[0-9]+/[0-9]+ passed' "/root/p2/c1b_fix_$name.log" | tail -n 1)" >> "$LOG"
  grep -E '^FAIL' "/root/p2/c1b_fix_$name.log" | cut -c1-900 >> "$LOG"
}
walk() {
  name=$1; runner=$2; log=$3
  echo "=== $name $(date -u +%T)" >> "$LOG"
  bash "$runner"
  echo "exit :: $(grep -E '^TOTAL' "$log" | tail -n 1)" >> "$LOG"
  grep -E '^FAIL|BRIDGE NOT READY' "$log" | cut -c1-600 >> "$LOG"
}
for s in "$@"; do
  case "$s" in
    ui_links255) walk ui_links255 /root/p2/links_ui.sh /root/p2/ui255.log ;;
    ui_names257) walk ui_names257 /root/p2/names_ui.sh /root/p2/ui257.log ;;
    *) one "$s" 1500 python -u "tests/$s.py" ;;
  esac
done
echo "FIXDONE $(date -u +%T)" >> "$LOG"
