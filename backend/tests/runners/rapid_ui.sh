#!/bin/bash
# TEST-ONLY iteration 260: one fresh bridge (a signed-in student in a disposable DB), the website's Rapid Fire marks walked on it
# (desk + 390 px), then the bridge is stopped (it drops only its own disposable test DB).
# Use: cd /app/backend && bash /root/p2/solo.sh bash /root/p2/rapid_ui.sh
cd /app/backend || exit 1
export BRIDGE_OUT=/tmp/uibridge260 BRIDGE_PORT=8783
rm -rf "$BRIDGE_OUT"; mkdir -p "$BRIDGE_OUT"
: > /root/p2/ui260.log
setsid nohup python tests/analysis_bridge196.py 900 > /root/p2/bridge260.log 2>&1 < /dev/null &
for i in $(seq 1 420); do grep -q "^READY" /root/p2/bridge260.log && break; pgrep -f "tests/analysis_bridge196.py" > /dev/null || break; sleep 1; done
if grep -q "^READY" /root/p2/bridge260.log; then
  python tests/ui_rapid260.py desk mob > /root/p2/ui260.log 2>&1
  echo "UI exit $?" >> /root/p2/ui260.log
else
  echo "BRIDGE NOT READY" > /root/p2/ui260.log
fi
pkill -INT -f "tests/analysis_bridge196.py"
for i in $(seq 1 60); do pgrep -f "tests/analysis_bridge196.py" > /dev/null || break; sleep 1; done
echo "UIDONE $(date -u +%T) bridge alive: $(pgrep -f tests/analysis_bridge196.py > /dev/null && echo yes || echo no)" >> /root/p2/ui260.log
