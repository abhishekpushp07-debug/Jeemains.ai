#!/bin/bash
# TEST-ONLY: the Packet E browser walk on its bridge, then the suites that touch the changed code, strictly one after another.
bash /root/p2/e_ui.sh
bash /root/p2/d_regress.sh picture_gate239 picture_gate_edge240 picture_proof238 storage_stuck231 master_iso181 library_aits_iso180 series_dates_iso187 storage_badge236 step_guard233 storage_wait224 structure_iso173
echo "CHAINDONE $(date -u +%T)" >> /root/p2/e_chain.log
