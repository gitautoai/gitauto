from unittest.mock import patch, MagicMock
import inspect
import datetime

import pytest

from config import TEST_OWNER_ID
from services.supabase.installations.get_installation import get_installation
from schemas.supabase.fastapi.schema_public_latest import Installations


@pytest.fixture
def mock_supabase_query():
    """Fixture to provide a mocked Supabase query chain."""
    with patch("services.supabase.installations.get_installation.supabase") as mock:
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq = MagicMock()
        mock_is = MagicMock()
        
        mock.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.is_.return_value = mock_is
        
        yield mock_is


@pytest.fixture
def sample_installation_data():
    """Fixture to provide sample installation data."""
    return {
        "installation_id": 12345678,
        "created_at": datetime.datetime(2023, 1, 1, 12, 0, 0),
        "created_by": "test_user",
        "owner_id": TEST_OWNER_ID,
        "owner_name": "test_owner",
        "owner_type": "Organization",
        "uninstalled_at": None,
        "uninstalled_by": None
    }


def test_get_installation_returns_installation_when_found(mock_supabase_query, sample_installation_data):
    """Test that get_installation returns the installation when found."""
    # Arrange
    mock_supabase_query.execute.return_value = (
        (None, [sample_installation_data]),
        None
    )
    
    # Act
    result = get_installation(owner_id=TEST_OWNER_ID)
    
    # Assert
    assert result is not None
    assert isinstance(result, dict)
    assert result["installation_id"] == sample_installation_data["installation_id"]
    assert result["owner_id"] == sample_installation_data["owner_id"]
    assert result["owner_name"] == sample_installation_data["owner_name"]
    assert result["owner_type"] == sample_installation_data["owner_type"]
    assert result["uninstalled_at"] is None


def test_get_installation_returns_first_installation_when_multiple_found(mock_supabase_query):
    """Test that get_installation returns the first installation when multiple are found."""
    # Arrange
    first_installation = {
        "installation_id": 11111,
        "owner_id": TEST_OWNER_ID,
        "owner_name": "first_owner",
        "owner_type": "Organization",
        "created_at": datetime.datetime(2023, 1, 1, 12, 0, 0),
        "created_by": "test_user",
        "uninstalled_at": None,
        "uninstalled_by": None
    }
    second_installation = {
        "installation_id": 22222,
        "owner_id": TEST_OWNER_ID,
        "owner_name": "second_owner",
        "owner_type": "User",
        "created_at": datetime.datetime(2023, 2, 1, 12, 0, 0),
        "created_by": "test_user",
        "uninstalled_at": None,
        "uninstalled_by": None
    }
    mock_supabase_query.execute.return_value = (
        (None, [first_installation, second_installation]),
        None
    )
    
    # Act
    result = get_installation(owner_id=TEST_OWNER_ID)
    
    # Assert
    assert result is not None
    assert result["installation_id"] == first_installation["installation_id"]
    assert result["owner_name"] == first_installation["owner_name"]


def test_get_installation_returns_none_when_no_data_found(mock_supabase_query):
    """Test that get_installation returns None when no data is found."""
    # Arrange
    mock_supabase_query.execute.return_value = (
        (None, []),
        None
    )
    
    # Act
    result = get_installation(owner_id=TEST_OWNER_ID)
    
    # Assert
    assert result is None


def test_get_installation_returns_none_when_data_is_none(mock_supabase_query):
    """Test that get_installation returns None when data[1] is None."""
    # Arrange
    mock_supabase_query.execute.return_value = (
        (None, None),
        None
    )
    
    # Act
    result = get_installation(owner_id=TEST_OWNER_ID)
    
    # Assert
    assert result is None


def test_get_installation_returns_none_when_exception_occurs(mock_supabase_query):
    """Test that get_installation returns None when an exception occurs."""
    # Arrange
    mock_supabase_query.execute.side_effect = Exception("Database error")
    
    # Act
    result = get_installation(owner_id=TEST_OWNER_ID)
    
    # Assert
    assert result is None


def test_get_installation_returns_none_when_index_error_occurs(mock_supabase_query):
    """Test that get_installation returns None when IndexError occurs accessing data."""
    # Arrange - simulate empty result that would cause IndexError
    mock_supabase_query.execute.return_value = (
        (None, []),
        None
    )
    
    # Act
    result = get_installation(owner_id=TEST_OWNER_ID)
    
    # Assert
    assert result is None


def test_get_installation_function_signature():
    """Test that get_installation has the correct function signature."""
    # Get function signature
    sig = inspect.signature(get_installation)
    
    # Assert parameter count and names
    assert len(sig.parameters) == 1
    assert "owner_id" in sig.parameters
    
    # Assert parameter type annotation
    owner_id_param = sig.parameters["owner_id"]
    assert owner_id_param.annotation == int


def test_get_installation_has_handle_exceptions_decorator():
    """Test that get_installation is decorated with handle_exceptions."""
    # Check if the function has the expected wrapper attributes from handle_exceptions
    assert hasattr(get_installation, "__wrapped__")
    
    # Verify the function name is preserved by the decorator
    assert get_installation.__name__ == "get_installation"
