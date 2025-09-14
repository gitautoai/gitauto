from utils.files.should_skip_ruby import should_skip_ruby


def test_export_only():
    # File with only require statements
    content = """require 'json'
require 'net/http'
require_relative 'user'
require_relative 'config'"""
    assert should_skip_ruby(content) is True


def test_constants_only():
    # Constants only
    content = """MAX_RETRIES = 3
API_URL = 'https://api.example.com'
DEBUG = true
STATUS_CODE = 200"""
    assert should_skip_ruby(content) is True


def test_multiline_string_constants():
    # Multi-line string constants
    content = """IDENTIFY_CAUSE = <<~TEXT
  You are a GitHub Actions expert.
  Given information such as a pull request title, identify the cause.
TEXT

ANOTHER_TEMPLATE = <<~TEXT
  This is another template
  with multiple lines
TEXT"""
    assert should_skip_ruby(content) is True


def test_typeddict_only():
    # Module definitions only
    content = """module UserModule
  attr_accessor :id, :name, :email
end

module Config
  attr_reader :timeout, :retries
end"""
    assert should_skip_ruby(content) is True


def test_exception_classes_only():
    # Simple empty classes
    content = """class CustomError < StandardError
end

class AuthenticationError < StandardError
end"""
    assert should_skip_ruby(content) is True


def test_mixed_imports_and_constants():
    # Mixed requires and constants
    content = """require 'logger'
require_relative 'cache'

MAX_RETRIES = 3
API_URL = 'https://api.example.com'

VERSION = '1.0.0'"""
    assert should_skip_ruby(content) is True


def test_function_with_logic():
    # Method definitions - should NOT be skipped
    content = """def calculate_total(items)
  items.sum(&:price)
end

def process_data(data)
  data.map { |x| x * 2 }
end"""
    assert should_skip_ruby(content) is False


def test_class_with_methods():
    # Class with methods - should NOT be skipped
    content = """class Calculator
  def initialize
    @value = 0
  end

  def add(a, b)
    a + b
  end

  def multiply(a, b)
    a * b
  end
end"""
    assert should_skip_ruby(content) is False


def test_mixed_constants_and_logic():
    # Mixed constants and logic - should NOT be skipped
    content = """MAX_SIZE = 100
API_URL = 'https://api.com'

def calculate_size
  MAX_SIZE * 2
end"""
    assert should_skip_ruby(content) is False


def test_constants_with_function_calls():
    # Constants with function calls - should NOT be skipped
    content = """require 'pathname'

IS_PRD = ENV['ENV'] == 'prod'
BASE_PATH = Pathname.new('/').join('app')"""
    assert should_skip_ruby(content) is False


def test_empty_file():
    # Empty content should be skipped
    assert should_skip_ruby("") is True


def test_whitespace_only():
    # File with only whitespace should be skipped
    content = """




    """
    assert should_skip_ruby(content) is True


def test_init_file_with_imports():
    # Typical module file with only requires
    content = """require_relative 'module1/class1'
require_relative 'module2/class2'
require_relative 'utils/helper'

require 'json'
require 'net/http'"""
    assert should_skip_ruby(content) is True


def test_empty_init_file():
    # Empty module file
    content = ""
    assert should_skip_ruby(content) is True


def test_comment_with_simple_class():
    # File with comment and simple empty class should be skipped
    content = """=begin
Base class for application components
=end
class BaseComponent
end"""
    assert should_skip_ruby(content) is True


def test_empty_class_single_line_braces():
    # Empty class on single line should be skipped
    content = """# Base class for components
class MyComponent; end

module MyModule; end"""
    assert should_skip_ruby(content) is True


def test_single_line_triple_quote_constant():
    # Single-line constant definition
    content = """API_KEY = "abc123"
DEBUG_MODE = true"""
    assert should_skip_ruby(content) is True


def test_namedtuple_class():
    # Simple constant assignments
    content = """POINT_X = 10
POINT_Y = 20

USER_NAME = "default"
USER_AGE = 0"""
    assert should_skip_ruby(content) is True


def test_multiline_string_assignment_parentheses():
    # Multi-line string using heredoc
    content = """TEMPLATE = <<~TEXT
This is a very long template
that spans multiple lines
TEXT

OTHER_CONSTANT = 42"""
    assert should_skip_ruby(content) is True


def test_multiline_list_assignment():
    # Simple constant assignments
    content = """EXTENSION_1 = ".rb"
EXTENSION_2 = ".js"
EXTENSION_3 = ".ts"
EXTENSION_4 = ".py"

MAX_SIZE = 100"""
    assert should_skip_ruby(content) is True


def test_complex_class_transitions():
    # Empty class definition
    content = """class MyError < StandardError
end

class DataClass
end

MAX_RETRIES = 5"""
    assert should_skip_ruby(content) is True


def test_mixed_assignment_patterns():
    # Test various assignment patterns that should be skipped
    content = """SIMPLE_VAR = "value"
BOOL_VAR = true
NUM_VAR = 42
FLOAT_VAR = 3.14
NIL_VAR = nil"""
    assert should_skip_ruby(content) is True


def test_bare_string_continuation():
    # Test comments and documentation
    content = '''# This is a module documentation
# that spans multiple lines

CONSTANT = "value"'''
    assert should_skip_ruby(content) is True


def test_autoload_statements():
    # Test autoload statements should be skipped
    content = '''require "pathname"
autoload :MyClass, "my_class"
CONSTANT = "value"'''
    assert should_skip_ruby(content) is True


def test_constants_with_square_brackets():
    # Test constants with square brackets should NOT be skipped
    content = '''ENV_VAR = ENV["PATH"]
API_URL = "http://example.com"'''
    assert should_skip_ruby(content) is False


def test_assignment_function_call_detection():
    # Method calls should NOT be skipped
    content = '''config = load_config()
value = "test"'''
    assert should_skip_ruby(content) is False


def test_field_definition_with_complex_types():
    # Class with method definitions
    content = """class Config
  def handler
    "error"
  end

  def process_data(items)
    items
  end
end"""
    assert should_skip_ruby(content) is False


def test_inside_exception_class_to_typeddict():
    # Test being inside class and encountering another class
    content = """class MyError < StandardError
end
class Config
  attr_accessor :name
end"""
    assert should_skip_ruby(content) is True


def test_inside_typeddict_class_to_exception():
    # Test being inside class and encountering exception class
    content = """class Config
  attr_accessor :name
end
class MyError < StandardError
end"""
    assert should_skip_ruby(content) is True


def test_inside_exception_class_to_namedtuple():
    # Test being inside class and encountering struct-like class
    content = """class MyError < StandardError
end
class Point
  attr_accessor :x, :y
end"""
    assert should_skip_ruby(content) is True


def test_enum_declarations():
    # Test constants
    content = """ACTIVE = :active
INACTIVE = :inactive
PENDING = :pending
MAX_SIZE = 100"""
    assert should_skip_ruby(content) is True


def test_extern_declarations():
    # Test require statements
    content = """require 'json'
require_relative 'utils'
MAX_SIZE = 100"""
    assert should_skip_ruby(content) is True


def test_forward_declarations():
    # Test module declarations
    content = """module MyModule
end
class ForwardClass; end
MAX_SIZE = 100"""
    assert should_skip_ruby(content) is True


def test_using_namespace_statements():
    # Test include/extend with logic - should NOT be skipped
    content = """include MyModule
extend OtherModule
result = process_data()"""
    assert should_skip_ruby(content) is False


def test_template_declarations():
    # Test module definitions
    content = """module Container
  def self.create(type)
    type.new
  end
end
MAX_SIZE = 100"""
    assert should_skip_ruby(content) is False


def test_static_extern_const():
    # Test constants and variables - class variables should NOT be skipped
    content = """@@internal_var = 42
VERSION = "1.0.0"
MAX_SIZE = 100"""
    assert should_skip_ruby(content) is False


def test_enum_and_macro_declarations():
    # Test constants
    content = """DEBUG_MODE = true
BUFFER_SIZE = 1024
MAX_SIZE = 100"""
    assert should_skip_ruby(content) is True


def test_macro_constants_only():
    # Test constants only
    content = """MAX_SIZE = 1024
BUFFER_SIZE = 512
VALUE = 42"""
    assert should_skip_ruby(content) is True


def test_annotation_interface_definitions():
    # Test module definitions
    content = '''module MyModule
  def self.method
    "implementation"
  end
end
CONSTANT = "value"'''
    assert should_skip_ruby(content) is False


def test_kotlin_data_class_definitions():
    # Test class definitions
    content = '''class User
  attr_accessor :id, :name, :email
end
CONSTANT = "value"'''
    assert should_skip_ruby(content) is True


def test_scala_case_class_definitions():
    # Test class definitions
    content = '''class Point
  attr_accessor :x, :y
end
CONSTANT = "value"'''
    assert should_skip_ruby(content) is True


def test_module_exports_only():
    # Test require statements
    content = '''require "json"
require_relative "exports"
CONSTANT = "value"'''
    assert should_skip_ruby(content) is True


def test_standalone_closing_brace_only():
    # Test class with end
    content = '''class MyClass
  attr_reader :value
end
CONSTANT = "value"'''
    assert should_skip_ruby(content) is True


def test_constant_with_function_call():
    # Test constant assignment with function call - should NOT be skipped
    content = '''CONFIG = load_config()
API_URL = "http://example.com"'''
    assert should_skip_ruby(content) is False
