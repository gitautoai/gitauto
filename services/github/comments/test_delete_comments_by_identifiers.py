# Standard imports
import inspect
from unittest.mock import patch

# Third-party imports
import pytest

# Local imports
from services.github.comments.delete_comments_by_identifiers import (
    delete_comments_by_identifiers,
)


@pytest.fixture
def mock_get_all_comments():
    """Fixture to provide a mocked get_all_comments function."""
    with patch(
        "services.github.comments.delete_comments_by_identifiers.get_all_comments"
    ) as mock:
        yield mock


@pytest.fixture
def mock_filter_comments_by_identifiers():
    """Fixture to provide a mocked filter_comments_by_identifiers function."""
    with patch(
        "services.github.comments.delete_comments_by_identifiers.filter_comments_by_identifiers"
    ) as mock:
        yield mock


@pytest.fixture
def mock_delete_comment():
    """Fixture to provide a mocked delete_comment function."""
    with patch(
        "services.github.comments.delete_comments_by_identifiers.delete_comment"
    ) as mock:
        yield mock


@pytest.fixture
def sample_base_args():
    """Fixture providing sample BaseArgs."""
    return {
        "owner": "test-owner",
        "repo": "test-repo",
        "issue_number": 123,
        "token": "test-token",
    }


@pytest.fixture
def sample_comments():
    """Fixture providing sample comments data."""
    return [
        {
            "id": 1,
            "body": "This comment contains test-identifier-1",
            "user": {"login": "gitauto-ai[bot]"},
        },
        {
            "id": 2,
            "body": "This comment contains test-identifier-2",
            "user": {"login": "gitauto-ai[bot]"},
        },
        {
            "id": 3,
            "body": "This comment has no identifier",
            "user": {"login": "gitauto-ai[bot]"},
        },
    ]


@pytest.fixture
def sample_matching_comments():
    """Fixture providing sample matching comments."""
    return [
        {
            "id": 1,
            "body": "This comment contains test-identifier-1",
            "user": {"login": "gitauto-ai[bot]"},
        },
        {
            "id": 2,
            "body": "This comment contains test-identifier-2",
            "user": {"login": "gitauto-ai[bot]"},
        },
    ]


def test_delete_comments_by_identifiers_successful_deletion(
    mock_get_all_comments,
    mock_filter_comments_by_identifiers,
    mock_delete_comment,
    sample_base_args,
    sample_comments,
    sample_matching_comments,
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
    mock_filter_comments_by_identifiers.assert_called_once_with(
        sample_comments, identifiers
    )

    # Verify delete_comment was called for each matching comment
    assert mock_delete_comment.call_count == 2
    mock_delete_comment.assert_any_call(base_args=sample_base_args, comment_id=1)
    mock_delete_comment.assert_any_call(base_args=sample_base_args, comment_id=2)


def test_delete_comments_by_identifiers_no_comments_found(
    mock_get_all_comments,
    mock_filter_comments_by_identifiers,
    mock_delete_comment,
    sample_base_args,
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
    sample_comments,
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
    mock_filter_comments_by_identifiers.assert_called_once_with(
        sample_comments, identifiers
    )
    mock_delete_comment.assert_not_called()


def test_delete_comments_by_identifiers_single_comment_deletion(
    mock_get_all_comments,
    mock_filter_comments_by_identifiers,
    mock_delete_comment,
    sample_base_args,
):
    """Test deletion of a single matching comment."""
    # Setup data
    comments = [
        {
            "id": 42,
            "body": "Single comment with test-id",
            "user": {"login": "gitauto-ai[bot]"},
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
    mock_delete_comment.assert_called_once_with(
        base_args=sample_base_args, comment_id=42
    )


def test_delete_comments_by_identifiers_empty_identifiers_list(
    mock_get_all_comments,
    mock_filter_comments_by_identifiers,
    mock_delete_comment,
    sample_base_args,
    sample_comments,
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
    mock_filter_comments_by_identifiers.assert_called_once_with(
        sample_comments, identifiers
    )
    mock_delete_comment.assert_not_called()


def test_delete_comments_by_identifiers_get_all_comments_returns_none(
    mock_get_all_comments,
    mock_filter_comments_by_identifiers,
    mock_delete_comment,
    sample_base_args,
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
    sample_base_args,
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
    sample_comments,
):
    """Test behavior when delete_comment raises an exception."""
    # Setup data
    matching_comments = [
        {"id": 1, "body": "test", "user": {"login": "gitauto-ai[bot]"}}
    ]

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
    mock_filter_comments_by_identifiers.assert_called_once_with(
        sample_comments, identifiers
    )
    mock_delete_comment.assert_called_once_with(
        base_args=sample_base_args, comment_id=1
    )


def test_delete_comments_by_identifiers_multiple_identifiers(
    mock_get_all_comments,
    mock_filter_comments_by_identifiers,
    mock_delete_comment,
    sample_base_args,
):
    """Test deletion with multiple identifiers."""
    # Setup data
    comments = [
        {
            "id": 1,
            "body": "Comment with first-id",
            "user": {"login": "gitauto-ai[bot]"},
        },
        {
            "id": 2,
            "body": "Comment with second-id",
            "user": {"login": "gitauto-ai[bot]"},
        },
        {
            "id": 3,
            "body": "Comment with both first-id and second-id",
            "user": {"login": "gitauto-ai[bot]"},
        },
    ]
    matching_comments = [comments[0], comments[1], comments[2]]

    # Setup mocks
    mock_get_all_comments.return_value = comments
    mock_filter_comments_by_identifiers.return_value = matching_comments
    mock_delete_comment.return_value = None

    identifiers = ["first-id", "second-id"]

    # Execute
    result = delete_comments_by_identifiers(sample_base_args, identifiers)

    # Verify
    assert result is None
    mock_get_all_comments.assert_called_once_with(sample_base_args)
    mock_filter_comments_by_identifiers.assert_called_once_with(comments, identifiers)
    assert mock_delete_comment.call_count == 3
    mock_delete_comment.assert_any_call(base_args=sample_base_args, comment_id=1)
    mock_delete_comment.assert_any_call(base_args=sample_base_args, comment_id=2)
    mock_delete_comment.assert_any_call(base_args=sample_base_args, comment_id=3)


def test_delete_comments_by_identifiers_filter_exception(
    mock_get_all_comments,
    mock_filter_comments_by_identifiers,
    mock_delete_comment,
    sample_base_args,
    sample_comments,
):
    """Test behavior when filter_comments_by_identifiers raises an exception."""
    # Setup mocks
    mock_get_all_comments.return_value = sample_comments
    mock_filter_comments_by_identifiers.side_effect = Exception("Filter failed")

    identifiers = ["test-identifier"]

    # Execute
    result = delete_comments_by_identifiers(sample_base_args, identifiers)

    # Verify that the decorator returns the default value (None) on exception
    assert result is None
    mock_get_all_comments.assert_called_once_with(sample_base_args)
    mock_filter_comments_by_identifiers.assert_called_once_with(
        sample_comments, identifiers
    )
    mock_delete_comment.assert_not_called()


def test_delete_comments_by_identifiers_partial_deletion_failure(
    mock_get_all_comments,
    mock_filter_comments_by_identifiers,
    mock_delete_comment,
    sample_base_args,
):
    """Test behavior when some comment deletions fail."""
    # Setup data
    matching_comments = [
        {"id": 1, "body": "First comment", "user": {"login": "gitauto-ai[bot]"}},
        {"id": 2, "body": "Second comment", "user": {"login": "gitauto-ai[bot]"}},
        {"id": 3, "body": "Third comment", "user": {"login": "gitauto-ai[bot]"}},
    ]

    # Setup mocks - first call succeeds, second fails, third succeeds
    mock_get_all_comments.return_value = matching_comments
    mock_filter_comments_by_identifiers.return_value = matching_comments
    mock_delete_comment.side_effect = [None, Exception("Delete failed"), None]

    identifiers = ["test-identifier"]

    # Execute - should not raise exception due to @handle_exceptions decorator
    result = delete_comments_by_identifiers(sample_base_args, identifiers)

    # Verify that the decorator returns the default value (None) on exception
    assert result is None
    mock_get_all_comments.assert_called_once_with(sample_base_args)
    mock_filter_comments_by_identifiers.assert_called_once_with(
        matching_comments, identifiers
    )
    # Should have attempted to delete the first two comments before the exception on the second
    assert mock_delete_comment.call_count == 2
    mock_delete_comment.assert_any_call(base_args=sample_base_args, comment_id=1)
    mock_delete_comment.assert_any_call(base_args=sample_base_args, comment_id=2)


def test_delete_comments_by_identifiers_large_number_of_comments(
    mock_get_all_comments,
    mock_filter_comments_by_identifiers,
    mock_delete_comment,
    sample_base_args,
):
    """Test deletion with a large number of matching comments."""
    # Setup data - create 100 comments
    matching_comments = [
        {
            "id": i,
            "body": f"Comment {i} with test-id",
            "user": {"login": "gitauto-ai[bot]"},
        }
        for i in range(1, 101)
    ]

    # Setup mocks
    mock_get_all_comments.return_value = matching_comments
    mock_filter_comments_by_identifiers.return_value = matching_comments
    mock_delete_comment.return_value = None

    identifiers = ["test-id"]

    # Execute
    result = delete_comments_by_identifiers(sample_base_args, identifiers)

    # Verify
    assert result is None
    mock_get_all_comments.assert_called_once_with(sample_base_args)
    mock_filter_comments_by_identifiers.assert_called_once_with(
        matching_comments, identifiers
    )
    assert mock_delete_comment.call_count == 100

    # Verify all comments were attempted to be deleted
    for i in range(1, 101):
        mock_delete_comment.assert_any_call(base_args=sample_base_args, comment_id=i)


def test_delete_comments_by_identifiers_function_signature():
    """Test that the function has the correct signature and docstring."""
    # Get the function signature
    sig = inspect.signature(delete_comments_by_identifiers)

    # Check parameter names and types
    params = sig.parameters
    assert "base_args" in params
    assert "identifiers" in params
    assert len(params) == 2

    # Check that the function has a docstring
    assert delete_comments_by_identifiers.__doc__ is not None
    assert (
        "Delete all comments containing the identifiers made by GitAuto"
        in delete_comments_by_identifiers.__doc__
    )


def test_delete_comments_by_identifiers_decorator_applied():
    """Test that the @handle_exceptions decorator is properly applied."""
    # Check that the function has the decorator applied
    assert hasattr(delete_comments_by_identifiers, "__wrapped__")


def test_delete_comments_by_identifiers_with_minimal_base_args(
    mock_get_all_comments,
    mock_filter_comments_by_identifiers,
    mock_delete_comment,
    create_test_base_args,
):
    """Test with minimal BaseArgs containing only required fields."""
    # Setup minimal base_args
    minimal_base_args = create_test_base_args(owner="owner", repo="repo", token="token")

    # Setup mocks
    mock_get_all_comments.return_value = []
    mock_filter_comments_by_identifiers.return_value = []

    identifiers = ["test-id"]

    # Execute
    result = delete_comments_by_identifiers(minimal_base_args, identifiers)

    # Verify
    assert result is None
    mock_get_all_comments.assert_called_once_with(minimal_base_args)
    mock_filter_comments_by_identifiers.assert_called_once_with([], identifiers)
    mock_delete_comment.assert_not_called()


def test_delete_comments_by_identifiers_comment_id_types(
    mock_get_all_comments,
    mock_filter_comments_by_identifiers,
    mock_delete_comment,
    sample_base_args,
):
    """Test that comment IDs are properly passed to delete_comment function."""
    # Setup data with various ID types (should all be integers)
    matching_comments = [
        {"id": 1, "body": "Comment 1", "user": {"login": "gitauto-ai[bot]"}},
        {"id": 999999, "body": "Comment 2", "user": {"login": "gitauto-ai[bot]"}},
        {"id": 42, "body": "Comment 3", "user": {"login": "gitauto-ai[bot]"}},
    ]

    # Setup mocks
    mock_get_all_comments.return_value = matching_comments
    mock_filter_comments_by_identifiers.return_value = matching_comments
    mock_delete_comment.return_value = None

    identifiers = ["test-id"]

    # Execute
    result = delete_comments_by_identifiers(sample_base_args, identifiers)

    # Verify
    assert result is None
    assert mock_delete_comment.call_count == 3

    # Verify that the correct IDs were passed
    mock_delete_comment.assert_any_call(base_args=sample_base_args, comment_id=1)
    mock_delete_comment.assert_any_call(base_args=sample_base_args, comment_id=999999)
    mock_delete_comment.assert_any_call(base_args=sample_base_args, comment_id=42)


@pytest.mark.parametrize(
    "identifiers",
    [
        ["single-identifier"],
        ["id1", "id2"],
        ["very-long-identifier-with-many-characters"],
        ["special-chars-!@#$%"],
        ["123-numeric-identifier"],
    ],
)
def test_delete_comments_by_identifiers_various_identifier_formats(
    mock_get_all_comments,
    mock_filter_comments_by_identifiers,
    mock_delete_comment,
    sample_base_args,
    identifiers,
):
    """Test with various identifier formats."""
    # Setup mocks
    mock_get_all_comments.return_value = []
    mock_filter_comments_by_identifiers.return_value = []

    # Execute
    result = delete_comments_by_identifiers(sample_base_args, identifiers)

    # Verify
    assert result is None
    mock_get_all_comments.assert_called_once_with(sample_base_args)
    mock_filter_comments_by_identifiers.assert_called_once_with([], identifiers)
    mock_delete_comment.assert_not_called()
