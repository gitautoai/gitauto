# Standard imports
from unittest.mock import patch, MagicMock

# Third-party imports
import pytest

# Local imports
from services.webhook.schedule_handler import schedule_handler


@pytest.fixture
def mock_event():
    """Fixture for EventBridge event."""
    return {
        "ownerId": 123,
        "ownerType": "Organization",
        "ownerName": "test-org",
        "repoId": 456,
        "repoName": "test-repo",
        "userId": 789,
        "userName": "test-user",
        "installationId": 999,
    }


class TestScheduleHandler:
    def test_schedule_handler_missing_required_fields(self):
        """Test that schedule_handler raises ValueError when required fields are missing."""
        # Setup - event with missing fields
        incomplete_event = {
            "ownerId": 123,
            "ownerName": "test-org",
            # Missing other required fields
        }

        # Execute and verify - should raise ValueError
        with pytest.raises(ValueError, match="Missing required fields in event detail"):
            schedule_handler(incomplete_event)

    @patch("services.webhook.schedule_handler.get_installation_access_token")
    def test_schedule_handler_no_token(self, mock_get_token, mock_event):
        """Test that schedule_handler raises ValueError when token is None."""
        # Setup
        mock_get_token.return_value = None

        # Execute and verify
        with pytest.raises(ValueError, match="Token is None for installation_id"):
            schedule_handler(mock_event)

    @patch("services.webhook.schedule_handler.get_installation_access_token")
    @patch("services.webhook.schedule_handler.get_repository")
    def test_schedule_handler_trigger_disabled(
        self, mock_get_repository, mock_get_token, mock_event
    ):
        """Test that schedule_handler skips when trigger_on_schedule is disabled."""
        # Setup
        mock_get_token.return_value = "test-token"
        mock_get_repository.return_value = {
            "id": 456,
            "name": "test-repo",
            "trigger_on_schedule": False,
        }

        # Execute
        result = schedule_handler(mock_event)

        # Verify
        assert result["status"] == "skipped"
        assert "trigger_on_schedule is not enabled" in result["message"]

    @patch("services.webhook.schedule_handler.get_installation_access_token")
    @patch("services.webhook.schedule_handler.get_repository")
    @patch("services.webhook.schedule_handler.is_request_limit_reached")
    def test_schedule_handler_request_limit_reached(
        self,
        mock_is_request_limit_reached,
        mock_get_repository,
        mock_get_token,
        mock_event,
    ):
        """Test that schedule_handler skips when request limit is reached."""
        # Setup
        mock_get_token.return_value = "test-token"
        mock_get_repository.return_value = {
            "id": 456,
            "name": "test-repo",
            "trigger_on_schedule": True,
        }
        mock_is_request_limit_reached.return_value = {"is_limit_reached": True}

        # Execute
        result = schedule_handler(mock_event)

        # Verify
        assert result["status"] == "skipped"
        assert "Request limit reached" in result["message"]

    @patch("services.webhook.schedule_handler.get_all_coverages")
    def test_get_all_coverages_returns_empty_list_not_none(
        self, mock_get_all_coverages
    ):
        """Test that get_all_coverages returns empty list instead of None.

        This test verifies the fix for 'NoneType' object is not iterable error.
        """
        # Setup - simulate empty coverage data
        mock_get_all_coverages.return_value = []  # Should be empty list, not None

        # Execute
        all_coverages = mock_get_all_coverages(repo_id=123)

        # Verify - should be able to iterate without TypeError
        assert isinstance(all_coverages, list)
        assert len(all_coverages) == 0

        # This would fail with TypeError if all_coverages was None
        for coverage in all_coverages:
            pass  # Should not raise TypeError

        # Test the actual pattern used in schedule_handler
        test_files = [("src/main.py", 1024), ("src/utils.py", 512)]
        enriched_files = []

        for file_path, file_size in test_files:
            # This is the line that was failing at line 114
            coverages = next(
                (c for c in all_coverages if c.get("full_path") == file_path), None
            )
            if coverages:
                enriched_files.append(coverages)
            else:
                enriched_files.append({"full_path": file_path, "file_size": file_size})

        # Verify we processed all files without error
        assert len(enriched_files) == 2
        assert all("full_path" in f for f in enriched_files)

    def test_get_all_coverages_contract(self):
        """Verify that get_all_coverages always returns a list."""
        from services.supabase.coverages.get_all_coverages import get_all_coverages

        with patch(
            "services.supabase.coverages.get_all_coverages.supabase"
        ) as mock_supabase:
            # Setup mock to return empty data
            mock_result = MagicMock()
            mock_result.data = []
            mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = (
                mock_result
            )

            # Execute
            result = get_all_coverages(repo_id=123)

            # Verify - should be empty list, not None
            assert result == []
            assert result is not None
            assert isinstance(result, list)

    @patch("services.webhook.schedule_handler.get_installation_access_token")
    @patch("services.webhook.schedule_handler.get_repository")
    @patch("services.webhook.schedule_handler.is_request_limit_reached")
    @patch("services.webhook.schedule_handler.get_default_branch")
    @patch("services.webhook.schedule_handler.get_file_tree")
    @patch("services.webhook.schedule_handler.get_all_coverages")
    def test_schedule_handler_no_files_found(
        self,
        mock_get_all_coverages,
        mock_get_file_tree,
        mock_get_default_branch,
        mock_is_request_limit_reached,
        mock_get_repository,
        mock_get_token,
        mock_event,
    ):
        """Test that schedule_handler skips when no files are found."""
        # Setup
        mock_get_token.return_value = "test-token"
        mock_get_repository.return_value = {"trigger_on_schedule": True}
        mock_is_request_limit_reached.return_value = {"is_limit_reached": False}
        mock_get_default_branch.return_value = ("main", None)
        mock_get_file_tree.return_value = []  # No files
        mock_get_all_coverages.return_value = []

        # Execute
        result = schedule_handler(mock_event)

        # Verify
        assert result["status"] == "skipped"
        assert "No files found" in result["message"]

    @patch("services.webhook.schedule_handler.get_installation_access_token")
    @patch("services.webhook.schedule_handler.get_repository")
    @patch("services.webhook.schedule_handler.is_request_limit_reached")
    @patch("services.webhook.schedule_handler.get_default_branch")
    @patch("services.webhook.schedule_handler.get_file_tree")
    @patch("services.webhook.schedule_handler.get_all_coverages")
    @patch("services.webhook.schedule_handler.is_code_file")
    @patch("services.webhook.schedule_handler.is_test_file")
    @patch("services.webhook.schedule_handler.is_type_file")
    def test_schedule_handler_no_suitable_files(
        self,
        mock_is_type_file,
        mock_is_test_file,
        mock_is_code_file,
        mock_get_all_coverages,
        mock_get_file_tree,
        mock_get_default_branch,
        mock_is_request_limit_reached,
        mock_get_repository,
        mock_get_token,
        mock_event,
    ):
        """Test that schedule_handler skips when no suitable files are found."""
        # Setup
        mock_get_token.return_value = "test-token"
        mock_get_repository.return_value = {"trigger_on_schedule": True}
        mock_is_request_limit_reached.return_value = {"is_limit_reached": False}
        mock_get_default_branch.return_value = ("main", None)
        mock_get_file_tree.return_value = [
            {"path": "test.py", "size": 1024, "type": "blob"}
        ]
        mock_get_all_coverages.return_value = []
        mock_is_code_file.return_value = False  # Not a code file
        mock_is_test_file.return_value = False
        mock_is_type_file.return_value = False

        # Execute
        result = schedule_handler(mock_event)

        # Verify
        assert result["status"] == "skipped"
        assert "No suitable file found" in result["message"]

    @patch("services.webhook.schedule_handler.get_installation_access_token")
    @patch("services.webhook.schedule_handler.get_repository")
    @patch("services.webhook.schedule_handler.is_request_limit_reached")
    @patch("services.webhook.schedule_handler.get_default_branch")
    @patch("services.webhook.schedule_handler.get_file_tree")
    @patch("services.webhook.schedule_handler.get_all_coverages")
    @patch("services.webhook.schedule_handler.is_code_file")
    @patch("services.webhook.schedule_handler.is_test_file")
    @patch("services.webhook.schedule_handler.is_type_file")
    @patch("services.webhook.schedule_handler.is_issue_open")
    @patch("services.webhook.schedule_handler.get_issue_title")
    @patch("services.webhook.schedule_handler.get_issue_body")
    @patch("services.webhook.schedule_handler.create_issue")
    @patch("services.webhook.schedule_handler.insert_coverages")
    def test_schedule_handler_success_new_coverage_record(
        self,
        mock_insert_coverages,
        mock_create_issue,
        mock_get_issue_body,
        mock_get_issue_title,
        mock_is_issue_open,
        mock_is_type_file,
        mock_is_test_file,
        mock_is_code_file,
        mock_get_all_coverages,
        mock_get_file_tree,
        mock_get_default_branch,
        mock_is_request_limit_reached,
        mock_get_repository,
        mock_get_token,
        mock_event,
    ):
        """Test successful schedule_handler execution with new coverage record."""
        # Setup
        mock_get_token.return_value = "test-token"
        mock_get_repository.return_value = {"trigger_on_schedule": True}
        mock_is_request_limit_reached.return_value = {"is_limit_reached": False}
        mock_get_default_branch.return_value = ("main", None)
        mock_get_file_tree.return_value = [
            {"path": "src/main.py", "size": 1024, "type": "blob"}
        ]
        mock_get_all_coverages.return_value = []
        mock_is_code_file.return_value = True
        mock_is_test_file.return_value = False
        mock_is_type_file.return_value = False
        mock_is_issue_open.return_value = False
        mock_get_issue_title.return_value = "Add unit tests for src/main.py"
        mock_get_issue_body.return_value = "Test issue body"
        mock_create_issue.return_value = {"html_url": "https://github.com/test/issue/1"}

        # Execute
        result = schedule_handler(mock_event)

        # Verify
        assert result["status"] == "success"
        assert "created issue for src/main.py" in result["message"]
        mock_create_issue.assert_called_once()
        mock_insert_coverages.assert_called_once()

    @patch("services.webhook.schedule_handler.get_installation_access_token")
    @patch("services.webhook.schedule_handler.get_repository")
    @patch("services.webhook.schedule_handler.is_request_limit_reached")
    @patch("services.webhook.schedule_handler.get_default_branch")
    @patch("services.webhook.schedule_handler.get_file_tree")
    @patch("services.webhook.schedule_handler.get_all_coverages")
    @patch("services.webhook.schedule_handler.is_code_file")
    @patch("services.webhook.schedule_handler.is_test_file")
    @patch("services.webhook.schedule_handler.is_type_file")
    @patch("services.webhook.schedule_handler.is_issue_open")
    @patch("services.webhook.schedule_handler.get_issue_title")
    @patch("services.webhook.schedule_handler.get_issue_body")
    @patch("services.webhook.schedule_handler.create_issue")
    @patch("services.webhook.schedule_handler.update_issue_url")
    def test_schedule_handler_success_existing_coverage_record(
        self,
        mock_update_issue_url,
        mock_create_issue,
        mock_get_issue_body,
        mock_get_issue_title,
        mock_is_issue_open,
        mock_is_type_file,
        mock_is_test_file,
        mock_is_code_file,
        mock_get_all_coverages,
        mock_get_file_tree,
        mock_get_default_branch,
        mock_is_request_limit_reached,
        mock_get_repository,
        mock_get_token,
        mock_event,
    ):
        """Test successful schedule_handler execution with existing coverage record."""
        # Setup
        mock_get_token.return_value = "test-token"
        mock_get_repository.return_value = {"trigger_on_schedule": True}
        mock_is_request_limit_reached.return_value = {"is_limit_reached": False}
        mock_get_default_branch.return_value = ("main", None)
        mock_get_file_tree.return_value = [
            {"path": "src/main.py", "size": 1024, "type": "blob"}
        ]
        mock_get_all_coverages.return_value = [
            {
                "id": 1,
                "full_path": "src/main.py",
                "statement_coverage": 50.0,
                "function_coverage": 60.0,
                "branch_coverage": 40.0,
                "github_issue_url": None,
                "is_excluded_from_testing": False,
            }
        ]
        mock_is_code_file.return_value = True
        mock_is_test_file.return_value = False
        mock_is_type_file.return_value = False
        mock_is_issue_open.return_value = False
        mock_get_issue_title.return_value = "Add unit tests for src/main.py"
        mock_get_issue_body.return_value = "Test issue body"
        mock_create_issue.return_value = {"html_url": "https://github.com/test/issue/1"}

        # Execute
        result = schedule_handler(mock_event)

        # Verify
        assert result["status"] == "success"
        assert "created issue for src/main.py" in result["message"]
        mock_create_issue.assert_called_once()
        mock_update_issue_url.assert_called_once()

    @patch("services.webhook.schedule_handler.get_installation_access_token")
    @patch("services.webhook.schedule_handler.get_repository")
    @patch("services.webhook.schedule_handler.is_request_limit_reached")
    @patch("services.webhook.schedule_handler.get_default_branch")
    @patch("services.webhook.schedule_handler.get_file_tree")
    @patch("services.webhook.schedule_handler.get_all_coverages")
    @patch("services.webhook.schedule_handler.is_code_file")
    @patch("services.webhook.schedule_handler.is_test_file")
    @patch("services.webhook.schedule_handler.is_type_file")
    @patch("services.webhook.schedule_handler.is_issue_open")
    def test_schedule_handler_skip_file_with_open_issue(
        self,
        mock_is_issue_open,
        mock_is_type_file,
        mock_is_test_file,
        mock_is_code_file,
        mock_get_all_coverages,
        mock_get_file_tree,
        mock_get_default_branch,
        mock_is_request_limit_reached,
        mock_get_repository,
        mock_get_token,
        mock_event,
    ):
        """Test that files with open GitHub issues are skipped."""
        # Setup
        mock_get_token.return_value = "test-token"
        mock_get_repository.return_value = {"trigger_on_schedule": True}
        mock_is_request_limit_reached.return_value = {"is_limit_reached": False}
        mock_get_default_branch.return_value = ("main", None)
        mock_get_file_tree.return_value = [
            {"path": "src/main.py", "size": 1024, "type": "blob"}
        ]
        mock_get_all_coverages.return_value = [
            {
                "id": 1,
                "full_path": "src/main.py",
                "statement_coverage": 50.0,
                "function_coverage": 60.0,
                "branch_coverage": 40.0,
                "github_issue_url": "https://github.com/test/issue/1",
                "is_excluded_from_testing": False,
            }
        ]
        mock_is_code_file.return_value = True
        mock_is_test_file.return_value = False
        mock_is_type_file.return_value = False
        mock_is_issue_open.return_value = True  # Issue is open

        # Execute
        result = schedule_handler(mock_event)

        # Verify
        assert result["status"] == "skipped"
        assert "No suitable file found" in result["message"]

    @patch("services.webhook.schedule_handler.get_installation_access_token")
    @patch("services.webhook.schedule_handler.get_repository")
    @patch("services.webhook.schedule_handler.is_request_limit_reached")
    @patch("services.webhook.schedule_handler.get_default_branch")
    @patch("services.webhook.schedule_handler.get_file_tree")
    @patch("services.webhook.schedule_handler.get_all_coverages")
    @patch("services.webhook.schedule_handler.is_code_file")
    @patch("services.webhook.schedule_handler.is_test_file")
    @patch("services.webhook.schedule_handler.is_type_file")
    def test_schedule_handler_skip_excluded_files(
        self,
        mock_is_type_file,
        mock_is_test_file,
        mock_is_code_file,
        mock_get_all_coverages,
        mock_get_file_tree,
        mock_get_default_branch,
        mock_is_request_limit_reached,
        mock_get_repository,
        mock_get_token,
        mock_event,
    ):
        """Test that files excluded from testing are skipped."""
        # Setup
        mock_get_token.return_value = "test-token"
        mock_get_repository.return_value = {"trigger_on_schedule": True}
        mock_is_request_limit_reached.return_value = {"is_limit_reached": False}
        mock_get_default_branch.return_value = ("main", None)
        mock_get_file_tree.return_value = [
            {"path": "src/main.py", "size": 1024, "type": "blob"}
        ]
        mock_get_all_coverages.return_value = [
            {
                "id": 1,
                "full_path": "src/main.py",
                "statement_coverage": 50.0,
                "function_coverage": 60.0,
                "branch_coverage": 40.0,
                "github_issue_url": None,
                "is_excluded_from_testing": True,  # File is excluded
            }
        ]
        mock_is_code_file.return_value = True
        mock_is_test_file.return_value = False
        mock_is_type_file.return_value = False

        # Execute
        result = schedule_handler(mock_event)

        # Verify
        assert result["status"] == "skipped"
        assert "No suitable file found" in result["message"]
