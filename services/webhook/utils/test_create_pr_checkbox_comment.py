# pylint: disable=redefined-outer-name
"""Unit tests for create_pr_checkbox_comment.py"""

from datetime import datetime
from typing import cast
from unittest.mock import patch

import pytest
from schemas.supabase.types import Repositories
from services.github.pulls.get_pull_request_files import FileChange
from services.github.types.installation import Installation
from services.github.types.organization import Organization
from services.github.types.pull_request import PullRequest
from services.github.types.pull_request_webhook_payload import \
    PullRequestWebhookPayload
from services.github.types.ref import Ref
from services.github.types.repository import Repository
from services.github.types.user import User
from services.webhook.utils.create_pr_checkbox_comment import \
    create_pr_checkbox_comment
from utils.text.comment_identifiers import TEST_SELECTION_COMMENT_IDENTIFIER


class TestCreatePrCheckboxComment:
    """Test cases for create_pr_checkbox_comment function."""

    def create_minimal_payload(self, sender_login: str = "testuser") -> PullRequestWebhookPayload:
        """Create a minimal payload for testing."""
        return cast(PullRequestWebhookPayload, {
            "action": "opened",
            "number": 1,
            "pull_request": cast(PullRequest, {
                "url": "https://api.github.com/repos/testowner/testrepo/pulls/1",
                "id": 1,
                "node_id": "PR_kgDOABCDEF",
                "number": 1,
                "head": cast(Ref, {
                    "label": "testowner:feature-branch",
                    "ref": "feature-branch",
                    "sha": "def456",
                    "user": cast(User, {"login": "testuser", "id": 123}),
                    "repo": cast(Repository, {"id": 789, "name": "testrepo"}),
                }),
                "base": cast(Ref, {
                    "label": "testowner:main",
                    "ref": "main",
                    "sha": "abc123",
                    "user": cast(User, {"login": "testuser", "id": 123}),
                    "repo": cast(Repository, {"id": 789, "name": "testrepo"}),
                }),
            }),
            "repository": cast(Repository, {
                "id": 789,
                "name": "testrepo",
                "owner": cast(User, {"login": "testowner", "id": 456}),
            }),
            "organization": cast(Organization, {
                "login": "testowner",
                "id": 456,
                "node_id": "O_kgDOABCDEF",
                "url": "https://api.github.com/orgs/testowner",
                "repos_url": "https://api.github.com/orgs/testowner/repos",
                "events_url": "https://api.github.com/orgs/testowner/events",
                "hooks_url": "https://api.github.com/orgs/testowner/hooks",
                "issues_url": "https://api.github.com/orgs/testowner/issues",
                "members_url": "https://api.github.com/orgs/testowner/members{/member}",
                "public_members_url": "https://api.github.com/orgs/testowner/public_members{/member}",
                "avatar_url": "https://avatars.githubusercontent.com/u/456?v=4",
                "description": "Test organization",
            }),
            "sender": cast(User, {"login": sender_login, "id": 123}),
            "installation": cast(Installation, {"id": 12345, "node_id": "I_kgDOABCDEF"}),
        })

    def create_repository_settings(self, trigger_on_pr_change: bool = True) -> Repositories:
        """Create repository settings for testing."""
        return cast(Repositories, {
            "id": 1,
            "owner_id": 456,
            "repo_id": 789,
            "repo_name": "testrepo",
            "created_at": datetime.now(),
            "created_by": "testuser",
            "updated_at": datetime.now(),
            "updated_by": "testuser",
            "use_screenshots": False,
            "production_url": None,
            "local_port": None,
            "startup_commands": None,
            "web_urls": None,
            "file_paths": None,
            "repo_rules": None,
            "file_count": 100,
            "blank_lines": 10,
            "comment_lines": 20,
            "code_lines": 70,
            "target_branch": "main",
            "trigger_on_review_comment": True,
            "trigger_on_test_failure": True,
            "trigger_on_commit": True,
            "trigger_on_merged": True,
            "trigger_on_schedule": False,
            "schedule_frequency": None,
            "schedule_minute": None,
            "schedule_time": None,
            "schedule_day_of_week": None,
            "schedule_include_weekends": False,
            "structured_rules": None,
            "trigger_on_pr_change": trigger_on_pr_change,
            "schedule_execution_count": 0,
            "schedule_interval_minutes": 60,
        })

    def create_file_change(self, filename: str, status: str = "modified") -> FileChange:
        """Create a file change for testing."""
        return {"filename": filename, "status": status}

    def test_skips_bot_sender(self):
        """Test that the function skips processing when sender is a bot."""
        payload = self.create_minimal_payload(sender_login="dependabot[bot]")

        with patch("services.webhook.utils.create_pr_checkbox_comment.logging") as mock_logging:
            result = create_pr_checkbox_comment(payload)

            assert result is None
            mock_logging.info.assert_called_once_with("Skipping PR test selection for bot dependabot[bot]")

    def test_skips_when_repository_not_found(self):
        """Test that the function skips processing when repository is not found."""
        payload = self.create_minimal_payload()

        with patch("services.webhook.utils.create_pr_checkbox_comment.get_repository") as mock_get_repo, \
             patch("services.webhook.utils.create_pr_checkbox_comment.logging") as mock_logging:
            mock_get_repo.return_value = None

            result = create_pr_checkbox_comment(payload)

            assert result is None
            mock_logging.info.assert_called_once_with(
                "Skipping PR test selection for repo testrepo because trigger_on_pr_change is False"
            )

    def test_skips_when_trigger_on_pr_change_is_false(self):
        """Test that the function skips processing when trigger_on_pr_change is False."""
        payload = self.create_minimal_payload()

        with patch("services.webhook.utils.create_pr_checkbox_comment.get_repository") as mock_get_repo, \
             patch("services.webhook.utils.create_pr_checkbox_comment.logging") as mock_logging:
            mock_get_repo.return_value = self.create_repository_settings(trigger_on_pr_change=False)

            result = create_pr_checkbox_comment(payload)

            assert result is None
            mock_logging.info.assert_called_once_with(
                "Skipping PR test selection for repo testrepo because trigger_on_pr_change is False"
            )

    def test_skips_when_no_code_files_changed(self):
        """Test that the function skips processing when no code files are changed."""
        payload = self.create_minimal_payload()

        with patch("services.webhook.utils.create_pr_checkbox_comment.get_repository") as mock_get_repo, \
             patch("services.webhook.utils.create_pr_checkbox_comment.get_installation_access_token") as mock_get_token, \
             patch("services.webhook.utils.create_pr_checkbox_comment.get_pull_request_files") as mock_get_files, \
             patch("services.webhook.utils.create_pr_checkbox_comment.is_code_file") as mock_is_code, \
             patch("services.webhook.utils.create_pr_checkbox_comment.is_test_file") as mock_is_test, \
             patch("services.webhook.utils.create_pr_checkbox_comment.is_type_file") as mock_is_type, \
             patch("services.webhook.utils.create_pr_checkbox_comment.logging") as mock_logging:

            mock_get_repo.return_value = self.create_repository_settings()
            mock_get_token.return_value = "test_token"
            mock_get_files.return_value = [
                self.create_file_change("test_file.py", "modified"),
                self.create_file_change("types.py", "added"),
            ]
            mock_is_code.side_effect = [True, True]  # Both are code files
            mock_is_test.side_effect = [True, False]  # First is test file
            mock_is_type.side_effect = [False, True]  # Second is type file

            result = create_pr_checkbox_comment(payload)

            assert result is None
            mock_logging.info.assert_called_once_with(
                "Skipping PR test selection for repo testrepo because no code files were changed"
            )

    def test_successful_comment_creation(self):
        """Test successful comment creation with valid code files."""
        payload = self.create_minimal_payload()

        with patch("services.webhook.utils.create_pr_checkbox_comment.get_repository") as mock_get_repo, \
             patch("services.webhook.utils.create_pr_checkbox_comment.get_installation_access_token") as mock_get_token, \
             patch("services.webhook.utils.create_pr_checkbox_comment.get_pull_request_files") as mock_get_files, \
             patch("services.webhook.utils.create_pr_checkbox_comment.is_code_file") as mock_is_code, \
             patch("services.webhook.utils.create_pr_checkbox_comment.is_test_file") as mock_is_test, \
             patch("services.webhook.utils.create_pr_checkbox_comment.is_type_file") as mock_is_type, \
             patch("services.webhook.utils.create_pr_checkbox_comment.get_coverages") as mock_get_cov, \
             patch("services.webhook.utils.create_pr_checkbox_comment.create_file_checklist") as mock_checklist, \
             patch("services.webhook.utils.create_pr_checkbox_comment.create_test_selection_comment") as mock_comment, \
             patch("services.webhook.utils.create_pr_checkbox_comment.delete_comments_by_identifiers") as mock_delete, \
             patch("services.webhook.utils.create_pr_checkbox_comment.combine_and_create_comment") as mock_create:

            mock_get_repo.return_value = self.create_repository_settings()
            mock_get_token.return_value = "test_token"
            mock_get_files.return_value = [self.create_file_change("src/main.py", "modified")]
            mock_is_code.return_value = True
            mock_is_test.return_value = False
            mock_is_type.return_value = False
            mock_get_cov.return_value = {}
            mock_checklist.return_value = []
            mock_comment.return_value = "Test selection comment"

            result = create_pr_checkbox_comment(payload)

            assert result is None
            mock_get_repo.assert_called_once_with(repo_id=789)
            mock_get_token.assert_called_once_with(installation_id=12345)
            mock_get_files.assert_called_once()
            mock_get_cov.assert_called_once()
            mock_checklist.assert_called_once()
            mock_comment.assert_called_once()
            mock_delete.assert_called_once()
            mock_create.assert_called_once()

    def test_handles_different_bot_names(self):
        """Test that different bot names are properly detected and skipped."""
        bot_names = ["dependabot[bot]", "renovate[bot]", "github-actions[bot]"]

        for bot_name in bot_names:
            payload = self.create_minimal_payload(sender_login=bot_name)

            with patch("services.webhook.utils.create_pr_checkbox_comment.logging") as mock_logging:
                result = create_pr_checkbox_comment(payload)

                assert result is None
                mock_logging.info.assert_called_once_with(f"Skipping PR test selection for bot {bot_name}")

    def test_error_handling_with_handle_exceptions_decorator(self):
        """Test that the @handle_exceptions decorator works correctly."""
        payload = self.create_minimal_payload()

        with patch("services.webhook.utils.create_pr_checkbox_comment.get_repository") as mock_get_repo:
            mock_get_repo.side_effect = Exception("Database error")

            result = create_pr_checkbox_comment(payload)

            assert result is None
            mock_get_repo.assert_called_once_with(repo_id=789)

    def test_handles_empty_file_changes_list(self):
        """Test handling when get_pull_request_files returns empty list."""
        payload = self.create_minimal_payload()

        with patch("services.webhook.utils.create_pr_checkbox_comment.get_repository") as mock_get_repo, \
             patch("services.webhook.utils.create_pr_checkbox_comment.get_installation_access_token") as mock_get_token, \
             patch("services.webhook.utils.create_pr_checkbox_comment.get_pull_request_files") as mock_get_files, \
             patch("services.webhook.utils.create_pr_checkbox_comment.logging") as mock_logging:

            mock_get_repo.return_value = self.create_repository_settings()
            mock_get_token.return_value = "test_token"
            mock_get_files.return_value = []  # Empty list

            result = create_pr_checkbox_comment(payload)

            assert result is None
            mock_logging.info.assert_called_once_with(
                "Skipping PR test selection for repo testrepo because no code files were changed"
            )

    def test_extracts_correct_branch_name(self):
        """Test that the correct branch name is extracted from the PR head ref."""
        payload = self.create_minimal_payload()
        # Modify the head ref to have a different branch name
        payload["pull_request"]["head"]["ref"] = "feature/new-feature"

        with patch("services.webhook.utils.create_pr_checkbox_comment.get_repository") as mock_get_repo, \
             patch("services.webhook.utils.create_pr_checkbox_comment.get_installation_access_token") as mock_get_token, \
             patch("services.webhook.utils.create_pr_checkbox_comment.get_pull_request_files") as mock_get_files, \
             patch("services.webhook.utils.create_pr_checkbox_comment.is_code_file") as mock_is_code, \
             patch("services.webhook.utils.create_pr_checkbox_comment.is_test_file") as mock_is_test, \
             patch("services.webhook.utils.create_pr_checkbox_comment.is_type_file") as mock_is_type, \
             patch("services.webhook.utils.create_pr_checkbox_comment.get_coverages") as mock_get_cov, \
             patch("services.webhook.utils.create_pr_checkbox_comment.create_file_checklist") as mock_checklist, \
             patch("services.webhook.utils.create_pr_checkbox_comment.create_test_selection_comment") as mock_comment, \
             patch("services.webhook.utils.create_pr_checkbox_comment.delete_comments_by_identifiers") as mock_delete, \
             patch("services.webhook.utils.create_pr_checkbox_comment.combine_and_create_comment") as mock_create:

            mock_get_repo.return_value = self.create_repository_settings()
            mock_get_token.return_value = "test_token"
            mock_get_files.return_value = [self.create_file_change("src/main.py", "modified")]
            mock_is_code.return_value = True
            mock_is_test.return_value = False
            mock_is_type.return_value = False
            mock_get_cov.return_value = {}
            mock_checklist.return_value = []
            mock_comment.return_value = "Test selection comment"

            create_pr_checkbox_comment(payload)

            mock_comment.assert_called_once_with([], "feature/new-feature")

    def test_delete_comments_called_with_correct_args(self):
        """Test that delete_comments_by_identifiers is called with correct arguments."""
        payload = self.create_minimal_payload()

        with patch("services.webhook.utils.create_pr_checkbox_comment.get_repository") as mock_get_repo, \
             patch("services.webhook.utils.create_pr_checkbox_comment.get_installation_access_token") as mock_get_token, \
             patch("services.webhook.utils.create_pr_checkbox_comment.get_pull_request_files") as mock_get_files, \
             patch("services.webhook.utils.create_pr_checkbox_comment.is_code_file") as mock_is_code, \
             patch("services.webhook.utils.create_pr_checkbox_comment.is_test_file") as mock_is_test, \
             patch("services.webhook.utils.create_pr_checkbox_comment.is_type_file") as mock_is_type, \
             patch("services.webhook.utils.create_pr_checkbox_comment.get_coverages") as mock_get_cov, \
             patch("services.webhook.utils.create_pr_checkbox_comment.create_file_checklist") as mock_checklist, \
             patch("services.webhook.utils.create_pr_checkbox_comment.create_test_selection_comment") as mock_comment, \
             patch("services.webhook.utils.create_pr_checkbox_comment.delete_comments_by_identifiers") as mock_delete, \
             patch("services.webhook.utils.create_pr_checkbox_comment.combine_and_create_comment") as mock_create:

            mock_get_repo.return_value = self.create_repository_settings()
            mock_get_token.return_value = "test_token"
            mock_get_files.return_value = [self.create_file_change("src/main.py", "modified")]
            mock_is_code.return_value = True
            mock_is_test.return_value = False
            mock_is_type.return_value = False
            mock_get_cov.return_value = {}
            mock_checklist.return_value = []
            mock_comment.return_value = "Test selection comment"

            create_pr_checkbox_comment(payload)

            expected_base_args = {
                "owner": "testowner",
                "repo": "testrepo",
                "issue_number": 1,
                "token": "test_token",
            }
            mock_delete.assert_called_once_with(
                base_args=expected_base_args,
                identifiers=[TEST_SELECTION_COMMENT_IDENTIFIER]
            )

    def test_combine_and_create_comment_called_with_correct_args(self):
        """Test that combine_and_create_comment is called with correct arguments."""
        payload = self.create_minimal_payload()

        with patch("services.webhook.utils.create_pr_checkbox_comment.get_repository") as mock_get_repo, \
             patch("services.webhook.utils.create_pr_checkbox_comment.get_installation_access_token") as mock_get_token, \
             patch("services.webhook.utils.create_pr_checkbox_comment.get_pull_request_files") as mock_get_files, \
             patch("services.webhook.utils.create_pr_checkbox_comment.is_code_file") as mock_is_code, \
             patch("services.webhook.utils.create_pr_checkbox_comment.is_test_file") as mock_is_test, \
             patch("services.webhook.utils.create_pr_checkbox_comment.is_type_file") as mock_is_type, \
             patch("services.webhook.utils.create_pr_checkbox_comment.get_coverages") as mock_get_cov, \
             patch("services.webhook.utils.create_pr_checkbox_comment.create_file_checklist") as mock_checklist, \
             patch("services.webhook.utils.create_pr_checkbox_comment.create_test_selection_comment") as mock_comment, \
             patch("services.webhook.utils.create_pr_checkbox_comment.delete_comments_by_identifiers") as mock_delete, \
             patch("services.webhook.utils.create_pr_checkbox_comment.combine_and_create_comment") as mock_create:

            mock_get_repo.return_value = self.create_repository_settings()
            mock_get_token.return_value = "test_token"
            mock_get_files.return_value = [self.create_file_change("src/main.py", "modified")]
            mock_is_code.return_value = True
            mock_is_test.return_value = False
            mock_is_type.return_value = False
            mock_get_cov.return_value = {}
            mock_checklist.return_value = []
            mock_comment.return_value = "Test selection comment"

            create_pr_checkbox_comment(payload)

            expected_base_args = {
                "owner": "testowner",
                "repo": "testrepo",
                "issue_number": 1,
                "token": "test_token",
            }
            mock_create.assert_called_once_with(
                base_comment="Test selection comment",
                installation_id=12345,
                owner_id=456,
                owner_name="testowner",
                sender_name="testuser",
                base_args=expected_base_args,
            )

    def test_handles_mixed_file_types(self):
        """Test handling of mixed file types (code, test, type files)."""
        payload = self.create_minimal_payload()

        with patch("services.webhook.utils.create_pr_checkbox_comment.get_repository") as mock_get_repo, \
             patch("services.webhook.utils.create_pr_checkbox_comment.get_installation_access_token") as mock_get_token, \
             patch("services.webhook.utils.create_pr_checkbox_comment.get_pull_request_files") as mock_get_files, \
             patch("services.webhook.utils.create_pr_checkbox_comment.is_code_file") as mock_is_code, \
             patch("services.webhook.utils.create_pr_checkbox_comment.is_test_file") as mock_is_test, \
             patch("services.webhook.utils.create_pr_checkbox_comment.is_type_file") as mock_is_type, \
             patch("services.webhook.utils.create_pr_checkbox_comment.get_coverages") as mock_get_cov, \
             patch("services.webhook.utils.create_pr_checkbox_comment.logging") as mock_logging:
