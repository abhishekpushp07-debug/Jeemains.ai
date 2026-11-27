#!/bin/bash
# TEST-ONLY pocket S1b ("Line hatao": the printed address painted out of pictures saved earlier; picture links get a new address after it):
# the new suite, the S1/R1 suites, the owner's two real AITS books and his chapter-wise Chemistry book through the real app, the
# page-reader suites, then every older suite that touches the changed code. Strictly one after another (each drops only its own disposable test DB).
cd /app/backend || exit 1
LOG=/root/p2/r2_chain.log
: > "$LOG"
one() {  # one <name in the log> <timeout> <command...>
  name=$1; limit=$2; shift 2
  echo "=== $name $(date -u +%T)" >> "$LOG"
  timeout "$limit" "$@" > "/root/p2/r2_$name.log" 2>&1
  echo "exit $? :: $(grep -E '^TOTAL [0-9]|[0-9]+/[0-9]+ passed|passed$|^RESULT|^OK|^ALL ' "/root/p2/r2_$name.log" | tail -n 1)" >> "$LOG"
  grep -E '^FAIL' "/root/p2/r2_$name.log" | sort -u | cut -c1-700 >> "$LOG"
}
one source_repaint250 1500 python -u tests/source_repaint250.py
one hidden_picture249 300 python -u tests/hidden_picture249.py
one source_hidden248 420 python -u tests/source_hidden248.py
one aits_real247_a 3300 python -u tests/aits_real247.py /root/pdfengine/aits/a.pdf a
one aits_real247_b 3300 python -u tests/aits_real247.py /root/pdfengine/aits/b.pdf b
one book_speed211_both 3300 python -u tests/book_speed211.py both
one source_repaint_full251 3500 python -u tests/source_repaint_full251.py
one cut_cases210 900 python -u tests/cut_cases210.py /root/aitsv_out/cut210
one reader_v7_edges213 300 python -u tests/reader_v7_edges213.py
one book_reader_regressions178 300 python -u tests/book_reader_regressions178.py
one key_table_split190 300 python -u tests/key_table_split190.py
one png_small218_5 900 python -u tests/png_small218.py 5
bash /root/p2/r2_regress.sh media_cdn_iso198 media_four_qa216 media_warm_iso217 pictures_iso220 storage_move225 storage_move_fix226 storage_wait224 get_ready_iso188 get_ready_iso189 publish_progress_iso217 publish_fail_iso211 reread_iso179 picture_hold245 picture_hold_edge246 written_live244 master_iso181 master_jee_series_iso181 series_dates_iso187 library_aits_iso180 picture_aits241 picture_gate239 picture_gate_edge240 picture_late242 picture_late_edge243 picture_proof238 storage_badge236 upload_delete234 upload_delete_edge235 storage_stuck231 storage_stuck_edge232 structure_iso173 structure_imports_iso174 section_preview_iso175 phase1_iso221 step_guard233 fresh_start_iso183 storage_book229 chapters_iso182 typed_delete_iso185 book_publishing_iso170 book_publishing_rules_iso170 book_scale_iso171
echo "CHAINDONE $(date -u +%T)" >> "$LOG"
