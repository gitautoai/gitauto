"""Test for create_user_request function."""

from unittest.mock import Mock, patch
import pytest

from services.supabase.create_user_request import create_user_request


@pytest.fixture
def sample_user_request_data():
    """Sample data for user request creation."""
    return {
        "user_id": 12345,
        "user_name": "test_user",
        "installation_id": 67890,
        "owner_id": 11111,
        "owner_type": "Organization",
        "owner_name": "test_owner",
        "repo_id": 22222,
        "repo_name": "test_repo",
        "issue_number": 123,
        "source": "github",
        "trigger": "issue_comment",
        "email": "test@example.com",
        "pr_number": 456,
    }


@patch("services.supabase.create_user_request.upsert_user")
@patch("services.supabase.create_user_request.insert_usage")
@patch("services.supabase.create_user_request.insert_issue")
@patch("services.supabase.create_user_request.get_issue")
def test_create_user_request_new_issue(
    mock_get_issue, mock_insert_issue, mock_insert_usage, mock_upsert_user, sample_user_request_data
):
    """Test creating user request when issue doesn't exist."""
    # Mock get_issue to return None (issue doesn't exist)
    mock_get_issue.return_value = None
    
    # Mock insert_usage to return a usage ID
    expected_usage_id = 999
    mock_insert_usage.return_value = expected_usage_id
    
    result = create_user_request(**sample_user_request_data)
    
    # Verify the result
    assert result == expected_usage_id
    
    # Verify get_issue was called with correct parameters
    mock_get_issue.assert_called_once_with(
        owner_type="Organization",
        owner_name="test_owner",
        repo_name="test_repo",
        issue_number=123,
    )
    
    # Verify insert_issue was called since issue doesn't exist
    mock_insert_issue.assert_called_once_with(
        owner_id=11111,
        owner_type="Organization",
        owner_name="test_owner",
        repo_id=22222,
        repo_name="test_repo",
        issue_number=123,
        installation_id=67890,
    )
    
    # Verify insert_usage was called
    mock_insert_usage.assert_called_once_with(
        owner_id=11111,
        owner_type="Organization",
        owner_name="test_owner",
        repo_id=22222,
        repo_name="test_repo",
        issue_number=123,
        user_id=12345,
        installation_id=67890,
        source="github",
        trigger="issue_comment",
        pr_number=456,
    )
    
    # Verify upsert_user was called
    mock_upsert_user.assert_called_once_with(
        user_id=12345,
        user_name="test_user",
        email="test@example.com",
    )


@patch("services.supabase.create_user_request.upsert_user")
@patch("services.supabase.create_user_request.insert_usage")
@patch("services.supabase.create_user_request.insert_issue")
@patch("services.supabase.create_user_request.get_issue")
def test_create_user_request_existing_issue(
    mock_get_issue, mock_insert_issue, mock_insert_usage, mock_upsert_user, sample_user_request_data
):
    """Test creating user request when issue already exists."""
    # Mock get_issue to return an existing issue
    mock_existing_issue = {"id": 1, "issue_number": 123}
    mock_get_issue.return_value = mock_existing_issue
    
    # Mock insert_usage to return a usage ID
    expected_usage_id = 888
    mock_insert_usage.return_value = expected_usage_id
    
    result = create_user_request(**sample_user_request_data)
    
    # Verify the result
    assert result == expected_usage_id
    
    # Verify get_issue was called
    mock_get_issue.assert_called_once_with(
        owner_type="Organization",
        owner_name="test_owner",
        repo_name="test_repo",
        issue_number=123,
    )
    
    # Verify insert_issue was NOT called since issue exists
    mock_insert_issue.assert_not_called()
    
    # Verify insert_usage was still called
    mock_insert_usage.assert_called_once()
    
    # Verify upsert_user was still called
    mock_upsert_user.assert_called_once()


@patch("services.supabase.create_user_request.upsert_user")
@patch("services.supabase.create_user_request.insert_usage")
@patch("services.supabase.create_user_request.insert_issue")
@patch("services.supabase.create_user_request.get_issue")
def test_create_user_request_without_pr_number(
    mock_get_issue, mock_insert_issue, mock_insert_usage, mock_upsert_user, sample_user_request_data
):
    """Test creating user request without pr_number."""
    # Remove pr_number from sample data
    sample_user_request_data.pop("pr_number")
    
    # Mock get_issue to return None
    mock_get_issue.return_value = None
    
    # Mock insert_usage to return a usage ID
    expected_usage_id = 777
    mock_insert_usage.return_value = expected_usage_id
    
    result = create_user_request(**sample_user_request_data)
    
    # Verify the result
    assert result == expected_usage_id
    
    # Verify insert_usage was called with pr_number=None
    mock_insert_usage.assert_called_once_with(
        owner_id=11111,
        owner_type="Organization",
        owner_name="test_owner",
        repo_id=22222,
        repo_name="test_repo",
        issue_number=123,
        user_id=12345,
        installation_id=67890,
        source="github",
        trigger="issue_comment",
        pr_number=None,
    )


@patch("services.supabase.create_user_request.upsert_user")
@patch("services.supabase.create_user_request.insert_usage")
@patch("services.supabase.create_user_request.insert_issue")
@patch("services.supabase.create_user_request.get_issue")
def test_create_user_request_without_email(
    mock_get_issue, mock_insert_issue, mock_insert_usage, mock_upsert_user, sample_user_request_data
):
    """Test creating user request without email."""
    # Set email to None
    sample_user_request_data["email"] = None
    
    # Mock get_issue to return None
    mock_get_issue.return_value = None
    
    # Mock insert_usage to return a usage ID
    expected_usage_id = 666
    mock_insert_usage.return_value = expected_usage_id
    
    result = create_user_request(**sample_user_request_data)
    
    # Verify the result
    assert result == expected_usage_id
    
    # Verify upsert_user was called with email=None
    mock_upsert_user.assert_called_once_with(
        user_id=12345,
        user_name="test_user",
        email=None,
    )


@patch("services.supabase.create_user_request.get_issue")
def test_create_user_request_get_issue_exception(mock_get_issue, sample_user_request_data):
    """Test creating user request when get_issue raises an exception."""
    # Mock get_issue to raise an exception
    mock_get_issue.side_effect = Exception("Database connection error")
    
    # Should raise exception due to @handle_exceptions(raise_on_error=True)
    with pytest.raises(Exception, match="Database connection error"):
        create_user_request(**sample_user_request_data)


@patch("services.supabase.create_user_request.upsert_user")
@patch("services.supabase.create_user_request.insert_usage")
@patch("services.supabase.create_user_request.insert_issue")
@patch("services.supabase.create_user_request.get_issue")
def test_create_user_request_insert_issue_exception(
    mock_get_issue, mock_insert_issue, mock_insert_usage, mock_upsert_user, sample_user_request_data
):
    """Test creating user request when insert_issue raises an exception."""
    # Mock get_issue to return None (so insert_issue will be called)
    mock_get_issue.return_value = None
    
    # Mock insert_issue to raise an exception
    mock_insert_issue.side_effect = Exception("Insert issue failed")
    
    # Should raise exception due to @handle_exceptions(raise_on_error=True)
    with pytest.raises(Exception, match="Insert issue failed"):
        create_user_request(**sample_user_request_data)


@patch("services.supabase.create_user_request.upsert_user")
@patch("services.supabase.create_user_request.insert_usage")
@patch("services.supabase.create_user_request.get_issue")
def test_create_user_request_different_trigger_types(
    mock_get_issue, mock_insert_usage, mock_upsert_user, sample_user_request_data
):
    """Test creating user request with different trigger types."""
    # Mock get_issue to return existing issue
    mock_get_issue.return_value = {"id": 1}
    mock_insert_usage.return_value = 555
    
    # Test with different trigger types
    trigger_types = ["issue_label", "review_comment", "test_failure", "pr_checkbox", "pr_merge"]
    
    for trigger in trigger_types:
        sample_user_request_data["trigger"] = trigger
        result = create_user_request(**sample_user_request_data)
        assert result == 555
