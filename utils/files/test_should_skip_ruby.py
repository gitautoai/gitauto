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
