#!/bin/bash
# TEST-ONLY pocket S1b: one fresh bridge, the browser walk on it, then the bridge is stopped (it drops only its own disposable test DB).
cd /app/backend || exit 1
rm -rf /tmp/uibridge250; mkdir -p /tmp/uibridge250
setsid nohup python tests/repaint_bridge250.py 1200 > /root/p2/bridge250.log 2>&1 < /dev/null &
for i in $(seq 1 240); do grep -q "^READY" /root/p2/bridge250.log && break; pgrep -f "tests/repaint_bridge250.py" > /dev/null || break; sleep 1; done
if grep -q "^READY" /root/p2/bridge250.log; then
  python tests/ui_repaint250.py desk mob > /root/p2/ui250.log 2>&1
  echo "UI exit $?" >> /root/p2/ui250.log
else
  echo "BRIDGE NOT READY" > /root/p2/ui250.log
fi
pkill -INT -f "tests/repaint_bridge250.py"
for i in $(seq 1 60); do pgrep -f "tests/repaint_bridge250.py" > /dev/null || break; sleep 1; done
echo "UIDONE $(date -u +%T) bridge alive: $(pgrep -f tests/repaint_bridge250.py > /dev/null && echo yes || echo no)" >> /root/p2/ui250.log
