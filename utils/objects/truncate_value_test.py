from datetime import datetime
from pydantic import BaseModel

from utils.objects.truncate_value import truncate_value


class SampleModel(BaseModel):
    """Test Pydantic model for testing truncate_value."""
    id: int
    name: str
    created_at: datetime


def test_truncate_value_with_pydantic_model():
    """Test that truncate_value handles Pydantic models correctly."""
    test_model = SampleModel(
        id=1,
        name="test_name",
        created_at=datetime(2023, 1, 1, 12, 0, 0)
    )
    
    result = truncate_value(test_model)
    
    # Should return a dict representation of the model
    assert isinstance(result, dict)
    assert result["id"] == 1
    assert result["name"] == "test_name"
    assert result["created_at"] == "2023-01-01T12:00:00"


def test_truncate_value_with_long_string():
    """Test that truncate_value handles long strings correctly."""
    long_string = "a" * 50
    result = truncate_value(long_string, max_length=30)
    
    assert result == "a" * 30 + "..."
    assert len(result) == 33  # 30 chars + "..."


def test_truncate_value_with_dict():
    """Test that truncate_value handles dictionaries correctly."""
    test_dict = {"key": "a" * 50}
    result = truncate_value(test_dict, max_length=30)
    
    assert result == {"key": "a" * 30 + "..."}


def test_truncate_value_with_datetime():
    """Test that truncate_value handles datetime objects correctly."""
    test_datetime = datetime(2023, 1, 1, 12, 0, 0)
    result = truncate_value(test_datetime)
    
    # Should return ISO format string
    assert result == "2023-01-01T12:00:00"
