from utils.objects.safe_get_attribute import safe_get_attribute


class SampleObject:
    def __init__(self):
        self.name = "test"
        self.value = 42


def test_dict_get_existing_key():
    d = {"name": "test", "value": 42}
    assert safe_get_attribute(d, "name", "default") == "test"
    assert safe_get_attribute(d, "value", 0) == 42


def test_dict_get_missing_key():
    d = {"name": "test"}
    assert safe_get_attribute(d, "missing", "default") == "default"
    assert safe_get_attribute(d, "missing", 0) == 0


def test_object_get_existing_attr():
    obj = SampleObject()
    assert safe_get_attribute(obj, "name", "default") == "test"
    assert safe_get_attribute(obj, "value", 0) == 42


def test_object_get_missing_attr():
    obj = SampleObject()
    assert safe_get_attribute(obj, "missing", "default") == "default"
    assert safe_get_attribute(obj, "missing", 0) == 0


def test_none_object():
    assert safe_get_attribute(None, "attr", "default") == "default"


def test_empty_dict():
    d = {}
    assert safe_get_attribute(d, "key", "default") == "default"


def test_nested_dict():
    d = {"outer": {"inner": "value"}}
    inner = safe_get_attribute(d, "outer", {})
    assert safe_get_attribute(inner, "inner", "default") == "value"


def test_object_with_get_method():
    class CustomContainer:
        def __init__(self):
            self.data = {"key": "value"}

        def get(self, key, default=None):
            return self.data.get(key, default)

    container = CustomContainer()
    assert safe_get_attribute(container, "key", "default") == "value"
    assert safe_get_attribute(container, "missing", "default") == "default"


def test_default_types():
    d = {"name": "test"}
    assert safe_get_attribute(d, "missing", None) is None
    assert safe_get_attribute(d, "missing", []) == []
    assert safe_get_attribute(d, "missing", {}) == {}
    assert safe_get_attribute(d, "missing", False) is False
