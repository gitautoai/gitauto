from unittest.mock import patch
import pytest
from services.github.types.pull_request_webhook_payload import (
    PullRequestWebhookPayload,
)
from services.webhook.utils.create_pr_checkbox_comment import (
    create_pr_checkbox_comment,
)


@pytest.fixture
def mock_get_repository():
    with patch(
        "services.webhook.utils.create_pr_checkbox_comment.get_repository"
    ) as mock:
        yield mock


@pytest.fixture
def mock_get_installation_access_token():
    with patch(
        "services.webhook.utils.create_pr_checkbox_comment.get_installation_access_token"
    ) as mock:
        mock.return_value = "test-token-123"
        yield mock


@pytest.fixture
def mock_get_pull_request_files():
    with patch(
        "services.webhook.utils.create_pr_checkbox_comment.get_pull_request_files"
    ) as mock:
        yield mock


@pytest.fixture
def mock_is_code_file():
    with patch("services.webhook.utils.create_pr_checkbox_comment.is_code_file") as mock:
        yield mock


@pytest.fixture
def mock_is_test_file():
    with patch("services.webhook.utils.create_pr_checkbox_comment.is_test_file") as mock:
        yield mock


@pytest.fixture
def mock_is_type_file():
    with patch("services.webhook.utils.create_pr_checkbox_comment.is_type_file") as mock:
        yield mock


@pytest.fixture
def mock_get_coverages():
    with patch(
        "services.webhook.utils.create_pr_checkbox_comment.get_coverages"
    ) as mock:
        yield mock


@pytest.fixture
def mock_create_file_checklist():
    with patch(
        "services.webhook.utils.create_pr_checkbox_comment.create_file_checklist"
    ) as mock:
        yield mock


@pytest.fixture
def mock_create_test_selection_comment():
    with patch(
        "services.webhook.utils.create_pr_checkbox_comment.create_test_selection_comment"
    ) as mock:
        yield mock


@pytest.fixture
def mock_delete_comments_by_identifiers():
    with patch(
        "services.webhook.utils.create_pr_checkbox_comment.delete_comments_by_identifiers"
    ) as mock:
        yield mock


@pytest.fixture
def mock_combine_and_create_comment():
    with patch(
        "services.webhook.utils.create_pr_checkbox_comment.combine_and_create_comment"
    ) as mock:
        yield mock


@pytest.fixture
def mock_logging():
    with patch("services.webhook.utils.create_pr_checkbox_comment.logging") as mock:
        yield mock


@pytest.fixture
def all_mocks(
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
    mock_logging,
):
    """Fixture that provides all mocks in a dictionary."""
    return {
        "get_repository": mock_get_repository,
        "get_installation_access_token": mock_get_installation_access_token,
        "get_pull_request_files": mock_get_pull_request_files,
        "is_code_file": mock_is_code_file,
        "is_test_file": mock_is_test_file,
        "is_type_file": mock_is_type_file,
        "get_coverages": mock_get_coverages,
        "create_file_checklist": mock_create_file_checklist,
        "create_test_selection_comment": mock_create_test_selection_comment,
        "delete_comments_by_identifiers": mock_delete_comments_by_identifiers,
        "combine_and_create_comment": mock_combine_and_create_comment,
        "logging": mock_logging,
    }


def create_test_payload(
    sender_name: str = "test-user",
    repo_id: int = 12345,
    repo_name: str = "test-repo",
    owner_id: int = 67890,
    owner_name: str = "test-owner",
    pull_number: int = 42,
    pull_url: str = "https://api.github.com/repos/test-owner/test-repo/pulls/42",
    installation_id: int = 11111,
    branch_name: str = "feature-branch",
) -> PullRequestWebhookPayload:
    """Helper function to create a test payload."""
    return {
        "action": "opened",
        "number": pull_number,
        "pull_request": {
            "id": 1,
            "number": pull_number,
            "url": pull_url,
            "html_url": f"https://github.com/{owner_name}/{repo_name}/pull/{pull_number}",
            "state": "open",
            "title": "Test PR",
            "body": "Test PR body",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
            "closed_at": None,
            "merged_at": None,
            "head": {
                "ref": branch_name,
                "sha": "abc123",
                "repo": {
                    "id": repo_id,
                    "name": repo_name,
                    "full_name": f"{owner_name}/{repo_name}",
                    "private": False,
                    "html_url": f"https://github.com/{owner_name}/{repo_name}",
                    "description": "Test repo",
                    "fork": False,
                    "created_at": "2023-01-01T00:00:00Z",
                    "updated_at": "2023-01-01T00:00:00Z",
                    "pushed_at": "2023-01-01T00:00:00Z",
                    "size": 100,
                    "stargazers_count": 0,
                    "watchers_count": 0,
                    "language": "Python",
                    "has_issues": True,
                    "has_projects": True,
                    "has_downloads": True,
                    "has_wiki": True,
                    "has_pages": False,
                    "forks_count": 0,
                    "archived": False,
                    "disabled": False,
                    "open_issues_count": 0,
                    "forks": 0,
                    "open_issues": 0,
                    "watchers": 0,
                    "default_branch": "main",
                    "owner": {
                        "login": owner_name,
                        "id": owner_id,
                        "avatar_url": "https://avatars.githubusercontent.com/u/1?v=4",
                        "html_url": f"https://github.com/{owner_name}",
                        "type": "User",
                    },
                },
            },
            "base": {
                "ref": "main",
                "sha": "def456",
                "repo": {
                    "id": repo_id,
                    "name": repo_name,
                    "full_name": f"{owner_name}/{repo_name}",
                    "private": False,
                    "html_url": f"https://github.com/{owner_name}/{repo_name}",
                    "description": "Test repo",
                    "fork": False,
                    "created_at": "2023-01-01T00:00:00Z",
                    "updated_at": "2023-01-01T00:00:00Z",
                    "pushed_at": "2023-01-01T00:00:00Z",
                    "size": 100,
                    "stargazers_count": 0,
                    "watchers_count": 0,
                    "language": "Python",
                    "has_issues": True,
                    "has_projects": True,
                    "has_downloads": True,
                    "has_wiki": True,
                    "has_pages": False,
                    "forks_count": 0,
                    "archived": False,
                    "disabled": False,
                    "open_issues_count": 0,
                    "forks": 0,
                    "open_issues": 0,
                    "watchers": 0,
                    "default_branch": "main",
                    "owner": {
                        "login": owner_name,
                        "id": owner_id,
                        "avatar_url": "https://avatars.githubusercontent.com/u/1?v=4",
                        "html_url": f"https://github.com/{owner_name}",
                        "type": "User",
                    },
                },
            },
            "user": {
                "login": sender_name,
                "id": 1,
                "avatar_url": "https://avatars.githubusercontent.com/u/1?v=4",
                "html_url": f"https://github.com/{sender_name}",
                "type": "User",
            },
            "merged": False,
            "mergeable": True,
            "mergeable_state": "clean",
            "merged_by": None,
            "comments": 0,
            "review_comments": 0,
            "maintainer_can_modify": False,
            "commits": 1,
            "additions": 10,
            "deletions": 5,
            "changed_files": 1,
        },
        "repository": {
            "id": repo_id,
            "name": repo_name,
            "full_name": f"{owner_name}/{repo_name}",
            "private": False,
            "html_url": f"https://github.com/{owner_name}/{repo_name}",
            "description": "Test repo",
            "fork": False,
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
            "pushed_at": "2023-01-01T00:00:00Z",
            "size": 100,
            "stargazers_count": 0,
            "watchers_count": 0,
            "language": "Python",
            "has_issues": True,
            "has_projects": True,
            "has_downloads": True,
            "has_wiki": True,
            "has_pages": False,
            "forks_count": 0,
            "archived": False,
            "disabled": False,
            "open_issues_count": 0,
            "forks": 0,
            "open_issues": 0,
            "watchers": 0,
            "default_branch": "main",
            "owner": {
                "login": owner_name,
                "id": owner_id,
                "avatar_url": "https://avatars.githubusercontent.com/u/1?v=4",
                "html_url": f"https://github.com/{owner_name}",
                "type": "User",
            },
        },
        "organization": {
            "login": owner_name,
            "id": owner_id,
            "avatar_url": "https://avatars.githubusercontent.com/u/1?v=4",
            "html_url": f"https://github.com/{owner_name}",
        },
        "sender": {
            "login": sender_name,
            "id": 1,
            "avatar_url": "https://avatars.githubusercontent.com/u/1?v=4",
            "html_url": f"https://github.com/{sender_name}",
            "type": "User",
        },
        "installation": {
            "id": installation_id,
        },
    }


def test_skips_bot_sender(all_mocks):
    """Test that the function skips processing when sender is a bot."""
    payload = create_test_payload(sender_name="dependabot[bot]")

    result = create_pr_checkbox_comment(payload)

    assert result is None
    all_mocks["logging"].info.assert_called_once()
    assert "Skipping PR test selection for bot dependabot[bot]" in str(
        all_mocks["logging"].info.call_args
    )
    all_mocks["get_repository"].assert_not_called()


def test_skips_when_repo_settings_not_found(all_mocks):
    """Test that the function skips when repository settings are not found."""
    payload = create_test_payload()
    all_mocks["get_repository"].return_value = None

    result = create_pr_checkbox_comment(payload)

    assert result is None
    all_mocks["get_repository"].assert_called_once_with(repo_id=12345)
    all_mocks["logging"].info.assert_called_once()
    assert "trigger_on_pr_change is False" in str(
        all_mocks["logging"].info.call_args
    )


def test_skips_when_trigger_on_pr_change_is_false(all_mocks):
    """Test that the function skips when trigger_on_pr_change is False."""
    payload = create_test_payload()
    all_mocks["get_repository"].return_value = {"trigger_on_pr_change": False}

    result = create_pr_checkbox_comment(payload)

    assert result is None
    all_mocks["get_repository"].assert_called_once_with(repo_id=12345)
    all_mocks["logging"].info.assert_called_once()
    assert "trigger_on_pr_change is False" in str(
        all_mocks["logging"].info.call_args
    )


def test_skips_when_no_code_files_changed(all_mocks):
    """Test that the function skips when no code files are changed."""
    payload = create_test_payload()
    all_mocks["get_repository"].return_value = {"trigger_on_pr_change": True}
    all_mocks["get_pull_request_files"].return_value = [
        {"filename": "test_file.py"},
        {"filename": "types.py"},
    ]
    all_mocks["is_code_file"].return_value = True
    all_mocks["is_test_file"].side_effect = lambda f: f == "test_file.py"
    all_mocks["is_type_file"].side_effect = lambda f: f == "types.py"

    result = create_pr_checkbox_comment(payload)

    assert result is None
    all_mocks["logging"].info.assert_called_once()
    assert "no code files were changed" in str(all_mocks["logging"].info.call_args)


def test_successful_comment_creation(all_mocks):
    """Test successful creation of PR checkbox comment."""
    payload = create_test_payload()
    all_mocks["get_repository"].return_value = {"trigger_on_pr_change": True}
    all_mocks["get_pull_request_files"].return_value = [
        {"filename": "src/file1.py"},
        {"filename": "src/file2.py"},
    ]
    all_mocks["is_code_file"].return_value = True
    all_mocks["is_test_file"].return_value = False
    all_mocks["is_type_file"].return_value = False
    all_mocks["get_coverages"].return_value = {}
    all_mocks["create_file_checklist"].return_value = [
        {"path": "src/file1.py", "checked": True, "coverage_info": "", "status": "added"}
    ]
    all_mocks["create_test_selection_comment"].return_value = "Test comment"

    result = create_pr_checkbox_comment(payload)

    assert result is None
    all_mocks["get_installation_access_token"].assert_called_once_with(
        installation_id=11111
    )
    all_mocks["get_pull_request_files"].assert_called_once_with(
        url="https://api.github.com/repos/test-owner/test-repo/pulls/42/files",
        token="test-token-123",
    )
    all_mocks["get_coverages"].assert_called_once_with(
        repo_id=12345, filenames=["src/file1.py", "src/file2.py"]
    )
    all_mocks["delete_comments_by_identifiers"].assert_called_once()
    all_mocks["combine_and_create_comment"].assert_called_once()


def test_filters_test_files_correctly(all_mocks):
    """Test that test files are filtered out correctly."""
    payload = create_test_payload()
    all_mocks["get_repository"].return_value = {"trigger_on_pr_change": True}
    all_mocks["get_pull_request_files"].return_value = [
        {"filename": "src/file1.py"},
        {"filename": "test_file1.py"},
        {"filename": "src/file2.py"},
    ]
    all_mocks["is_code_file"].return_value = True
    all_mocks["is_test_file"].side_effect = lambda f: "test_" in f
    all_mocks["is_type_file"].return_value = False
    all_mocks["get_coverages"].return_value = {}
    all_mocks["create_file_checklist"].return_value = [
        {"path": "src/file1.py", "checked": True, "coverage_info": "", "status": "added"}
    ]
    all_mocks["create_test_selection_comment"].return_value = "Test comment"

    create_pr_checkbox_comment(payload)

    all_mocks["get_coverages"].assert_called_once_with(
        repo_id=12345, filenames=["src/file1.py", "src/file2.py"]
    )


def test_filters_type_files_correctly(all_mocks):
    """Test that type files are filtered out correctly."""
    payload = create_test_payload()
    all_mocks["get_repository"].return_value = {"trigger_on_pr_change": True}
    all_mocks["get_pull_request_files"].return_value = [
        {"filename": "src/file1.py"},
        {"filename": "types.py"},
        {"filename": "src/file2.py"},
    ]
    all_mocks["is_code_file"].return_value = True
    all_mocks["is_test_file"].return_value = False
    all_mocks["is_type_file"].side_effect = lambda f: "types" in f
    all_mocks["get_coverages"].return_value = {}
    all_mocks["create_file_checklist"].return_value = [
        {"path": "src/file1.py", "checked": True, "coverage_info": "", "status": "added"}
    ]
    all_mocks["create_test_selection_comment"].return_value = "Test comment"

    create_pr_checkbox_comment(payload)

    all_mocks["get_coverages"].assert_called_once_with(
        repo_id=12345, filenames=["src/file1.py", "src/file2.py"]
    )


def test_filters_non_code_files_correctly(all_mocks):
    """Test that non-code files are filtered out correctly."""
    payload = create_test_payload()
    all_mocks["get_repository"].return_value = {"trigger_on_pr_change": True}
    all_mocks["get_pull_request_files"].return_value = [
        {"filename": "src/file1.py"},
        {"filename": "README.md"},
        {"filename": "src/file2.py"},
    ]
    all_mocks["is_code_file"].side_effect = lambda f: f.endswith(".py")
    all_mocks["is_test_file"].return_value = False
    all_mocks["is_type_file"].return_value = False
    all_mocks["get_coverages"].return_value = {}
    all_mocks["create_file_checklist"].return_value = [
        {"path": "src/file1.py", "checked": True, "coverage_info": "", "status": "added"}
    ]
    all_mocks["create_test_selection_comment"].return_value = "Test comment"

    create_pr_checkbox_comment(payload)

    all_mocks["get_coverages"].assert_called_once_with(
        repo_id=12345, filenames=["src/file1.py", "src/file2.py"]
    )


def test_passes_correct_base_args_to_delete_comments(all_mocks):
    """Test that correct base_args are passed to delete_comments_by_identifiers."""
    payload = create_test_payload(
        owner_name="my-owner", repo_name="my-repo", pull_number=99
    )
    all_mocks["get_repository"].return_value = {"trigger_on_pr_change": True}
    all_mocks["get_pull_request_files"].return_value = [{"filename": "src/file1.py"}]
    all_mocks["is_code_file"].return_value = True
    all_mocks["is_test_file"].return_value = False
    all_mocks["is_type_file"].return_value = False
    all_mocks["get_coverages"].return_value = {}
    all_mocks["create_file_checklist"].return_value = [
        {"path": "src/file1.py", "checked": True, "coverage_info": "", "status": "added"}
    ]
    all_mocks["create_test_selection_comment"].return_value = "Test comment"

    create_pr_checkbox_comment(payload)

    call_args = all_mocks["delete_comments_by_identifiers"].call_args
    base_args = call_args.kwargs["base_args"]
    assert base_args["owner"] == "my-owner"
    assert base_args["repo"] == "my-repo"
    assert base_args["issue_number"] == 99
    assert base_args["token"] == "test-token-123"


def test_passes_correct_args_to_combine_and_create_comment(all_mocks):
    """Test that correct arguments are passed to combine_and_create_comment."""
    payload = create_test_payload(
        sender_name="john-doe",
        owner_name="my-owner",
        owner_id=55555,
        installation_id=22222,
    )
    all_mocks["get_repository"].return_value = {"trigger_on_pr_change": True}
    all_mocks["get_pull_request_files"].return_value = [{"filename": "src/file1.py"}]
    all_mocks["is_code_file"].return_value = True
    all_mocks["is_test_file"].return_value = False
    all_mocks["is_type_file"].return_value = False
    all_mocks["get_coverages"].return_value = {}
    all_mocks["create_file_checklist"].return_value = [
        {"path": "src/file1.py", "checked": True, "coverage_info": "", "status": "added"}
    ]
    all_mocks["create_test_selection_comment"].return_value = "Test comment"

    create_pr_checkbox_comment(payload)

    call_args = all_mocks["combine_and_create_comment"].call_args
    assert call_args.kwargs["base_comment"] == "Test comment"
    assert call_args.kwargs["installation_id"] == 22222
    assert call_args.kwargs["owner_id"] == 55555
    assert call_args.kwargs["owner_name"] == "my-owner"
    assert call_args.kwargs["sender_name"] == "john-doe"


def test_uses_branch_name_from_pull_request(all_mocks):
    """Test that branch name is correctly extracted from pull request."""
    payload = create_test_payload(branch_name="feature/new-feature")
    all_mocks["get_repository"].return_value = {"trigger_on_pr_change": True}
    all_mocks["get_pull_request_files"].return_value = [{"filename": "src/file1.py"}]
    all_mocks["is_code_file"].return_value = True
    all_mocks["is_test_file"].return_value = False
    all_mocks["is_type_file"].return_value = False
    all_mocks["get_coverages"].return_value = {}
    all_mocks["create_file_checklist"].return_value = [
        {"path": "src/file1.py", "checked": True, "coverage_info": "", "status": "added"}
    ]
    all_mocks["create_test_selection_comment"].return_value = "Test comment"

    create_pr_checkbox_comment(payload)

    all_mocks["create_test_selection_comment"].assert_called_once()
    call_args = all_mocks["create_test_selection_comment"].call_args
    assert call_args[0][1] == "feature/new-feature"


def test_handles_multiple_code_files(all_mocks):
    """Test handling of multiple code files."""
    payload = create_test_payload()
    all_mocks["get_repository"].return_value = {"trigger_on_pr_change": True}
    all_mocks["get_pull_request_files"].return_value = [
        {"filename": "src/file1.py"},
        {"filename": "src/file2.py"},
        {"filename": "src/file3.py"},
        {"filename": "test_file.py"},
        {"filename": "README.md"},
    ]
    all_mocks["is_code_file"].side_effect = lambda f: f.endswith(".py")
    all_mocks["is_test_file"].side_effect = lambda f: "test_" in f
    all_mocks["is_type_file"].return_value = False
    all_mocks["get_coverages"].return_value = {}
    all_mocks["create_file_checklist"].return_value = [
        {"path": "src/file1.py", "checked": True, "coverage_info": "", "status": "added"}
    ]
    all_mocks["create_test_selection_comment"].return_value = "Test comment"

    create_pr_checkbox_comment(payload)

    all_mocks["get_coverages"].assert_called_once_with(
        repo_id=12345, filenames=["src/file1.py", "src/file2.py", "src/file3.py"]
    )


def test_bot_names_with_different_formats(all_mocks):
    """Test that different bot name formats are handled correctly."""
    bot_names = [
        "dependabot[bot]",
        "github-actions[bot]",
        "renovate[bot]",
        "codecov[bot]",
    ]

    for bot_name in bot_names:
        payload = create_test_payload(sender_name=bot_name)
        result = create_pr_checkbox_comment(payload)
        assert result is None


def test_non_bot_names_are_processed(all_mocks):
    """Test that non-bot names are processed normally."""
    payload = create_test_payload(sender_name="regular-user")
    all_mocks["get_repository"].return_value = {"trigger_on_pr_change": True}
    all_mocks["get_pull_request_files"].return_value = [{"filename": "src/file1.py"}]
    all_mocks["is_code_file"].return_value = True
    all_mocks["is_test_file"].return_value = False
    all_mocks["is_type_file"].return_value = False
    all_mocks["get_coverages"].return_value = {}
    all_mocks["create_file_checklist"].return_value = [
        {"path": "src/file1.py", "checked": True, "coverage_info": "", "status": "added"}
    ]
    all_mocks["create_test_selection_comment"].return_value = "Test comment"

    create_pr_checkbox_comment(payload)

    all_mocks["combine_and_create_comment"].assert_called_once()


def test_coverage_data_passed_to_checklist(all_mocks):
    """Test that coverage data is correctly passed to create_file_checklist."""
    payload = create_test_payload()
    all_mocks["get_repository"].return_value = {"trigger_on_pr_change": True}
    all_mocks["get_pull_request_files"].return_value = [{"filename": "src/file1.py"}]
    all_mocks["is_code_file"].return_value = True
    all_mocks["is_test_file"].return_value = False
    all_mocks["is_type_file"].return_value = False
    coverage_data = {"src/file1.py": {"line_coverage": 80.0}}
    all_mocks["get_coverages"].return_value = coverage_data
    all_mocks["create_file_checklist"].return_value = [
        {"path": "src/file1.py", "checked": True, "coverage_info": "", "status": "added"}
    ]
    all_mocks["create_test_selection_comment"].return_value = "Test comment"

    create_pr_checkbox_comment(payload)

    call_args = all_mocks["create_file_checklist"].call_args
    assert call_args[0][1] == coverage_data


def test_checklist_passed_to_comment_creation(all_mocks):
    """Test that checklist is correctly passed to create_test_selection_comment."""
    payload = create_test_payload()
    all_mocks["get_repository"].return_value = {"trigger_on_pr_change": True}
    all_mocks["get_pull_request_files"].return_value = [{"filename": "src/file1.py"}]
    all_mocks["is_code_file"].return_value = True
    all_mocks["is_test_file"].return_value = False
    all_mocks["is_type_file"].return_value = False
    all_mocks["get_coverages"].return_value = {}
    checklist = [
        {"path": "src/file1.py", "checked": True, "coverage_info": "", "status": "added"}
    ]
    all_mocks["create_file_checklist"].return_value = checklist
    all_mocks["create_test_selection_comment"].return_value = "Test comment"

    create_pr_checkbox_comment(payload)

    call_args = all_mocks["create_test_selection_comment"].call_args
    assert call_args[0][0] == checklist
