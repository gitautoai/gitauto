# pylint: disable=redefined-outer-name
from unittest.mock import patch, MagicMock
import pytest
from schemas.supabase.fastapi.schema_public_latest import OwnersInsert
from services.supabase.owners.insert_owner import insert_owner


@pytest.fixture
def mock_supabase():
    """Fixture to provide a mocked supabase client."""
    with patch("services.supabase.owners.insert_owner.supabase") as mock:
        mock_table = MagicMock()
        mock_insert = MagicMock()
        mock_execute = MagicMock()
        
        mock.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = None
        
        yield mock


@pytest.fixture
def valid_owner_data():
    """Fixture providing valid owner data for testing."""
    return {
        "owner_id": 123456789,
        "owner_type": "Organization",
        "owner_name": "test-organization",
        "stripe_customer_id": "cus_test123456789"
    }


@pytest.fixture
def mock_owners_insert():
    """Fixture to mock OwnersInsert model."""
    with patch("services.supabase.owners.insert_owner.OwnersInsert") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        mock_instance.model_dump.return_value = {
            "owner_id": 123456789,
            "owner_type": "Organization",
            "owner_name": "test-organization",
            "stripe_customer_id": "cus_test123456789"
        }
        yield mock


@pytest.fixture
def sample_test_constants():
    """Fixture providing test constants from config."""
    from config import TEST_OWNER_ID, TEST_OWNER_TYPE, TEST_OWNER_NAME
    return TEST_OWNER_ID, TEST_OWNER_TYPE, TEST_OWNER_NAME


def test_insert_owner_successful_insertion(mock_supabase, valid_owner_data):
    """Test successful owner insertion with valid data."""
    result = insert_owner(**valid_owner_data)
    
    # Verify supabase operations were called correctly
    mock_supabase.table.assert_called_once_with(table_name="owners")
    mock_supabase.table.return_value.insert.assert_called_once()
    mock_supabase.table.return_value.insert.return_value.execute.assert_called_once()
    
    # Function should return None (no explicit return value)
    assert result is None


def test_insert_owner_creates_correct_owners_insert_object(mock_owners_insert, valid_owner_data):
    """Test that OwnersInsert object is created with correct parameters."""
    insert_owner(**valid_owner_data)
    
    # Verify OwnersInsert was called with correct parameters
    mock_owners_insert.assert_called_once_with(
        owner_id=valid_owner_data["owner_id"],
        owner_type=valid_owner_data["owner_type"],
        owner_name=valid_owner_data["owner_name"],
        stripe_customer_id=valid_owner_data["stripe_customer_id"]
    )
    
    # Verify model_dump was called with exclude_none=True
    mock_owners_insert.return_value.model_dump.assert_called_once_with(exclude_none=True)


def test_insert_owner_with_integer_owner_id(mock_supabase):
    """Test insertion with integer owner_id."""
    insert_owner(
        owner_id=987654321,
        owner_type="User",
        owner_name="test-user",
        stripe_customer_id="cus_user123"
    )
    
    mock_supabase.table.assert_called_once_with(table_name="owners")
    mock_supabase.table.return_value.insert.assert_called_once()
    mock_supabase.table.return_value.insert.return_value.execute.assert_called_once()


def test_insert_owner_with_user_owner_type(mock_supabase):
    """Test insertion with User owner_type."""
    insert_owner(
        owner_id=111222333,
        owner_type="User",
        owner_name="individual-user",
        stripe_customer_id="cus_individual123"
    )
    
    mock_supabase.table.assert_called_once_with(table_name="owners")
    mock_supabase.table.return_value.insert.assert_called_once()
    mock_supabase.table.return_value.insert.return_value.execute.assert_called_once()


def test_insert_owner_with_organization_owner_type(mock_supabase):
    """Test insertion with Organization owner_type."""
    insert_owner(
        owner_id=444555666,
        owner_type="Organization",
        owner_name="test-org",
        stripe_customer_id="cus_org456"
    )
    
    mock_supabase.table.assert_called_once_with(table_name="owners")
    mock_supabase.table.return_value.insert.assert_called_once()
    mock_supabase.table.return_value.insert.return_value.execute.assert_called_once()


def test_insert_owner_with_special_characters_in_name(mock_supabase):
    """Test insertion with special characters in owner_name."""
    insert_owner(
        owner_id=777888999,
        owner_type="Organization",
        owner_name="test-org-with-special-chars_123",
        stripe_customer_id="cus_special789"
    )
    
    mock_supabase.table.assert_called_once_with(table_name="owners")
    mock_supabase.table.return_value.insert.assert_called_once()
    mock_supabase.table.return_value.insert.return_value.execute.assert_called_once()


def test_insert_owner_with_long_stripe_customer_id(mock_supabase):
    """Test insertion with long stripe_customer_id."""
    long_customer_id = "cus_" + "a" * 50  # Very long customer ID
    insert_owner(
        owner_id=123123123,
        owner_type="User",
        owner_name="test-user-long-id",
        stripe_customer_id=long_customer_id
    )
    
    mock_supabase.table.assert_called_once_with(table_name="owners")
    mock_supabase.table.return_value.insert.assert_called_once()
    mock_supabase.table.return_value.insert.return_value.execute.assert_called_once()


def test_insert_owner_exception_handling_returns_none(mock_supabase):
    """Test that function returns None when an exception occurs (due to handle_exceptions decorator)."""
    # Make the execute method raise an exception
    mock_supabase.table.return_value.insert.return_value.execute.side_effect = Exception("Database error")
    
    result = insert_owner(
        owner_id=999999999,
        owner_type="Organization",
        owner_name="error-test-org",
        stripe_customer_id="cus_error123"
    )
    
    # Due to handle_exceptions decorator with default_return_value=None and raise_on_error=False
    assert result is None


def test_insert_owner_supabase_table_called_with_correct_table_name(mock_supabase, valid_owner_data):
    """Test that supabase.table is called with the correct table name."""
    insert_owner(**valid_owner_data)
    
    mock_supabase.table.assert_called_once_with(table_name="owners")


def test_insert_owner_model_dump_excludes_none_values():
    """Test that model_dump is called with exclude_none=True."""
    with patch("services.supabase.owners.insert_owner.OwnersInsert") as mock_owners_insert:
        mock_instance = MagicMock()
        mock_owners_insert.return_value = mock_instance
        
        insert_owner(
            owner_id=555666777,
            owner_type="User",
            owner_name="test-exclude-none",
            stripe_customer_id="cus_exclude123"
        )
        
        mock_instance.model_dump.assert_called_once_with(exclude_none=True)


@pytest.mark.parametrize("owner_id,owner_type,owner_name,stripe_customer_id", [
    (123456789, "Organization", "test-org-1", "cus_test1"),
    (987654321, "User", "test-user-1", "cus_user1"),
    (111222333, "Organization", "test-org-2", "cus_test2"),
    (444555666, "User", "test-user-2", "cus_user2"),
    (777888999, "Organization", "test-org-with-dashes", "cus_dashes"),
    (101010101, "User", "test_user_with_underscores", "cus_underscores"),
])
def test_insert_owner_with_various_parameter_combinations(mock_supabase, owner_id, owner_type, owner_name, stripe_customer_id):
    """Test insert_owner with various valid parameter combinations."""
    result = insert_owner(
        owner_id=owner_id,
        owner_type=owner_type,
        owner_name=owner_name,
        stripe_customer_id=stripe_customer_id
    )
    
    mock_supabase.table.assert_called_once_with(table_name="owners")
    mock_supabase.table.return_value.insert.assert_called_once()
    mock_supabase.table.return_value.insert.return_value.execute.assert_called_once()
    assert result is None


def test_insert_owner_with_config_test_constants(mock_supabase, sample_test_constants):
    """Test insertion using test constants from config."""
    test_owner_id, test_owner_type, test_owner_name = sample_test_constants
    
    insert_owner(
        owner_id=test_owner_id,
        owner_type=test_owner_type,
        owner_name=test_owner_name,
        stripe_customer_id="cus_config_test"
    )
    
    mock_supabase.table.assert_called_once_with(table_name="owners")
    mock_supabase.table.return_value.insert.assert_called_once()
    mock_supabase.table.return_value.insert.return_value.execute.assert_called_once()


def test_insert_owner_supabase_chain_method_calls(mock_supabase, valid_owner_data):
    """Test that the Supabase method chain is called in the correct order."""
    insert_owner(**valid_owner_data)
    
    # Verify the method chain: supabase.table().insert().execute()
    mock_supabase.table.assert_called_once_with(table_name="owners")
    table_result = mock_supabase.table.return_value
    table_result.insert.assert_called_once()
    insert_result = table_result.insert.return_value
    insert_result.execute.assert_called_once()


def test_insert_owner_function_signature_compliance():
    """Test that the function signature matches expected parameters."""
    import inspect
    
    sig = inspect.signature(insert_owner)
    params = list(sig.parameters.keys())
    
    # Verify parameter names and order
    expected_params = ["owner_id", "owner_type", "owner_name", "stripe_customer_id"]
    assert params == expected_params
    
    # Verify parameter types
    assert sig.parameters["owner_id"].annotation == int
    assert sig.parameters["owner_type"].annotation == str
    assert sig.parameters["owner_name"].annotation == str
    assert sig.parameters["stripe_customer_id"].annotation == str
    assert sig.return_annotation == inspect.Signature.empty  # No explicit return annotation


def test_insert_owner_data_passed_to_insert_method():
    """Test that the correct data is passed to the insert method."""
    with patch("services.supabase.owners.insert_owner.supabase") as mock_supabase, \
         patch("services.supabase.owners.insert_owner.OwnersInsert") as mock_owners_insert:
        
        # Setup mock data
        expected_data = {
            "owner_id": 999888777,
            "owner_type": "Organization",
            "owner_name": "test-data-org",
            "stripe_customer_id": "cus_data_test"
        }
        mock_owners_insert.return_value.model_dump.return_value = expected_data
        
        # Call function
        insert_owner(**expected_data)
        
        # Verify the insert method was called with the correct data
        mock_supabase.table.return_value.insert.assert_called_once_with(json=expected_data)
        mock_supabase.table.return_value.insert.return_value.execute.assert_called_once()
