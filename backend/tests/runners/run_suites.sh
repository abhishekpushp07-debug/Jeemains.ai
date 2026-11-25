#!/bin/bash
# TEST-ONLY: runs the named isolated suites ONE AT A TIME (never side by side) and writes one line per suite.
# Usage: bash /root/p2/run_suites.sh <tag> suite1 suite2 ...   -> /root/p2/suites_<tag>.log (+ full output per suite in /root/p2/out_<suite>.log)
cd /app/backend || exit 1
tag=$1; shift
log=/root/p2/suites_$tag.log
: > "$log"
for s in "$@"; do
  start=$(date +%s)
  timeout 900 python -u tests/$s.py > /root/p2/out_$s.log 2>&1
  code=$?
  line=$(grep -E "^TOTAL |passed$|[0-9]+/[0-9]+ passed|^RESULT" /root/p2/out_$s.log | tail -1)
  fails=$(grep -c "^FAIL " /root/p2/out_$s.log)
  echo "$s exit=$code secs=$(( $(date +%s) - start )) fail_lines=$fails :: $line" >> "$log"
done
P=$(pgrep -f "mongod --bind_ip_all" | head -1)
echo "ALLDONE $(date -u +%T) mongod=$P handles=$(ls /proc/$P/fd | wc -l)" >> "$log"
