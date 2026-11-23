#!/bin/bash
# Regression gate: runs the isolated suites one after another (never in parallel) and prints one line per suite.
# Usage: bash tests/gate219.sh <label> [suite ...]
cd /app/backend
label=${1:-run}; shift
suites=("$@")
[ ${#suites[@]} -eq 0 ] && suites=(wrong_pin_iso197 forgot_pin_iso184 override_guard_iso192 typed_delete_iso185 master_iso181 structure_iso173 library_aits_iso180 fresh_start_iso183 chapters_iso182 reread_iso179 storage_fail215 storage_dual216 png_small218 cut_cases210 book_reader_regressions178 key_table_split190)
out=/tmp/gate/$label; mkdir -p $out; : > $out/summary.txt
for s in "${suites[@]}"; do
  [ -f tests/$s.py ] || { echo "$s MISSING" >> $out/summary.txt; continue; }
  start=$(date +%s)
  timeout 900 python tests/$s.py > $out/$s.log 2>&1; code=$?
  line=$(grep -E "[0-9]+/[0-9]+ passed|RESULT|passed" $out/$s.log | tail -1)
  fails=$(grep -c "^FAIL" $out/$s.log)
  echo "$s exit=$code fails=$fails $(( $(date +%s)-start ))s :: $line" >> $out/summary.txt
done
echo DONE >> $out/summary.txt
