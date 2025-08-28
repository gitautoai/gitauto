from unittest.mock import patch

import pytest

from services.github.commits.create_empty_commit import create_empty_commit


@pytest.fixture
def sample_base_args(test_owner, test_repo, test_token):
    """Fixture providing sample BaseArgs for testing."""
    return {
        "owner": test_owner,
        "repo": test_repo,
        "token": test_token,
        "new_branch": "test-branch",
    }


@pytest.fixture
def mock_get_reference():
    """Fixture to mock get_reference function."""
    with patch("services.github.commits.create_empty_commit.get_reference") as mock:
        mock.return_value = "current_sha_123"
        yield mock


@pytest.fixture
def mock_get_commit():
    """Fixture to mock get_commit function."""
    with patch("services.github.commits.create_empty_commit.get_commit") as mock:
        mock.return_value = "tree_sha_456"
        yield mock


@pytest.fixture
def mock_create_commit():
    """Fixture to mock create_commit function."""
    with patch("services.github.commits.create_empty_commit.create_commit") as mock:
        mock.return_value = "new_commit_sha_789"
        yield mock


@pytest.fixture
def mock_update_reference():
    """Fixture to mock update_reference function."""
    with patch("services.github.commits.create_empty_commit.update_reference") as mock:
        mock.return_value = True
        yield mock


@pytest.fixture
def all_mocks_successful(
    mock_get_reference, mock_get_commit, mock_create_commit, mock_update_reference
):
    """Fixture that provides all mocks configured for successful execution."""
    # pylint: disable=redefined-outer-name
    return {
        "get_reference": mock_get_reference,
        "get_commit": mock_get_commit,
        "create_commit": mock_create_commit,
        "update_reference": mock_update_reference,
    }


def test_create_empty_commit_success_with_default_message(
    all_mocks_successful, sample_base_args
):
    """Test successful empty commit creation with default message."""
    # pylint: disable=redefined-outer-name
    result = create_empty_commit(sample_base_args)

    # Verify the function returns True for successful execution
    assert result is True

    # Verify all functions were called in the correct order
    all_mocks_successful["get_reference"].assert_called_once_with(sample_base_args)
    all_mocks_successful["get_commit"].assert_called_once_with(
        sample_base_args, "current_sha_123"
    )
    all_mocks_successful["create_commit"].assert_called_once_with(
        sample_base_args,
        "Empty commit to trigger final tests",
        "tree_sha_456",
        "current_sha_123",
    )
    all_mocks_successful["update_reference"].assert_called_once_with(
        sample_base_args, "new_commit_sha_789"
    )


def test_create_empty_commit_success_with_custom_message(
    all_mocks_successful, sample_base_args
):
    """Test successful empty commit creation with custom message."""
    # pylint: disable=redefined-outer-name
    custom_message = "Custom empty commit message"
    result = create_empty_commit(sample_base_args, custom_message)

    # Verify the function returns True for successful execution
    assert result is True

    # Verify create_commit was called with the custom message
    all_mocks_successful["create_commit"].assert_called_once_with(
        sample_base_args, custom_message, "tree_sha_456", "current_sha_123"
    )


def test_create_empty_commit_get_reference_fails(
    mock_get_reference,
    mock_get_commit,
    mock_create_commit,
    mock_update_reference,
    sample_base_args,
):
    """Test behavior when get_reference returns None."""
    # pylint: disable=redefined-outer-name
    mock_get_reference.return_value = None

    result = create_empty_commit(sample_base_args)

    # Verify the function returns False when get_reference fails
    assert result is False

    # Verify only get_reference was called
    mock_get_reference.assert_called_once_with(sample_base_args)
    mock_get_commit.assert_not_called()
    mock_create_commit.assert_not_called()
    mock_update_reference.assert_not_called()


def test_create_empty_commit_get_reference_returns_falsy_value(
    mock_get_reference,
    mock_get_commit,
    mock_create_commit,
    mock_update_reference,
    sample_base_args,
):
    """Test behavior when get_reference returns falsy values."""
    # pylint: disable=redefined-outer-name
    falsy_values = [None, "", False, 0]

    for falsy_value in falsy_values:
        # Reset mocks for each test
        mock_get_reference.reset_mock()
        mock_get_commit.reset_mock()
        mock_create_commit.reset_mock()
        mock_update_reference.reset_mock()

        mock_get_reference.return_value = falsy_value

        result = create_empty_commit(sample_base_args)

        # Verify the function returns False for all falsy values
        assert result is False

        # Verify only get_reference was called
        mock_get_reference.assert_called_once_with(sample_base_args)
        mock_get_commit.assert_not_called()
        mock_create_commit.assert_not_called()
        mock_update_reference.assert_not_called()


def test_create_empty_commit_get_commit_fails(
    mock_get_reference,
    mock_get_commit,
    mock_create_commit,
    mock_update_reference,
    sample_base_args,
):
    """Test behavior when get_commit returns None."""
    # pylint: disable=redefined-outer-name
    mock_get_reference.return_value = "current_sha_123"
    mock_get_commit.return_value = None

    result = create_empty_commit(sample_base_args)

    # Verify the function returns False when get_commit fails
    assert result is False

    # Verify get_reference and get_commit were called, but not the others
    mock_get_reference.assert_called_once_with(sample_base_args)
    mock_get_commit.assert_called_once_with(sample_base_args, "current_sha_123")
    mock_create_commit.assert_not_called()
    mock_update_reference.assert_not_called()


def test_create_empty_commit_get_commit_returns_falsy_value(
    mock_get_reference,
    mock_get_commit,
    mock_create_commit,
    mock_update_reference,
    sample_base_args,
):
    """Test behavior when get_commit returns falsy values."""
    # pylint: disable=redefined-outer-name
    mock_get_reference.return_value = "current_sha_123"
    falsy_values = [None, "", False, 0]

    for falsy_value in falsy_values:
        # Reset mocks for each test
        mock_get_reference.reset_mock()
        mock_get_commit.reset_mock()
        mock_create_commit.reset_mock()
        mock_update_reference.reset_mock()

        mock_get_reference.return_value = "current_sha_123"
        mock_get_commit.return_value = falsy_value

        result = create_empty_commit(sample_base_args)

        # Verify the function returns False for all falsy values
        assert result is False

        # Verify get_reference and get_commit were called, but not the others
        mock_get_reference.assert_called_once_with(sample_base_args)
        mock_get_commit.assert_called_once_with(sample_base_args, "current_sha_123")
        mock_create_commit.assert_not_called()
        mock_update_reference.assert_not_called()


def test_create_empty_commit_create_commit_fails(
    mock_get_reference,
    mock_get_commit,
    mock_create_commit,
    mock_update_reference,
    sample_base_args,
):
    """Test behavior when create_commit returns None."""
    # pylint: disable=redefined-outer-name
    mock_get_reference.return_value = "current_sha_123"
    mock_get_commit.return_value = "tree_sha_456"
    mock_create_commit.return_value = None

    result = create_empty_commit(sample_base_args)

    # Verify the function returns False when create_commit fails
    assert result is False

    # Verify all functions except update_reference were called
    mock_get_reference.assert_called_once_with(sample_base_args)
    mock_get_commit.assert_called_once_with(sample_base_args, "current_sha_123")
    mock_create_commit.assert_called_once_with(
        sample_base_args,
        "Empty commit to trigger final tests",
        "tree_sha_456",
        "current_sha_123",
    )
    mock_update_reference.assert_not_called()


def test_create_empty_commit_create_commit_returns_falsy_value(
    mock_get_reference,
    mock_get_commit,
    mock_create_commit,
    mock_update_reference,
    sample_base_args,
):
    """Test behavior when create_commit returns falsy values."""
    # pylint: disable=redefined-outer-name
    mock_get_reference.return_value = "current_sha_123"
    mock_get_commit.return_value = "tree_sha_456"
    falsy_values = [None, "", False, 0]

    for falsy_value in falsy_values:
        # Reset mocks for each test
        mock_get_reference.reset_mock()
        mock_get_commit.reset_mock()
        mock_create_commit.reset_mock()
        mock_update_reference.reset_mock()

        mock_get_reference.return_value = "current_sha_123"
        mock_get_commit.return_value = "tree_sha_456"
        mock_create_commit.return_value = falsy_value

        result = create_empty_commit(sample_base_args)

        # Verify the function returns False for all falsy values
        assert result is False

        # Verify all functions except update_reference were called
        mock_get_reference.assert_called_once_with(sample_base_args)
        mock_get_commit.assert_called_once_with(sample_base_args, "current_sha_123")
        mock_create_commit.assert_called_once_with(
            sample_base_args,
            "Empty commit to trigger final tests",
            "tree_sha_456",
            "current_sha_123",
        )
        mock_update_reference.assert_not_called()


def test_create_empty_commit_update_reference_fails(
    mock_get_reference,
    mock_get_commit,
    mock_create_commit,
    mock_update_reference,
    sample_base_args,
):
    """Test behavior when update_reference returns False."""
    # pylint: disable=redefined-outer-name
    mock_get_reference.return_value = "current_sha_123"
    mock_get_commit.return_value = "tree_sha_456"
    mock_create_commit.return_value = "new_commit_sha_789"
    mock_update_reference.return_value = False

    result = create_empty_commit(sample_base_args)

    # Verify the function returns False when update_reference fails
    assert result is False

    # Verify all functions were called
    mock_get_reference.assert_called_once_with(sample_base_args)
    mock_get_commit.assert_called_once_with(sample_base_args, "current_sha_123")
    mock_create_commit.assert_called_once_with(
        sample_base_args,
        "Empty commit to trigger final tests",
        "tree_sha_456",
        "current_sha_123",
    )
    mock_update_reference.assert_called_once_with(
        sample_base_args, "new_commit_sha_789"
    )


def test_create_empty_commit_with_different_base_args(all_mocks_successful):
    """Test create_empty_commit with different BaseArgs values."""
    # pylint: disable=redefined-outer-name
    base_args = {
        "owner": "test-owner",
        "repo": "test-repo",
        "token": "test-token-123",
        "new_branch": "feature-branch",
    }

    result = create_empty_commit(base_args, "Test commit message")

    # Verify the function returns True for successful execution
    assert result is True

    # Verify all functions were called with the correct base_args
    all_mocks_successful["get_reference"].assert_called_once_with(base_args)
    all_mocks_successful["get_commit"].assert_called_once_with(
        base_args, "current_sha_123"
    )
    all_mocks_successful["create_commit"].assert_called_once_with(
        base_args, "Test commit message", "tree_sha_456", "current_sha_123"
    )
    all_mocks_successful["update_reference"].assert_called_once_with(
        base_args, "new_commit_sha_789"
    )


def test_create_empty_commit_with_empty_message(all_mocks_successful, sample_base_args):
    """Test create_empty_commit with empty message."""
    # pylint: disable=redefined-outer-name
    result = create_empty_commit(sample_base_args, "")

    # Verify the function returns True for successful execution
    assert result is True

    # Verify create_commit was called with empty message
    all_mocks_successful["create_commit"].assert_called_once_with(
        sample_base_args, "", "tree_sha_456", "current_sha_123"
    )


def test_create_empty_commit_with_long_message(all_mocks_successful, sample_base_args):
    """Test create_empty_commit with very long message."""
    # pylint: disable=redefined-outer-name
    long_message = "A" * 1000  # Very long commit message
    result = create_empty_commit(sample_base_args, long_message)

    # Verify the function returns True for successful execution
    assert result is True

    # Verify create_commit was called with the long message
    all_mocks_successful["create_commit"].assert_called_once_with(
        sample_base_args, long_message, "tree_sha_456", "current_sha_123"
    )


def test_create_empty_commit_with_special_characters_in_message(
    all_mocks_successful, sample_base_args
):
    """Test create_empty_commit with special characters in message."""
    # pylint: disable=redefined-outer-name
    special_message = "Test commit with émojis 🚀 and special chars: !@#$%^&*()"
    result = create_empty_commit(sample_base_args, special_message)

    # Verify the function returns True for successful execution
    assert result is True

    # Verify create_commit was called with the special message
    all_mocks_successful["create_commit"].assert_called_once_with(
        sample_base_args, special_message, "tree_sha_456", "current_sha_123"
    )


def test_create_empty_commit_function_call_sequence(
    all_mocks_successful, sample_base_args
):
    """Test that functions are called in the correct sequence."""
    # pylint: disable=redefined-outer-name
    call_order = []

    def track_get_reference(*_args, **_kwargs):
        call_order.append("get_reference")
        return "current_sha_123"

    def track_get_commit(*_args, **_kwargs):
        call_order.append("get_commit")
        return "tree_sha_456"

    def track_create_commit(*_args, **_kwargs):
        call_order.append("create_commit")
        return "new_commit_sha_789"

    def track_update_reference(*_args, **_kwargs):
        call_order.append("update_reference")
        return True

    all_mocks_successful["get_reference"].side_effect = track_get_reference
    all_mocks_successful["get_commit"].side_effect = track_get_commit
    all_mocks_successful["create_commit"].side_effect = track_create_commit
    all_mocks_successful["update_reference"].side_effect = track_update_reference

    result = create_empty_commit(sample_base_args)

    # Verify the function returns True for successful execution
    assert result is True

    # Verify functions were called in the correct order
    expected_order = [
        "get_reference",
        "get_commit",
        "create_commit",
        "update_reference",
    ]
    assert call_order == expected_order


def test_create_empty_commit_exception_in_get_reference(
    mock_get_reference,
    mock_get_commit,
    mock_create_commit,
    mock_update_reference,
    sample_base_args,
):
    """Test behavior when get_reference raises an exception."""
    # pylint: disable=redefined-outer-name
    mock_get_reference.side_effect = Exception("Network error")

    result = create_empty_commit(sample_base_args)

    # Verify the function returns False due to handle_exceptions decorator
    assert result is False

    # Verify only get_reference was called
    mock_get_reference.assert_called_once_with(sample_base_args)
    mock_get_commit.assert_not_called()
    mock_create_commit.assert_not_called()
    mock_update_reference.assert_not_called()


def test_create_empty_commit_exception_in_get_commit(
    mock_get_reference,
    mock_get_commit,
    mock_create_commit,
    mock_update_reference,
    sample_base_args,
):
    """Test behavior when get_commit raises an exception."""
    # pylint: disable=redefined-outer-name
    mock_get_reference.return_value = "current_sha_123"
    mock_get_commit.side_effect = Exception("API error")

    result = create_empty_commit(sample_base_args)

    # Verify the function returns False due to handle_exceptions decorator
    assert result is False

    # Verify get_reference and get_commit were called, but not the others
    mock_get_reference.assert_called_once_with(sample_base_args)
    mock_get_commit.assert_called_once_with(sample_base_args, "current_sha_123")
    mock_create_commit.assert_not_called()
    mock_update_reference.assert_not_called()


def test_create_empty_commit_exception_in_create_commit(
    mock_get_reference,
    mock_get_commit,
    mock_create_commit,
    mock_update_reference,
    sample_base_args,
):
    """Test behavior when create_commit raises an exception."""
    # pylint: disable=redefined-outer-name
    mock_get_reference.return_value = "current_sha_123"
    mock_get_commit.return_value = "tree_sha_456"
    mock_create_commit.side_effect = Exception("Commit creation failed")

    result = create_empty_commit(sample_base_args)

    # Verify the function returns False due to handle_exceptions decorator
    assert result is False

    # Verify all functions except update_reference were called
    mock_get_reference.assert_called_once_with(sample_base_args)
    mock_get_commit.assert_called_once_with(sample_base_args, "current_sha_123")
    mock_create_commit.assert_called_once_with(
        sample_base_args,
        "Empty commit to trigger final tests",
        "tree_sha_456",
        "current_sha_123",
    )
    mock_update_reference.assert_not_called()


def test_create_empty_commit_exception_in_update_reference(
    mock_get_reference,
    mock_get_commit,
    mock_create_commit,
    mock_update_reference,
    sample_base_args,
):
    """Test behavior when update_reference raises an exception."""
    # pylint: disable=redefined-outer-name
    mock_get_reference.return_value = "current_sha_123"
    mock_get_commit.return_value = "tree_sha_456"
    mock_create_commit.return_value = "new_commit_sha_789"
    mock_update_reference.side_effect = Exception("Reference update failed")

    result = create_empty_commit(sample_base_args)

    # Verify the function returns False due to handle_exceptions decorator
    assert result is False

    # Verify all functions were called
    mock_get_reference.assert_called_once_with(sample_base_args)
    mock_get_commit.assert_called_once_with(sample_base_args, "current_sha_123")
    mock_create_commit.assert_called_once_with(
        sample_base_args,
        "Empty commit to trigger final tests",
        "tree_sha_456",
        "current_sha_123",
    )
    mock_update_reference.assert_called_once_with(
        sample_base_args, "new_commit_sha_789"
    )


def test_create_empty_commit_return_value_from_update_reference(
    all_mocks_successful, sample_base_args
):
    """Test that the function returns the result from update_reference."""
    # pylint: disable=redefined-outer-name
    # Test with True return value
    all_mocks_successful["update_reference"].return_value = True
    result = create_empty_commit(sample_base_args)
    assert result is True

    # Reset mocks and test with False return value
    for mock in all_mocks_successful.values():
        mock.reset_mock()

    all_mocks_successful["get_reference"].return_value = "current_sha_123"
    all_mocks_successful["get_commit"].return_value = "tree_sha_456"
    all_mocks_successful["create_commit"].return_value = "new_commit_sha_789"
    all_mocks_successful["update_reference"].return_value = False

    result = create_empty_commit(sample_base_args)
    assert result is False
