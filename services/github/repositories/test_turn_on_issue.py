from unittest.mock import patch, MagicMock

from github import Github
from github.Repository import Repository
from github.GithubException import GithubException

from services.github.repositories.turn_on_issue import turn_on_issue


def test_turn_on_issue_when_issues_already_enabled():
    """Test turn_on_issue when repository already has issues enabled."""
    full_name = "owner/repo"
    token = "test_token"

    with patch(
        "services.github.repositories.turn_on_issue.Auth.Token"
    ) as mock_auth_token, patch(
        "services.github.repositories.turn_on_issue.Github"
    ) as mock_github:
        # Setup Auth.Token mock
        mock_auth = MagicMock()
        mock_auth_token.return_value = mock_auth

        # Setup mock repository with issues already enabled
        mock_repo = MagicMock(spec=Repository)
        mock_repo.has_issues = True

        mock_github_instance = MagicMock(spec=Github)
        mock_github_instance.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_instance

        # Call the function
        result = turn_on_issue(full_name, token)

        # Verify Auth.Token was initialized with the token
        mock_auth_token.assert_called_once_with(token)
        # Verify Github was initialized with auth
        mock_github.assert_called_once_with(auth=mock_auth)

        # Verify get_repo was called with the full_name
        mock_github_instance.get_repo.assert_called_once_with(full_name_or_id=full_name)

        # Verify edit was NOT called since issues are already enabled
        mock_repo.edit.assert_not_called()

        # Verify function returns None
        assert result is None


def test_turn_on_issue_when_issues_disabled():
    """Test turn_on_issue when repository has issues disabled."""
    full_name = "owner/repo"
    token = "test_token"

    with patch(
        "services.github.repositories.turn_on_issue.Auth.Token"
    ) as mock_auth_token, patch(
        "services.github.repositories.turn_on_issue.Github"
    ) as mock_github:
        # Setup Auth.Token mock
        mock_auth = MagicMock()
        mock_auth_token.return_value = mock_auth

        # Setup mock repository with issues disabled
        mock_repo = MagicMock(spec=Repository)
        mock_repo.has_issues = False

        mock_github_instance = MagicMock(spec=Github)
        mock_github_instance.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_instance

        # Call the function
        result = turn_on_issue(full_name, token)

        # Verify Auth.Token was initialized with the token
        mock_auth_token.assert_called_once_with(token)
        # Verify Github was initialized with auth
        mock_github.assert_called_once_with(auth=mock_auth)

        # Verify get_repo was called with the full_name
        mock_github_instance.get_repo.assert_called_once_with(full_name_or_id=full_name)

        # Verify edit was called to enable issues
        mock_repo.edit.assert_called_once_with(has_issues=True)

        # Verify function returns None
        assert result is None


def test_turn_on_issue_with_github_exception():
    """Test turn_on_issue when Github raises an exception."""
    full_name = "owner/repo"
    token = "test_token"

    with patch(
        "services.github.repositories.turn_on_issue.Auth.Token"
    ) as mock_auth_token, patch(
        "services.github.repositories.turn_on_issue.Github"
    ) as mock_github:
        # Setup Auth.Token mock
        mock_auth = MagicMock()
        mock_auth_token.return_value = mock_auth

        # Make Github constructor raise an exception
        mock_github.side_effect = GithubException(status=401, data="Unauthorized")

        # Call the function - should return None due to handle_exceptions decorator
        result = turn_on_issue(full_name, token)

        # Verify Auth.Token was initialized with the token
        mock_auth_token.assert_called_once_with(token)
        # Verify Github was initialized with auth
        mock_github.assert_called_once_with(auth=mock_auth)

        # Verify function returns None due to exception handling
        assert result is None


def test_turn_on_issue_with_get_repo_exception():
    """Test turn_on_issue when get_repo raises an exception."""
    full_name = "owner/repo"
    token = "test_token"

    with patch(
        "services.github.repositories.turn_on_issue.Auth.Token"
    ) as mock_auth_token, patch(
        "services.github.repositories.turn_on_issue.Github"
    ) as mock_github:
        # Setup Auth.Token mock
        mock_auth = MagicMock()
        mock_auth_token.return_value = mock_auth

        mock_github_instance = MagicMock(spec=Github)
        mock_github_instance.get_repo.side_effect = GithubException(
            status=404, data="Not Found"
        )
        mock_github.return_value = mock_github_instance

        # Call the function - should return None due to handle_exceptions decorator
        result = turn_on_issue(full_name, token)

        # Verify Auth.Token was initialized with the token
        mock_auth_token.assert_called_once_with(token)
        # Verify Github was initialized with auth
        mock_github.assert_called_once_with(auth=mock_auth)

        # Verify get_repo was called
        mock_github_instance.get_repo.assert_called_once_with(full_name_or_id=full_name)

        # Verify function returns None due to exception handling
        assert result is None


def test_turn_on_issue_with_edit_exception():
    """Test turn_on_issue when repo.edit raises an exception."""
    full_name = "owner/repo"
    token = "test_token"

    with patch(
        "services.github.repositories.turn_on_issue.Auth.Token"
    ) as mock_auth_token, patch(
        "services.github.repositories.turn_on_issue.Github"
    ) as mock_github:
        # Setup Auth.Token mock
        mock_auth = MagicMock()
        mock_auth_token.return_value = mock_auth

        # Setup mock repository with issues disabled
        mock_repo = MagicMock(spec=Repository)
        mock_repo.has_issues = False
        mock_repo.edit.side_effect = GithubException(status=403, data="Forbidden")

        mock_github_instance = MagicMock(spec=Github)
        mock_github_instance.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_instance

        # Call the function - should return None due to handle_exceptions decorator
        result = turn_on_issue(full_name, token)

        # Verify Auth.Token was initialized with the token
        mock_auth_token.assert_called_once_with(token)
        # Verify Github was initialized with auth
        mock_github.assert_called_once_with(auth=mock_auth)

        # Verify get_repo was called
        mock_github_instance.get_repo.assert_called_once_with(full_name_or_id=full_name)

        # Verify edit was called
        mock_repo.edit.assert_called_once_with(has_issues=True)

        # Verify function returns None due to exception handling
        assert result is None


def test_turn_on_issue_with_empty_full_name():
    """Test turn_on_issue with empty full_name parameter."""
    full_name = ""
    token = "test_token"

    with patch(
        "services.github.repositories.turn_on_issue.Auth.Token"
    ) as mock_auth_token, patch(
        "services.github.repositories.turn_on_issue.Github"
    ) as mock_github:
        # Setup Auth.Token mock
        mock_auth = MagicMock()
        mock_auth_token.return_value = mock_auth

        mock_github_instance = MagicMock(spec=Github)
        mock_github_instance.get_repo.side_effect = GithubException(
            status=400, data="Bad Request"
        )
        mock_github.return_value = mock_github_instance

        # Call the function - should return None due to handle_exceptions decorator
        result = turn_on_issue(full_name, token)

        # Verify Auth.Token was initialized with the token
        mock_auth_token.assert_called_once_with(token)
        # Verify Github was initialized with auth
        mock_github.assert_called_once_with(auth=mock_auth)

        # Verify get_repo was called with empty string
        mock_github_instance.get_repo.assert_called_once_with(full_name_or_id=full_name)

        # Verify function returns None due to exception handling
        assert result is None


def test_turn_on_issue_with_empty_token():
    """Test turn_on_issue with empty token parameter."""
    full_name = "owner/repo"
    token = ""

    with patch(
        "services.github.repositories.turn_on_issue.Auth.Token"
    ) as mock_auth_token, patch(
        "services.github.repositories.turn_on_issue.Github"
    ) as mock_github:
        # Setup Auth.Token mock
        mock_auth = MagicMock()
        mock_auth_token.return_value = mock_auth

        mock_github_instance = MagicMock(spec=Github)
        mock_repo = MagicMock(spec=Repository)
        mock_repo.has_issues = False
        mock_github_instance.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_instance

        # Call the function
        result = turn_on_issue(full_name, token)

        # Verify Auth.Token was initialized with empty token
        mock_auth_token.assert_called_once_with(token)
        # Verify Github was initialized with auth
        mock_github.assert_called_once_with(auth=mock_auth)

        # Verify get_repo was called
        mock_github_instance.get_repo.assert_called_once_with(full_name_or_id=full_name)

        # Verify edit was called to enable issues
        mock_repo.edit.assert_called_once_with(has_issues=True)

        # Verify function returns None
        assert result is None


def test_turn_on_issue_with_none_parameters():
    """Test turn_on_issue with None parameters."""
    result = turn_on_issue(None, None)  # type: ignore
    assert result is None


def test_turn_on_issue_with_different_repo_formats():
    """Test turn_on_issue with different repository name formats."""
    test_cases = [
        "owner/repo",
        "organization/repository-name",
        "user/repo_with_underscores",
        "123456789",  # Repository ID
    ]

    for full_name in test_cases:
        with patch(
            "services.github.repositories.turn_on_issue.Auth.Token"
        ) as mock_auth_token, patch(
            "services.github.repositories.turn_on_issue.Github"
        ) as mock_github:
            # Setup Auth.Token mock
            mock_auth = MagicMock()
            mock_auth_token.return_value = mock_auth

            # Setup mock repository with issues disabled
            mock_repo = MagicMock(spec=Repository)
            mock_repo.has_issues = False

            mock_github_instance = MagicMock(spec=Github)
            mock_github_instance.get_repo.return_value = mock_repo
            mock_github.return_value = mock_github_instance

            # Call the function
            result = turn_on_issue(full_name, "test_token")

            # Verify get_repo was called with the correct full_name
            mock_github_instance.get_repo.assert_called_once_with(
                full_name_or_id=full_name
            )

            # Verify edit was called to enable issues
            mock_repo.edit.assert_called_once_with(has_issues=True)

            # Verify function returns None
            assert result is None


def test_turn_on_issue_function_signature():
    """Test that the function has the correct signature and type hints."""
    import inspect
    from services.github.repositories.turn_on_issue import turn_on_issue

    sig = inspect.signature(turn_on_issue)
    assert len(sig.parameters) == 2
    assert "full_name" in sig.parameters
