import subprocess
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from services.git.clone_repo import clone_repo
from tests.constants import OWNER, REPO, TOKEN


def test_clone_repo_success():
    """Test successful repository cloning."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock subprocess.run to avoid actual git clone
        with patch("subprocess.run") as mock_run:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_run.return_value = mock_process

            # Call the function
            clone_repo(OWNER, REPO, TOKEN, temp_dir)

            # Verify subprocess.run was called with correct arguments
            expected_repo_url = (
                f"https://x-access-token:{TOKEN}@github.com/{OWNER}/{REPO}.git"
            )
            expected_cmd = f"git clone {expected_repo_url} {temp_dir}"
            mock_run.assert_called_once_with(
                expected_cmd, shell=True, capture_output=True, text=True, check=True
            )


def test_clone_repo_subprocess_error():
    """Test error handling when subprocess.run fails."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock subprocess.run to simulate a failure
        with patch("subprocess.run") as mock_run:
            # Create a subprocess error
            mock_run.side_effect = subprocess.CalledProcessError(
                returncode=1,
                cmd="git clone",
                output="",
                stderr="fatal: repository not found",
            )

            # The function should raise an exception due to raise_on_error=True
            with pytest.raises(subprocess.CalledProcessError):
                clone_repo(OWNER, REPO, TOKEN, temp_dir)


def test_clone_repo_with_invalid_parameters():
    """Test with invalid parameters to ensure proper error handling."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock subprocess.run to avoid actual git clone but simulate failure
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                returncode=1,
                cmd="git clone",
                output="",
                stderr="fatal: repository not found",
            )

            # Test with invalid repo name
            with pytest.raises(subprocess.CalledProcessError):
                clone_repo(OWNER, "non-existent-repo", TOKEN, temp_dir)
