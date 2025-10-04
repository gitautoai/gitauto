# check
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


def test_single_line_triple_quote_constant():
    # Single-line triple quoted constant
    content = '''API_KEY = """abc123"""
DEBUG_MODE = True'''
    assert should_skip_python(content) is True


def test_namedtuple_class():
    # NamedTuple class definitions
    content = """from typing import NamedTuple

class Point(NamedTuple):
    x: int
    y: int

class User(typing.NamedTuple):
    name: str
    age: int"""
    assert should_skip_python(content) is True


def test_multiline_string_assignment_parentheses():
    # Multi-line string assignment with parentheses
    content = """TEMPLATE = (
    "This is a very long template "
    "that spans multiple lines "
    "and uses parentheses"
)

OTHER_CONSTANT = 42"""
    assert should_skip_python(content) is True


def test_multiline_list_assignment():
    # Multi-line list assignment
    content = """ALLOWED_EXTENSIONS = [
    ".py",
    ".js",
    ".ts",
    ".java"
]

MAX_SIZE = 100"""
    assert should_skip_python(content) is True


def test_complex_class_transitions():
    # Test complex class definition transitions - should NOT skip due to TypedTuple typo
    content = """class MyError(Exception):
    \"\"\"Custom error\"\"\"
    pass

class DataClass(TypedDict):
    id: int
    name: str

MAX_RETRIES = 5"""
    assert should_skip_python(content) is True


def test_mixed_assignment_patterns():
    # Test various assignment patterns that should be skipped
    content = """SIMPLE_VAR = "value"
LIST_VAR = [1, 2, 3]
DICT_VAR = {"key": "value"}
TUPLE_VAR = (1, 2, 3)
BOOL_VAR = True
NUM_VAR = 42
FLOAT_VAR = 3.14
NONE_VAR = None"""
    assert should_skip_python(content) is True


def test_bare_string_continuation():
    # Test bare string continuation
    content = '''"""
This is a module docstring
that spans multiple lines
"""

CONSTANT = "value"'''
    assert should_skip_python(content) is True


def test_autoload_statements():
    # Test autoload statements should be skipped
    content = '''from typing import TypedDict
import os
CONSTANT = "value"'''
    assert should_skip_python(content) is True


def test_constants_with_square_brackets():
    # Test constants with square brackets should NOT be skipped - dictionary access has logic
    content = '''ENV_VAR = ENV["PATH"]
API_URL = "http://example.com"'''
    assert should_skip_python(content) is False


def test_assignment_function_call_detection():
    # Test assignment with function calls should NOT be skipped
    content = '''config = load_config()
value = "test"'''
    assert should_skip_python(content) is False


def test_field_definition_with_complex_types():
    # Test class with method definitions should NOT be skipped
    content = """class Config:
    def handler(self) -> str:
        return "error"

    def process_data(self, items: List[str]) -> List[str]:
        return items"""
    assert should_skip_python(content) is False


def test_class_reprocessing_after_exit():
    # Test class re-processing after exiting a class - triggers lines 114-126
    content = '''class MyException(Exception):
    """Custom error"""
    pass
class DataClass(TypedDict):
    id: int
    name: str'''
    assert should_skip_python(content) is True


def test_class_reprocessing_typeddict():
    # Test TypedDict class re-processing - triggers lines 115-116
    content = """class FirstClass:
    pass
class SecondClass(TypedDict):
    field: str"""
    assert should_skip_python(content) is True


def test_class_reprocessing_exception():
    # Test Exception class re-processing - triggers lines 118-119
    content = """class FirstClass:
    pass
class SecondError(Exception):
    pass"""
    assert should_skip_python(content) is True


def test_class_reprocessing_namedtuple():
    # Test NamedTuple class re-processing - triggers lines 123-124
    content = """class FirstClass:
    pass
class SecondTuple(NamedTuple):
    field: str"""
    assert should_skip_python(content) is True


def test_multiline_import_with_parentheses():
    # Test multi-line imports with parentheses - triggers lines 131-132, 134-136
    content = '''from typing import (
    Dict,
    List,
    Optional
)
CONSTANT = "value"'''
    assert should_skip_python(content) is True


def test_assignment_with_literals():
    # Test assignment with literals - triggers line 173
    content = """var1 = 42
var2 = "string"
var3 = True
var4 = [1, 2, 3]"""
    assert should_skip_python(content) is True


def test_bare_string_lines():
    # Test bare string lines - triggers line 177
    content = '''"""Module docstring"""
"standalone string"
CONSTANT = "value"'''
    assert should_skip_python(content) is True


def test_class_with_logic_after_simple_class():
    # Test class with logic after a simple class - should NOT skip (line 126)
    content = """class SimpleClass:
    pass
class ComplexClass(SomeBase):
    def method(self):
        return 42"""
    assert should_skip_python(content) is False


def test_class_exit_to_typeddict():
    # Test exiting TypedDict class and immediately starting another TypedDict - triggers lines 115-116
    content = """class FirstClass(TypedDict):
    field: str
class SecondClass(TypedDict):
    id: int"""
    assert should_skip_python(content) is True


def test_class_exit_to_exception():
    # Test exiting Exception class and immediately starting another Exception - triggers lines 118-119
    content = """class FirstError(Exception):
    pass
class MyError(Exception):
    pass"""
    assert should_skip_python(content) is True


def test_class_exit_to_namedtuple():
    # Test exiting NamedTuple class and immediately starting another NamedTuple - triggers lines 123-124
    content = """class FirstTuple(NamedTuple):
    name: str
class MyTuple(NamedTuple):
    name: str"""
    assert should_skip_python(content) is True


def test_inside_exception_class_to_typeddict():
    # Test being inside exception class and encountering TypedDict - triggers lines 115-116
    content = """class MyError(Exception):
    pass
    some_var = "test"  # This keeps us in the class
class Config(TypedDict):
    name: str"""
    assert should_skip_python(content) is True


def test_inside_typeddict_class_to_exception():
    # Test being inside TypedDict class and encountering Exception - triggers lines 118-119
    content = """class Config(TypedDict):
    name: str
    other: int  # This keeps us in the class
class MyError(Exception):
    pass"""
    assert should_skip_python(content) is True


def test_inside_exception_class_to_namedtuple():
    # Test being inside exception class and encountering NamedTuple - triggers lines 123-124
    content = """class MyError(Exception):
    pass
    value = 42  # This keeps us in the class
class Point(NamedTuple):
    x: int
    y: int"""
    assert should_skip_python(content) is True


def test_direct_class_transitions_typeddict():
    # Direct transition to trigger line 115-116
    content = """class MyError(Exception):
    pass
class Config(TypedDict):
    name: str"""
    assert should_skip_python(content) is True


def test_direct_class_transitions_exception():
    # Direct transition to trigger line 118-119
    content = """class Config(TypedDict):
    name: str
class MyError(Exception):
    pass"""
    assert should_skip_python(content) is True


def test_direct_class_transitions_namedtuple():
    # Direct transition to trigger line 123-124
    content = """class MyError(Exception):
    pass
class Point(NamedTuple):
    x: int
    y: int"""
    assert should_skip_python(content) is True


def test_enum_declarations():
    # Test enum-like constants without methods - should be skipped
    content = """from enum import Enum
class Status(Enum):
    ACTIVE = 1
    INACTIVE = 2"""
    assert should_skip_python(content) is True


def test_extern_declarations():
    # Test import statements
    content = """import sys
from typing import Dict
MAX_SIZE = 100"""
    assert should_skip_python(content) is True


def test_forward_declarations():
    # Test type annotations and forward references - has if statement, should NOT be skipped
    content = """from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .other import SomeClass
MAX_SIZE = 100"""
    assert should_skip_python(content) is False


def test_using_namespace_statements():
    # Test import aliases
    content = """from collections import defaultdict as dd
from typing import List as L
import numpy as np
result = process()"""
    assert should_skip_python(content) is False


def test_template_declarations():
    # Test generic types - has function calls, should NOT be skipped
    content = """from typing import TypeVar, Generic
T = TypeVar('T')
class Container(Generic[T]):
    pass"""
    assert should_skip_python(content) is False


def test_static_extern_const():
    # Test module-level variables
    content = """_internal_var = 42
__version__ = "1.0.0"
MAX_SIZE = 100"""
    assert should_skip_python(content) is True


def test_enum_and_macro_declarations():
    # Test constants and enums
    content = """from enum import Enum
DEBUG_MODE = True
BUFFER_SIZE = 1024
MAX_SIZE = 100"""
    assert should_skip_python(content) is True


def test_macro_constants_only():
    # Test constants only
    content = """MAX_SIZE = 1024
BUFFER_SIZE = 512
value = 42"""
    assert should_skip_python(content) is True


def test_class_inside_then_nonindented_typeddict():
    # Critical test: inside exception class, indented content, then non-indented TypedDict - triggers 115-116
    content = """class MyError(Exception):
    pass
    x = 1
class Config(TypedDict):
    name: str"""
    assert should_skip_python(content) is True


def test_class_inside_then_nonindented_exception():
    # Critical test: inside TypedDict class, indented content, then non-indented Exception - triggers 118-119
    content = """class Config(TypedDict):
    name: str
    y = 2
class MyError(Exception):
    pass"""
    assert should_skip_python(content) is True


def test_class_inside_then_nonindented_namedtuple():
    # Critical test: inside exception class, indented content, then non-indented NamedTuple - triggers 123-124
    content = """class MyError(Exception):
    pass
    z = 3
class Point(NamedTuple):
    x: int
    y: int"""
    assert should_skip_python(content) is True


def test_annotation_interface_definitions():
    # Test decorator definitions - should NOT be skipped (protocol with method)
    content = '''from typing import Protocol

@protocol
class MyProtocol(Protocol):
    def method(self) -> str: ...

CONSTANT = "value"'''
    assert should_skip_python(content) is False


def test_kotlin_data_class_definitions():
    # Test dataclass definitions - should NOT be skipped (dataclass generates methods)
    content = '''from dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str
    email: str

CONSTANT = "value"'''
    assert should_skip_python(content) is False


def test_scala_case_class_definitions():
    # Test NamedTuple definitions
    content = '''from typing import NamedTuple

class Point(NamedTuple):
    x: int
    y: int

CONSTANT = "value"'''
    assert should_skip_python(content) is True


def test_module_exports_only():
    # Test module imports and __all__
    content = '''from typing import List
from collections import defaultdict

__all__ = ["CONSTANT"]
CONSTANT = "value"'''
    assert should_skip_python(content) is True


def test_standalone_closing_brace_only():
    # Test standalone statements
    content = '''class MyClass:
    pass

CONSTANT = "value"'''
    assert should_skip_python(content) is True


def test_class_closing_only():
    # Test empty class definitions
    content = """class Empty:
    pass"""
    assert should_skip_python(content) is True


def test_interface_closing_only():
    # Test Protocol definitions (Python's interface equivalent)
    content = """from typing import Protocol

class Config(Protocol):
    timeout: int"""
    assert should_skip_python(content) is True


def test_enum_closing_only():
    # Test enum definitions
    content = """from enum import Enum

class Status(Enum):
    ACTIVE = 1
    INACTIVE = 2"""
    assert should_skip_python(content) is True


def test_closing_brace_only():
    # Test closing braces (not applicable to Python - use pass)
    content = """pass"""
    assert should_skip_python(content) is True


def test_uppercase_constant_only():
    # Test uppercase constant
    content = '''API_URL = "https://api.example.com"'''
    assert should_skip_python(content) is True


def test_regular_constant_only():
    # Test regular constant
    content = """flag = True"""
    assert should_skip_python(content) is True
