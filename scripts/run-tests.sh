#!/bin/bash
# Test Runner Script

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_DIR="$PROJECT_DIR/scripts"
API_TEST_DIR="$PROJECT_DIR/tests/api"

echo "=========================================="
echo "Taurus Load Testing Suite"
echo "=========================================="
echo "Project: $PROJECT_DIR"
echo ""

# Start mock server
echo "Starting mock API server..."
python "$SCRIPT_DIR/mock-api-server.py" &
SERVER_PID=$!
sleep 2

# Run tests
TEST_FILES=($(ls "$API_TEST_DIR"/test-api-*.yml | sort))
echo "Found ${#TEST_FILES[@]} tests"
echo ""

PASSED=0
FAILED=0

for test_file in "${TEST_FILES[@]}"; do
    test_name=$(basename "$test_file" .yml)
    
    echo "────────────────────────────────────────"
    echo "Running: $test_name"
    echo "────────────────────────────────────────"
    
    if bzt "$test_file"; then
        echo "✓ PASSED: $test_name"
        ((PASSED++))
    else
        echo "✗ FAILED: $test_name"
        ((FAILED++))
    fi
    echo ""
done

# Stop server
echo "Stopping mock API server..."
kill $SERVER_PID 2>/dev/null

# Summary
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo "Total Tests: ${#TEST_FILES[@]}"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo "=========================================="

exit $FAILED
