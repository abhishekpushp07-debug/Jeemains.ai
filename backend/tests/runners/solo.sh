#!/bin/bash
# TEST-ONLY: ONE isolated suite, bridge or chain at a time. Refuses to start while another holds the lock or any suite is still alive.
# The lock is inherited by everything this starts, so it stays held until the last child has ended (even if this shell is stopped).
# Use: bash /root/p2/solo.sh python -u tests/X.py     or     bash /root/p2/solo.sh bash /root/p2/<chain>.sh ...
exec 9> /root/p2/suite.lock
flock -n 9 || { echo "REFUSED $(date -u +%T): another suite or chain holds /root/p2/suite.lock"; exit 75; }
# Only a process that IS python running a test (its command line starts with python): never this shell, whose own line also names the test.
if pgrep -f "^([^ ]*/)?python[0-9.]*( -u)? tests/" > /dev/null; then echo "REFUSED $(date -u +%T): a suite is still running"; exit 75; fi
# The preview mongod starts with 1024 open files and aborts above that; a chain of suites passes it. Raised here for the running process only.
prlimit --pid "$(pgrep -x mongod | head -n1)" --nofile=65536:1048576 2>/dev/null || echo "WARNING: mongod open-file limit not raised"
cd /app/backend || exit 1
"$@"
