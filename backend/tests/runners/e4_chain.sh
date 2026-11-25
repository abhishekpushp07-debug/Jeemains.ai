#!/bin/bash
# TEST-ONLY Packet E step 4 (written mocks): the browser walk on its bridge, then the new suite and every older suite that touches the changed code, strictly one after another.
bash /root/p2/e_ui.sh
bash /root/p2/d_regress.sh written_live244 master_iso181 master_jee_series_iso181 series_dates_iso187 library_aits_iso180 picture_aits241 picture_gate239 picture_gate_edge240 picture_late242 picture_late_edge243 picture_proof238 storage_badge236 storage_badge_edge237 upload_delete234 storage_stuck231 storage_stuck_edge232 structure_iso173 structure_imports_iso174 section_preview_iso175 phase1_iso221 storage_wait224 step_guard233 fresh_start_iso183 storage_book229
echo "CHAINDONE $(date -u +%T)" >> /root/p2/e4_chain.log
