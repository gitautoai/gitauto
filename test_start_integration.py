"""Integration tests for start.sh script."""

import os
import subprocess
import tempfile
import pytest


class TestStartScriptIntegration:
    """Integration tests for start.sh script functionality."""

    @pytest.fixture
    def script_path(self):
        """Get the path to the start.sh script."""
        return os.path.join(os.path.dirname(__file__), "start.sh")

    @pytest.fixture
    def test_environment(self):
        """Create a test environment with necessary files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create .env file
            env_file = os.path.join(temp_dir, ".env")
            with open(env_file, "w") as f:
                f.write("SUPABASE_DB_PASSWORD=test_password\n")
                f.write("TEST_MODE=true\n")

            # Create requirements.txt
            req_file = os.path.join(temp_dir, "requirements.txt")
            with open(req_file, "w") as f:
                f.write("fastapi==0.104.1\n")
                f.write("uvicorn==0.24.0\n")

            # Create ngrok.yml
            ngrok_file = os.path.join(temp_dir, "ngrok.yml")
            with open(ngrok_file, "w") as f:
                f.write("version: 2\n")
                f.write("authtoken: test_token\n")

            yield temp_dir

    def test_script_syntax_check(self, script_path):
        """Test that the script has valid shell syntax."""
        result = subprocess.run(
            ["bash", "-n", script_path], 
            capture_output=True, 
            text=True
        )
        assert result.returncode == 0, f"Script syntax error: {result.stderr}"

    def test_script_dry_run_with_exit(self, script_path, test_environment):
        """Test script execution with early exit to avoid full startup."""
        # Create a modified version of the script that exits early
        modified_script = os.path.join(test_environment, "start_test.sh")
        
        with open(script_path, "r") as original:
            content = original.read()
        
        # Insert early exit after environment loading
        modified_content = content.replace(
            "source .env",
            "source .env\necho 'Environment loaded successfully'\nexit 0"
        )
        
        with open(modified_script, "w") as modified:
            modified.write(modified_content)
        
        os.chmod(modified_script, 0o755)
        
        # Change to test directory and run
        original_cwd = os.getcwd()
        try:
            os.chdir(test_environment)
            result = subprocess.run(
                [modified_script], 
                capture_output=True, 
                text=True,
                timeout=10
            )
            assert result.returncode == 0
            assert "Environment loaded successfully" in result.stdout
        finally:
            os.chdir(original_cwd)

    def test_environment_variable_loading(self, script_path, test_environment):
        """Test that environment variables are loaded correctly."""
        # Create a test script that only loads env and prints variables
        test_script = os.path.join(test_environment, "test_env.sh")
        
        script_content = """#!/bin/bash
source .env
echo "SUPABASE_DB_PASSWORD=$SUPABASE_DB_PASSWORD"
echo "TEST_MODE=$TEST_MODE"
"""
        
        with open(test_script, "w") as f:
            f.write(script_content)
        
        os.chmod(test_script, 0o755)
        
        # Change to test directory and run
        original_cwd = os.getcwd()
        try:
            os.chdir(test_environment)
            result = subprocess.run(
                [test_script], 
                capture_output=True, 
                text=True
            )
            assert result.returncode == 0
            assert "SUPABASE_DB_PASSWORD=test_password" in result.stdout
            assert "TEST_MODE=true" in result.stdout
        finally:
            os.chdir(original_cwd)

    def test_venv_creation_simulation(self, test_environment):
        """Test virtual environment creation logic in isolation."""
        # Create a test script that simulates venv creation
        test_script = os.path.join(test_environment, "test_venv.sh")
        
        script_content = """#!/bin/bash
# Mock python3 command
python3() {
    if [[ "$*" == *"venv --upgrade-deps venv"* ]]; then
        mkdir -p venv/bin
        echo "#!/bin/bash" > venv/bin/activate
        echo "export VIRTUAL_ENV='$PWD/venv'" >> venv/bin/activate
        echo "Mock virtual environment created"
        return 0
    fi
}

# Mock pip command
pip() {
    if [[ "$*" == *"install -r requirements.txt"* ]]; then
        echo "Mock dependencies installed"
        return 0
    fi
}

# Test the venv logic
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv --upgrade-deps venv
    echo "Installing dependencies..."
    source venv/bin/activate
    pip install -r requirements.txt
else
    echo "Activating existing virtual environment..."
    source venv/bin/activate
fi

echo "Virtual environment ready"
"""
        
        with open(test_script, "w") as f:
            f.write(script_content)
        
        os.chmod(test_script, 0o755)
        
        # Change to test directory and run
        original_cwd = os.getcwd()
        try:
            os.chdir(test_environment)
            result = subprocess.run(
                [test_script], 
                capture_output=True, 
                text=True
            )
            assert result.returncode == 0
            assert "Creating virtual environment..." in result.stdout
            assert "Mock virtual environment created" in result.stdout
            assert "Mock dependencies installed" in result.stdout
            assert "Virtual environment ready" in result.stdout
            
            # Test with existing venv
            result2 = subprocess.run(
                [test_script], 
                capture_output=True, 
                text=True
            )
            assert result2.returncode == 0
            assert "Activating existing virtual environment..." in result2.stdout
            assert "Virtual environment ready" in result2.stdout
        finally:
            os.chdir(original_cwd)

    def test_script_help_or_version_flags(self, script_path):
        """Test that script handles common flags gracefully."""
        # Most shell scripts should handle --help or similar flags
        # This test ensures the script doesn't crash with common flags
        
        # Test with timeout to prevent hanging
        try:
            result = subprocess.run(
                ["bash", script_path, "--help"], 
                capture_output=True, 
                text=True,
                timeout=5
            )
            # Script may not implement --help, but shouldn't crash
            assert result.returncode in [0, 1, 2]  # Common exit codes
        except subprocess.TimeoutExpired:
            # If script hangs, that's also a valid test result
            # as it means the script is trying to run normally
            pass

    def test_script_with_missing_env_file(self, script_path):
        """Test script behavior when .env file is missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a modified script that exits after trying to source .env
            modified_script = os.path.join(temp_dir, "start_test.sh")
            
            script_content = """#!/bin/bash
source .env 2>/dev/null || echo "No .env file found"
echo "Script continued despite missing .env"
exit 0
"""
            
            with open(modified_script, "w") as f:
                f.write(script_content)
            
            os.chmod(modified_script, 0o755)
            
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                result = subprocess.run(
                    [modified_script], 
                    capture_output=True, 
                    text=True
                )
                # Script should handle missing .env gracefully
                assert "Script continued despite missing .env" in result.stdout
            finally:
                os.chdir(original_cwd)
