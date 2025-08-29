from utils.files.should_skip_python import should_skip_python


def test_export_only():
    # File with only import statements and __all__
    content = """from .module import Class1, Class2
from .another import func1, func2
import os

__all__ = ['Class1', 'Class2', 'func1', 'func2']"""
    assert should_skip_python(content) is True


def test_constants_only():
    # Constants only
    content = """MAX_RETRIES = 3
API_URL = "https://api.example.com"
DEFAULT_CONFIG = {"debug": True}
STATUS_CODES = [200, 201, 404]"""
    assert should_skip_python(content) is True


def test_multiline_string_constants():
    # Multi-line string constants
    content = """IDENTIFY_CAUSE = \"\"\"
You are a GitHub Actions expert.
Given information such as a pull request title, identify the cause.
\"\"\"

ANOTHER_TEMPLATE = '''
This is another template
with multiple lines
'''"""
    assert should_skip_python(content) is True


def test_typeddict_only():
    # TypedDict class definitions only
    content = """from typing import TypedDict

class User(TypedDict):
    id: int
    name: str
    email: str

class Config(TypedDict):
    timeout: int
    retries: int"""
    assert should_skip_python(content) is True


def test_exception_classes_only():
    # Simple exception classes with only docstrings
    content = """class CustomError(Exception):
    \"\"\"Raised when something goes wrong\"\"\"

class AuthenticationError(Exception):
    \"\"\"Raised when authentication fails\"\"\"
    pass"""
    assert should_skip_python(content) is True


def test_mixed_imports_and_constants():
    # Mixed imports and constants
    content = """import os
from typing import Dict

MAX_RETRIES = 3
API_URL = "https://api.example.com"

__all__ = ['MAX_RETRIES', 'API_URL']"""
    assert should_skip_python(content) is True


def test_function_with_logic():
    # Function definitions - should NOT be skipped
    content = """def calculate_total(items):
    return sum(item.price for item in items)

def process_data(data):
    return [x * 2 for x in data]"""
    assert should_skip_python(content) is False


def test_class_with_methods():
    # Class with methods - should NOT be skipped
    content = """class Calculator:
    def __init__(self):
        self.value = 0

    def add(self, a, b):
        return a + b

    def multiply(self, a, b):
        return a * b"""
    assert should_skip_python(content) is False


def test_mixed_constants_and_logic():
    # Mixed constants and logic - should NOT be skipped
    content = """MAX_SIZE = 100
API_URL = "https://api.com"

def calculate_size():
    return MAX_SIZE * 2"""
    assert should_skip_python(content) is False


def test_constants_with_function_calls():
    # Constants with function calls - should NOT be skipped
    content = """import os
from config import get_env_var

IS_PRD = get_env_var("ENV") == "prod"
BASE_PATH = os.path.join("/", "app")"""
    assert should_skip_python(content) is False


def test_empty_file():
    # Empty content should be skipped
    assert should_skip_python("") is True


def test_whitespace_only():
    # File with only whitespace should be skipped
    content = """




    """
    assert should_skip_python(content) is True


def test_init_file_with_imports():
    # Typical __init__.py file with only imports and __all__
    content = """from .module1 import Class1, function1
from .module2 import Class2
from .utils import helper_function

__all__ = ['Class1', 'Class2', 'function1', 'helper_function']"""
    assert should_skip_python(content) is True


def test_empty_init_file():
    # Empty __init__.py file
    content = ""
    assert should_skip_python(content) is True


def test_comment_with_simple_class():
    # File with comment and simple empty class should be skipped
    content = '''"""
Base class for application components
"""
class BaseComponent:
    pass

__all__ = ["BaseComponent"]'''
    assert should_skip_python(content) is True


def test_empty_class_single_line_braces():
    # Empty class with pass on same line should be skipped
    content = """# Base class for components
class MyComponent: pass

__all__ = ['MyComponent']"""
    assert should_skip_python(content) is True
