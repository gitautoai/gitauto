from typing import cast
from unittest.mock import patch

from services.github.commits.apply_diff_to_file import apply_diff_to_file
from services.github.types.github_types import BaseArgs


@patch("services.github.commits.apply_diff_to_file.requests.get")
def test_deletion_diff_rejected(mock_get):
    """Test that deletion diffs are rejected with proper error message."""
    base_args = cast(BaseArgs, {
        "owner": "test_owner",
        "repo": "test_repo",
        "token": "test_token",
        "new_branch": "test_branch",
    })

    deletion_diff = """--- utils/files/test_file.py
+++ /dev/null
@@ -1 +0,0 @@
-# Temporary file to check existing content"""

    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "content": "IyBUZW1wb3JhcnkgZmlsZSB0byBjaGVjayBleGlzdGluZyBjb250ZW50",
        "sha": "test_sha",
    }

    result = apply_diff_to_file(
        diff=deletion_diff, file_path="utils/files/test_file.py", base_args=base_args
    )

    assert isinstance(result, str)
    assert "Cannot delete files using apply_diff_to_file" in result
    assert "Use the delete_file tool instead" in result
    assert "utils/files/test_file.py" in result


def test_missing_new_branch_error():
    """Test that missing new_branch returns False due to handle_exceptions."""
    base_args = cast(BaseArgs, {
        "owner": "test_owner",
        "repo": "test_repo",
        "token": "test_token",
        "new_branch": None,
    })

    result = apply_diff_to_file(
        diff="--- test\n+++ test\n@@ -1,1 +1,1 @@\n-old\n+new",
        file_path="test.py",
        base_args=base_args,
    )

    assert result is False
