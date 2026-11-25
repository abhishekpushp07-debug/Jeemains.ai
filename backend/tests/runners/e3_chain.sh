#!/bin/bash
# TEST-ONLY Packet E step 3: the browser walk on its bridge, then every older suite that touches the changed code, strictly one after another.
bash /root/p2/e_ui.sh
bash /root/p2/d_regress.sh picture_gate239 picture_gate_edge240 picture_aits241 picture_proof238 storage_stuck231 storage_stuck_edge232 master_iso181 structure_iso173 structure_imports_iso174 section_preview_iso175 book_publishing_rules_iso170 book_scale_iso171 phase1_iso221 storage_wait224 step_guard233 library_aits_iso180 series_dates_iso187 fresh_start_iso183 storage_badge236 storage_book229
echo "CHAINDONE $(date -u +%T)" >> /root/p2/e3_chain.log
