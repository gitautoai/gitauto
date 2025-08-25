from unittest.mock import patch, MagicMock
import inspect
import requests

import pytest

from config import (
    TEST_INSTALLATION_ID,
    TEST_OWNER_ID,
    TEST_OWNER_TYPE,
    TEST_OWNER_NAME,
)
from services.supabase.installations.insert_installation import insert_installation


@pytest.fixture
def mock_supabase_client():
    """Fixture to provide a mocked Supabase client."""
    with patch("services.supabase.installations.insert_installation.supabase") as mock:
        mock_table = MagicMock()
        mock_insert = MagicMock()
        MagicMock()

        mock.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = None

        yield mock


@pytest.fixture
def valid_installation_data():
    """Fixture providing valid installation data."""
    return {
        "installation_id": TEST_INSTALLATION_ID,
        "owner_id": TEST_OWNER_ID,
        "owner_type": TEST_OWNER_TYPE,
        "owner_name": TEST_OWNER_NAME,
    }


def test_insert_installation_success(mock_supabase_client, valid_installation_data):
    """Test successful installation insertion."""
    result = insert_installation(**valid_installation_data)

    # Verify function returns None (implicit return)
    assert result is None

    # Verify Supabase operations were called correctly
    mock_supabase_client.table.assert_called_once_with(table_name="installations")

    # Verify insert was called with correct data structure
    insert_call_args = mock_supabase_client.table.return_value.insert.call_args
    assert insert_call_args is not None

    inserted_data = insert_call_args[1]["json"]
    assert inserted_data["installation_id"] == TEST_INSTALLATION_ID
    assert inserted_data["owner_id"] == TEST_OWNER_ID
    assert inserted_data["owner_type"] == TEST_OWNER_TYPE
    assert inserted_data["owner_name"] == TEST_OWNER_NAME

    # Verify execute was called
    mock_supabase_client.table.return_value.insert.return_value.execute.assert_called_once()


def test_insert_installation_with_minimal_data(mock_supabase_client):
    """Test installation insertion with minimal required data."""
    minimal_data = {
        "installation_id": 12345,
        "owner_id": 67890,
        "owner_type": "User",
        "owner_name": "test-user",
    }

    result = insert_installation(**minimal_data)

    assert result is None
    mock_supabase_client.table.assert_called_once_with(table_name="installations")

    # Verify the data was processed correctly
    insert_call_args = mock_supabase_client.table.return_value.insert.call_args
    inserted_data = insert_call_args[1]["json"]

    assert inserted_data["installation_id"] == 12345
    assert inserted_data["owner_id"] == 67890
    assert inserted_data["owner_type"] == "User"
    assert inserted_data["owner_name"] == "test-user"


def test_insert_installation_with_organization_owner(mock_supabase_client):
    """Test installation insertion with Organization owner type."""
    org_data = {
        "installation_id": 98765,
        "owner_id": 11111,
        "owner_type": "Organization",
        "owner_name": "test-org",
    }

    result = insert_installation(**org_data)

    assert result is None

    insert_call_args = mock_supabase_client.table.return_value.insert.call_args
    inserted_data = insert_call_args[1]["json"]

    assert inserted_data["owner_type"] == "Organization"
    assert inserted_data["owner_name"] == "test-org"


@pytest.mark.parametrize(
    "installation_id,owner_id,owner_type,owner_name",
    [
        (1, 100, "User", "user1"),
        (999999, 888888, "Organization", "big-org"),
        (42, 24, "User", "special-user"),
        (123456789, 987654321, "Organization", "enterprise-org"),
    ],
)
def test_insert_installation_with_various_data_types(
    mock_supabase_client, installation_id, owner_id, owner_type, owner_name
):
    """Test installation insertion with various valid data combinations."""
    result = insert_installation(
        installation_id=installation_id,
        owner_id=owner_id,
        owner_type=owner_type,
        owner_name=owner_name,
    )

    assert result is None

    insert_call_args = mock_supabase_client.table.return_value.insert.call_args
    inserted_data = insert_call_args[1]["json"]

    assert inserted_data["installation_id"] == installation_id
    assert inserted_data["owner_id"] == owner_id
    assert inserted_data["owner_type"] == owner_type
    assert inserted_data["owner_name"] == owner_name


def test_insert_installation_supabase_chain_calls(mock_supabase_client):
    """Test that Supabase method chain is called in correct order."""
    insert_installation(
        installation_id=TEST_INSTALLATION_ID,
        owner_id=TEST_OWNER_ID,
        owner_type=TEST_OWNER_TYPE,
        owner_name=TEST_OWNER_NAME,
    )

    # Verify the method chain: supabase.table().insert().execute()
    mock_supabase_client.table.assert_called_once_with(table_name="installations")
    mock_supabase_client.table.return_value.insert.assert_called_once()
    mock_supabase_client.table.return_value.insert.return_value.execute.assert_called_once()


def test_insert_installation_handles_exceptions_decorator():
    """Test that the function is properly decorated with handle_exceptions."""
    # Verify the function has the handle_exceptions decorator applied
    assert hasattr(insert_installation, "__wrapped__")

    # The decorator should be configured with raise_on_error=True
    # This is tested implicitly by the fact that exceptions would be raised
    # rather than returning the default value (None)


def test_insert_installation_function_signature():
    """Test that insert_installation has the correct function signature."""
    sig = inspect.signature(insert_installation)

    # Assert parameter count and names
    assert len(sig.parameters) == 4
    expected_params = ["installation_id", "owner_id", "owner_type", "owner_name"]
    for param in expected_params:
        assert param in sig.parameters

    # Assert parameter type annotations
    assert sig.parameters["installation_id"].annotation is int
    assert sig.parameters["owner_id"].annotation is int
    assert sig.parameters["owner_type"].annotation is str
    assert sig.parameters["owner_name"].annotation is str


def test_insert_installation_with_supabase_exception():
    """Test that exceptions from Supabase operations are raised due to raise_on_error=True."""
    with patch(
        "services.supabase.installations.insert_installation.supabase"
    ) as mock_supabase:
        # Configure mock to raise an exception
        mock_supabase.table.return_value.insert.return_value.execute.side_effect = (
            Exception("Database error")
        )

        # Since raise_on_error=True, the exception should be raised
        with pytest.raises(Exception, match="Database error"):
            insert_installation(
                installation_id=TEST_INSTALLATION_ID,
                owner_id=TEST_OWNER_ID,
                owner_type=TEST_OWNER_TYPE,
                owner_name=TEST_OWNER_NAME,
            )


def test_insert_installation_with_http_error():
    """Test that HTTP errors from Supabase operations are raised due to raise_on_error=True."""
    with patch(
        "services.supabase.installations.insert_installation.supabase"
    ) as mock_supabase:
        # Create a mock HTTP error
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.reason = "Internal Server Error"
        mock_response.text = "Database connection failed"

        http_error = requests.exceptions.HTTPError("500 Server Error")
        http_error.response = mock_response

        mock_supabase.table.return_value.insert.return_value.execute.side_effect = (
            http_error
        )

        # Since raise_on_error=True, the exception should be raised
        with pytest.raises(requests.exceptions.HTTPError):
            insert_installation(
                installation_id=TEST_INSTALLATION_ID,
                owner_id=TEST_OWNER_ID,
                owner_type=TEST_OWNER_TYPE,
                owner_name=TEST_OWNER_NAME,
            )


def test_insert_installation_with_special_characters_in_owner_name(
    mock_supabase_client,
):
    """Test installation insertion with special characters in owner name."""
    special_names = [
        "test-org-123",
        "test_user_456",
        "org.with.dots",
        "user@domain",
        "org-with-unicode-ñ",
    ]

    for owner_name in special_names:
        insert_installation(
            installation_id=TEST_INSTALLATION_ID,
            owner_id=TEST_OWNER_ID,
            owner_type=TEST_OWNER_TYPE,
            owner_name=owner_name,
        )

        # Verify the special characters are preserved
        insert_call_args = mock_supabase_client.table.return_value.insert.call_args
        inserted_data = insert_call_args[1]["json"]
        assert inserted_data["owner_name"] == owner_name

        # Reset mock for next iteration
        mock_supabase_client.reset_mock()


def test_insert_installation_with_large_ids(mock_supabase_client):
    """Test installation insertion with large integer IDs."""
    large_installation_id = 999999999999
    large_owner_id = 888888888888

    insert_installation(
        installation_id=large_installation_id,
        owner_id=large_owner_id,
        owner_type=TEST_OWNER_TYPE,
        owner_name=TEST_OWNER_NAME,
    )

    insert_call_args = mock_supabase_client.table.return_value.insert.call_args
    inserted_data = insert_call_args[1]["json"]

    assert inserted_data["installation_id"] == large_installation_id
    assert inserted_data["owner_id"] == large_owner_id


def test_insert_installation_preserves_function_name():
    """Test that the decorator preserves the original function name."""
    assert insert_installation.__name__ == "insert_installation"


def test_insert_installation_with_empty_owner_name(mock_supabase_client):
    """Test installation insertion with empty owner name."""
    insert_installation(
        installation_id=TEST_INSTALLATION_ID,
        owner_id=TEST_OWNER_ID,
        owner_type=TEST_OWNER_TYPE,
        owner_name="",
    )

    insert_call_args = mock_supabase_client.table.return_value.insert.call_args
    inserted_data = insert_call_args[1]["json"]

    assert inserted_data["owner_name"] == ""


def test_insert_installation_with_different_owner_types(mock_supabase_client):
    """Test installation insertion with different valid owner types."""
    owner_types = ["User", "Organization"]

    for owner_type in owner_types:
        insert_installation(
            installation_id=TEST_INSTALLATION_ID,
            owner_id=TEST_OWNER_ID,
            owner_type=owner_type,
            owner_name=TEST_OWNER_NAME,
        )

        insert_call_args = mock_supabase_client.table.return_value.insert.call_args
        inserted_data = insert_call_args[1]["json"]

        assert inserted_data["owner_type"] == owner_type

        # Reset mock for next iteration
        mock_supabase_client.reset_mock()
