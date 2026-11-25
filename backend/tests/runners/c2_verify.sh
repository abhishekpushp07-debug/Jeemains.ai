#!/bin/bash
# TEST-ONLY: after the review fixes (signs of life inside a long batch, AITS dustbin). Suites ONE AT A TIME, then one bridge + browser walk.
cd /app/backend || exit 1
bash /root/p2/run_suites.sh C2 step_guard233 upload_delete234 upload_delete_edge235 book_scale_iso171 phase1_iso221 storage_book229 storage_stuck231 storage_stuck_edge232 pictures_iso220 chapters_iso182 master_iso181 library_aits_iso180 series_dates_iso187 structure_imports_iso174
bash /root/p2/c_ui.sh
echo "C2DONE $(date -u +%T)" >> /root/p2/suites_C2.log
