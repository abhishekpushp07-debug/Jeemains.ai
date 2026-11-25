#!/bin/bash
# TEST-ONLY packet E step 2: one fresh bridge, the browser walk on it, then the bridge is stopped (it drops only its own disposable test DB).
cd /app/backend || exit 1
rm -rf /tmp/uibridge239; mkdir -p /tmp/uibridge239
: > /root/p2/ui239.log   # never leave the result of an older run to be read as this one
setsid nohup python tests/picture_bridge239.py 3000 > /root/p2/bridge239.log 2>&1 < /dev/null &
sleep 3
for i in $(seq 1 300); do grep -q "^READY" /root/p2/bridge239.log && break; pgrep -f "tests/picture_bridge239.py" > /dev/null || break; sleep 1; done
grep -q "^READY" /root/p2/bridge239.log || { echo "BRIDGE FAILED $(date -u +%T): see /root/p2/bridge239.log" >> /root/p2/ui239.log; pkill -INT -f "tests/picture_bridge239.py"; exit 1; }
python tests/ui_picture239.py desk mob fix > /root/p2/ui239.log 2>&1
echo "UI exit $?" >> /root/p2/ui239.log
pkill -INT -f "tests/picture_bridge239.py"
for i in $(seq 1 60); do pgrep -f "tests/picture_bridge239.py" > /dev/null || break; sleep 1; done
echo "UIDONE $(date -u +%T) bridge alive: $(pgrep -f tests/picture_bridge239.py > /dev/null && echo yes || echo no)" >> /root/p2/ui239.log
