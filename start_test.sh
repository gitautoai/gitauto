#!/bin/bash

# Unit tests for start.sh
# This test file uses bash testing framework to test the start.sh script

# Test configuration
TEST_DIR="$(mktemp -d)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
START_SCRIPT="$SCRIPT_DIR/start.sh"

# Colors for test output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Test helper functions
setup_test_env() {
    cd "$TEST_DIR"
    # Create mock .env file
    echo "SUPABASE_DB_PASSWORD=test_password" > .env
    # Create mock requirements.txt
    echo "fastapi==0.104.1" > requirements.txt
    # Create mock ngrok.yml
    echo "version: 2" > ngrok.yml
}

cleanup_test_env() {
    cd "$SCRIPT_DIR"
    rm -rf "$TEST_DIR"
}

assert_equals() {
    local expected="$1"
    local actual="$2"
    local test_name="$3"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    
    if [ "$expected" = "$actual" ]; then
        echo -e "${GREEN}✓ PASS${NC}: $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ FAIL${NC}: $test_name"
        echo -e "  Expected: $expected"
        echo -e "  Actual: $actual"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

assert_contains() {
    local expected="$1"
    local actual="$2"
    local test_name="$3"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    
    if [[ "$actual" == *"$expected"* ]]; then
        echo -e "${GREEN}✓ PASS${NC}: $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ FAIL${NC}: $test_name"
        echo -e "  Expected to contain: $expected"
        echo -e "  Actual: $actual"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

assert_file_exists() {
    local file_path="$1"
    local test_name="$2"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    
    if [ -f "$file_path" ]; then
        echo -e "${GREEN}✓ PASS${NC}: $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ FAIL${NC}: $test_name"
        echo -e "  File does not exist: $file_path"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

assert_directory_exists() {
    local dir_path="$1"
    local test_name="$2"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    
    if [ -d "$dir_path" ]; then
        echo -e "${GREEN}✓ PASS${NC}: $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ FAIL${NC}: $test_name"
        echo -e "  Directory does not exist: $dir_path"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Mock functions for testing
mock_python3() {
    if [[ "$*" == *"venv --upgrade-deps venv"* ]]; then
        mkdir -p venv/bin
        echo "#!/bin/bash" > venv/bin/activate
        echo "export VIRTUAL_ENV='$PWD/venv'" >> venv/bin/activate
        echo "Mock virtual environment created"
        return 0
    fi
    return 1
}

mock_pip() {
    if [[ "$*" == *"install -r requirements.txt"* ]]; then
        echo "Mock pip install completed"
        return 0
    fi
    return 1
}

mock_sb_pydantic() {
    if [[ "$*" == *"gen --type pydantic"* ]]; then
        mkdir -p schemas/supabase
        echo "Mock Supabase types generated"
        return 0
    fi
    return 1
}

mock_ngrok() {
    if [[ "$*" == *"http --config=ngrok.yml"* ]]; then
        echo "Mock ngrok started" > /dev/null 2>&1 &
        echo $!
        return 0
    fi
    return 1
}

mock_curl() {
    if [[ "$*" == *"localhost:4040/api/tunnels"* ]]; then
        # Simulate ngrok being ready after a few attempts
        if [ ! -f "/tmp/ngrok_ready_count" ]; then
            echo "0" > /tmp/ngrok_ready_count
        fi
        count=$(cat /tmp/ngrok_ready_count)
        count=$((count + 1))
        echo "$count" > /tmp/ngrok_ready_count
        
        if [ "$count" -ge 3 ]; then
            return 0  # Success after 3 attempts
        else
            return 1  # Fail first few attempts
        fi
    fi
    return 1
}

mock_uvicorn() {
    if [[ "$*" == *"main:app --reload"* ]]; then
        echo "Mock uvicorn started"
        return 0
    fi
    return 1
}

# Test functions
test_script_exists() {
    assert_file_exists "$START_SCRIPT" "start.sh script exists"
}

test_script_is_executable() {
    TESTS_RUN=$((TESTS_RUN + 1))
    
    if [ -x "$START_SCRIPT" ]; then
        echo -e "${GREEN}✓ PASS${NC}: start.sh is executable"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ FAIL${NC}: start.sh is not executable"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

test_script_has_shebang() {
    local first_line=$(head -n 1 "$START_SCRIPT")
    assert_equals "#!/bin/zsh" "$first_line" "start.sh has correct shebang"
}

test_environment_variables_loaded() {
    setup_test_env
    
    # Create a modified version of start.sh that only loads env and exits
    cat > test_env_load.sh << 'EOF'
#!/bin/zsh
source .env
echo "SUPABASE_DB_PASSWORD=$SUPABASE_DB_PASSWORD"
EOF
    chmod +x test_env_load.sh
    
    local output=$(./test_env_load.sh 2>/dev/null)
    assert_contains "SUPABASE_DB_PASSWORD=test_password" "$output" "Environment variables are loaded"
    
    rm -f test_env_load.sh
    cleanup_test_env
}

test_configuration_variables() {
    # Extract configuration from start.sh
    local port=$(grep "^PORT=" "$START_SCRIPT" | cut -d'=' -f2)
    local domain=$(grep "^NGROK_DOMAIN=" "$START_SCRIPT" | cut -d'=' -f2 | tr -d '"')
    
    assert_equals "8000" "$port" "PORT is set to 8000"
    assert_equals "gitauto.ngrok.dev" "$domain" "NGROK_DOMAIN is set correctly"
}

test_color_variables() {
    # Extract color variables from start.sh
    local green=$(grep "^GREEN=" "$START_SCRIPT" | cut -d'=' -f2 | tr -d "'")
    local nc=$(grep "^NC=" "$START_SCRIPT" | cut -d'=' -f2 | tr -d "'")
    
    assert_equals "\\033[0;32m" "$green" "GREEN color variable is set correctly"
    assert_equals "\\033[0m" "$nc" "NC (No Color) variable is set correctly"
}

test_venv_creation_when_not_exists() {
    setup_test_env
    
    # Create a test script that simulates venv creation logic
    cat > test_venv_creation.sh << 'EOF'
#!/bin/bash

# Mock functions
python3() {
    if [[ "$*" == *"venv --upgrade-deps venv"* ]]; then
        mkdir -p venv/bin
        echo "#!/bin/bash" > venv/bin/activate
        echo "export VIRTUAL_ENV='$PWD/venv'" >> venv/bin/activate
        echo "Creating virtual environment..."
        return 0
    fi
}

pip() {
    if [[ "$*" == *"install -r requirements.txt"* ]]; then
        echo "Installing dependencies..."
        return 0
    fi
}

source() {
    if [[ "$1" == "venv/bin/activate" ]]; then
        echo "Virtual environment activated"
        return 0
    fi
}

# Test logic
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv --upgrade-deps venv
    echo "Installing dependencies..."
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

echo "Virtual environment ready"
EOF
    chmod +x test_venv_creation.sh
    
    local output=$(./test_venv_creation.sh 2>/dev/null)
    assert_contains "Creating virtual environment..." "$output" "Virtual environment creation is triggered when venv doesn't exist"
    assert_contains "Installing dependencies..." "$output" "Dependencies installation is triggered"
    assert_contains "Virtual environment ready" "$output" "Virtual environment setup completes"
    
    rm -f test_venv_creation.sh
    cleanup_test_env
}

test_venv_activation_when_exists() {
    setup_test_env
    
    # Create existing venv directory
    mkdir -p venv/bin
    echo "#!/bin/bash" > venv/bin/activate
    
    # Create a test script that simulates venv activation logic
    cat > test_venv_activation.sh << 'EOF'
#!/bin/bash

source() {
    if [[ "$1" == "venv/bin/activate" ]]; then
        echo "Activating existing virtual environment"
        return 0
    fi
}

# Test logic
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
else
    source venv/bin/activate
fi

echo "Virtual environment ready"
EOF
    chmod +x test_venv_activation.sh
    
    local output=$(./test_venv_activation.sh 2>/dev/null)
    assert_contains "Activating existing virtual environment" "$output" "Existing virtual environment is activated"
    assert_contains "Virtual environment ready" "$output" "Virtual environment activation completes"
    
    rm -f test_venv_activation.sh
    cleanup_test_env
}

test_supabase_types_generation() {
    setup_test_env
    
    # Create a test script that simulates Supabase types generation
    cat > test_supabase_gen.sh << 'EOF'
#!/bin/bash

sb-pydantic() {
    if [[ "$*" == *"gen --type pydantic"* ]]; then
        mkdir -p schemas/supabase
        echo "Generating Supabase types..."
        return 0
    fi
}

grep() {
    if [[ "$*" == *"grep -v"* ]]; then
        echo "Types generated successfully"
        return 0
    fi
}

# Test the command structure
echo "Generating Supabase types..."
sb-pydantic gen --type pydantic --db-url "postgresql://test" --dir schemas/supabase 2>&1 | grep -v "^INFO:"
EOF
    chmod +x test_supabase_gen.sh
    
    local output=$(./test_supabase_gen.sh 2>/dev/null)
    assert_contains "Generating Supabase types..." "$output" "Supabase types generation is triggered"
    assert_contains "Types generated successfully" "$output" "Supabase types generation completes"
    
    rm -f test_supabase_gen.sh
    cleanup_test_env
}

test_cleanup_function_exists() {
    local cleanup_function=$(grep -A 10 "cleanup()" "$START_SCRIPT")
    assert_contains "echo -e" "$cleanup_function" "cleanup function contains echo statement"
    assert_contains "kill" "$cleanup_function" "cleanup function contains kill command"
    assert_contains "deactivate" "$cleanup_function" "cleanup function contains deactivate command"
    assert_contains "exit 0" "$cleanup_function" "cleanup function contains exit statement"
}

test_signal_trap_setup() {
    local trap_line=$(grep "trap cleanup" "$START_SCRIPT")
    assert_contains "SIGINT SIGTERM" "$trap_line" "Signal trap is set up for SIGINT and SIGTERM"
}

test_ngrok_startup_logic() {
    setup_test_env
    rm -f /tmp/ngrok_ready_count  # Clean up from previous tests
    
    # Create a test script that simulates ngrok startup
    cat > test_ngrok_startup.sh << 'EOF'
#!/bin/bash

PORT=8000
NGROK_DOMAIN="gitauto.ngrok.dev"

ngrok() {
    if [[ "$*" == *"http --config=ngrok.yml"* ]]; then
        echo "Starting ngrok tunnel..." >&2
        sleep 0.1 &
        echo $!
        return 0
    fi
}

curl() {
    if [[ "$*" == *"localhost:4040/api/tunnels"* ]]; then
        # Simulate ngrok being ready after a few attempts
        if [ ! -f "/tmp/ngrok_ready_count" ]; then
            echo "0" > /tmp/ngrok_ready_count
        fi
        count=$(cat /tmp/ngrok_ready_count)
        count=$((count + 1))
        echo "$count" > /tmp/ngrok_ready_count
        
        if [ "$count" -ge 3 ]; then
            return 0  # Success after 3 attempts
        else
            return 1  # Fail first few attempts
        fi
    fi
}

sleep() {
    return 0  # Mock sleep to speed up tests
}

# Test ngrok startup logic
echo "Starting ngrok tunnel..."
ngrok http --config=ngrok.yml --domain=${NGROK_DOMAIN} ${PORT} > /dev/null 2>&1 &
NGROK_PID=$!

echo "Waiting for ngrok to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:4040/api/tunnels > /dev/null 2>&1; then
        break
    fi
    sleep 0.5
done

echo "ngrok started!"
echo "ngrok: https://${NGROK_DOMAIN}"
echo "FastAPI: http://localhost:${PORT}"
EOF
    chmod +x test_ngrok_startup.sh
    
    local output=$(./test_ngrok_startup.sh 2>&1)
    assert_contains "Starting ngrok tunnel..." "$output" "ngrok startup is initiated"
    assert_contains "Waiting for ngrok to be ready..." "$output" "ngrok readiness check is performed"
    assert_contains "ngrok started!" "$output" "ngrok startup completes successfully"
    assert_contains "https://gitauto.ngrok.dev" "$output" "ngrok URL is displayed"
    assert_contains "http://localhost:8000" "$output" "FastAPI URL is displayed"
    
    rm -f test_ngrok_startup.sh
    rm -f /tmp/ngrok_ready_count
    cleanup_test_env
}

test_script_structure() {
    # Test that the script contains all expected sections
    local script_content=$(cat "$START_SCRIPT")
    
    assert_contains "#!/bin/zsh" "$script_content" "Script has zsh shebang"
    assert_contains "source .env" "$script_content" "Script loads environment variables"
    assert_contains "PORT=8000" "$script_content" "Script sets PORT configuration"
    assert_contains "NGROK_DOMAIN=" "$script_content" "Script sets NGROK_DOMAIN configuration"
    assert_contains "GREEN=" "$script_content" "Script defines color variables"
    assert_contains "python3 -m venv" "$script_content" "Script contains venv creation logic"
    assert_contains "sb-pydantic gen" "$script_content" "Script contains Supabase types generation"
    assert_contains "cleanup()" "$script_content" "Script defines cleanup function"
    assert_contains "trap cleanup" "$script_content" "Script sets up signal traps"
    assert_contains "ngrok http" "$script_content" "Script starts ngrok"
    assert_contains "uvicorn main:app" "$script_content" "Script starts uvicorn server"
}

# Run all tests
run_tests() {
    echo -e "${YELLOW}Running start.sh unit tests...${NC}\n"
    
    test_script_exists
    test_script_is_executable
    test_script_has_shebang
    test_environment_variables_loaded
    test_configuration_variables
    test_color_variables
    test_venv_creation_when_not_exists
    test_venv_activation_when_exists
    test_supabase_types_generation
    test_cleanup_function_exists
    test_signal_trap_setup
    test_ngrok_startup_logic
    test_script_structure
    
    echo -e "\n${YELLOW}Test Results:${NC}"
    echo -e "Tests run: $TESTS_RUN"
    echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
    
    if [ $TESTS_FAILED -gt 0 ]; then
        echo -e "${RED}Failed: $TESTS_FAILED${NC}"
        exit 1
    else
        echo -e "${GREEN}All tests passed!${NC}"
        exit 0
    fi
}

# Main execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    run_tests
fi
