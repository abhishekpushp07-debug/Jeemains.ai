#!/bin/bash
# Run fault injection tests individually to avoid Motor event loop issues
# Each test uses its own event loop to avoid Motor different loops problem

echo "Running V5 Fault Injection Tests..."
echo "===================================="
echo ""

cd /app/backend

echo "Test 1: Crash between close and enqueue"
python -m pytest tests/test_v5_faults.py::test_crash_between_close_and_enqueue -v -s
TEST1=$?

echo ""
echo "Test 2: Poison job retry"
python -m pytest tests/test_v5_faults.py::test_poison_job_retry -v -s
TEST2=$?

echo ""
echo "Test 3: Done report job lease protection"
python -m pytest tests/test_v5_faults.py::test_done_report_job_lease_protection -v -s
TEST3=$?

echo ""
echo "Test 4: Replay protection"
python -m pytest tests/test_v5_faults.py::test_replay_protection -v -s
TEST4=$?

echo ""
echo "===================================="
echo "Test Results Summary:"
echo "===================================="
echo "Test 1 (Crash between close and enqueue): $([ $TEST1 -eq 0 ] && echo 'PASSED' || echo 'FAILED')"
echo "Test 2 (Poison job retry): $([ $TEST2 -eq 0 ] && echo 'PASSED' || echo 'FAILED')"
echo "Test 3 (Done report job lease protection): $([ $TEST3 -eq 0 ] && echo 'PASSED' || echo 'FAILED')"
echo "Test 4 (Replay protection): $([ $TEST4 -eq 0 ] && echo 'PASSED' || echo 'FAILED')"
echo ""

# Exit with failure if any test failed
if [ $TEST1 -ne 0 ] || [ $TEST2 -ne 0 ] || [ $TEST3 -ne 0 ] || [ $TEST4 -ne 0 ]; then
    echo "Some tests failed"
    exit 1
else
    echo "All tests passed!"
    exit 0
fi
