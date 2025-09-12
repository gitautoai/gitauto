# Standard imports
import os
import tempfile
import shutil

# Third-party imports
import pytest

# Local imports
from services.github.repositories.initialize_repo import initialize_repo


def test_integration_initialize_repo_with_temp_directory(test_token):
    """Integration test for initialize_repo with a temporary directory."""
    # Create a temporary directory for testing
    temp_dir = tempfile.mkdtemp()
    test_repo_path = os.path.join(temp_dir, "test-integration-repo")
    test_remote_url = "https://github.com/test-owner/test-integration-repo.git"
    
    try:
        # This will fail at the git push step since the remote doesn't exist,
        # but it should create the directory and README file
        result = initialize_repo(test_repo_path, test_remote_url, test_token)
        
        # The function should return None due to exception handling
        assert result is None
        
        # Verify that the directory was created
        assert os.path.exists(test_repo_path)
        
        # Verify that README.md was created
        readme_path = os.path.join(test_repo_path, "README.md")
        assert os.path.exists(readme_path)
        
        # Verify README content
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "## GitAuto resources" in content
            assert "GitAuto homepage" in content
    finally:
        # Clean up the temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)
