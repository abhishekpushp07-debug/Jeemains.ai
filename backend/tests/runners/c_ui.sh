#!/bin/bash
# TEST-ONLY: one fresh bridge, the browser walk on it, then the bridge is stopped (it drops only its own disposable test DB).
cd /app/backend || exit 1
rm -rf /tmp/uibridge234; mkdir -p /tmp/uibridge234
setsid nohup python tests/delete_bridge234.py 3000 > /root/p2/bridge234.log 2>&1 < /dev/null &
for i in $(seq 1 150); do grep -q "^READY" /root/p2/bridge234.log && break; sleep 1; done
python tests/ui_delete234.py desk mob fix > /root/p2/ui234.log 2>&1
echo "UI exit $?" >> /root/p2/ui234.log
pkill -INT -f "tests/delete_bridge234.py"
for i in $(seq 1 60); do pgrep -f "tests/delete_bridge234.py" > /dev/null || break; sleep 1; done
echo "UIDONE $(date -u +%T) bridge alive: $(pgrep -f tests/delete_bridge234.py > /dev/null && echo yes || echo no)" >> /root/p2/ui234.log
