#!/bin/bash
# TEST-ONLY: ONE isolated suite, bridge or chain at a time. Refuses to start while another holds the lock or any suite is still alive.
# The lock is inherited by everything this starts, so it stays held until the last child has ended (even if this shell is stopped).
exec 9> /root/p2/suite.lock
flock -n 9 || { echo "REFUSED $(date -u +%T): another suite or chain holds /root/p2/suite.lock"; exit 75; }
if pgrep -f "python( -u)? tests/" > /dev/null; then echo "REFUSED $(date -u +%T): a suite is still running"; exit 75; fi
cd /app/backend || exit 1
"$@"
