#!/bin/bash
# TEST-ONLY pocket C1a: one fresh bridge, the browser walk on it, then the bridge is stopped (it drops only its own disposable test DB).
cd /app/backend || exit 1
rm -rf /tmp/uibridge255; mkdir -p /tmp/uibridge255
: > /root/p2/ui255.log
setsid nohup python tests/links_bridge255.py 1200 > /root/p2/bridge255.log 2>&1 < /dev/null &
for i in $(seq 1 300); do grep -q "^READY" /root/p2/bridge255.log && break; pgrep -f "tests/links_bridge255.py" > /dev/null || break; sleep 1; done
if grep -q "^READY" /root/p2/bridge255.log; then
  python tests/ui_links255.py desk mob > /root/p2/ui255.log 2>&1
  echo "UI exit $?" >> /root/p2/ui255.log
else
  echo "BRIDGE NOT READY" > /root/p2/ui255.log
fi
pkill -INT -f "tests/links_bridge255.py"
for i in $(seq 1 60); do pgrep -f "tests/links_bridge255.py" > /dev/null || break; sleep 1; done
echo "UIDONE $(date -u +%T) bridge alive: $(pgrep -f tests/links_bridge255.py > /dev/null && echo yes || echo no)" >> /root/p2/ui255.log
