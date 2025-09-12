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


def test_autoload_statements():
    # File with autoload statements should be skipped
    content = """autoload :MyClass, 'my_class'
autoload :AnotherClass, 'another_class'
require 'json'"""
    assert should_skip_ruby(content) is True


def test_heredoc_with_end_marker():
    # Heredoc with proper end marker should be skipped
    content = """TEMPLATE = <<~EOF
  This is a template
  with multiple lines
EOF

ANOTHER = <<~MARKER
  Another template
MARKER"""
    assert should_skip_ruby(content) is True


def test_heredoc_without_proper_end():
    # Heredoc that doesn't end properly should still be handled
    content = """TEMPLATE = <<~TEXT
  This is a template
  that continues
  without proper end"""
    assert should_skip_ruby(content) is True


def test_multiline_comment_complete():
    # Complete multi-line comment should be skipped
    content = """=begin
This is a multi-line comment
that spans several lines
=end

MAX_SIZE = 100"""
    assert should_skip_ruby(content) is True


def test_multiline_comment_incomplete():
    # Incomplete multi-line comment (missing =end) should be handled
    content = """=begin
This is a multi-line comment
that doesn't end properly

MAX_SIZE = 100"""
    assert should_skip_ruby(content) is True


def test_constants_with_brackets_no_function():
    # Constants with brackets but no function calls should be skipped
    content = """ARRAY_CONST = [1, 2, 3]
HASH_CONST = {key: 'value'}
STRING_CONST = 'simple string'"""
    assert should_skip_ruby(content) is False  # Brackets are treated as function calls


def test_constants_with_parentheses_no_function():
    # Constants with parentheses but no actual function calls
    content = """MATH_EXPR = (1 + 2) * 3
GROUPED = (value)"""
    assert should_skip_ruby(content) is False  # Parentheses are treated as function calls


def test_mixed_comments_and_constants():
    # Mix of comments, constants, and requires
    content = """# This is a configuration file
require 'logger'

# Maximum retries
MAX_RETRIES = 5

=begin
API configuration
=end
API_URL = 'https://example.com'

# Debug flag
DEBUG = false"""
    assert should_skip_ruby(content) is True


def test_class_with_content_inside():
    # Class with non-attr content should not be skipped
    content = """class MyClass
  CONSTANT = 'value'
end"""
    assert should_skip_ruby(content) is False


def test_nested_heredoc_markers():
    # Test heredoc with nested << markers
    content = """TEMPLATE = <<~TEXT
  This has << inside
  and more << markers
TEXT"""
    assert should_skip_ruby(content) is True


def test_heredoc_end_marker_with_spaces():
    # Test heredoc end marker that starts with spaces (should not end heredoc)
    content = """TEMPLATE = <<~TEXT
  This is content
  TEXT"""
    assert should_skip_ruby(content) is True


def test_heredoc_end_marker_non_alpha():
    # Test heredoc end marker that is not alphabetic (should not end heredoc)
    content = """TEMPLATE = <<~TEXT
  This is content
  123"""
    assert should_skip_ruby(content) is True


def test_constants_with_complex_regex():
    # Test constants that match the regex pattern
    content = """MY_CONSTANT = 'value'
ANOTHER_CONST_123 = 42
_PRIVATE_CONST = true
A = 'simple'"""
    assert should_skip_ruby(content) is True


def test_module_with_multiple_attr_types():
    # Test module with different attr_ declarations
    content = """module TestModule
  attr_accessor :name, :age
  attr_reader :id
  attr_writer :status
end"""
    assert should_skip_ruby(content) is True


def test_only_comments_and_empty_lines():
    # File with only comments and empty lines should be skipped
    content = """# This is a comment

# Another comment

# Final comment"""
    assert should_skip_ruby(content) is True


def test_executable_code():
    # File with executable code should not be skipped
    content = """puts 'Hello World'
x = 1 + 2"""
    assert should_skip_ruby(content) is False


def test_lowercase_variable_assignment():
    # Lowercase variable assignment should not be skipped
    content = """my_variable = 'value'
another_var = 42"""
    assert should_skip_ruby(content) is False