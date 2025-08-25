from utils.files.should_skip_ruby import should_skip_ruby


def test_requires_only():
    # File with only require statements
    content = """require 'json'
require 'net/http'
require_relative 'config'
require_relative '../lib/helper'

autoload :Parser, 'parser'
autoload :Validator, 'validator'"""
    assert should_skip_ruby(content) is True


def test_constants_only():
    # Constants only
    content = """MAX_RETRIES = 3
API_URL = 'https://api.example.com'
DEFAULT_CONFIG = { debug: true }
STATUS_CODES = [200, 201, 404]
VERSION = '1.0.0'"""
    assert should_skip_ruby(content) is True


def test_mixed_requires_and_constants():
    # Mix of requires and constants
    content = """require 'json'
require_relative 'config'

API_ENDPOINT = 'https://api.github.com'
MAX_TIMEOUT = 30
SUPPORTED_FORMATS = ['json', 'xml']

autoload :Client, 'client'"""
    assert should_skip_ruby(content) is True


def test_with_method_definition():
    # File with method definition should not be skipped
    content = """require 'json'

API_URL = 'https://api.example.com'

def fetch_data(url)
  Net::HTTP.get(URI(url))
end"""
    assert should_skip_ruby(content) is False


def test_with_class_definition():
    # File with class should not be skipped
    content = """require 'net/http'

class ApiClient
  def initialize(base_url)
    @base_url = base_url
  end

  def get(path)
    # implementation
  end
end"""
    assert should_skip_ruby(content) is False


def test_with_module_and_methods():
    # Module with methods should not be skipped
    content = """MAX_SIZE = 100

module Utils
  def self.format_time(time)
    time.strftime('%Y-%m-%d')
  end
end"""
    assert should_skip_ruby(content) is False


def test_empty_content():
    # Empty content should be skipped
    content = ""
    assert should_skip_ruby(content) is True


def test_only_comments():
    # File with only comments should be skipped
    content = """# This is a comment
# Another comment
# Yet another comment"""
    assert should_skip_ruby(content) is True


def test_only_empty_lines():
    # File with only empty lines should be skipped
    content = """


"""
    assert should_skip_ruby(content) is True


def test_comments_and_empty_lines():
    # File with only comments and empty lines should be skipped
    content = """# Header comment

# Another comment

# Final comment
"""
    assert should_skip_ruby(content) is True


def test_constants_with_comments():
    # Constants with comments should be skipped
    content = """# Configuration constants
MAX_RETRIES = 3
# API endpoint
API_URL = 'https://api.example.com'

# Default settings
DEFAULT_CONFIG = { debug: true }"""
    assert should_skip_ruby(content) is True


def test_requires_with_comments():
    # Requires with comments should be skipped
    content = """# External dependencies
require 'json'
require 'net/http'

# Internal dependencies
require_relative 'config'
require_relative '../lib/helper'"""
    assert should_skip_ruby(content) is True


def test_constant_with_underscore_prefix():
    # Constants starting with underscore should be skipped
    content = """_PRIVATE_CONSTANT = 'secret'
_INTERNAL_CONFIG = { private: true }"""
    assert should_skip_ruby(content) is True


def test_constant_with_numbers():
    # Constants with numbers should be skipped
    content = """API_V2_URL = 'https://api.v2.example.com'
MAX_RETRY_COUNT_3 = 3
CONFIG_2023 = { year: 2023 }"""
    assert should_skip_ruby(content) is True


def test_autoload_variations():
    # Different autoload formats should be skipped
    content = """autoload :Parser, 'parser'
autoload :Validator, 'lib/validator'
autoload :Client, File.join(__dir__, 'client')"""
    assert should_skip_ruby(content) is True


def test_require_variations():
    # Different require formats should be skipped
    content = """require 'json'
require "net/http"
require_relative 'config'
require_relative "../lib/helper" """
    assert should_skip_ruby(content) is True


def test_with_variable_assignment():
    # Variable assignment (lowercase) should not be skipped
    content = """require 'json'

api_url = 'https://api.example.com'
MAX_RETRIES = 3"""
    assert should_skip_ruby(content) is False


def test_with_method_call():
    # Method call should not be skipped
    content = """require 'json'

MAX_RETRIES = 3
puts "Starting application" """
    assert should_skip_ruby(content) is False


def test_with_if_statement():
    # Conditional statement should not be skipped
    content = """require 'json'

MAX_RETRIES = 3

if ENV['DEBUG']
  puts "Debug mode enabled"
end"""
    assert should_skip_ruby(content) is False


def test_with_loop():
    # Loop should not be skipped
    content = """require 'json'

ITEMS = [1, 2, 3]

ITEMS.each do |item|
  puts item
end"""
    assert should_skip_ruby(content) is False


def test_with_instance_variable():
    # Instance variable assignment should not be skipped
    content = """require 'json'

MAX_RETRIES = 3
@instance_var = "value" """
    assert should_skip_ruby(content) is False


def test_with_class_variable():
    # Class variable assignment should not be skipped
    content = """require 'json'

MAX_RETRIES = 3
@@class_var = "value" """
    assert should_skip_ruby(content) is False


def test_with_global_variable():
    # Global variable assignment should not be skipped
    content = """require 'json'

MAX_RETRIES = 3
$global_var = "value" """
    assert should_skip_ruby(content) is False


def test_with_attr_accessor():
    # attr_accessor should not be skipped
    content = """require 'json'

MAX_RETRIES = 3
attr_accessor :name"""
    assert should_skip_ruby(content) is False


def test_with_include_statement():
    # include statement should not be skipped
    content = """require 'json'

MAX_RETRIES = 3
include SomeModule"""
    assert should_skip_ruby(content) is False


def test_with_extend_statement():
    # extend statement should not be skipped
    content = """require 'json'

MAX_RETRIES = 3
extend SomeModule"""
    assert should_skip_ruby(content) is False


def test_with_case_statement():
    # case statement should not be skipped
    content = """require 'json'

MAX_RETRIES = 3

case ENV['ENVIRONMENT']
when 'production'
  puts "Production mode"
end"""
    assert should_skip_ruby(content) is False


def test_complex_constant_expressions():
    # Complex constant expressions should be skipped
    content = """API_BASE_URL = 'https://api.example.com'
API_VERSION = 'v1'
FULL_API_URL = "#{API_BASE_URL}/#{API_VERSION}"
CONFIG_HASH = {
  timeout: 30,
  retries: 3
}"""
    assert should_skip_ruby(content) is True


def test_mixed_whitespace_and_content():
    # Mixed whitespace with valid content should be skipped
    content = """   
# Comment with leading spaces
   require 'json'   
   
   MAX_RETRIES = 3   
   
   autoload :Parser, 'parser'   
   """
    assert should_skip_ruby(content) is True


def test_inline_comments_with_constants():
    # Constants with inline comments should be skipped
    content = """MAX_RETRIES = 3 # Maximum retry attempts
API_URL = 'https://api.example.com' # Base API URL
DEBUG_MODE = true # Enable debug logging"""
    assert should_skip_ruby(content) is True