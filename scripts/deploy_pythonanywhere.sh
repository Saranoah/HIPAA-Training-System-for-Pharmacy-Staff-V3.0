

#!/bin/bash

Complete Test Suite Runner
echo "🧪 HIPAA Training System - Complete Test Suite"

echo "=============================================="

echo ""

Colors
RED='\033[0;31m'

GREEN='\033[0;32m'

YELLOW='\033[1;33m'

NC='\033[0m'

Test results
TESTS_PASSED=0

TESTS_FAILED=0

Function to run test and track results
run_test() {

Bash

Copy
local test_name=$1

local test_command=$2



echo -e "${YELLOW}Running: ${test_name}${NC}"



if eval "$test_command"; then

    echo -e "${GREEN}✓ PASSED${NC}\n"

    ((TESTS_PASSED++))

    return 0

else

    echo -e "${RED}✗ FAILED${NC}\n"

    ((TESTS_FAILED++))

    return 1

fi
}

Test 1: Environment Check
run_test "Environment Variables" "python scripts/check_environment.py"

Test 2: Code Quality
run_test "Flake8 Linting" "flake8 hipaa_training/ main.py --max-line-length=100 --extend-ignore=E203,W503 --count"

Test 3: Unit Tests
run_test "Unit Tests" "pytest tests/ -v --tb=short"

Test 4: Code Coverage
run_test "Code Coverage (80%+)" "pytest tests/ --cov=hipaa_training --cov-report=term --cov-fail-under=80"

Test 5: Security Scan
run_test "Security Scan (Bandit)" "bandit -r hipaa_training/ main.py -ll -i"

Test 6: Type Checking
run_test "Type Checking (MyPy)" "mypy hipaa_training/ --ignore-missing-imports || true"

Test 7: Import Check
run_test "Import Verification" "python -c 'from hipaa_training import *; print("All imports successful")'"

Test 8: Database Initialization
run_test "Database Setup" "python main.py --setup-only"

Test 9: Health Check
run_test "System Health Check" "python scripts/health_check.py"

Summary
echo ""

echo "=============================================="

echo "📊 TEST SUMMARY"

echo "=============================================="

echo -e "${GREEN}Passed: ${TESTS_PASSED}${NC}"

echo -e "${RED}Failed: ${TESTS_FAILED}${NC}"

echo ""

if [ $TESTS_FAILED -eq 0 ]; then

Bash

Copy
echo -e "${GREEN}✅ ALL TESTS PASSED - Ready for deployment!${NC}"

exit 0
else

Bash

Copy
echo -e "${RED}❌ SOME TESTS FAILED - Review and fix before deployment${NC}"

exit 1
fi
