# Standard imports
from unittest.mock import patch, MagicMock

# Third-party imports
import pytest

# Local imports
from services.github.comments.delete_comments_by_identifiers import delete_comments_by_identifiers


@pytest.fixture
def mock_get_all_comments():
    """Fixture to provide a mocked get_all_comments function."""
    with patch("services.github.comments.delete_comments_by_identifiers.get_all_comments") as mock:
        yield mock


@pytest.fixture
def mock_filter_comments_by_identifiers():
    """Fixture to provide a mocked filter_comments_by_identifiers function."""
    with patch("services.github.comments.delete_comments_by_identifiers.filter_comments_by_identifiers") as mock:
        yield mock


@pytest.fixture
def mock_delete_comment():
    """Fixture to provide a mocked delete_comment function."""
    with patch("services.github.comments.delete_comments_by_identifiers.delete_comment") as mock:
        yield mock


@pytest.fixture
def sample_base_args():
    """Fixture providing sample BaseArgs."""
    return {
        "owner": "test-owner",
        "repo": "test-repo",
        "issue_number": 123,
        "token": "test-token"
    }


@pytest.fixture
def sample_comments():
    """Fixture providing sample comments data."""
    return [
        {
            "id": 1,
            "body": "This comment contains test-identifier-1",
            "user": {"login": "gitauto-ai[bot]"}
        },
        {
            "id": 2,
            "body": "This comment contains test-identifier-2",
            "user": {"login": "gitauto-ai[bot]"}
        },
        {
            "id": 3,
            "body": "This comment has no identifier",
            "user": {"login": "gitauto-ai[bot]"}
        }
    ]


@pytest.fixture
def sample_matching_comments():
    """Fixture providing sample matching comments."""
    return [
        {
            "id": 1,
            "body": "This comment contains test-identifier-1",
            "user": {"login": "gitauto-ai[bot]"}
        },
        {
            "id": 2,
            "body": "This comment contains test-identifier-2",
            "user": {"login": "gitauto-ai[bot]"}
        }
    ]


def test_delete_comments_by_identifiers_successful_deletion(
    mock_get_all_comments,
    mock_filter_comments_by_identifiers,
    mock_delete_comment,
    sample_base_args,
    sample_comments,
    sample_matching_comments
):
    """Test successful deletion of comments with matching identifiers."""
    # Setup mocks
    mock_get_all_comments.return_value = sample_comments
    mock_filter_comments_by_identifiers.return_value = sample_matching_comments
    mock_delete_comment.return_value = None
    
    identifiers = ["test-identifier-1", "test-identifier-2"]
    
    # Execute
    result = delete_comments_by_identifiers(sample_base_args, identifiers)
    
    # Verify
    assert result is None  # Function returns None on success
    mock_get_all_comments.assert_called_once_with(sample_base_args)
    mock_filter_comments_by_identifiers.assert_called_once_with(sample_comments, identifiers)
    
    # Verify delete_comment was called for each matching comment
    assert mock_delete_comment.call_count == 2
    mock_delete_comment.assert_any_call(base_args=sample_base_args, comment_id=1)
    mock_delete_comment.assert_any_call(base_args=sample_base_args, comment_id=2)


def test_delete_comments_by_identifiers_no_comments_found(
    mock_get_all_comments,
    mock_filter_comments_by_identifiers,
    mock_delete_comment,
    sample_base_args
):
    """Test behavior when no comments are found."""
    # Setup mocks
    mock_get_all_comments.return_value = []
    mock_filter_comments_by_identifiers.return_value = []
    
    identifiers = ["test-identifier"]
    
    # Execute
    result = delete_comments_by_identifiers(sample_base_args, identifiers)
    
    # Verify
    assert result is None
    mock_get_all_comments.assert_called_once_with(sample_base_args)
    mock_filter_comments_by_identifiers.assert_called_once_with([], identifiers)
    mock_delete_comment.assert_not_called()


def test_delete_comments_by_identifiers_no_matching_comments(
    mock_get_all_comments,
    mock_filter_comments_by_identifiers,
    mock_delete_comment,
    sample_base_args,
    sample_comments
):
    """Test behavior when no comments match the identifiers."""
    # Setup mocks
    mock_get_all_comments.return_value = sample_comments
    mock_filter_comments_by_identifiers.return_value = []
    
    identifiers = ["non-existent-identifier"]
    
    # Execute
    result = delete_comments_by_identifiers(sample_base_args, identifiers)
    
    # Verify
    assert result is None
    mock_get_all_comments.assert_called_once_with(sample_base_args)
    mock_filter_comments_by_identifiers.assert_called_once_with(sample_comments, identifiers)
    mock_delete_comment.assert_not_called()


def test_delete_comments_by_identifiers_single_comment_deletion(
    mock_get_all_comments,
    mock_filter_comments_by_identifiers,
    mock_delete_comment,
    sample_base_args
):
    """Test deletion of a single matching comment."""
    # Setup data
    comments = [
        {
            "id": 42,
            "body": "Single comment with test-id",
            "user": {"login": "gitauto-ai[bot]"}
        }
    ]
    matching_comments = [comments[0]]
    
    # Setup mocks
    mock_get_all_comments.return_value = comments
    mock_filter_comments_by_identifiers.return_value = matching_comments
    mock_delete_comment.return_value = None
    
    identifiers = ["test-id"]
    
    # Execute
    result = delete_comments_by_identifiers(sample_base_args, identifiers)
    
    # Verify
    assert result is None
    mock_get_all_comments.assert_called_once_with(sample_base_args)
    mock_filter_comments_by_identifiers.assert_called_once_with(comments, identifiers)
    mock_delete_comment.assert_called_once_with(base_args=sample_base_args, comment_id=42)


def test_delete_comments_by_identifiers_empty_identifiers_list(
    mock_get_all_comments,
    mock_filter_comments_by_identifiers,
    mock_delete_comment,
    sample_base_args,
    sample_comments
):
    """Test behavior with empty identifiers list."""
    # Setup mocks
    mock_get_all_comments.return_value = sample_comments
    mock_filter_comments_by_identifiers.return_value = []
    
    identifiers = []
    
    # Execute
    result = delete_comments_by_identifiers(sample_base_args, identifiers)
    
    # Verify
    assert result is None
    mock_get_all_comments.assert_called_once_with(sample_base_args)
    mock_filter_comments_by_identifiers.assert_called_once_with(sample_comments, identifiers)
    mock_delete_comment.assert_not_called()


def test_delete_comments_by_identifiers_get_all_comments_returns_none(
    mock_get_all_comments,
    mock_filter_comments_by_identifiers,
    mock_delete_comment,
    sample_base_args
):
    """Test behavior when get_all_comments returns None."""
    # Setup mocks
    mock_get_all_comments.return_value = None
    mock_filter_comments_by_identifiers.return_value = []
    
    identifiers = ["test-identifier"]
    
    # Execute
    result = delete_comments_by_identifiers(sample_base_args, identifiers)
    
    # Verify
    assert result is None
    mock_get_all_comments.assert_called_once_with(sample_base_args)
    mock_filter_comments_by_identifiers.assert_called_once_with(None, identifiers)
    mock_delete_comment.assert_not_called()


def test_delete_comments_by_identifiers_exception_handling(
    mock_get_all_comments,
    mock_filter_comments_by_identifiers,
    mock_delete_comment,
    sample_base_args
):
    """Test that exceptions are handled gracefully due to @handle_exceptions decorator."""
    # Setup mocks to raise exceptions
    mock_get_all_comments.side_effect = Exception("API error")
    
    identifiers = ["test-identifier"]
    
    # Execute
    result = delete_comments_by_identifiers(sample_base_args, identifiers)
    
    # Verify that the decorator returns the default value (None) on exception
    assert result is None
    mock_get_all_comments.assert_called_once_with(sample_base_args)
    # Other functions should not be called due to exception
    mock_filter_comments_by_identifiers.assert_not_called()
    mock_delete_comment.assert_not_called()


def test_delete_comments_by_identifiers_delete_comment_exception(
    mock_get_all_comments,
    mock_filter_comments_by_identifiers,
    mock_delete_comment,
    sample_base_args,
    sample_comments
):
    """Test behavior when delete_comment raises an exception."""
    # Setup data
    matching_comments = [{"id": 1, "body": "test", "user": {"login": "gitauto-ai[bot]"}}]
    
    # Setup mocks
    mock_get_all_comments.return_value = sample_comments
    mock_filter_comments_by_identifiers.return_value = matching_comments
    mock_delete_comment.side_effect = Exception("Delete failed")
    
    identifiers = ["test-identifier"]
    
    # Execute - should not raise exception due to @handle_exceptions decorator
    result = delete_comments_by_identifiers(sample_base_args, identifiers)
    
    # Verify that the decorator returns the default value (None) on exception
    assert result is None
    mock_get_all_comments.assert_called_once_with(sample_base_args)
    mock_filter_comments_by_identifiers.assert_called_once_with(sample_comments, identifiers)
    mock_delete_comment.assert_called_once_with(base_args=sample_base_args, comment_id=1)
