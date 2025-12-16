from unittest.mock import patch


import pytest

from services.webhook.utils.create_pr_checkbox_comment import (
    create_pr_checkbox_comment,
)


@pytest.fixture
def mock_get_installation_access_token():
    """Mock get_installation_access_token function."""
    with patch(
        "services.webhook.utils.create_pr_checkbox_comment.get_installation_access_token"
    ) as mock:
        mock.return_value = "test-token-123"
        yield mock


@pytest.fixture
def mock_get_repository():
    """Mock get_repository function."""
    with patch(
        "services.webhook.utils.create_pr_checkbox_comment.get_repository"
    ) as mock:
        yield mock


@pytest.fixture
def mock_get_pull_request_files():
    """Mock get_pull_request_files function."""
    with patch(
        "services.webhook.utils.create_pr_checkbox_comment.get_pull_request_files"
    ) as mock:
        yield mock


@pytest.fixture
def mock_get_coverages():
    """Mock get_coverages function."""
    with patch(
        "services.webhook.utils.create_pr_checkbox_comment.get_coverages"
    ) as mock:
        yield mock


@pytest.fixture
def mock_is_code_file():
    """Mock is_code_file function."""
    with patch(
        "services.webhook.utils.create_pr_checkbox_comment.is_code_file"
    ) as mock:
        yield mock


@pytest.fixture
def mock_is_test_file():
    """Mock is_test_file function."""
    with patch(
        "services.webhook.utils.create_pr_checkbox_comment.is_test_file"
    ) as mock:
        yield mock


@pytest.fixture
def mock_is_type_file():
    """Mock is_type_file function."""
    with patch(
        "services.webhook.utils.create_pr_checkbox_comment.is_type_file"
    ) as mock:
        yield mock


@pytest.fixture
def mock_create_file_checklist():
    """Mock create_file_checklist function."""
    with patch(
        "services.webhook.utils.create_pr_checkbox_comment.create_file_checklist"
    ) as mock:
        yield mock


@pytest.fixture
def mock_create_test_selection_comment():
    """Mock create_test_selection_comment function."""
    with patch(
        "services.webhook.utils.create_pr_checkbox_comment.create_test_selection_comment"
    ) as mock:
        yield mock


@pytest.fixture
def mock_delete_comments_by_identifiers():
    """Mock delete_comments_by_identifiers function."""
    with patch(
        "services.webhook.utils.create_pr_checkbox_comment.delete_comments_by_identifiers"
    ) as mock:
        yield mock


@pytest.fixture
def mock_combine_and_create_comment():
    """Mock combine_and_create_comment function."""
    with patch(
        "services.webhook.utils.create_pr_checkbox_comment.combine_and_create_comment"
    ) as mock:
        yield mock


@pytest.fixture
def mock_logging():
    """Mock logging module."""
    with patch("services.webhook.utils.create_pr_checkbox_comment.logging") as mock:
        yield mock


def create_test_payload(
    sender_name="test-user",
    repo_id=12345,
    repo_name="test-repo",
    owner_id=67890,
    owner_name="test-owner",
    pull_number=42,
    pull_url="https://api.github.com/repos/test-owner/test-repo/pulls/42",
    installation_id=11111,
    branch_name="feature-branch",
):
    """Helper function to create a test payload."""
    return {
        "sender": {"login": sender_name},
        "repository": {
            "id": repo_id,
            "name": repo_name,
            "owner": {"id": owner_id, "login": owner_name},
        },
        "pull_request": {
            "number": pull_number,
            "url": pull_url,
            "head": {"ref": branch_name},
        },
        "installation": {"id": installation_id},
    }


def test_skips_bot_sender(
    mock_logging,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_pull_request_files,
    mock_get_coverages,
    mock_is_code_file,
    mock_is_test_file,
    mock_is_type_file,
    mock_create_file_checklist,
    mock_create_test_selection_comment,
    mock_delete_comments_by_identifiers,
    mock_combine_and_create_comment,
):
    """Test that the function skips processing when sender is a bot."""
    payload = create_test_payload(sender_name="dependabot[bot]")

    result = create_pr_checkbox_comment(payload)

    assert result is None
    mock_logging.info.assert_called_once()
    assert "Skipping PR test selection for bot dependabot[bot]" in str(
        mock_logging.info.call_args
    )
    mock_get_repository.assert_not_called()
    mock_get_installation_access_token.assert_not_called()
    mock_get_pull_request_files.assert_not_called()


def test_skips_when_repository_not_found(
    mock_logging,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_pull_request_files,
    mock_get_coverages,
    mock_is_code_file,
    mock_is_test_file,
    mock_is_type_file,
    mock_create_file_checklist,
    mock_create_test_selection_comment,
    mock_delete_comments_by_identifiers,
    mock_combine_and_create_comment,
):
    """Test that the function skips when repository settings are not found."""
    payload = create_test_payload()
    mock_get_repository.return_value = None

    result = create_pr_checkbox_comment(payload)

    assert result is None
    mock_logging.info.assert_called_once()
    assert (
        "Skipping PR test selection for repo test-repo because trigger_on_pr_change is False"
        in str(mock_logging.info.call_args)
    )
    mock_get_installation_access_token.assert_not_called()
    mock_get_pull_request_files.assert_not_called()


def test_skips_when_trigger_on_pr_change_is_false(
    mock_logging,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_pull_request_files,
    mock_get_coverages,
    mock_is_code_file,
    mock_is_test_file,
    mock_is_type_file,
    mock_create_file_checklist,
    mock_create_test_selection_comment,
    mock_delete_comments_by_identifiers,
    mock_combine_and_create_comment,
):
    """Test that the function skips when trigger_on_pr_change is False."""
    payload = create_test_payload()
    mock_get_repository.return_value = {"trigger_on_pr_change": False}

    result = create_pr_checkbox_comment(payload)

    assert result is None
    mock_logging.info.assert_called_once()
    assert (
        "Skipping PR test selection for repo test-repo because trigger_on_pr_change is False"
        in str(mock_logging.info.call_args)
    )
    mock_get_installation_access_token.assert_not_called()
    mock_get_pull_request_files.assert_not_called()


def test_skips_when_no_code_files_changed(
    mock_logging,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_pull_request_files,
    mock_get_coverages,
    mock_is_code_file,
    mock_is_test_file,
    mock_is_type_file,
    mock_create_file_checklist,
    mock_create_test_selection_comment,
    mock_delete_comments_by_identifiers,
    mock_combine_and_create_comment,
):
    """Test that the function skips when no code files are changed."""
    payload = create_test_payload()
    mock_get_repository.return_value = {"trigger_on_pr_change": True}
    mock_get_pull_request_files.return_value = [
        {"filename": "test_file.py"},
        {"filename": "types.py"},
    ]
    mock_is_code_file.return_value = True
    mock_is_test_file.side_effect = lambda f: f == "test_file.py"
    mock_is_type_file.side_effect = lambda f: f == "types.py"

    result = create_pr_checkbox_comment(payload)

    assert result is None
    mock_logging.info.assert_called()
    assert (
        "Skipping PR test selection for repo test-repo because no code files were changed"
        in str(mock_logging.info.call_args)
    )
    mock_get_coverages.assert_not_called()
    mock_create_file_checklist.assert_not_called()


def test_successful_comment_creation(
    mock_logging,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_pull_request_files,
    mock_get_coverages,
    mock_is_code_file,
    mock_is_test_file,
    mock_is_type_file,
    mock_create_file_checklist,
    mock_create_test_selection_comment,
    mock_delete_comments_by_identifiers,
    mock_combine_and_create_comment,
):
    """Test successful creation of PR checkbox comment."""
    payload = create_test_payload()
    mock_get_repository.return_value = {"trigger_on_pr_change": True}
    mock_get_pull_request_files.return_value = [
        {"filename": "src/file1.py"},
        {"filename": "src/file2.py"},
    ]
    mock_is_code_file.return_value = True
    mock_is_test_file.return_value = False
    mock_is_type_file.return_value = False
    mock_get_coverages.return_value = {"src/file1.py": {}, "src/file2.py": {}}
    mock_create_file_checklist.return_value = [
        {"path": "src/file1.py", "checked": True},
        {"path": "src/file2.py", "checked": True},
    ]
    mock_create_test_selection_comment.return_value = "Test selection comment"

    result = create_pr_checkbox_comment(payload)

    assert result is None
    mock_get_repository.assert_called_once_with(repo_id=12345)
    mock_get_installation_access_token.assert_called_once_with(installation_id=11111)
    mock_get_pull_request_files.assert_called_once_with(
        url="https://api.github.com/repos/test-owner/test-repo/pulls/42/files",
        token="test-token-123",
    )
    mock_get_coverages.assert_called_once_with(
        repo_id=12345, filenames=["src/file1.py", "src/file2.py"]
    )
    mock_create_file_checklist.assert_called_once()
    mock_create_test_selection_comment.assert_called_once()
    mock_delete_comments_by_identifiers.assert_called_once()
    mock_combine_and_create_comment.assert_called_once()


def test_filters_test_files_correctly(
    mock_logging,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_pull_request_files,
    mock_get_coverages,
    mock_is_code_file,
    mock_is_test_file,
    mock_is_type_file,
    mock_create_file_checklist,
    mock_create_test_selection_comment,
    mock_delete_comments_by_identifiers,
    mock_combine_and_create_comment,
):
    """Test that test files are filtered out correctly."""
    payload = create_test_payload()
    mock_get_repository.return_value = {"trigger_on_pr_change": True}
    mock_get_pull_request_files.return_value = [
        {"filename": "src/file.py"},
        {"filename": "test_file.py"},
    ]
    mock_is_code_file.return_value = True
    mock_is_test_file.side_effect = lambda f: "test_" in f
    mock_is_type_file.return_value = False
    mock_get_coverages.return_value = {"src/file.py": {}}
    mock_create_file_checklist.return_value = [{"path": "src/file.py", "checked": True}]
    mock_create_test_selection_comment.return_value = "Test selection comment"

    result = create_pr_checkbox_comment(payload)

    assert result is None
    mock_get_coverages.assert_called_once_with(repo_id=12345, filenames=["src/file.py"])


def test_filters_type_files_correctly(
    mock_logging,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_pull_request_files,
    mock_get_coverages,
    mock_is_code_file,
    mock_is_test_file,
    mock_is_type_file,
    mock_create_file_checklist,
    mock_create_test_selection_comment,
    mock_delete_comments_by_identifiers,
    mock_combine_and_create_comment,
):
    """Test that type files are filtered out correctly."""
    payload = create_test_payload()
    mock_get_repository.return_value = {"trigger_on_pr_change": True}
    mock_get_pull_request_files.return_value = [
        {"filename": "src/file.py"},
        {"filename": "types.py"},
    ]
    mock_is_code_file.return_value = True
    mock_is_test_file.return_value = False
    mock_is_type_file.side_effect = lambda f: "types" in f
    mock_get_coverages.return_value = {"src/file.py": {}}
    mock_create_file_checklist.return_value = [{"path": "src/file.py", "checked": True}]
    mock_create_test_selection_comment.return_value = "Test selection comment"

    result = create_pr_checkbox_comment(payload)

    assert result is None
    mock_get_coverages.assert_called_once_with(repo_id=12345, filenames=["src/file.py"])


def test_filters_non_code_files_correctly(
    mock_logging,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_pull_request_files,
    mock_get_coverages,
    mock_is_code_file,
    mock_is_test_file,
    mock_is_type_file,
    mock_create_file_checklist,
    mock_create_test_selection_comment,
    mock_delete_comments_by_identifiers,
    mock_combine_and_create_comment,
):
    """Test that non-code files are filtered out correctly."""
    payload = create_test_payload()
    mock_get_repository.return_value = {"trigger_on_pr_change": True}
    mock_get_pull_request_files.return_value = [
        {"filename": "src/file.py"},
        {"filename": "README.md"},
    ]
    mock_is_code_file.side_effect = lambda f: f.endswith(".py")
    mock_is_test_file.return_value = False
    mock_is_type_file.return_value = False
    mock_get_coverages.return_value = {"src/file.py": {}}
    mock_create_file_checklist.return_value = [{"path": "src/file.py", "checked": True}]
    mock_create_test_selection_comment.return_value = "Test selection comment"

    result = create_pr_checkbox_comment(payload)

    assert result is None
    mock_get_coverages.assert_called_once_with(repo_id=12345, filenames=["src/file.py"])


def test_passes_correct_base_args_to_delete_comments(
    mock_logging,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_pull_request_files,
    mock_get_coverages,
    mock_is_code_file,
    mock_is_test_file,
    mock_is_type_file,
    mock_create_file_checklist,
    mock_create_test_selection_comment,
    mock_delete_comments_by_identifiers,
    mock_combine_and_create_comment,
):
    """Test that correct base_args are passed to delete_comments_by_identifiers."""
    payload = create_test_payload(
        owner_name="test-owner", repo_name="test-repo", pull_number=42
    )
    mock_get_repository.return_value = {"trigger_on_pr_change": True}
    mock_get_pull_request_files.return_value = [{"filename": "src/file.py"}]
    mock_is_code_file.return_value = True
    mock_is_test_file.return_value = False
    mock_is_type_file.return_value = False
    mock_get_coverages.return_value = {"src/file.py": {}}
    mock_create_file_checklist.return_value = [{"path": "src/file.py", "checked": True}]
    mock_create_test_selection_comment.return_value = "Test selection comment"

    create_pr_checkbox_comment(payload)

    mock_delete_comments_by_identifiers.assert_called_once()
    call_args = mock_delete_comments_by_identifiers.call_args
    base_args = call_args[1]["base_args"]
    assert base_args["owner"] == "test-owner"
    assert base_args["repo"] == "test-repo"
    assert base_args["issue_number"] == 42
    assert base_args["token"] == "test-token-123"


def test_passes_correct_args_to_combine_and_create_comment(
    mock_logging,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_pull_request_files,
    mock_get_coverages,
    mock_is_code_file,
    mock_is_test_file,
    mock_is_type_file,
    mock_create_file_checklist,
    mock_create_test_selection_comment,
    mock_delete_comments_by_identifiers,
    mock_combine_and_create_comment,
):
    """Test that correct arguments are passed to combine_and_create_comment."""
    payload = create_test_payload(
        sender_name="test-sender",
        owner_id=67890,
        owner_name="test-owner",
        installation_id=11111,
    )
    mock_get_repository.return_value = {"trigger_on_pr_change": True}
    mock_get_pull_request_files.return_value = [{"filename": "src/file.py"}]
    mock_is_code_file.return_value = True
    mock_is_test_file.return_value = False
    mock_is_type_file.return_value = False
    mock_get_coverages.return_value = {"src/file.py": {}}
    mock_create_file_checklist.return_value = [{"path": "src/file.py", "checked": True}]
    mock_create_test_selection_comment.return_value = "Test selection comment"

    create_pr_checkbox_comment(payload)

    mock_combine_and_create_comment.assert_called_once()
    call_args = mock_combine_and_create_comment.call_args
    assert call_args[1]["base_comment"] == "Test selection comment"
    assert call_args[1]["installation_id"] == 11111
    assert call_args[1]["owner_id"] == 67890
    assert call_args[1]["owner_name"] == "test-owner"
    assert call_args[1]["sender_name"] == "test-sender"


def test_handles_multiple_code_files(
    mock_logging,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_pull_request_files,
    mock_get_coverages,
    mock_is_code_file,
    mock_is_test_file,
    mock_is_type_file,
    mock_create_file_checklist,
    mock_create_test_selection_comment,
    mock_delete_comments_by_identifiers,
    mock_combine_and_create_comment,
):
    """Test handling of multiple code files."""
    payload = create_test_payload()
    mock_get_repository.return_value = {"trigger_on_pr_change": True}
    mock_get_pull_request_files.return_value = [
        {"filename": "src/file1.py"},
        {"filename": "src/file2.py"},
        {"filename": "src/file3.py"},
    ]
    mock_is_code_file.return_value = True
    mock_is_test_file.return_value = False
    mock_is_type_file.return_value = False
    mock_get_coverages.return_value = {
        "src/file1.py": {},
        "src/file2.py": {},
        "src/file3.py": {},
    }
    mock_create_file_checklist.return_value = [
        {"path": "src/file1.py", "checked": True},
        {"path": "src/file2.py", "checked": True},
        {"path": "src/file3.py", "checked": True},
    ]
    mock_create_test_selection_comment.return_value = "Test selection comment"

    result = create_pr_checkbox_comment(payload)

    assert result is None
    mock_get_coverages.assert_called_once_with(
        repo_id=12345, filenames=["src/file1.py", "src/file2.py", "src/file3.py"]
    )


def test_handles_mixed_file_types(
    mock_logging,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_pull_request_files,
    mock_get_coverages,
    mock_is_code_file,
    mock_is_test_file,
    mock_is_type_file,
    mock_create_file_checklist,
    mock_create_test_selection_comment,
    mock_delete_comments_by_identifiers,
    mock_combine_and_create_comment,
):
    """Test handling of mixed file types (code, test, type, non-code)."""
    payload = create_test_payload()
    mock_get_repository.return_value = {"trigger_on_pr_change": True}
    mock_get_pull_request_files.return_value = [
        {"filename": "src/code.py"},
        {"filename": "test_code.py"},
        {"filename": "types.py"},
        {"filename": "README.md"},
    ]

    def is_code_file_side_effect(filename):
        return filename.endswith(".py")

    def is_test_file_side_effect(filename):
        return filename.startswith("test_")

    def is_type_file_side_effect(filename):
        return "types" in filename

    mock_is_code_file.side_effect = is_code_file_side_effect
    mock_is_test_file.side_effect = is_test_file_side_effect
    mock_is_type_file.side_effect = is_type_file_side_effect
    mock_get_coverages.return_value = {"src/code.py": {}}
    mock_create_file_checklist.return_value = [{"path": "src/code.py", "checked": True}]
    mock_create_test_selection_comment.return_value = "Test selection comment"

    result = create_pr_checkbox_comment(payload)

    assert result is None
    mock_get_coverages.assert_called_once_with(repo_id=12345, filenames=["src/code.py"])


def test_extracts_branch_name_correctly(
    mock_logging,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_pull_request_files,
    mock_get_coverages,
    mock_is_code_file,
    mock_is_test_file,
    mock_is_type_file,
    mock_create_file_checklist,
    mock_create_test_selection_comment,
    mock_delete_comments_by_identifiers,
    mock_combine_and_create_comment,
):
    """Test that branch name is extracted correctly from payload."""
    payload = create_test_payload(branch_name="feature/new-feature")
    mock_get_repository.return_value = {"trigger_on_pr_change": True}
    mock_get_pull_request_files.return_value = [{"filename": "src/file.py"}]
    mock_is_code_file.return_value = True
    mock_is_test_file.return_value = False
    mock_is_type_file.return_value = False
    mock_get_coverages.return_value = {"src/file.py": {}}
    mock_create_file_checklist.return_value = [{"path": "src/file.py", "checked": True}]
    mock_create_test_selection_comment.return_value = "Test selection comment"

    create_pr_checkbox_comment(payload)

    mock_create_test_selection_comment.assert_called_once()
    call_args = mock_create_test_selection_comment.call_args
    assert call_args[0][1] == "feature/new-feature"


def test_bot_with_different_suffixes(
    mock_logging,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_pull_request_files,
    mock_get_coverages,
    mock_is_code_file,
    mock_is_test_file,
    mock_is_type_file,
    mock_create_file_checklist,
    mock_create_test_selection_comment,
    mock_delete_comments_by_identifiers,
    mock_combine_and_create_comment,
):
    """Test that different bot name suffixes are handled correctly."""
    bot_names = [
        "dependabot[bot]",
        "github-actions[bot]",
        "renovate[bot]",
        "gitauto[bot]",
    ]

    for bot_name in bot_names:
        payload = create_test_payload(sender_name=bot_name)
        result = create_pr_checkbox_comment(payload)
        assert result is None
        mock_get_repository.assert_not_called()


def test_non_bot_user_is_processed(
    mock_logging,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_pull_request_files,
    mock_get_coverages,
    mock_is_code_file,
    mock_is_test_file,
    mock_is_type_file,
    mock_create_file_checklist,
    mock_create_test_selection_comment,
    mock_delete_comments_by_identifiers,
    mock_combine_and_create_comment,
):
    """Test that non-bot users are processed normally."""
    payload = create_test_payload(sender_name="regular-user")
    mock_get_repository.return_value = {"trigger_on_pr_change": True}
    mock_get_pull_request_files.return_value = [{"filename": "src/file.py"}]
    mock_is_code_file.return_value = True
    mock_is_test_file.return_value = False
    mock_is_type_file.return_value = False
    mock_get_coverages.return_value = {"src/file.py": {}}
    mock_create_file_checklist.return_value = [{"path": "src/file.py", "checked": True}]
    mock_create_test_selection_comment.return_value = "Test selection comment"

    result = create_pr_checkbox_comment(payload)

    assert result is None
    mock_get_repository.assert_called_once()
    mock_combine_and_create_comment.assert_called_once()


def test_empty_changed_files_list(
    mock_logging,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_pull_request_files,
    mock_get_coverages,
    mock_is_code_file,
    mock_is_test_file,
    mock_is_type_file,
    mock_create_file_checklist,
    mock_create_test_selection_comment,
    mock_delete_comments_by_identifiers,
    mock_combine_and_create_comment,
):
    """Test handling of empty changed files list."""
    payload = create_test_payload()
    mock_get_repository.return_value = {"trigger_on_pr_change": True}
    mock_get_pull_request_files.return_value = []

    result = create_pr_checkbox_comment(payload)

    assert result is None
    mock_logging.info.assert_called()
    assert (
        "Skipping PR test selection for repo test-repo because no code files were changed"
        in str(mock_logging.info.call_args)
    )


def test_coverage_data_passed_to_checklist(
    mock_logging,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_pull_request_files,
    mock_get_coverages,
    mock_is_code_file,
    mock_is_test_file,
    mock_is_type_file,
    mock_create_file_checklist,
    mock_create_test_selection_comment,
    mock_delete_comments_by_identifiers,
    mock_combine_and_create_comment,
):
    """Test that coverage data is correctly passed to create_file_checklist."""
    payload = create_test_payload()
    mock_get_repository.return_value = {"trigger_on_pr_change": True}
    changed_files = [{"filename": "src/file.py"}]
    mock_get_pull_request_files.return_value = changed_files
    mock_is_code_file.return_value = True
    mock_is_test_file.return_value = False
    mock_is_type_file.return_value = False
    coverage_data = {"src/file.py": {"line_coverage": 80.0}}
    mock_get_coverages.return_value = coverage_data
    mock_create_file_checklist.return_value = [{"path": "src/file.py", "checked": True}]
    mock_create_test_selection_comment.return_value = "Test selection comment"

    create_pr_checkbox_comment(payload)

    mock_create_file_checklist.assert_called_once()
    call_args = mock_create_file_checklist.call_args
    assert call_args[0][0] == changed_files
    assert call_args[0][1] == coverage_data


def test_checklist_passed_to_comment_creation(
    mock_logging,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_pull_request_files,
    mock_get_coverages,
    mock_is_code_file,
    mock_is_test_file,
    mock_is_type_file,
    mock_create_file_checklist,
    mock_create_test_selection_comment,
    mock_delete_comments_by_identifiers,
    mock_combine_and_create_comment,
):
    """Test that checklist is correctly passed to create_test_selection_comment."""
    payload = create_test_payload()
    mock_get_repository.return_value = {"trigger_on_pr_change": True}
    mock_get_pull_request_files.return_value = [{"filename": "src/file.py"}]
    mock_is_code_file.return_value = True
    mock_is_test_file.return_value = False
    mock_is_type_file.return_value = False
    mock_get_coverages.return_value = {"src/file.py": {}}
    checklist = [{"path": "src/file.py", "checked": True}]
    mock_create_file_checklist.return_value = checklist
    mock_create_test_selection_comment.return_value = "Test selection comment"

    create_pr_checkbox_comment(payload)

    mock_create_test_selection_comment.assert_called_once()
    call_args = mock_create_test_selection_comment.call_args
    assert call_args[0][0] == checklist


def test_pull_files_url_construction(
    mock_logging,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_pull_request_files,
    mock_get_coverages,
    mock_is_code_file,
    mock_is_test_file,
    mock_is_type_file,
    mock_create_file_checklist,
    mock_create_test_selection_comment,
    mock_delete_comments_by_identifiers,
    mock_combine_and_create_comment,
):
    """Test that pull files URL is constructed correctly."""
    payload = create_test_payload(
        pull_url="https://api.github.com/repos/owner/repo/pulls/123"
    )
    mock_get_repository.return_value = {"trigger_on_pr_change": True}
    mock_get_pull_request_files.return_value = [{"filename": "src/file.py"}]
    mock_is_code_file.return_value = True
    mock_is_test_file.return_value = False
    mock_is_type_file.return_value = False
    mock_get_coverages.return_value = {"src/file.py": {}}
    mock_create_file_checklist.return_value = [{"path": "src/file.py", "checked": True}]
    mock_create_test_selection_comment.return_value = "Test selection comment"

    create_pr_checkbox_comment(payload)

    mock_get_pull_request_files.assert_called_once()
    call_args = mock_get_pull_request_files.call_args
    assert call_args[1]["url"] == "https://api.github.com/repos/owner/repo/pulls/123/files"


def test_installation_token_used_correctly(
    mock_logging,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_pull_request_files,
    mock_get_coverages,
    mock_is_code_file,
    mock_is_test_file,
    mock_is_type_file,
    mock_create_file_checklist,
    mock_create_test_selection_comment,
    mock_delete_comments_by_identifiers,
    mock_combine_and_create_comment,
):
    """Test that installation token is retrieved and used correctly."""
    payload = create_test_payload(installation_id=99999)
    mock_get_repository.return_value = {"trigger_on_pr_change": True}
    mock_get_installation_access_token.return_value = "custom-token-xyz"
    mock_get_pull_request_files.return_value = [{"filename": "src/file.py"}]
    mock_is_code_file.return_value = True
    mock_is_test_file.return_value = False
    mock_is_type_file.return_value = False
    mock_get_coverages.return_value = {"src/file.py": {}}
    mock_create_file_checklist.return_value = [{"path": "src/file.py", "checked": True}]
    mock_create_test_selection_comment.return_value = "Test selection comment"

    create_pr_checkbox_comment(payload)

    mock_get_installation_access_token.assert_called_once_with(installation_id=99999)
    mock_get_pull_request_files.assert_called_once()
    call_args = mock_get_pull_request_files.call_args
    assert call_args[1]["token"] == "custom-token-xyz"


def test_delete_comments_called_with_correct_identifier(
    mock_logging,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_pull_request_files,
    mock_get_coverages,
    mock_is_code_file,
    mock_is_test_file,
    mock_is_type_file,
    mock_create_file_checklist,
    mock_create_test_selection_comment,
    mock_delete_comments_by_identifiers,
    mock_combine_and_create_comment,
):
    """Test that delete_comments_by_identifiers is called with correct identifier."""
    payload = create_test_payload()
    mock_get_repository.return_value = {"trigger_on_pr_change": True}
    mock_get_pull_request_files.return_value = [{"filename": "src/file.py"}]
    mock_is_code_file.return_value = True
    mock_is_test_file.return_value = False
    mock_is_type_file.return_value = False
    mock_get_coverages.return_value = {"src/file.py": {}}
    mock_create_file_checklist.return_value = [{"path": "src/file.py", "checked": True}]
    mock_create_test_selection_comment.return_value = "Test selection comment"

    create_pr_checkbox_comment(payload)

    mock_delete_comments_by_identifiers.assert_called_once()
    call_args = mock_delete_comments_by_identifiers.call_args
    from utils.text.comment_identifiers import \
        TEST_SELECTION_COMMENT_IDENTIFIER

    assert call_args[1]["identifiers"] == [TEST_SELECTION_COMMENT_IDENTIFIER]


def test_all_file_filtering_conditions(
    mock_logging,
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_pull_request_files,
    mock_get_coverages,
    mock_is_code_file,
    mock_is_test_file,
    mock_is_type_file,
    mock_create_file_checklist,
    mock_create_test_selection_comment,
    mock_delete_comments_by_identifiers,
    mock_combine_and_create_comment,
):
    """Test that all file filtering conditions work together correctly."""
    payload = create_test_payload()
    mock_get_repository.return_value = {"trigger_on_pr_change": True}
    mock_get_pull_request_files.return_value = [
        {"filename": "src/code.py"},
        {"filename": "test_code.py"},
        {"filename": "types.py"},
        {"filename": "README.md"},
        {"filename": "src/another_code.py"},
    ]

    def is_code_file_side_effect(filename):
        return filename.endswith(".py")

    def is_test_file_side_effect(filename):
        return filename.startswith("test_")

    def is_type_file_side_effect(filename):
        return "types" in filename

    mock_is_code_file.side_effect = is_code_file_side_effect
    mock_is_test_file.side_effect = is_test_file_side_effect
    mock_is_type_file.side_effect = is_type_file_side_effect
    mock_get_coverages.return_value = {"src/code.py": {}, "src/another_code.py": {}}
    mock_create_file_checklist.return_value = [
        {"path": "src/code.py", "checked": True},
        {"path": "src/another_code.py", "checked": True},
    ]
    mock_create_test_selection_comment.return_value = "Test selection comment"

    create_pr_checkbox_comment(payload)

    mock_get_coverages.assert_called_once_with(
        repo_id=12345, filenames=["src/code.py", "src/another_code.py"]
    )
