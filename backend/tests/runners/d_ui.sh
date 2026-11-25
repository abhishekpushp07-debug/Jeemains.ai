#!/bin/bash
# TEST-ONLY packet D: one fresh bridge, the browser walk on it, then the bridge is stopped (it drops only its own disposable test DB).
cd /app/backend || exit 1
rm -rf /tmp/uibridge236; mkdir -p /tmp/uibridge236
setsid nohup python tests/badge_bridge236.py 3000 > /root/p2/bridge236.log 2>&1 < /dev/null &
for i in $(seq 1 150); do grep -q "^READY" /root/p2/bridge236.log && break; sleep 1; done
python tests/ui_badge236.py desk mob fix > /root/p2/ui236.log 2>&1
echo "UI exit $?" >> /root/p2/ui236.log
pkill -INT -f "tests/badge_bridge236.py"
for i in $(seq 1 60); do pgrep -f "tests/badge_bridge236.py" > /dev/null || break; sleep 1; done
echo "UIDONE $(date -u +%T) bridge alive: $(pgrep -f tests/badge_bridge236.py > /dev/null && echo yes || echo no)" >> /root/p2/ui236.log
