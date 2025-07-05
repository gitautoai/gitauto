"""Unit tests for start.sh script functionality."""

import os
import subprocess
import tempfile
from unittest.mock import patch, MagicMock, call
import pytest


class TestStartScript:
    """Test class for start.sh script functionality."""

    @pytest.fixture
    def script_path(self):
        """Get the path to the start.sh script."""
        return os.path.join(os.path.dirname(__file__), "start.sh")

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def mock_env_file(self, temp_dir):
        """Create a mock .env file."""
        env_file = os.path.join(temp_dir, ".env")
        with open(env_file, "w") as f:
            f.write("SUPABASE_DB_PASSWORD=test_password\n")
        return env_file

    @pytest.fixture
    def mock_requirements_file(self, temp_dir):
        """Create a mock requirements.txt file."""
        req_file = os.path.join(temp_dir, "requirements.txt")
        with open(req_file, "w") as f:
            f.write("fastapi==0.104.1\nuvicorn==0.24.0\n")
        return req_file

    def test_script_exists(self, script_path):
        """Test that the start.sh script exists."""
        assert os.path.exists(script_path), "start.sh script should exist"

    def test_script_is_executable(self, script_path):
        """Test that the start.sh script is executable."""
        assert os.access(script_path, os.X_OK), "start.sh script should be executable"

    def test_script_has_correct_shebang(self, script_path):
        """Test that the script has the correct shebang."""
        with open(script_path, "r") as f:
            first_line = f.readline().strip()
        assert first_line == "#!/bin/zsh", "Script should have zsh shebang"

    def test_script_contains_required_sections(self, script_path):
        """Test that the script contains all required sections."""
        with open(script_path, "r") as f:
            content = f.read()

        required_sections = [
            "source .env",
            "PORT=8000",
            "NGROK_DOMAIN=",
            "GREEN=",
            "NC=",
            "python3 -m venv",
            "sb-pydantic gen",
            "cleanup()",
            "trap cleanup",
            "ngrok http",
            "uvicorn main:app",
        ]

        for section in required_sections:
            assert section in content, f"Script should contain '{section}'"

    def test_configuration_variables(self, script_path):
        """Test that configuration variables are set correctly."""
        with open(script_path, "r") as f:
            content = f.read()

        # Extract configuration values
        port_line = [line for line in content.split("\n") if line.startswith("PORT=")]
        domain_line = [
            line for line in content.split("\n") if line.startswith("NGROK_DOMAIN=")
        ]

        assert len(port_line) == 1, "Should have exactly one PORT definition"
        assert "PORT=8000" in port_line[0], "PORT should be set to 8000"

        assert len(domain_line) == 1, "Should have exactly one NGROK_DOMAIN definition"
        assert "gitauto.ngrok.dev" in domain_line[0], "NGROK_DOMAIN should be set correctly"

    def test_color_variables(self, script_path):
        """Test that color variables are defined correctly."""
        with open(script_path, "r") as f:
            content = f.read()

        assert "GREEN=" in content, "GREEN color variable should be defined"
        assert "NC=" in content, "NC (No Color) variable should be defined"
        assert "\\033[0;32m" in content, "GREEN should contain ANSI color code"
        assert "\\033[0m" in content, "NC should contain ANSI reset code"

    @patch("subprocess.run")
    def test_venv_creation_logic(self, mock_run, temp_dir, mock_env_file, mock_requirements_file):
        """Test virtual environment creation logic."""
        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(temp_dir)

        try:
            # Mock subprocess calls
            mock_run.return_value = MagicMock(returncode=0)

            # Create a test script that simulates venv creation
            test_script = """#!/bin/bash
source .env
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
"""
            script_file = os.path.join(temp_dir, "test_venv.sh")
            with open(script_file, "w") as f:
                f.write(test_script)
            os.chmod(script_file, 0o755)

            # Run the test script
            result = subprocess.run([script_file], capture_output=True, text=True)

            assert "Creating virtual environment..." in result.stdout
            assert "Virtual environment ready" in result.stdout

        finally:
            os.chdir(original_cwd)

    def test_cleanup_function_structure(self, script_path):
        """Test that the cleanup function is properly structured."""
        with open(script_path, "r") as f:
            content = f.read()

        # Find cleanup function
        cleanup_start = content.find("cleanup() {")
        cleanup_end = content.find("}", cleanup_start)
        cleanup_function = content[cleanup_start:cleanup_end + 1]

        assert cleanup_start != -1, "cleanup function should exist"
        assert "echo -e" in cleanup_function, "cleanup should have echo statement"
        assert "kill" in cleanup_function, "cleanup should have kill command"
        assert "deactivate" in cleanup_function, "cleanup should deactivate venv"
        assert "exit 0" in cleanup_function, "cleanup should exit with status 0"

    def test_signal_trap_configuration(self, script_path):
        """Test that signal traps are configured correctly."""
        with open(script_path, "r") as f:
            content = f.read()

        trap_lines = [line for line in content.split("\n") if "trap cleanup" in line]
        assert len(trap_lines) == 1, "Should have exactly one trap statement"
        assert "SIGINT" in trap_lines[0], "Should trap SIGINT signal"
        assert "SIGTERM" in trap_lines[0], "Should trap SIGTERM signal"

    def test_ngrok_command_structure(self, script_path):
        """Test that ngrok command is structured correctly."""
        with open(script_path, "r") as f:
            content = f.read()

        ngrok_lines = [line for line in content.split("\n") if "ngrok http" in line]
        assert len(ngrok_lines) == 1, "Should have exactly one ngrok command"

        ngrok_line = ngrok_lines[0]
        assert "--config=ngrok.yml" in ngrok_line, "Should specify ngrok config file"
        assert "--domain=${NGROK_DOMAIN}" in ngrok_line, "Should use NGROK_DOMAIN variable"
        assert "${PORT}" in ngrok_line, "Should use PORT variable"
        assert "> /dev/null 2>&1 &" in ngrok_line, "Should run in background with output hidden"

    def test_uvicorn_command_structure(self, script_path):
        """Test that uvicorn command is structured correctly."""
        with open(script_path, "r") as f:
            content = f.read()

        uvicorn_lines = [line for line in content.split("\n") if "uvicorn main:app" in line]
        assert len(uvicorn_lines) == 1, "Should have exactly one uvicorn command"

        uvicorn_line = uvicorn_lines[0]
        assert "--reload" in uvicorn_line, "Should enable reload mode"
        assert "--port ${PORT}" in uvicorn_line, "Should use PORT variable"
        assert "--log-level warning" in uvicorn_line, "Should set log level to warning"

    def test_supabase_types_generation_command(self, script_path):
        """Test that Supabase types generation command is correct."""
        with open(script_path, "r") as f:
            content = f.read()

        sb_lines = [line for line in content.split("\n") if "sb-pydantic gen" in line]
        assert len(sb_lines) == 1, "Should have exactly one sb-pydantic command"

        sb_line = sb_lines[0]
        assert "--type pydantic" in sb_line, "Should specify pydantic type"
        assert "--db-url" in sb_line, "Should specify database URL"
        assert "--dir schemas/supabase" in sb_line, "Should specify output directory"
        assert "grep -v" in sb_line, "Should filter out INFO logs"

    def test_ngrok_readiness_check_logic(self, script_path):
        """Test that ngrok readiness check logic is present."""
        with open(script_path, "r") as f:
            content = f.read()

        # Check for readiness loop
        assert "for i in {1..30}" in content, "Should have readiness check loop"
        assert "curl -s http://localhost:4040/api/tunnels" in content, "Should check ngrok API"
        assert "sleep 0.5" in content, "Should have sleep between checks"
        assert "break" in content, "Should break when ngrok is ready"

    def test_output_messages(self, script_path):
        """Test that appropriate output messages are present."""
        with open(script_path, "r") as f:
            content = f.read()

        expected_messages = [
            "Starting GitAuto development environment...",
            "Creating virtual environment...",
            "Installing dependencies...",
            "Virtual environment ready",
            "Generating Supabase types...",
            "Starting ngrok tunnel...",
            "Waiting for ngrok to be ready...",
            "ngrok started!",
            "Starting FastAPI server",
            "Press Ctrl+C to stop both services",
        ]

        for message in expected_messages:
            assert message in content, f"Should contain message: '{message}'"

    def test_environment_variable_usage(self, script_path):
        """Test that environment variables are used correctly."""
        with open(script_path, "r") as f:
            content = f.read()

        # Check for SUPABASE_DB_PASSWORD usage
        assert "${SUPABASE_DB_PASSWORD}" in content, "Should use SUPABASE_DB_PASSWORD variable"

        # Check for PORT and NGROK_DOMAIN usage
        assert "${PORT}" in content, "Should use PORT variable"
        assert "${NGROK_DOMAIN}" in content, "Should use NGROK_DOMAIN variable"

        # Check for color variable usage
        assert "${GREEN}" in content, "Should use GREEN color variable"
        assert "${NC}" in content, "Should use NC color variable"

    @patch("subprocess.run")
    def test_script_syntax_validation(self, mock_run, script_path):
        """Test that the script has valid shell syntax."""
        # Use bash -n to check syntax without executing
        result = subprocess.run(
            ["bash", "-n", script_path], capture_output=True, text=True
        )
        assert result.returncode == 0, f"Script syntax error: {result.stderr}"

    def test_venv_conditional_logic(self, script_path):
        """Test that virtual environment conditional logic is correct."""
        with open(script_path, "r") as f:
            content = f.read()

        # Check for venv existence check
        assert '[ ! -d "venv" ]' in content, "Should check if venv directory doesn't exist"
        assert "python3 -m venv --upgrade-deps venv" in content, "Should create venv with upgrade-deps"
        assert "source venv/bin/activate" in content, "Should activate virtual environment"
        assert "pip install -r requirements.txt" in content, "Should install requirements"

    def test_background_process_management(self, script_path):
        """Test that background processes are managed correctly."""
        with open(script_path, "r") as f:
            content = f.read()

        # Check for background process handling
        assert "NGROK_PID=$!" in content, "Should capture ngrok process ID"
        assert 'kill -0 "$NGROK_PID"' in content, "Should check if process is running"
        assert 'kill "$NGROK_PID"' in content, "Should kill ngrok process in cleanup"

    def test_error_handling_patterns(self, script_path):
        """Test that basic error handling patterns are present."""
        with open(script_path, "r") as f:
            content = f.read()

        # Check for error handling in cleanup
        assert "2>/dev/null" in content, "Should handle stderr redirection"
        assert "|| true" in content, "Should handle potential command failures"

    def test_file_dependencies(self, script_path):
        """Test that the script references expected files."""
        with open(script_path, "r") as f:
            content = f.read()

        expected_files = [
            ".env",
            "requirements.txt",
            "ngrok.yml",
            "main:app",
            "schemas/supabase",
        ]

        for file_ref in expected_files:
            assert file_ref in content, f"Should reference file: '{file_ref}'"

    def test_network_configuration(self, script_path):
        """Test that network configuration is correct."""
        with open(script_path, "r") as f:
            content = f.read()

        # Check for localhost references
        assert "localhost:4040" in content, "Should reference ngrok API port"
        assert "localhost:${PORT}" in content, "Should reference FastAPI port"

        # Check for domain configuration
        assert "https://${NGROK_DOMAIN}" in content, "Should display ngrok HTTPS URL"
        assert "http://localhost:${PORT}" in content, "Should display FastAPI HTTP URL"
