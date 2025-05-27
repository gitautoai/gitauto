from utils.objects.safe_get_attribute import safe_get_attribute


class MockObject:
    """Mock object for testing attribute access."""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def test_safe_get_attribute_dict_existing_key():
    """Test getting existing key from dictionary."""
    test_dict = {"name": "John", "age": 30}
    result = safe_get_attribute(test_dict, "name")
    assert result == "John"


def test_safe_get_attribute_dict_missing_key():
    """Test getting missing key from dictionary returns default."""
    test_dict = {"name": "John", "age": 30}
    result = safe_get_attribute(test_dict, "email")
    assert result is None


def test_safe_get_attribute_dict_missing_key_custom_default():
    """Test getting missing key from dictionary returns custom default."""
    test_dict = {"name": "John", "age": 30}
    result = safe_get_attribute(test_dict, "email", "no-email")
    assert result == "no-email"


def test_safe_get_attribute_object_existing_attribute():
    """Test getting existing attribute from object."""
    obj = MockObject(name="Jane", age=25)
    result = safe_get_attribute(obj, "name")
    assert result == "Jane"


def test_safe_get_attribute_object_missing_attribute():
    """Test getting missing attribute from object returns default."""
    obj = MockObject(name="Jane", age=25)
    result = safe_get_attribute(obj, "email")
    assert result is None


def test_safe_get_attribute_object_missing_attribute_custom_default():
    """Test getting missing attribute from object returns custom default."""
    obj = MockObject(name="Jane", age=25)
    result = safe_get_attribute(obj, "email", "no-email")
    assert result == "no-email"


def test_safe_get_attribute_none_object():
    """Test safe_get_attribute with None object."""
    result = safe_get_attribute(None, "any_attr")
    assert result is None


def test_safe_get_attribute_none_object_custom_default():
    """Test safe_get_attribute with None object and custom default."""
    result = safe_get_attribute(None, "any_attr", "default_value")
    assert result == "default_value"


def test_safe_get_attribute_primitive_types():
    """Test safe_get_attribute with primitive types."""
    # String
    result = safe_get_attribute("hello", "length")
    assert result is None
    
    # Integer
    result = safe_get_attribute(42, "value")
    assert result is None
    
    # Boolean
    result = safe_get_attribute(True, "state")
    assert result is None


def test_safe_get_attribute_list():
    """Test safe_get_attribute with list (no get method, no attributes)."""
    test_list = [1, 2, 3]
    result = safe_get_attribute(test_list, "length")
    assert result is None


def test_safe_get_attribute_custom_object_with_get():
    """Test with custom object that has a get method."""
    class CustomDict:
        def get(self, key, default=None):
            data = {"custom_key": "custom_value"}
            return data.get(key, default)
    
    obj = CustomDict()
    result = safe_get_attribute(obj, "custom_key")
    assert result == "custom_value"
    
    result = safe_get_attribute(obj, "missing_key", "fallback")
    assert result == "fallback"