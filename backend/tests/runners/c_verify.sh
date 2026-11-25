#!/bin/bash
# TEST-ONLY, packet C: every suite ONE AT A TIME, then (only after they end) one bridge and the browser walk on it, then the bridge is stopped.
cd /app/backend || exit 1
bash /root/p2/run_suites.sh C upload_delete234 storage_nocallback234 step_guard233 storage_stuck_edge232 storage_stuck231 phase1_iso221 storage_book229 storage_big229 storage_before229 storage_edge230 storage_dual216 storage_fail215 storage_wait224 storage_move225 storage_move_edge225 storage_move_fix226 pictures_iso220 structure_imports_iso174 master_iso181 chapters_iso182 structure_iso173 typed_delete_iso185 library_aits_iso180 series_dates_iso187 get_ready_iso188
rm -rf /tmp/uibridge234; mkdir -p /tmp/uibridge234
setsid nohup python tests/delete_bridge234.py 3000 > /root/p2/bridge234.log 2>&1 < /dev/null &
for i in $(seq 1 150); do grep -q "^READY" /root/p2/bridge234.log && break; sleep 1; done
grep "^READY" /root/p2/bridge234.log | cut -c1-300 > /root/p2/ui234.log
python tests/ui_delete234.py desk mob fix >> /root/p2/ui234.log 2>&1
echo "UI exit $?" >> /root/p2/ui234.log
echo "UIDONE $(date -u +%T)" >> /root/p2/ui234.log
