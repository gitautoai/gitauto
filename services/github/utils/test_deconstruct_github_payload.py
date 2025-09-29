"""Unit tests for deconstruct_github_payload function."""

from datetime import datetime
from unittest.mock import patch, MagicMock
import pytest

from services.github.utils.deconstruct_github_payload import deconstruct_github_payload


@pytest.fixture
def mock_datetime():
    """Mock datetime to ensure consistent test results."""
    with patch('services.github.utils.deconstruct_github_payload.datetime') as mock_dt:
        mock_dt.now.return_value.strftime.side_effect = lambda format: {
            "%Y%m%d": "20241224",
            "%H%M%S": "120000"
        }[format]
        yield mock_dt


@pytest.fixture
def mock_choices():
    """Mock random choices to ensure consistent test results."""
    with patch('services.github.utils.deconstruct_github_payload.choices') as mock_choices:
        mock_choices.return_value = ['A', 'B', 'C', 'D']
        yield mock_choices


@pytest.fixture
def mock_dependencies():
    """Mock all external dependencies."""
    with patch('services.github.utils.deconstruct_github_payload.get_installation_access_token') as mock_token, \
         patch('services.github.utils.deconstruct_github_payload.get_repository') as mock_repo, \
         patch('services.github.utils.deconstruct_github_payload.check_branch_exists') as mock_branch, \
         patch('services.github.utils.deconstruct_github_payload.extract_urls') as mock_urls, \
         patch('services.github.utils.deconstruct_github_payload.get_user_public_email') as mock_email, \
         patch('services.github.utils.deconstruct_github_payload.get_parent_issue') as mock_parent:

        mock_token.return_value = "test_token"
        mock_repo.return_value = {"target_branch": None}
        mock_branch.return_value = False
        mock_urls.return_value = (["https://github.com/test"], ["https://example.com"])
        mock_email.return_value = "test@example.com"
        mock_parent.return_value = None

        yield {
            'token': mock_token,
            'repo': mock_repo,
            'branch': mock_branch,
            'urls': mock_urls,
            'email': mock_email,
            'parent': mock_parent
        }


@pytest.fixture
def mock_config():
    """Mock configuration constants."""
    with patch('services.github.utils.deconstruct_github_payload.PRODUCT_ID', 'gitauto'), \
         patch('services.github.utils.deconstruct_github_payload.ISSUE_NUMBER_FORMAT', '/issue-'), \
         patch('services.github.utils.deconstruct_github_payload.GITHUB_APP_USER_ID', 161652217):
        yield


@pytest.fixture
def sample_payload():
    """Create a sample GitHub payload for testing."""
    return {
        "action": "labeled",
        "issue": {
            "number": 123,
            "title": "Test Issue",
            "body": "This is a test issue with https://github.com/test/repo",
            "user": {
                "login": "test_user"
            }
        },
        "repository": {
            "id": 456,
            "name": "test-repo",
            "clone_url": "https://github.com/test/test-repo.git",
            "fork": False,
            "default_branch": "main",
            "owner": {
                "type": "Organization",
                "login": "test_owner",
                "id": 789
            }
        },
        "installation": {
            "id": 12345
        },
        "sender": {
            "id": 999,
            "login": "sender_user"
        },
        "label": {
            "name": "test-label"
        },
        "organization": {
            "login": "test_org"
        }
    }


def test_deconstruct_github_payload_happy_path(
    sample_payload, mock_dependencies, mock_config, mock_datetime, mock_choices
):
    """Test successful payload deconstruction with all required data."""
    # pylint: disable=redefined-outer-name
    base_args, repo_settings = deconstruct_github_payload(sample_payload)

    # Verify base_args structure
    assert base_args["input_from"] == "github"
    assert base_args["owner_type"] == "Organization"
    assert base_args["owner_id"] == 789
    assert base_args["owner"] == "test_owner"
    assert base_args["repo_id"] == 456
    assert base_args["repo"] == "test-repo"
    assert base_args["clone_url"] == "https://github.com/test/test-repo.git"
    assert base_args["is_fork"] is False
    assert base_args["issue_number"] == 123
    assert base_args["issue_title"] == "Test Issue"
    assert base_args["issue_body"] == "This is a test issue with https://github.com/test/repo"
    assert base_args["issuer_name"] == "test_user"
    assert base_args["base_branch"] == "main"
    assert base_args["new_branch"] == "gitauto/issue-123-20241224-120000-ABCD"
    assert base_args["installation_id"] == 12345
    assert base_args["token"] == "test_token"
    assert base_args["sender_id"] == 999
    assert base_args["sender_name"] == "sender_user"
    assert base_args["sender_email"] == "test@example.com"
    assert base_args["is_automation"] is False
    assert base_args["reviewers"] == ["sender_user", "test_user"]
    assert base_args["github_urls"] == ["https://github.com/test"]
    assert base_args["other_urls"] == ["https://example.com"]
    assert base_args["parent_issue_number"] is None
    assert base_args["parent_issue_title"] is None
    assert base_args["parent_issue_body"] is None

    # Verify repo_settings
    assert repo_settings == {"target_branch": None}

    # Verify external function calls
    mock_dependencies['token'].assert_called_once_with(installation_id=12345)
    mock_dependencies['repo'].assert_called_once_with(repo_id=456)
    mock_dependencies['urls'].assert_called_once_with(text="This is a test issue with https://github.com/test/repo")
    mock_dependencies['email'].assert_called_once_with(username="sender_user", token="test_token")
    mock_dependencies['parent'].assert_called_once_with(
        owner="test_owner", repo="test-repo", issue_number=123, token="test_token"
    )


def test_deconstruct_github_payload_no_token_raises_error(
    sample_payload, mock_dependencies, mock_config
):
    """Test that ValueError is raised when no installation token is found."""
    # pylint: disable=redefined-outer-name
    mock_dependencies['token'].return_value = None

    with pytest.raises(ValueError, match="Installation access token is not found for test_owner/test-repo"):
        deconstruct_github_payload(sample_payload)


def test_deconstruct_github_payload_empty_issue_body(
    sample_payload, mock_dependencies, mock_config, mock_datetime, mock_choices
):
    """Test handling of empty issue body."""
    # pylint: disable=redefined-outer-name
    sample_payload["issue"]["body"] = None

    base_args, _ = deconstruct_github_payload(sample_payload)

    assert base_args["issue_body"] == ""
    mock_dependencies['urls'].assert_called_once_with(text="")


def test_deconstruct_github_payload_fork_repository(
    sample_payload, mock_dependencies, mock_config, mock_datetime, mock_choices
):
    """Test handling of fork repository."""
    # pylint: disable=redefined-outer-name
    sample_payload["repository"]["fork"] = True

    base_args, _ = deconstruct_github_payload(sample_payload)

    assert base_args["is_fork"] is True


def test_deconstruct_github_payload_missing_fork_field(
    sample_payload, mock_dependencies, mock_config, mock_datetime, mock_choices
):
    """Test handling when fork field is missing from repository."""
    # pylint: disable=redefined-outer-name
    del sample_payload["repository"]["fork"]

    base_args, _ = deconstruct_github_payload(sample_payload)

    assert base_args["is_fork"] is False


def test_deconstruct_github_payload_with_target_branch_exists(
    sample_payload, mock_dependencies, mock_config, mock_datetime, mock_choices
):
    """Test using target branch when it exists in repository."""
    # pylint: disable=redefined-outer-name
    mock_dependencies['repo'].return_value = {"target_branch": "develop"}
    mock_dependencies['branch'].return_value = True

    with patch('builtins.print') as mock_print:
        base_args, _ = deconstruct_github_payload(sample_payload)

    assert base_args["base_branch"] == "develop"
    mock_dependencies['branch'].assert_called_once_with(
        owner="test_owner", repo="test-repo", branch_name="develop", token="test_token"
    )
    mock_print.assert_called_once_with("Using target branch: develop")


def test_deconstruct_github_payload_with_target_branch_not_exists(
    sample_payload, mock_dependencies, mock_config, mock_datetime, mock_choices
):
    """Test using default branch when target branch doesn't exist."""
    # pylint: disable=redefined-outer-name
    mock_dependencies['repo'].return_value = {"target_branch": "develop"}
    mock_dependencies['branch'].return_value = False

    base_args, _ = deconstruct_github_payload(sample_payload)

    assert base_args["base_branch"] == "main"
    mock_dependencies['branch'].assert_called_once_with(
        owner="test_owner", repo="test-repo", branch_name="develop", token="test_token"
    )


def test_deconstruct_github_payload_no_repo_settings(
    sample_payload, mock_dependencies, mock_config, mock_datetime, mock_choices
):
    """Test handling when no repository settings are found."""
    # pylint: disable=redefined-outer-name
    mock_dependencies['repo'].return_value = None

    base_args, repo_settings = deconstruct_github_payload(sample_payload)

    assert base_args["base_branch"] == "main"
    assert repo_settings is None


def test_deconstruct_github_payload_automation_user(
    sample_payload, mock_dependencies, mock_config, mock_datetime, mock_choices
):
    """Test detection of automation user."""
    # pylint: disable=redefined-outer-name
    sample_payload["sender"]["id"] = 161652217  # GITHUB_APP_USER_ID

    base_args, _ = deconstruct_github_payload(sample_payload)

    assert base_args["is_automation"] is True


def test_deconstruct_github_payload_bot_users_excluded_from_reviewers(
    sample_payload, mock_dependencies, mock_config, mock_datetime, mock_choices
):
    """Test that bot users are excluded from reviewers list."""
    # pylint: disable=redefined-outer-name
    sample_payload["sender"]["login"] = "dependabot[bot]"
    sample_payload["issue"]["user"]["login"] = "github-actions[bot]"

    base_args, _ = deconstruct_github_payload(sample_payload)

    assert base_args["reviewers"] == []


def test_deconstruct_github_payload_duplicate_reviewers_removed(
    sample_payload, mock_dependencies, mock_config, mock_datetime, mock_choices
):
    """Test that duplicate reviewers are removed."""
    # pylint: disable=redefined-outer-name
    sample_payload["sender"]["login"] = "same_user"
    sample_payload["issue"]["user"]["login"] = "same_user"

    base_args, _ = deconstruct_github_payload(sample_payload)

    assert base_args["reviewers"] == ["same_user"]


def test_deconstruct_github_payload_with_parent_issue(
    sample_payload, mock_dependencies, mock_config, mock_datetime, mock_choices
):
    """Test handling when parent issue exists."""
    # pylint: disable=redefined-outer-name
    mock_dependencies['parent'].return_value = {
        "number": 456,
        "title": "Parent Issue",
        "body": "Parent issue body"
    }

    base_args, _ = deconstruct_github_payload(sample_payload)

    assert base_args["parent_issue_number"] == 456
    assert base_args["parent_issue_title"] == "Parent Issue"
    assert base_args["parent_issue_body"] == "Parent issue body"


def test_deconstruct_github_payload_parent_issue_missing_fields(
    sample_payload, mock_dependencies, mock_config, mock_datetime, mock_choices
):
    """Test handling when parent issue has missing fields."""
    # pylint: disable=redefined-outer-name
    mock_dependencies['parent'].return_value = {}

    base_args, _ = deconstruct_github_payload(sample_payload)

    assert base_args["parent_issue_number"] is None
    assert base_args["parent_issue_title"] is None
    assert base_args["parent_issue_body"] is None


def test_deconstruct_github_payload_empty_string_issue_body(
    sample_payload, mock_dependencies, mock_config, mock_datetime, mock_choices
):
    """Test handling of empty string issue body."""
    # pylint: disable=redefined-outer-name
    sample_payload["issue"]["body"] = ""

    base_args, _ = deconstruct_github_payload(sample_payload)

    assert base_args["issue_body"] == ""
    mock_dependencies['urls'].assert_called_once_with(text="")


def test_deconstruct_github_payload_target_branch_none(
    sample_payload, mock_dependencies, mock_config, mock_datetime, mock_choices
):
    """Test handling when target_branch is None in repo settings."""
    # pylint: disable=redefined-outer-name
    mock_dependencies['repo'].return_value = {"target_branch": None}

    base_args, _ = deconstruct_github_payload(sample_payload)

    assert base_args["base_branch"] == "main"
    mock_dependencies['branch'].assert_not_called()


def test_deconstruct_github_payload_target_branch_empty_string(
    sample_payload, mock_dependencies, mock_config, mock_datetime, mock_choices
):
    """Test handling when target_branch is empty string."""
    # pylint: disable=redefined-outer-name
    mock_dependencies['repo'].return_value = {"target_branch": ""}

    base_args, _ = deconstruct_github_payload(sample_payload)

    assert base_args["base_branch"] == "main"
    mock_dependencies['branch'].assert_not_called()


def test_deconstruct_github_payload_complex_branch_name_generation(
    sample_payload, mock_dependencies, mock_config, mock_datetime, mock_choices
):
    """Test branch name generation with different issue numbers."""
    # pylint: disable=redefined-outer-name
    sample_payload["issue"]["number"] = 9999

    base_args, _ = deconstruct_github_payload(sample_payload)

    assert base_args["new_branch"] == "gitauto/issue-9999-20241224-120000-ABCD"


def test_deconstruct_github_payload_all_external_calls_made(
    sample_payload, mock_dependencies, mock_config, mock_datetime, mock_choices
):
    """Test that all external function calls are made with correct parameters."""
    # pylint: disable=redefined-outer-name
    deconstruct_github_payload(sample_payload)

    # Verify all external calls were made
    mock_dependencies['token'].assert_called_once_with(installation_id=12345)
    mock_dependencies['repo'].assert_called_once_with(repo_id=456)
    mock_dependencies['urls'].assert_called_once_with(text="This is a test issue with https://github.com/test/repo")
    mock_dependencies['email'].assert_called_once_with(username="sender_user", token="test_token")
    mock_dependencies['parent'].assert_called_once_with(
        owner="test_owner", repo="test-repo", issue_number=123, token="test_token"
    )


def test_deconstruct_github_payload_user_type_organization(
    sample_payload, mock_dependencies, mock_config, mock_datetime, mock_choices
):
    """Test handling of Organization owner type."""
    # pylint: disable=redefined-outer-name
    sample_payload["repository"]["owner"]["type"] = "Organization"

    base_args, _ = deconstruct_github_payload(sample_payload)

    assert base_args["owner_type"] == "Organization"


def test_deconstruct_github_payload_user_type_user(
    sample_payload, mock_dependencies, mock_config, mock_datetime, mock_choices
):
    """Test handling of User owner type."""
    # pylint: disable=redefined-outer-name
    sample_payload["repository"]["owner"]["type"] = "User"

    base_args, _ = deconstruct_github_payload(sample_payload)

    assert base_args["owner_type"] == "User"


def test_deconstruct_github_payload_mixed_bot_and_human_reviewers(
    sample_payload, mock_dependencies, mock_config, mock_datetime, mock_choices
):
    """Test reviewer filtering with mixed bot and human users."""
    # pylint: disable=redefined-outer-name
    sample_payload["sender"]["login"] = "human_user"
    sample_payload["issue"]["user"]["login"] = "bot[bot]"

    base_args, _ = deconstruct_github_payload(sample_payload)

    assert base_args["reviewers"] == ["human_user"]


def test_deconstruct_github_payload_return_tuple_structure(
    sample_payload, mock_dependencies, mock_config, mock_datetime, mock_choices
):
    """Test that function returns correct tuple structure."""
    # pylint: disable=redefined-outer-name
    result = deconstruct_github_payload(sample_payload)

    assert isinstance(result, tuple)
    assert len(result) == 2

    base_args, repo_settings = result
    assert isinstance(base_args, dict)
    assert isinstance(repo_settings, dict) or repo_settings is None


def test_deconstruct_github_payload_all_base_args_keys_present(
    sample_payload, mock_dependencies, mock_config, mock_datetime, mock_choices
):
    """Test that all expected BaseArgs keys are present in the result."""
    # pylint: disable=redefined-outer-name
    base_args, _ = deconstruct_github_payload(sample_payload)

    expected_keys = {
        "input_from", "owner_type", "owner_id", "owner", "repo_id", "repo",
        "clone_url", "is_fork", "issue_number", "issue_title", "issue_body",
        "issuer_name", "parent_issue_number", "parent_issue_title", "parent_issue_body",
        "base_branch", "new_branch", "installation_id", "token", "sender_id",
        "sender_name", "sender_email", "is_automation", "reviewers", "github_urls",
        "other_urls"
    }

    assert set(base_args.keys()) == expected_keys


def test_deconstruct_github_payload_edge_case_zero_ids(
    sample_payload, mock_dependencies, mock_config, mock_datetime, mock_choices
):
    """Test handling of zero IDs."""
    # pylint: disable=redefined-outer-name
    sample_payload["repository"]["id"] = 0
    sample_payload["repository"]["owner"]["id"] = 0
    sample_payload["sender"]["id"] = 0
    sample_payload["installation"]["id"] = 0

    base_args, _ = deconstruct_github_payload(sample_payload)

    assert base_args["repo_id"] == 0
    assert base_args["owner_id"] == 0
    assert base_args["sender_id"] == 0
    assert base_args["installation_id"] == 0
    assert base_args["is_automation"] is False  # 0 != GITHUB_APP_USER_ID


def test_deconstruct_github_payload_large_issue_number(
    sample_payload, mock_dependencies, mock_config, mock_datetime, mock_choices
):
    """Test handling of large issue numbers."""
    # pylint: disable=redefined-outer-name
    sample_payload["issue"]["number"] = 999999

    base_args, _ = deconstruct_github_payload(sample_payload)

    assert base_args["issue_number"] == 999999
    assert base_args["new_branch"] == "gitauto/issue-999999-20241224-120000-ABCD"
