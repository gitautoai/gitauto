from utils.files.should_skip_php import should_skip_php


def test_export_only():
    # File with only require statements
    content = """<?php
require_once 'vendor/autoload.php';
require_once 'config/database.php';
use App\\Models\\User;
use App\\Services\\Logger;"""
    assert should_skip_php(content) is True


def test_constants_only():
    # Constants only
    content = """<?php
const MAX_RETRIES = 3;
const API_URL = 'https://api.example.com';
const DEBUG = true;
define('STATUS_CODE', 200);"""
    assert should_skip_php(content) is True


def test_multiline_string_constants():
    # Multi-line string constants
    content = """<?php
const IDENTIFY_CAUSE = <<<EOT
You are a GitHub Actions expert.
Given information such as a pull request title, identify the cause.
EOT;

const ANOTHER_TEMPLATE = <<<EOT
This is another template
with multiple lines
EOT;"""
    assert should_skip_php(content) is True


def test_typeddict_only():
    # Interface definitions only
    content = """<?php
interface User
{
    public function getId(): int;
    public function getName(): string;
    public function getEmail(): string;
}

interface Config
{
    public function getTimeout(): int;
    public function getRetries(): int;
}"""
    assert should_skip_php(content) is True


def test_exception_classes_only():
    # Simple empty classes
    content = """<?php
class CustomError extends Exception
{
}

class AuthenticationError extends Exception
{
}"""
    assert should_skip_php(content) is True


def test_mixed_imports_and_constants():
    # Mixed requires and constants
    content = """<?php
require_once 'config/app.php';
use App\\Services\\Cache;

const MAX_RETRIES = 3;
const API_URL = 'https://api.example.com';

const VERSION = '1.0.0';"""
    assert should_skip_php(content) is True


def test_function_with_logic():
    # Function definitions - should NOT be skipped
    content = """<?php
function calculateTotal(array $items): float
{
    return array_sum(array_column($items, 'price'));
}

function processData(array $data): array
{
    return array_map(fn($x) => $x * 2, $data);
}"""
    assert should_skip_php(content) is False


def test_class_with_methods():
    # Class with methods - should NOT be skipped
    content = """<?php
class Calculator
{
    private int $value = 0;

    public function add(int $a, int $b): int
    {
        return $a + $b;
    }

    public function multiply(int $a, int $b): int
    {
        return $a * $b;
    }
}"""
    assert should_skip_php(content) is False


def test_mixed_constants_and_logic():
    # Mixed constants and logic - should NOT be skipped
    content = """<?php
const MAX_SIZE = 100;
const API_URL = 'https://api.com';

function calculateSize(): int
{
    return MAX_SIZE * 2;
}"""
    assert should_skip_php(content) is False


def test_constants_with_function_calls():
    # Constants with function calls - should NOT be skipped
    content = """<?php
$isPrd = getenv('ENV') === 'prod';
$basePath = realpath('/') . DIRECTORY_SEPARATOR . 'app';"""
    assert should_skip_php(content) is False


def test_empty_file():
    # Empty content should be skipped
    assert should_skip_php("") is True


def test_whitespace_only():
    # File with only whitespace should be skipped
    content = """




    """
    assert should_skip_php(content) is True


def test_init_file_with_imports():
    # Typical module file with only requires
    content = """<?php
require_once 'src/Module1/Class1.php';
require_once 'src/Module2/Class2.php';
require_once 'src/Utils/Helper.php';

use App\\Module1\\Class1;
use App\\Module2\\Class2;"""
    assert should_skip_php(content) is True


def test_empty_init_file():
    # Empty module file
    content = ""
    assert should_skip_php(content) is True


def test_comment_with_simple_class():
    # File with comment and simple empty class should be skipped
    content = """<?php
/*
Base class for application components
*/
class BaseComponent
{
}"""
    assert should_skip_php(content) is True


def test_empty_class_single_line_braces():
    # Empty class with braces on same line should be skipped
    content = """<?php
// Base class for components
class MyComponent {}

interface MyInterface {}"""
    assert should_skip_php(content) is True
