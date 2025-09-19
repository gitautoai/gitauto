# pylint: disable=redefined-outer-name
"""Unit tests for create_pr_checkbox_comment.py"""

from unittest.mock import patch, MagicMock
from datetime import datetime
from typing import cast
import pytest
import logging

from schemas.supabase.types import Repositories, Coverages
from services.github.types.pull_request_webhook_payload import PullRequestWebhookPayload
from services.github.types.pull_request import PullRequest
from services.github.types.repository import Repository
from services.github.types.user import User
from services.github.types.owner import Owner
from services.github.types.installation import Installation
from services.github.types.ref import Ref
from services.github.pulls.get_pull_request_files import FileChange
from services.webhook.utils.create_pr_checkbox_comment import create_pr_checkbox_comment
from utils.text.comment_identifiers import TEST_SELECTION_COMMENT_IDENTIFIER


def create_user(login: str = "testuser", user_id: int = 123) -> User:
    """Helper function to create a User object."""
    return cast(User, {
        "login": login,
        "id": user_id,
        "node_id": "U_kgDOABCDEF",
        "avatar_url": "https://avatars.githubusercontent.com/u/123?v=4",
        "gravatar_id": "",
        "url": "https://api.github.com/users/testuser",
        "html_url": "https://github.com/testuser",
        "followers_url": "https://api.github.com/users/testuser/followers",
        "following_url": "https://api.github.com/users/testuser/following{/other_user}",
        "gists_url": "https://api.github.com/users/testuser/gists{/gist_id}",
        "starred_url": "https://api.github.com/users/testuser/starred{/owner}{/repo}",
        "subscriptions_url": "https://api.github.com/users/testuser/subscriptions",
        "organizations_url": "https://api.github.com/users/testuser/orgs",
        "repos_url": "https://api.github.com/users/testuser/repos",
        "events_url": "https://api.github.com/users/testuser/events{/privacy}",
        "received_events_url": "https://api.github.com/users/testuser/received_events",
        "type": "User",
        "site_admin": False,
    })


def create_owner(login: str = "testowner", owner_id: int = 456) -> Owner:
    """Helper function to create an Owner object."""
    return cast(Owner, {
        "login": login,
        "id": owner_id,
        "type": "Organization",
        "node_id": "O_kgDOABCDEF",
        "avatar_url": "https://avatars.githubusercontent.com/u/456?v=4",
        "gravatar_id": "",
        "url": "https://api.github.com/users/testowner",
        "html_url": "https://github.com/testowner",
        "followers_url": "https://api.github.com/users/testowner/followers",
        "following_url": "https://api.github.com/users/testowner/following{/other_user}",
        "gists_url": "https://api.github.com/users/testowner/gists{/gist_id}",
        "starred_url": "https://api.github.com/users/testowner/starred{/owner}{/repo}",
        "subscriptions_url": "https://api.github.com/users/testowner/subscriptions",
        "organizations_url": "https://api.github.com/users/testowner/orgs",
        "repos_url": "https://api.github.com/users/testowner/repos",
        "events_url": "https://api.github.com/users/testowner/events{/privacy}",
        "received_events_url": "https://api.github.com/users/testowner/received_events",
        "user_view_type": "public",
        "site_admin": False,
    })


def create_ref(ref: str = "main", sha: str = "abc123") -> Ref:
    """Helper function to create a Ref object."""
    return cast(Ref, {
        "label": f"testowner:{ref}",
        "ref": ref,
        "sha": sha,
        "user": create_user(),
        "repo": create_repository(),
    })


def create_repository(repo_id: int = 789, name: str = "testrepo") -> Repository:
    """Helper function to create a Repository object."""
    return cast(Repository, {
        "id": repo_id,
        "node_id": "R_kgDOABCDEF",
        "name": name,
        "full_name": f"testowner/{name}",
        "private": False,
        "owner": create_owner(),
        "html_url": f"https://github.com/testowner/{name}",
        "description": "Test repository",
        "fork": False,
        "url": f"https://api.github.com/repos/testowner/{name}",
        "forks_url": f"https://api.github.com/repos/testowner/{name}/forks",
        "keys_url": f"https://api.github.com/repos/testowner/{name}/keys{{/key_id}}",
        "collaborators_url": f"https://api.github.com/repos/testowner/{name}/collaborators{{/collaborator}}",
        "teams_url": f"https://api.github.com/repos/testowner/{name}/teams",
        "hooks_url": f"https://api.github.com/repos/testowner/{name}/hooks",
        "issue_events_url": f"https://api.github.com/repos/testowner/{name}/issues/events{{/number}}",
        "events_url": f"https://api.github.com/repos/testowner/{name}/events",
        "assignees_url": f"https://api.github.com/repos/testowner/{name}/assignees{{/user}}",
        "branches_url": f"https://api.github.com/repos/testowner/{name}/branches{{/branch}}",
        "tags_url": f"https://api.github.com/repos/testowner/{name}/tags",
        "blobs_url": f"https://api.github.com/repos/testowner/{name}/git/blobs{{/sha}}",
        "git_tags_url": f"https://api.github.com/repos/testowner/{name}/git/tags{{/sha}}",
        "git_refs_url": f"https://api.github.com/repos/testowner/{name}/git/refs{{/sha}}",
        "trees_url": f"https://api.github.com/repos/testowner/{name}/git/trees{{/sha}}",
        "statuses_url": f"https://api.github.com/repos/testowner/{name}/statuses/{{sha}}",
        "languages_url": f"https://api.github.com/repos/testowner/{name}/languages",
        "stargazers_url": f"https://api.github.com/repos/testowner/{name}/stargazers",
        "contributors_url": f"https://api.github.com/repos/testowner/{name}/contributors",
        "subscribers_url": f"https://api.github.com/repos/testowner/{name}/subscribers",
        "subscription_url": f"https://api.github.com/repos/testowner/{name}/subscription",
        "commits_url": f"https://api.github.com/repos/testowner/{name}/commits{{/sha}}",
        "git_commits_url": f"https://api.github.com/repos/testowner/{name}/git/commits{{/sha}}",
        "comments_url": f"https://api.github.com/repos/testowner/{name}/comments{{/number}}",
        "issue_comment_url": f"https://api.github.com/repos/testowner/{name}/issues/comments{{/number}}",
        "contents_url": f"https://api.github.com/repos/testowner/{name}/contents/{{+path}}",
        "compare_url": f"https://api.github.com/repos/testowner/{name}/compare/{{base}}...{{head}}",
        "merges_url": f"https://api.github.com/repos/testowner/{name}/merges",
        "archive_url": f"https://api.github.com/repos/testowner/{name}/{{archive_format}}{{/ref}}",
        "downloads_url": f"https://api.github.com/repos/testowner/{name}/downloads",
        "issues_url": f"https://api.github.com/repos/testowner/{name}/issues{{/number}}",
        "pulls_url": f"https://api.github.com/repos/testowner/{name}/pulls{{/number}}",
        "milestones_url": f"https://api.github.com/repos/testowner/{name}/milestones{{/number}}",
        "notifications_url": f"https://api.github.com/repos/testowner/{name}/notifications{{?since,all,participating}}",
        "labels_url": f"https://api.github.com/repos/testowner/{name}/labels{{/name}}",
        "releases_url": f"https://api.github.com/repos/testowner/{name}/releases{{/id}}",
        "deployments_url": f"https://api.github.com/repos/testowner/{name}/deployments",
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:00Z",
        "pushed_at": "2023-01-01T00:00:00Z",
        "git_url": f"git://github.com/testowner/{name}.git",
        "ssh_url": f"git@github.com:testowner/{name}.git",
        "clone_url": f"https://github.com/testowner/{name}.git",
        "svn_url": f"https://github.com/testowner/{name}",
        "homepage": None,
        "size": 1000,
        "stargazers_count": 0,
        "watchers_count": 0,
        "language": "Python",
        "has_issues": True,
        "has_projects": True,
        "has_downloads": True,
        "has_wiki": True,
        "has_pages": False,
        "has_discussions": False,
        "forks_count": 0,
        "mirror_url": None,
        "archived": False,
        "disabled": False,
        "open_issues_count": 0,
        "license": None,
        "allow_forking": True,
        "is_template": False,
        "web_commit_signoff_required": False,
        "topics": [],
        "visibility": "public",
        "forks": 0,
        "open_issues": 0,
        "watchers": 0,
        "default_branch": "main",
        "custom_properties": {},
    })


def create_pull_request(number: int = 1, url: str = "https://api.github.com/repos/testowner/testrepo/pulls/1") -> PullRequest:
    """Helper function to create a PullRequest object."""
    return cast(PullRequest, {
        "url": url,
        "id": 1,
        "node_id": "PR_kgDOABCDEF",
        "number": number,
        "head": create_ref("feature-branch", "def456"),
        "base": create_ref("main", "abc123"),
        "html_url": f"https://github.com/testowner/testrepo/pull/{number}",
        "diff_url": f"https://github.com/testowner/testrepo/pull/{number}.diff",
        "patch_url": f"https://github.com/testowner/testrepo/pull/{number}.patch",
        "issue_url": f"https://api.github.com/repos/testowner/testrepo/issues/{number}",
        "state": "open",
        "locked": False,
        "title": "Test PR",
        "user": create_user(),
        "body": "Test PR body",
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:00Z",
        "closed_at": None,
        "merged_at": None,
        "merge_commit_sha": None,
        "assignee": None,
        "assignees": [],
        "requested_reviewers": [],
        "requested_teams": [],
        "labels": [],
        "milestone": None,
        "draft": False,
        "commits_url": f"https://api.github.com/repos/testowner/testrepo/pulls/{number}/commits",
        "review_comments_url": f"https://api.github.com/repos/testowner/testrepo/pulls/{number}/comments",
        "review_comment_url": f"https://api.github.com/repos/testowner/testrepo/pulls/comments{{/number}}",
        "comments_url": f"https://api.github.com/repos/testowner/testrepo/issues/{number}/comments",
        "statuses_url": f"https://api.github.com/repos/testowner/testrepo/statuses/def456",
        "_links": {},
        "author_association": "OWNER",
        "auto_merge": None,
        "active_lock_reason": None,
        "merged": False,
        "mergeable": True,
        "rebaseable": True,
        "mergeable_state": "clean",
        "merged_by": None,
        "comments": 0,
        "review_comments": 0,
        "maintainer_can_modify": True,
        "commits": 1,
        "additions": 10,
        "deletions": 5,
        "changed_files": 2,
    })


def create_installation(installation_id: int = 12345) -> Installation:
    """Helper function to create an Installation object."""
    return cast(Installation, {
        "id": installation_id,
        "node_id": "I_kgDOABCDEF",
    })


def create_payload(
    sender_login: str = "testuser",
    repo_id: int = 789,
    repo_name: str = "testrepo",
    owner_id: int = 456,
    owner_login: str = "testowner",
    pull_number: int = 1,
    installation_id: int = 12345,
    **overrides
) -> PullRequestWebhookPayload:
    """Helper function to create a PullRequestWebhookPayload."""
    base_payload = {
        "action": "opened",
        "number": pull_number,
        "pull_request": create_pull_request(pull_number),
        "repository": create_repository(repo_id, repo_name),
        "organization": create_owner(owner_login, owner_id),
        "sender": create_user(sender_login),
        "installation": create_installation(installation_id),
    }
    base_payload.update(overrides)
    return cast(PullRequestWebhookPayload, base_payload)


def create_file_change(filename: str, status: str = "modified") -> FileChange:
    """Helper function to create a FileChange object."""
    return {"filename": filename, "status": status}


def create_repository_settings(
    repo_id: int = 789,
    trigger_on_pr_change: bool = True,
    **overrides
) -> Repositories:
    """Helper function to create repository settings."""
    base_settings = {
        "id": 1,
        "owner_id": 456,
        "repo_id": repo_id,
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
    }
    base_settings.update(overrides)
    return cast(Repositories, base_settings)


def create_coverage_data(
    filename: str,
    line_coverage: float | None = None,
    function_coverage: float | None = None,
    branch_coverage: float | None = None,
    **overrides
) -> Coverages:
    """Helper function to create coverage data."""
    base_data = {
        "id": 1,
        "owner_id": 456,
        "repo_id": 789,
        "language": "python",
        "package_name": "test_package",
        "level": "file",
        "full_path": filename,
        "statement_coverage": 80.0,
        "function_coverage": function_coverage,
        "branch_coverage": branch_coverage,
        "path_coverage": 60.0,
        "line_coverage": line_coverage,
        "uncovered_lines": "1,2,3",
        "created_at": datetime.now(),
        "created_by": "testuser",
        "updated_at": datetime.now(),
        "updated_by": "testuser",
        "github_issue_url": None,
        "uncovered_functions": "func1,func2",
        "uncovered_branches": "branch1,branch2",
        "branch_name": "main",
        "file_size": 1000,
        "is_excluded_from_testing": False,
    }
    base_data.update(overrides)
    return cast(Coverages, base_data)


@pytest.fixture
def mock_get_repository():
    """Mock the get_repository function."""
    with patch("services.webhook.utils.create_pr_checkbox_comment.get_repository") as mock:
        yield mock


@pytest.fixture
def mock_get_installation_access_token():
    """Mock the get_installation_access_token function."""
    with patch("services.webhook.utils.create_pr_checkbox_comment.get_installation_access_token") as mock:
        mock.return_value = "test_token"
        yield mock


@pytest.fixture
def mock_get_pull_request_files():
    """Mock the get_pull_request_files function."""
    with patch("services.webhook.utils.create_pr_checkbox_comment.get_pull_request_files") as mock:
        yield mock


@pytest.fixture
def mock_is_code_file():
    """Mock the is_code_file function."""
    with patch("services.webhook.utils.create_pr_checkbox_comment.is_code_file") as mock:
        yield mock


@pytest.fixture
def mock_is_test_file():
    """Mock the is_test_file function."""
    with patch("services.webhook.utils.create_pr_checkbox_comment.is_test_file") as mock:
        yield mock


@pytest.fixture
def mock_is_type_file():
    """Mock the is_type_file function."""
    with patch("services.webhook.utils.create_pr_checkbox_comment.is_type_file") as mock:
        yield mock


@pytest.fixture
def mock_get_coverages():
    """Mock the get_coverages function."""
    with patch("services.webhook.utils.create_pr_checkbox_comment.get_coverages") as mock:
        yield mock


@pytest.fixture
def mock_create_file_checklist():
    """Mock the create_file_checklist function."""
    with patch("services.webhook.utils.create_pr_checkbox_comment.create_file_checklist") as mock:
        yield mock


@pytest.fixture
def mock_create_test_selection_comment():
    """Mock the create_test_selection_comment function."""
    with patch("services.webhook.utils.create_pr_checkbox_comment.create_test_selection_comment") as mock:
        mock.return_value = "Test selection comment"
        yield mock


@pytest.fixture
def mock_delete_comments_by_identifiers():
    """Mock the delete_comments_by_identifiers function."""
    with patch("services.webhook.utils.create_pr_checkbox_comment.delete_comments_by_identifiers") as mock:
        yield mock


@pytest.fixture
def mock_combine_and_create_comment():
    """Mock the combine_and_create_comment function."""
    with patch("services.webhook.utils.create_pr_checkbox_comment.combine_and_create_comment") as mock:
        yield mock


@pytest.fixture
def mock_logging():
    """Mock the logging module."""
    with patch("services.webhook.utils.create_pr_checkbox_comment.logging") as mock:
        yield mock


class TestCreatePrCheckboxComment:
    """Test cases for create_pr_checkbox_comment function."""

    def test_skips_bot_sender(
        self,
        mock_logging,
        mock_get_repository,
        mock_get_installation_access_token,
        mock_get_pull_request_files,
        mock_is_code_file,
        mock_is_test_file,
        mock_is_type_file,
        mock_get_coverages,
        mock_create_file_checklist,
        mock_create_test_selection_comment,
        mock_delete_comments_by_identifiers,
        mock_combine_and_create_comment,
    ):
        """Test that the function skips processing when sender is a bot."""
        # Arrange
        payload = create_payload(sender_login="dependabot[bot]")

        # Act
        result = create_pr_checkbox_comment(payload)

        # Assert
        assert result is None
        mock_logging.info.assert_called_once_with("Skipping PR test selection for bot dependabot[bot]")
        mock_get_repository.assert_not_called()
        mock_get_installation_access_token.assert_not_called()
        mock_get_pull_request_files.assert_not_called()
        mock_is_code_file.assert_not_called()
        mock_is_test_file.assert_not_called()
        mock_is_type_file.assert_not_called()
        mock_get_coverages.assert_not_called()
        mock_create_file_checklist.assert_not_called()
        mock_create_test_selection_comment.assert_not_called()
        mock_delete_comments_by_identifiers.assert_not_called()
        mock_combine_and_create_comment.assert_not_called()

    def test_skips_when_repository_not_found(
        self,
        mock_logging,
        mock_get_repository,
        mock_get_installation_access_token,
        mock_get_pull_request_files,
        mock_is_code_file,
        mock_is_test_file,
        mock_is_type_file,
        mock_get_coverages,
        mock_create_file_checklist,
        mock_create_test_selection_comment,
        mock_delete_comments_by_identifiers,
        mock_combine_and_create_comment,
    ):
        """Test that the function skips processing when repository is not found."""
        # Arrange
        payload = create_payload()
        mock_get_repository.return_value = None

        # Act
        result = create_pr_checkbox_comment(payload)

        # Assert
        assert result is None
        mock_logging.info.assert_called_once_with(
            "Skipping PR test selection for repo testrepo because trigger_on_pr_change is False"
        )
        mock_get_repository.assert_called_once_with(repo_id=789)
        mock_get_installation_access_token.assert_not_called()
        mock_get_pull_request_files.assert_not_called()
        mock_is_code_file.assert_not_called()
        mock_is_test_file.assert_not_called()
        mock_is_type_file.assert_not_called()
        mock_get_coverages.assert_not_called()
        mock_create_file_checklist.assert_not_called()
        mock_create_test_selection_comment.assert_not_called()
        mock_delete_comments_by_identifiers.assert_not_called()
        mock_combine_and_create_comment.assert_not_called()

    def test_skips_when_trigger_on_pr_change_is_false(
        self,
        mock_logging,
        mock_get_repository,
        mock_get_installation_access_token,
        mock_get_pull_request_files,
        mock_is_code_file,
        mock_is_test_file,
        mock_is_type_file,
        mock_get_coverages,
        mock_create_file_checklist,
        mock_create_test_selection_comment,
        mock_delete_comments_by_identifiers,
        mock_combine_and_create_comment,
    ):
        """Test that the function skips processing when trigger_on_pr_change is False."""
        # Arrange
        payload = create_payload()
        mock_get_repository.return_value = create_repository_settings(trigger_on_pr_change=False)

        # Act
        result = create_pr_checkbox_comment(payload)

        # Assert
        assert result is None
        mock_logging.info.assert_called_once_with(
            "Skipping PR test selection for repo testrepo because trigger_on_pr_change is False"
        )
        mock_get_repository.assert_called_once_with(repo_id=789)
        mock_get_installation_access_token.assert_not_called()
        mock_get_pull_request_files.assert_not_called()
        mock_is_code_file.assert_not_called()
        mock_is_test_file.assert_not_called()
        mock_is_type_file.assert_not_called()
        mock_get_coverages.assert_not_called()
        mock_create_file_checklist.assert_not_called()
        mock_create_test_selection_comment.assert_not_called()
        mock_delete_comments_by_identifiers.assert_not_called()
        mock_combine_and_create_comment.assert_not_called()

    def test_skips_when_no_code_files_changed(
        self,
        mock_logging,
        mock_get_repository,
        mock_get_installation_access_token,
        mock_get_pull_request_files,
        mock_is_code_file,
        mock_is_test_file,
        mock_is_type_file,
        mock_get_coverages,
        mock_create_file_checklist,
        mock_create_test_selection_comment,
        mock_delete_comments_by_identifiers,
        mock_combine_and_create_comment,
    ):
        """Test that the function skips processing when no code files are changed."""
        # Arrange
        payload = create_payload()
        mock_get_repository.return_value = create_repository_settings()
        mock_get_pull_request_files.return_value = [
            create_file_change("test_file.py", "modified"),
            create_file_change("types.py", "added"),
        ]
        mock_is_code_file.side_effect = [True, True]  # Both are code files
        mock_is_test_file.side_effect = [True, False]  # First is test file
        mock_is_type_file.side_effect = [False, True]  # Second is type file

        # Act
        result = create_pr_checkbox_comment(payload)

        # Assert
        assert result is None
        mock_logging.info.assert_called_once_with(
            "Skipping PR test selection for repo testrepo because no code files were changed"
        )
        mock_get_repository.assert_called_once_with(repo_id=789)
        mock_get_installation_access_token.assert_called_once_with(installation_id=12345)
        mock_get_pull_request_files.assert_called_once_with(
            url="https://api.github.com/repos/testowner/testrepo/pulls/1/files",
            token="test_token"
        )
        mock_is_code_file.assert_any_call("test_file.py")
        mock_is_code_file.assert_any_call("types.py")
        mock_is_test_file.assert_any_call("test_file.py")
        mock_is_test_file.assert_any_call("types.py")
        mock_is_type_file.assert_any_call("test_file.py")
        mock_is_type_file.assert_any_call("types.py")
        mock_get_coverages.assert_not_called()
        mock_create_file_checklist.assert_not_called()
        mock_create_test_selection_comment.assert_not_called()
        mock_delete_comments_by_identifiers.assert_not_called()
        mock_combine_and_create_comment.assert_not_called()

    def test_successful_comment_creation(
        self,
        mock_logging,
        mock_get_repository,
        mock_get_installation_access_token,
        mock_get_pull_request_files,
        mock_is_code_file,
        mock_is_test_file,
        mock_is_type_file,
        mock_get_coverages,
        mock_create_file_checklist,
        mock_create_test_selection_comment,
        mock_delete_comments_by_identifiers,
        mock_combine_and_create_comment,
    ):
        """Test successful comment creation with valid code files."""
        # Arrange
        payload = create_payload()
        mock_get_repository.return_value = create_repository_settings()
        mock_get_pull_request_files.return_value = [
            create_file_change("src/main.py", "modified"),
            create_file_change("src/utils.py", "added"),
        ]
        mock_is_code_file.return_value = True
        mock_is_test_file.return_value = False
        mock_is_type_file.return_value = False
        mock_get_coverages.return_value = {
            "src/main.py": create_coverage_data("src/main.py", line_coverage=85.0),
            "src/utils.py": create_coverage_data("src/utils.py", line_coverage=60.0),
        }
        mock_create_file_checklist.return_value = [
            {"path": "src/main.py", "checked": True, "status": "modified", "coverage_info": " (Line: 85.0%)"},
            {"path": "src/utils.py", "checked": True, "status": "added", "coverage_info": " (Line: 60.0%)"},
        ]

        # Act
        result = create_pr_checkbox_comment(payload)

        # Assert
        assert result is None  # Function returns None on success
        mock_get_repository.assert_called_once_with(repo_id=789)
        mock_get_installation_access_token.assert_called_once_with(installation_id=12345)
        mock_get_pull_request_files.assert_called_once_with(
            url="https://api.github.com/repos/testowner/testrepo/pulls/1/files",
            token="test_token"
        )
        mock_get_coverages.assert_called_once_with(
            repo_id=789,
            filenames=["src/main.py", "src/utils.py"]
        )
        mock_create_file_checklist.assert_called_once()
        mock_create_test_selection_comment.assert_called_once_with(
            mock_create_file_checklist.return_value,
            "feature-branch"
        )
        mock_delete_comments_by_identifiers.assert_called_once()
        mock_combine_and_create_comment.assert_called_once()

    def test_handles_mixed_file_types(
        self,
        mock_logging,
        mock_get_repository,
        mock_get_installation_access_token,
        mock_get_pull_request_files,
        mock_is_code_file,
        mock_is_test_file,
        mock_is_type_file,
        mock_get_coverages,
        mock_create_file_checklist,
        mock_create_test_selection_comment,
        mock_delete_comments_by_identifiers,
        mock_combine_and_create_comment,
    ):
        """Test handling of mixed file types (code, test, type files)."""
        # Arrange
        payload = create_payload()
        mock_get_repository.return_value = create_repository_settings()
        mock_get_pull_request_files.return_value = [
            create_file_change("src/main.py", "modified"),
            create_file_change("test_main.py", "added"),
            create_file_change("types.py", "modified"),
            create_file_change("README.md", "modified"),
        ]

        def is_code_file_side_effect(filename):
            return filename.endswith('.py')

        def is_test_file_side_effect(filename):
            return filename.startswith('test_')

        def is_type_file_side_effect(filename):
            return filename == 'types.py'

        mock_is_code_file.side_effect = is_code_file_side_effect
        mock_is_test_file.side_effect = is_test_file_side_effect
        mock_is_type_file.side_effect = is_type_file_side_effect

        mock_get_coverages.return_value = {
            "src/main.py": create_coverage_data("src/main.py", line_coverage=85.0),
        }
        mock_create_file_checklist.return_value = [
            {"path": "src/main.py", "checked": True, "status": "modified", "coverage_info": " (Line: 85.0%)"},
        ]

        # Act
        result = create_pr_checkbox_comment(payload)

        # Assert
        assert result is None
        mock_get_coverages.assert_called_once_with(
            repo_id=789,
            filenames=["src/main.py"]  # Only the non-test, non-type code file
        )
        mock_create_file_checklist.assert_called_once()
        mock_create_test_selection_comment.assert_called_once()
        mock_delete_comments_by_identifiers.assert_called_once()
        mock_combine_and_create_comment.assert_called_once()

    def test_delete_comments_called_with_correct_args(
        self,
        mock_logging,
        mock_get_repository,
        mock_get_installation_access_token,
        mock_get_pull_request_files,
        mock_is_code_file,
        mock_is_test_file,
        mock_is_type_file,
        mock_get_coverages,
        mock_create_file_checklist,
        mock_create_test_selection_comment,
        mock_delete_comments_by_identifiers,
        mock_combine_and_create_comment,
    ):
        """Test that delete_comments_by_identifiers is called with correct arguments."""
        # Arrange
        payload = create_payload()
        mock_get_repository.return_value = create_repository_settings()
        mock_get_pull_request_files.return_value = [
            create_file_change("src/main.py", "modified"),
        ]
        mock_is_code_file.return_value = True
        mock_is_test_file.return_value = False
        mock_is_type_file.return_value = False
        mock_get_coverages.return_value = {}
        mock_create_file_checklist.return_value = []

        # Act
        create_pr_checkbox_comment(payload)

        # Assert
        expected_base_args = {
            "owner": "testowner",
            "repo": "testrepo",
            "issue_number": 1,
            "token": "test_token",
        }
        mock_delete_comments_by_identifiers.assert_called_once_with(
            base_args=expected_base_args,
            identifiers=[TEST_SELECTION_COMMENT_IDENTIFIER]
        )

    def test_combine_and_create_comment_called_with_correct_args(
        self,
        mock_logging,
        mock_get_repository,
        mock_get_installation_access_token,
        mock_get_pull_request_files,
        mock_is_code_file,
        mock_is_test_file,
        mock_is_type_file,
        mock_get_coverages,
        mock_create_file_checklist,
        mock_create_test_selection_comment,
        mock_delete_comments_by_identifiers,
        mock_combine_and_create_comment,
    ):
        """Test that combine_and_create_comment is called with correct arguments."""
        # Arrange
        payload = create_payload()
        mock_get_repository.return_value = create_repository_settings()
        mock_get_pull_request_files.return_value = [
            create_file_change("src/main.py", "modified"),
        ]
        mock_is_code_file.return_value = True
        mock_is_test_file.return_value = False
        mock_is_type_file.return_value = False
        mock_get_coverages.return_value = {}
        mock_create_file_checklist.return_value = []

        # Act
        create_pr_checkbox_comment(payload)

        # Assert
        expected_base_args = {
            "owner": "testowner",
            "repo": "testrepo",
            "issue_number": 1,
            "token": "test_token",
        }
        mock_combine_and_create_comment.assert_called_once_with(
            base_comment="Test selection comment",
            installation_id=12345,
            owner_id=456,
            owner_name="testowner",
            sender_name="testuser",
            base_args=expected_base_args,
        )

    def test_handles_empty_coverage_data(
        self,
        mock_logging,
        mock_get_repository,
        mock_get_installation_access_token,
        mock_get_pull_request_files,
        mock_is_code_file,
        mock_is_test_file,
        mock_is_type_file,
        mock_get_coverages,
        mock_create_file_checklist,
        mock_create_test_selection_comment,
        mock_delete_comments_by_identifiers,
        mock_combine_and_create_comment,
    ):
        """Test handling when coverage data is empty."""
        # Arrange
        payload = create_payload()
        mock_get_repository.return_value = create_repository_settings()
        mock_get_pull_request_files.return_value = [
            create_file_change("src/main.py", "modified"),
        ]
        mock_is_code_file.return_value = True
        mock_is_test_file.return_value = False
        mock_is_type_file.return_value = False
        mock_get_coverages.return_value = {}  # Empty coverage data
        mock_create_file_checklist.return_value = [
            {"path": "src/main.py", "checked": True, "status": "modified", "coverage_info": ""},
        ]

        # Act
        result = create_pr_checkbox_comment(payload)

        # Assert
        assert result is None
        mock_get_coverages.assert_called_once_with(
            repo_id=789,
            filenames=["src/main.py"]
        )
        mock_create_file_checklist.assert_called_once_with(
            [create_file_change("src/main.py", "modified")],
            {}
        )
        mock_create_test_selection_comment.assert_called_once()
        mock_delete_comments_by_identifiers.assert_called_once()
        mock_combine_and_create_comment.assert_called_once()

    def test_handles_different_file_statuses(
        self,
        mock_logging,
        mock_get_repository,
        mock_get_installation_access_token,
        mock_get_pull_request_files,
        mock_is_code_file,
        mock_is_test_file,
        mock_is_type_file,
        mock_get_coverages,
        mock_create_file_checklist,
        mock_create_test_selection_comment,
        mock_delete_comments_by_identifiers,
        mock_combine_and_create_comment,
    ):
        """Test handling of different file statuses (added, modified, removed)."""
        # Arrange
        payload = create_payload()
        mock_get_repository.return_value = create_repository_settings()
        mock_get_pull_request_files.return_value = [
            create_file_change("src/added.py", "added"),
            create_file_change("src/modified.py", "modified"),
            create_file_change("src/removed.py", "removed"),
        ]
        mock_is_code_file.return_value = True
        mock_is_test_file.return_value = False
        mock_is_type_file.return_value = False
        mock_get_coverages.return_value = {}
        mock_create_file_checklist.return_value = [
            {"path": "src/added.py", "checked": True, "status": "added", "coverage_info": ""},
            {"path": "src/modified.py", "checked": True, "status": "modified", "coverage_info": ""},
            {"path": "src/removed.py", "checked": True, "status": "removed", "coverage_info": ""},
        ]

        # Act
        result = create_pr_checkbox_comment(payload)

        # Assert
        assert result is None
        mock_get_coverages.assert_called_once_with(
            repo_id=789,
            filenames=["src/added.py", "src/modified.py", "src/removed.py"]
        )
        mock_create_file_checklist.assert_called_once()
        mock_create_test_selection_comment.assert_called_once()
        mock_delete_comments_by_identifiers.assert_called_once()
        mock_combine_and_create_comment.assert_called_once()

    def test_handles_different_bot_names(
        self,
        mock_logging,
        mock_get_repository,
        mock_get_installation_access_token,
        mock_get_pull_request_files,
        mock_is_code_file,
        mock_is_test_file,
        mock_is_type_file,
        mock_get_coverages,
        mock_create_file_checklist,
        mock_create_test_selection_comment,
        mock_delete_comments_by_identifiers,
        mock_combine_and_create_comment,
    ):
        """Test that different bot names are properly detected and skipped."""
        bot_names = [
            "dependabot[bot]",
            "renovate[bot]",
            "github-actions[bot]",
            "codecov[bot]",
            "custom-bot[bot]",
        ]

        for bot_name in bot_names:
            # Arrange
            payload = create_payload(sender_login=bot_name)
            mock_logging.reset_mock()

            # Act
            result = create_pr_checkbox_comment(payload)

            # Assert
            assert result is None
            mock_logging.info.assert_called_once_with(f"Skipping PR test selection for bot {bot_name}")
            mock_get_repository.assert_not_called()

    def test_handles_non_bot_users(
        self,
        mock_logging,
        mock_get_repository,
        mock_get_installation_access_token,
        mock_get_pull_request_files,
        mock_is_code_file,
        mock_is_test_file,
        mock_is_type_file,
        mock_get_coverages,
        mock_create_file_checklist,
        mock_create_test_selection_comment,
        mock_delete_comments_by_identifiers,
        mock_combine_and_create_comment,
    ):
        """Test that non-bot users are processed normally."""
        # Arrange
        payload = create_payload(sender_login="regular-user")
        mock_get_repository.return_value = create_repository_settings()
        mock_get_pull_request_files.return_value = [
            create_file_change("src/main.py", "modified"),
        ]
        mock_is_code_file.return_value = True
        mock_is_test_file.return_value = False
        mock_is_type_file.return_value = False
        mock_get_coverages.return_value = {}
        mock_create_file_checklist.return_value = []

        # Act
        result = create_pr_checkbox_comment(payload)

        # Assert
        assert result is None
        mock_get_repository.assert_called_once_with(repo_id=789)
        # Should not log bot skip message
        mock_logging.info.assert_not_called()

    def test_extracts_correct_branch_name(
        self,
        mock_logging,
        mock_get_repository,
        mock_get_installation_access_token,
        mock_get_pull_request_files,
        mock_is_code_file,
        mock_is_test_file,
        mock_is_type_file,
        mock_get_coverages,
        mock_create_file_checklist,
        mock_create_test_selection_comment,
        mock_delete_comments_by_identifiers,
        mock_combine_and_create_comment,
    ):
        """Test that the correct branch name is extracted from the PR head ref."""
        # Arrange
        payload = create_payload()
        # Modify the head ref to have a different branch name
        payload["pull_request"]["head"]["ref"] = "feature/new-feature"

        mock_get_repository.return_value = create_repository_settings()
        mock_get_pull_request_files.return_value = [
            create_file_change("src/main.py", "modified"),
        ]
        mock_is_code_file.return_value = True
        mock_is_test_file.return_value = False
        mock_is_type_file.return_value = False
        mock_get_coverages.return_value = {}
        mock_create_file_checklist.return_value = []

        # Act
        create_pr_checkbox_comment(payload)

        # Assert
        mock_create_test_selection_comment.assert_called_once_with(
            [],
            "feature/new-feature"
        )

    def test_handles_large_number_of_files(
        self,
        mock_logging,
        mock_get_repository,
        mock_get_installation_access_token,
        mock_get_pull_request_files,
        mock_is_code_file,
        mock_is_test_file,
        mock_is_type_file,
        mock_get_coverages,
        mock_create_file_checklist,
        mock_create_test_selection_comment,
        mock_delete_comments_by_identifiers,
        mock_combine_and_create_comment,
    ):
        """Test handling of a large number of changed files."""
        # Arrange
        payload = create_payload()
        mock_get_repository.return_value = create_repository_settings()

        # Create 50 files
        file_changes = []
        expected_filenames = []
        for i in range(50):
            filename = f"src/file_{i:03d}.py"
            file_changes.append(create_file_change(filename, "modified"))
            expected_filenames.append(filename)

        mock_get_pull_request_files.return_value = file_changes
        mock_is_code_file.return_value = True
        mock_is_test_file.return_value = False
        mock_is_type_file.return_value = False
        mock_get_coverages.return_value = {}
        mock_create_file_checklist.return_value = []

        # Act
        result = create_pr_checkbox_comment(payload)

        # Assert
        assert result is None
        mock_get_coverages.assert_called_once_with(
            repo_id=789,
            filenames=expected_filenames
        )
        mock_create_file_checklist.assert_called_once()
        mock_create_test_selection_comment.assert_called_once()
        mock_delete_comments_by_identifiers.assert_called_once()
        mock_combine_and_create_comment.assert_called_once()

    def test_integration_with_actual_dependencies(self):
        """Test the function with minimal mocking to verify integration."""
        # Arrange
        payload = create_payload()

        with patch("services.webhook.utils.create_pr_checkbox_comment.get_repository") as mock_get_repo, \
             patch("services.webhook.utils.create_pr_checkbox_comment.get_installation_access_token") as mock_get_token, \
             patch("services.webhook.utils.create_pr_checkbox_comment.get_pull_request_files") as mock_get_files, \
             patch("services.webhook.utils.create_pr_checkbox_comment.get_coverages") as mock_get_cov, \
             patch("services.webhook.utils.create_pr_checkbox_comment.delete_comments_by_identifiers") as mock_delete, \
             patch("services.webhook.utils.create_pr_checkbox_comment.combine_and_create_comment") as mock_create:

            mock_get_repo.return_value = create_repository_settings()
            mock_get_token.return_value = "test_token"
            mock_get_files.return_value = [create_file_change("src/main.py", "modified")]
            mock_get_cov.return_value = {"src/main.py": create_coverage_data("src/main.py", line_coverage=85.0)}

            # Act
            result = create_pr_checkbox_comment(payload)

            # Assert
            assert result is None
            mock_get_repo.assert_called_once()
            mock_get_token.assert_called_once()
            mock_get_files.assert_called_once()
            mock_get_cov.assert_called_once()
            mock_delete.assert_called_once()
            mock_create.assert_called_once()

    def test_error_handling_with_handle_exceptions_decorator(self):
        """Test that the @handle_exceptions decorator works correctly."""
        # Arrange
        payload = create_payload()

        with patch("services.webhook.utils.create_pr_checkbox_comment.get_repository") as mock_get_repo:
            # Make get_repository raise an exception
            mock_get_repo.side_effect = Exception("Database error")

            # Act
            result = create_pr_checkbox_comment(payload)

            # Assert
            # The @handle_exceptions decorator should catch the exception and return None
            assert result is None
            mock_get_repo.assert_called_once_with(repo_id=789)
