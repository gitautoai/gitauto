import pytest
from unittest.mock import patch, MagicMock
import base64

from services.github.commits.apply_diff_to_file import apply_diff_to_file
from tests.constants import OWNER, REPO, TOKEN


def test_apply_diff_to_file_skip_ci_true():
    """Test apply_diff_to_file with skip_ci=True adds [skip ci] to commit message."""
    # Arrange
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "new_branch": "test-branch",
        "skip_ci": True
    }
    file_path = "test/file.py"
    diff = """--- test/file.py
+++ test/file.py
@@ -1,3 +1,4 @@
 def hello():
     print("Hello")
+    print("World")
     return True"""
    
    # Mock existing file response
    get_response = MagicMock()
    get_response.status_code = 200
    get_response.json.return_value = {
        "type": "file",
        "sha": "existing_sha_123",
        "content": base64.b64encode(b'def hello():\n    print("Hello")\n    return True').decode()
    }
    
    put_response = MagicMock()
    
    # Act
    with patch("services.github.commits.apply_diff_to_file.requests.get") as mock_get, \
         patch("services.github.commits.apply_diff_to_file.requests.put") as mock_put, \
         patch("services.github.commits.apply_diff_to_file.create_headers") as mock_create_headers:
        
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_get.return_value = get_response
        mock_put.return_value = put_response
        
        result = apply_diff_to_file(diff, file_path, base_args)
    
    # Assert
    assert result == f"diff applied to the file: {file_path} successfully by apply_diff_to_file()."
    
    # Verify the commit message includes [skip ci]
    put_call_args = mock_put.call_args
    commit_data = put_call_args[1]["json"]
    assert commit_data["message"] == f"Update {file_path} [skip ci]"


def test_apply_diff_to_file_skip_ci_false():
    """Test apply_diff_to_file with skip_ci=False does not add [skip ci] to commit message."""
    # Arrange
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "new_branch": "test-branch",
        "skip_ci": False
    }
    file_path = "test/file.py"
    diff = """--- test/file.py
+++ test/file.py
@@ -1,3 +1,4 @@
 def hello():
     print("Hello")
+    print("World")
     return True"""
    
    # Mock existing file response
    get_response = MagicMock()
    get_response.status_code = 200
    get_response.json.return_value = {
        "type": "file",
        "sha": "existing_sha_123",
        "content": base64.b64encode(b'def hello():\n    print("Hello")\n    return True').decode()
    }
    
    put_response = MagicMock()
    
    # Act
    with patch("services.github.commits.apply_diff_to_file.requests.get") as mock_get, \
         patch("services.github.commits.apply_diff_to_file.requests.put") as mock_put, \
         patch("services.github.commits.apply_diff_to_file.create_headers") as mock_create_headers:
        
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_get.return_value = get_response
        mock_put.return_value = put_response
        
        result = apply_diff_to_file(diff, file_path, base_args)
    
    # Assert
    assert result == f"diff applied to the file: {file_path} successfully by apply_diff_to_file()."
    
    # Verify the commit message does not include [skip ci]
    put_call_args = mock_put.call_args
    commit_data = put_call_args[1]["json"]
    assert commit_data["message"] == f"Update {file_path}"


def test_apply_diff_to_file_skip_ci_default():
    """Test apply_diff_to_file without skip_ci parameter defaults to False."""
    # Arrange
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "new_branch": "test-branch"
        # skip_ci not provided, should default to False
    }
    file_path = "test/file.py"
    diff = """--- test/file.py
+++ test/file.py
@@ -1,3 +1,4 @@
 def hello():
     print("Hello")
+    print("World")
     return True"""
    
    # Mock existing file response
    get_response = MagicMock()
    get_response.status_code = 200
    get_response.json.return_value = {
        "type": "file",
        "sha": "existing_sha_123",
        "content": base64.b64encode(b'def hello():\n    print("Hello")\n    return True').decode()
    }
    
    put_response = MagicMock()
    
    # Act
    with patch("services.github.commits.apply_diff_to_file.requests.get") as mock_get, \
         patch("services.github.commits.apply_diff_to_file.requests.put") as mock_put, \
         patch("services.github.commits.apply_diff_to_file.create_headers") as mock_create_headers:
        
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_get.return_value = get_response
        mock_put.return_value = put_response
        
        result = apply_diff_to_file(diff, file_path, base_args)
    
    # Assert
    assert result == f"diff applied to the file: {file_path} successfully by apply_diff_to_file()."
    
    # Verify the commit message does not include [skip ci] (default behavior)
    put_call_args = mock_put.call_args
    commit_data = put_call_args[1]["json"]
    assert commit_data["message"] == f"Update {file_path}"


def test_apply_diff_to_file_skip_ci_new_file():
    """Test apply_diff_to_file with skip_ci=True for new file (404 response)."""
    # Arrange
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "new_branch": "test-branch",
        "skip_ci": True
    }
    file_path = "test/new_file.py"
    diff = """--- /dev/null
+++ test/new_file.py
@@ -0,0 +1,3 @@
+def hello():
+    print("Hello")
+    return True"""
    
    # Mock file not found response
    get_response = MagicMock()
    get_response.status_code = 404
    
    put_response = MagicMock()
    
    # Act
    with patch("services.github.commits.apply_diff_to_file.requests.get") as mock_get, \
         patch("services.github.commits.apply_diff_to_file.requests.put") as mock_put, \
         patch("services.github.commits.apply_diff_to_file.create_headers") as mock_create_headers:
        
        mock_create_headers.return_value = {"Authorization": f"Bearer {TOKEN}"}
        mock_get.return_value = get_response
        mock_put.return_value = put_response
        
        result = apply_diff_to_file(diff, file_path, base_args)
    
    # Assert
    assert result == f"diff applied to the file: {file_path} successfully by apply_diff_to_file()."
    
    # Verify the commit message includes [skip ci] even for new files
    put_call_args = mock_put.call_args
    commit_data = put_call_args[1]["json"]
    assert commit_data["message"] == f"Update {file_path} [skip ci]"
    # Verify no SHA is included for new files
    assert "sha" not in commit_data
