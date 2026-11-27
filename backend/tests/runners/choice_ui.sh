#!/bin/bash
# TEST-ONLY Student Choice: one fresh bridge, the browser walk on it, then the bridge is stopped (it drops only its own disposable test DB).
cd /app/backend || exit 1
rm -rf /tmp/uibridge229; mkdir -p /tmp/uibridge229
: > /root/p2/ui229.log
setsid nohup python tests/choice_bridge229.py 1200 > /root/p2/bridge229.log 2>&1 < /dev/null &
for i in $(seq 1 300); do grep -q "^READY" /root/p2/bridge229.log && break; pgrep -f "tests/choice_bridge229.py" > /dev/null || break; sleep 1; done
if grep -q "^READY" /root/p2/bridge229.log; then
  python tests/ui_choice229.py "$@" > /root/p2/ui229.log 2>&1
  echo "UI exit $?" >> /root/p2/ui229.log
else
  echo "BRIDGE NOT READY" > /root/p2/ui229.log
fi
pkill -INT -f "tests/choice_bridge229.py"
for i in $(seq 1 60); do pgrep -f "tests/choice_bridge229.py" > /dev/null || break; sleep 1; done
echo "UIDONE $(date -u +%T) bridge alive: $(pgrep -f tests/choice_bridge229.py > /dev/null && echo yes || echo no)" >> /root/p2/ui229.log
