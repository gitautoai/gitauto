from unittest.mock import patch, MagicMock

import pytest
from github import Github
from github.Repository import Repository
from github.GithubException import GithubException

from services.github.repositories.turn_on_issue import turn_on_issue


def test_turn_on_issue_when_issues_already_enabled():
    """Test turn_on_issue when repository already has issues enabled."""
    full_name = "owner/repo"
    token = "test_token"
    
    with patch("services.github.repositories.turn_on_issue.Github") as mock_github:
        # Setup mock repository with issues already enabled
        mock_repo = MagicMock(spec=Repository)
        mock_repo.has_issues = True
        
        mock_github_instance = MagicMock(spec=Github)
        mock_github_instance.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_instance
        
        # Call the function
        result = turn_on_issue(full_name, token)
        
        # Verify Github was initialized with the token
        mock_github.assert_called_once_with(login_or_token=token)
        
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
    
    with patch("services.github.repositories.turn_on_issue.Github") as mock_github:
        # Setup mock repository with issues disabled
        mock_repo = MagicMock(spec=Repository)
        mock_repo.has_issues = False
        
        mock_github_instance = MagicMock(spec=Github)
        mock_github_instance.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_instance
        
        # Call the function
        result = turn_on_issue(full_name, token)
        
        # Verify Github was initialized with the token
        mock_github.assert_called_once_with(login_or_token=token)
        
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
    
    with patch("services.github.repositories.turn_on_issue.Github") as mock_github:
        # Make Github constructor raise an exception
        mock_github.side_effect = GithubException(status=401, data="Unauthorized")
        
        # Call the function - should return None due to handle_exceptions decorator
        result = turn_on_issue(full_name, token)
        
        # Verify Github was called with the token
        mock_github.assert_called_once_with(login_or_token=token)
        
        # Verify function returns None due to exception handling
        assert result is None


def test_turn_on_issue_with_get_repo_exception():
    """Test turn_on_issue when get_repo raises an exception."""
    full_name = "owner/repo"
    token = "test_token"
    
    with patch("services.github.repositories.turn_on_issue.Github") as mock_github:
        mock_github_instance = MagicMock(spec=Github)
        mock_github_instance.get_repo.side_effect = GithubException(status=404, data="Not Found")
        mock_github.return_value = mock_github_instance
        
        # Call the function - should return None due to handle_exceptions decorator
        result = turn_on_issue(full_name, token)
        
        # Verify Github was initialized with the token
        mock_github.assert_called_once_with(login_or_token=token)
        
        # Verify get_repo was called
        mock_github_instance.get_repo.assert_called_once_with(full_name_or_id=full_name)
        
        # Verify function returns None due to exception handling
        assert result is None


def test_turn_on_issue_with_edit_exception():
    """Test turn_on_issue when repo.edit raises an exception."""
    full_name = "owner/repo"
    token = "test_token"
    
    with patch("services.github.repositories.turn_on_issue.Github") as mock_github:
        # Setup mock repository with issues disabled
        mock_repo = MagicMock(spec=Repository)
        mock_repo.has_issues = False
        mock_repo.edit.side_effect = GithubException(status=403, data="Forbidden")
        
        mock_github_instance = MagicMock(spec=Github)
        mock_github_instance.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_instance
        
        # Call the function - should return None due to handle_exceptions decorator
        result = turn_on_issue(full_name, token)
        
        # Verify Github was initialized with the token
        mock_github.assert_called_once_with(login_or_token=token)
        
        # Verify get_repo was called
        mock_github_instance.get_repo.assert_called_once_with(full_name_or_id=full_name)
        
        # Verify edit was called
        mock_repo.edit.assert_called_once_with(has_issues=True)
        
        # Verify function returns None due to exception handling
        assert result is None