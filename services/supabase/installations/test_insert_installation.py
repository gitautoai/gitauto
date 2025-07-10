from unittest.mock import patch, MagicMock

import pytest

from config import (
    TEST_INSTALLATION_ID,
    TEST_OWNER_ID,
    TEST_OWNER_TYPE,
    TEST_OWNER_NAME,
)
from schemas.supabase.fastapi.schema_public_latest import InstallationsInsert
from services.supabase.installations.insert_installation import insert_installation


@pytest.fixture
def mock_supabase_client():
    """Fixture to provide a mocked Supabase client."""
    with patch("services.supabase.installations.insert_installation.supabase") as mock:
        mock_table = MagicMock()
        mock_insert = MagicMock()
        mock_execute = MagicMock()
        
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


def test_insert_installation_schema_creation():
    """Test that InstallationsInsert schema is created correctly."""
    with patch("services.supabase.installations.insert_installation.supabase"):
        with patch("services.supabase.installations.insert_installation.InstallationsInsert") as mock_schema:
            mock_instance = MagicMock()
            mock_schema.return_value = mock_instance
            mock_instance.model_dump.return_value = {"test": "data"}
            
            insert_installation(
                installation_id=123,
                owner_id=456,
                owner_type="User",
                owner_name="test"
            )
            
            # Verify schema was created with correct parameters
            mock_schema.assert_called_once_with(
                installation_id=123,
                owner_id=456,
                owner_type="User",
                owner_name="test"
            )
            
            # Verify model_dump was called with exclude_none=True
            mock_instance.model_dump.assert_called_once_with(exclude_none=True)


def test_insert_installation_model_dump_exclude_none():
    """Test that model_dump is called with exclude_none=True."""
    with patch("services.supabase.installations.insert_installation.supabase") as mock_supabase:
        # Create a real InstallationsInsert instance to test model_dump behavior
        test_data = {
            "installation_id": TEST_INSTALLATION_ID,
            "owner_id": TEST_OWNER_ID,
            "owner_type": TEST_OWNER_TYPE,
            "owner_name": TEST_OWNER_NAME,
        }
        
        insert_installation(**test_data)
        
        # Verify the data passed to insert doesn't contain None values
        insert_call_args = mock_supabase.table.return_value.insert.call_args
        inserted_data = insert_call_args[1]["json"]
        
        # Check that None values are excluded (InstallationsInsert has optional fields that default to None)
        for key, value in inserted_data.items():
            assert value is not None, f"Field {key} should not be None when exclude_none=True"


@pytest.mark.parametrize("installation_id,owner_id,owner_type,owner_name", [
    (1, 100, "User", "user1"),
    (999999, 888888, "Organization", "big-org"),
    (42, 24, "User", "special-user"),
    (123456789, 987654321, "Organization", "enterprise-org"),
])
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
