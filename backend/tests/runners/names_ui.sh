#!/bin/bash
# TEST-ONLY pocket C1b: one fresh bridge, the owner's switch and the student's analysis walked on it, then the bridge is stopped
# (it drops only its own disposable test DB).
cd /app/backend || exit 1
rm -rf /tmp/uibridge257; mkdir -p /tmp/uibridge257
: > /root/p2/ui257.log
setsid nohup python tests/names_bridge257.py 1200 > /root/p2/bridge257.log 2>&1 < /dev/null &
for i in $(seq 1 600); do grep -q "^READY" /root/p2/bridge257.log && break; pgrep -f "tests/names_bridge257.py" > /dev/null || break; sleep 1; done
if grep -q "^READY" /root/p2/bridge257.log; then
  python tests/ui_names257.py desk mob > /root/p2/ui257.log 2>&1
  echo "UI exit $?" >> /root/p2/ui257.log
else
  echo "BRIDGE NOT READY" > /root/p2/ui257.log
fi
pkill -INT -f "tests/names_bridge257.py"
for i in $(seq 1 60); do pgrep -f "tests/names_bridge257.py" > /dev/null || break; sleep 1; done
echo "UIDONE $(date -u +%T) bridge alive: $(pgrep -f tests/names_bridge257.py > /dev/null && echo yes || echo no)" >> /root/p2/ui257.log
