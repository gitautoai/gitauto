import os
import shutil
import tempfile

import pytest

from services.git.clone_repo import clone_repo
from tests.constants import OWNER, REPO, TOKEN


@pytest.mark.integration
def test_clone_repo_integration():
    """
    Integration test for clone_repo function.
    This test actually clones a repository, so it should be run only in integration test environments.
    """
    # Create a temporary directory for the test
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Clone the repository
        clone_repo(OWNER, REPO, TOKEN, temp_dir)
        
        # Verify that the repository was cloned successfully
        # Check if .git directory exists
        assert os.path.isdir(os.path.join(temp_dir, ".git")), ".git directory not found"
        
        # Check if README.md exists (assuming the repo has a README.md)
        assert os.path.isfile(os.path.join(temp_dir, "README.md")), "README.md not found"
        
    finally:
        # Clean up the temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)