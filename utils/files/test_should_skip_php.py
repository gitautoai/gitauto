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


def test_single_line_triple_quote_constant():
    # Single-line constant definition
    content = """<?php
const API_KEY = "abc123";
const DEBUG_MODE = true;"""
    assert should_skip_php(content) is True


def test_namedtuple_class():
    # Class definitions with properties
    content = """<?php
namespace Example;

class Point {
    public int $x;
    public int $y;
}

class User {
    public string $name;
    public int $age;
}"""
    assert should_skip_php(content) is True


def test_multiline_string_assignment_parentheses():
    # Simple string constant
    content = """<?php
const TEMPLATE = "This is a template";

const OTHER_CONSTANT = 42;"""
    assert should_skip_php(content) is True


def test_multiline_list_assignment():
    # Simple constant definitions
    content = """<?php
const EXT_PHP = ".php";
const EXT_JS = ".js";
const EXT_TS = ".ts";

const MAX_SIZE = 100;"""
    assert should_skip_php(content) is True


def test_complex_class_transitions():
    # Empty class definitions
    content = """<?php
class MyException extends Exception
{
}

class DataClass {
}

const MAX_RETRIES = 5;"""
    assert should_skip_php(content) is True


def test_mixed_assignment_patterns():
    # Test various assignment patterns that should be skipped
    content = """<?php
const SIMPLE_VAR = "value";
const LIST_VAR = [1, 2, 3];
const BOOL_VAR = true;
const NUM_VAR = 42;
const FLOAT_VAR = 3.14;
const NULL_VAR = null;"""
    assert should_skip_php(content) is True


def test_bare_string_continuation():
    # Test comments and documentation
    content = """<?php
/**
 * This is a module documentation
 * that spans multiple lines
 */

const CONSTANT = "value";"""
    assert should_skip_php(content) is True


def test_autoload_statements():
    # Test require statements should be skipped
    content = """<?php
require_once "config.php";
include "helper.php";
const CONSTANT = "value";"""
    assert should_skip_php(content) is True


def test_constants_with_square_brackets():
    # Test constants with square brackets should NOT be skipped
    content = """<?php
$ENV_VAR = $ENV["PATH"];
const API_URL = "http://example.com";"""
    assert should_skip_php(content) is False


def test_assignment_function_call_detection():
    # Test assignment with function calls should NOT be skipped
    content = """<?php
$config = loadConfig();
const API_URL = "http://example.com";"""
    assert should_skip_php(content) is False


def test_field_definition_with_complex_types():
    # Test class with methods should NOT be skipped
    content = """<?php
class Config {
    public function handler(): string {
        return "error";
    }

    public function processData(array $items): array {
        return $items;
    }
}"""
    assert should_skip_php(content) is False


def test_inside_exception_class_to_typeddict():
    # Test class definitions should be skipped
    content = """<?php
class MyError extends Exception {
}
class Config {
    public $name;
}"""
    assert should_skip_php(content) is True


def test_inside_typeddict_class_to_exception():
    # Test class definitions should be skipped
    content = """<?php
class Config {
    public $name;
}
class MyError extends Exception {
}"""
    assert should_skip_php(content) is True


def test_inside_exception_class_to_namedtuple():
    # Test class definitions should be skipped
    content = """<?php
class MyError extends Exception {
}
class Point {
    public $x;
    public $y;
}"""
    assert should_skip_php(content) is True


def test_enum_declarations():
    # Test constants and enums
    content = """<?php
const Status = [
    'ACTIVE' => 'active',
    'INACTIVE' => 'inactive',
    'PENDING' => 'pending'
];
const MAX_SIZE = 100;"""
    assert should_skip_php(content) is True


def test_extern_declarations():
    # Test require/include statements
    content = """<?php
require_once 'utils.php';
include 'config.php';
const MAX_SIZE = 100;"""
    assert should_skip_php(content) is True


def test_forward_declarations():
    # Test class/interface declarations
    content = """<?php
class ForwardClass {}
interface ForwardInterface {}
const MAX_SIZE = 100;"""
    assert should_skip_php(content) is True


def test_using_namespace_statements():
    # Test namespace usage with logic - should NOT be skipped
    content = """<?php
use App\\Utils\\Helper;
use App\\Services\\Processor;
$result = Processor::process();"""
    assert should_skip_php(content) is False


def test_template_declarations():
    # Test class with method - should NOT be skipped (has executable logic)
    content = """<?php
class Container {
    private $items = [];

    public function add($item) {
        $this->items[] = $item;
    }
}"""
    assert should_skip_php(content) is False


def test_static_extern_const():
    # Test variables and constants - should NOT be skipped (variables are mutable)
    content = """<?php
$internalVar = 42;
const VERSION = "1.0.0";
const MAX_SIZE = 100;"""
    assert should_skip_php(content) is False


def test_enum_and_macro_declarations():
    # Test constants
    content = """<?php
const DEBUG_MODE = true;
const BUFFER_SIZE = 1024;
const MAX_SIZE = 100;"""
    assert should_skip_php(content) is True


def test_macro_constants_only():
    # Test constants only
    content = """<?php
const MAX_SIZE = 1024;
const BUFFER_SIZE = 512;
const VALUE = 42;"""
    assert should_skip_php(content) is True


def test_annotation_interface_definitions():
    # Test interface definitions
    content = """<?php
interface MyInterface {
    public function method(): string;
}
const CONSTANT = "value";"""
    assert should_skip_php(content) is True


def test_kotlin_data_class_definitions():
    # Test class definitions
    content = """<?php
class User {
    public $id;
    public $name;
    public $email;
}
const CONSTANT = "value";"""
    assert should_skip_php(content) is True


def test_scala_case_class_definitions():
    # Test class definitions
    content = """<?php
class Point {
    public $x;
    public $y;
}
const CONSTANT = "value";"""
    assert should_skip_php(content) is True


def test_module_exports_only():
    # Test require/namespace statements
    content = """<?php
namespace App\\Models;
use App\\Contracts\\UserInterface;
const CONSTANT = "value";"""
    assert should_skip_php(content) is True


def test_standalone_closing_brace_only():
    # Test class with closing brace
    content = """<?php
class MyClass {
    public $value;
}
const CONSTANT = "value";"""
    assert should_skip_php(content) is True


def test_abstract_function_declaration():
    # Test line 74: abstract function declaration
    content = """<?php
interface UserInterface {
    public function getName(): string;
    protected function getId();
}"""
    assert should_skip_php(content) is True


def test_trait_definition():
    # Test lines 79-81: trait opening
    content = """<?php
trait Loggable {
}"""
    assert should_skip_php(content) is True


def test_trait_closing():
    # Test lines 83-85: trait closing logic
    content = """<?php
trait Configurable {
    public $config = [];
}"""
    assert should_skip_php(content) is True


def test_constructor_parameter_promotion():
    # Test line 100: constructor parameter promotion (PHP 8.0+) - should NOT be skipped (has constructor function)
    content = """<?php
class User {
    public function __construct(
        public string $name,
        private int $id
    ) {}
}"""
    assert should_skip_php(content) is False


def test_array_initialization():
    # Test lines 129-131: array initialization detection
    content = """<?php
$CONFIG = [
    'debug' => true,
    'timeout' => 30
];"""
    assert should_skip_php(content) is True


def test_return_array_statement():
    # Test lines 134-136: return statement with array
    content = """<?php
return [
    'name' => 'test',
    'version' => '1.0'
];"""
    assert should_skip_php(content) is True


def test_multiline_array_closing():
    # Test lines 139-141: multi-line array closing
    content = """<?php
$settings = [
    'debug' => true,
    'cache' => false
];"""
    assert should_skip_php(content) is True


def test_nested_array_elements():
    # Test line 147: nested array elements
    content = """<?php
$config = [
    'database' => [
        'host' => 'localhost'
    ]
];"""
    assert should_skip_php(content) is True


def test_array_closing_comma():
    # Test line 150: array closing with comma
    content = """<?php
$data = [
    'key' => 'value'
];"""
    assert should_skip_php(content) is True


def test_control_structures():
    # Test line 163: control structure detection (should return False)
    content = """<?php
if ($condition) {
    echo "test";
}"""
    assert should_skip_php(content) is False


def test_constructor_parameter_promotion_exact():
    # Test line 100: exact constructor parameter promotion pattern - should NOT be skipped (has constructor function)
    content = """<?php
class User {
    public function __construct(
        public $name,
        private $id,
    ) {}
}"""
    assert should_skip_php(content) is False


def test_nested_array_elements_exact():
    # Test line 147: exact nested array elements pattern
    content = """<?php
$config = [
    'database' => [
        'host' => 'localhost',
        'port' => 3306
    ],
    'cache' => [
        'driver' => 'redis'
    ]
];"""
    assert should_skip_php(content) is True


def test_array_closing_comma_exact():
    # Test line 150: exact array closing with comma pattern
    content = """<?php
$data = [
    'items' => [
        'first',
        'second'
    ],
];"""
    assert should_skip_php(content) is True


def test_trait_without_opening_brace():
    # Test trait without opening brace on same line - covers branch 79->81
    content = """<?php
trait MyTrait
{
}
const MAX_SIZE = 100;"""
    assert should_skip_php(content) is True


def test_variable_assignment_multiline_array():
    # Test variable assignment with multiline array - covers branch 126->128
    content = """<?php
$config = [
    'key1' => 'value1',
    'key2' => 'value2'
];
const MAX_SIZE = 100;"""
    assert should_skip_php(content) is True


def test_return_statement_multiline_array():
    # Test return statement with multiline array - covers branch 131->133
    content = """<?php
return [
    'config' => 'value',
    'setting' => 'data'
];"""
    assert should_skip_php(content) is True


def test_variable_assignment_opening_bracket_no_closing():
    # Test line 132: variable assignment with opening bracket but no closing on same line
    # This covers the uncovered branch: line 132, block 0, if branch: 132 -> 134
    content = """<?php
$config = [
    'key1' => 'value1',
    'key2' => 'value2',
    'key3' => 'value3'
];"""
    assert should_skip_php(content) is True


def test_return_statement_opening_bracket_no_closing():
    # Test line 137: return statement with opening bracket but no closing on same line
    # This covers the uncovered branch: line 137, block 0, if branch: 137 -> 139
    content = """<?php
return [
    'status' => 'success',
    'data' => [
        'id' => 1,
        'name' => 'test'
    ]
];"""
    assert should_skip_php(content) is True


def test_variable_assignment_with_string_opening_bracket():
    # Test variable assignment starting with string (not array)
    content = """<?php
$message = "Hello World";
const MAX_SIZE = 100;"""
    assert should_skip_php(content) is True


def test_return_statement_with_string_opening_bracket():
    # Test return statement starting with string (not array)
    content = """<?php
return "success";"""
    assert should_skip_php(content) is True


def test_variable_assignment_single_line_array():
    # Test variable assignment with single-line array (opening and closing on same line)
    content = """<?php
$config = ['key' => 'value'];
const MAX_SIZE = 100;"""
    assert should_skip_php(content) is True


def test_return_statement_single_line_array():
    # Test return statement with single-line array (opening and closing on same line)
    content = """<?php
return ['status' => 'ok'];"""
    assert should_skip_php(content) is True


def test_variable_assignment_with_curly_brace():
    # Test variable assignment starting with curly brace (object notation)
    content = """<?php
$obj = {
    'property' => 'value'
};"""
    assert should_skip_php(content) is True


def test_return_statement_with_curly_brace():
    # Test return statement starting with curly brace
    content = """<?php
return {
    'data' => 'value'
};"""
    assert should_skip_php(content) is True


def test_multiline_array_with_nested_arrays():
    # Test complex nested array structure
    content = """<?php
$config = [
    'database' => [
        'connections' => [
            'mysql' => [
                'host' => 'localhost',
                'port' => 3306
            ],
            'pgsql' => [
                'host' => 'localhost',
                'port' => 5432
            ]
        ]
    ],
    'cache' => [
        'default' => 'redis'
    ]
];"""
    assert should_skip_php(content) is True


def test_return_multiline_array_with_nested_arrays():
    # Test return with complex nested array structure
    content = """<?php
return [
    'users' => [
        'admin' => [
            'name' => 'Admin',
            'role' => 'administrator'
        ],
        'guest' => [
            'name' => 'Guest',
            'role' => 'viewer'
        ]
    ],
    'settings' => [
        'theme' => 'dark'
    ]
];"""
    assert should_skip_php(content) is True


def test_variable_assignment_empty_array():
    # Test variable assignment with empty array
    content = """<?php
$empty = [];
const MAX_SIZE = 100;"""
    assert should_skip_php(content) is True


def test_return_statement_empty_array():
    # Test return statement with empty array
    content = """<?php
return [];"""
    assert should_skip_php(content) is True


def test_for_loop_detection():
    # Test for loop detection - should NOT be skipped
    content = """<?php
for ($i = 0; $i < 10; $i++) {
    echo $i;
}"""
    assert should_skip_php(content) is False


def test_while_loop_detection():
    # Test while loop detection - should NOT be skipped
    content = """<?php
while ($condition) {
    doSomething();
}"""
    assert should_skip_php(content) is False


def test_heredoc_multiline():
    # Test heredoc string handling
    content = """<?php
const TEMPLATE = <<<EOT
Line 1
Line 2
Line 3
EOT;
const MAX_SIZE = 100;"""
    assert should_skip_php(content) is True


def test_heredoc_with_semicolon():
    # Test heredoc ending detection
    content = """<?php
const SQL = <<<SQL
SELECT * FROM users
WHERE active = 1
SQL;
const VERSION = "1.0";"""
    assert should_skip_php(content) is True


def test_multiline_comment_handling():
    # Test multi-line comment handling
    content = """<?php
/*
 * This is a multi-line comment
 * that spans several lines
 * and should be ignored
 */
const MAX_SIZE = 100;"""
    assert should_skip_php(content) is True


def test_single_line_comment_hash():
    # Test single-line comment with hash
    content = """<?php
# This is a comment
const MAX_SIZE = 100;"""
    assert should_skip_php(content) is True


def test_single_line_comment_double_slash():
    # Test single-line comment with double slash
    content = """<?php
// This is a comment
const MAX_SIZE = 100;"""
    assert should_skip_php(content) is True


def test_php_tags_handling():
    # Test PHP tags handling
    content = """<?php
const MAX_SIZE = 100;
?>"""
    assert should_skip_php(content) is True


def test_short_php_tag():
    # Test short PHP tag
    content = """<?
const MAX_SIZE = 100;
?>"""
    assert should_skip_php(content) is True


def test_interface_with_abstract_modifier():
    # Test interface with abstract modifier
    content = """<?php
abstract interface MyInterface {
    public function method(): void;
}"""
    assert should_skip_php(content) is True


def test_interface_with_final_modifier():
    # Test interface with final modifier
    content = """<?php
final interface MyInterface {
    public function method(): void;
}"""
    assert should_skip_php(content) is True


def test_class_with_abstract_modifier():
    # Test class with abstract modifier
    content = """<?php
abstract class MyClass {
    public $property;
}"""
    assert should_skip_php(content) is True


def test_class_with_final_modifier():
    # Test class with final modifier
    content = """<?php
final class MyClass {
    public $property;
}"""
    assert should_skip_php(content) is True


def test_class_property_with_visibility():
    # Test class property with different visibility modifiers
    content = """<?php
class MyClass {
    public $publicProp;
    private $privateProp;
    protected $protectedProp;
}"""
    assert should_skip_php(content) is True


def test_class_property_without_visibility():
    # Test class property without visibility modifier
    content = """<?php
class MyClass {
    $property;
}"""
    assert should_skip_php(content) is True


def test_constant_with_visibility():
    # Test constant with visibility modifiers
    content = """<?php
class MyClass {
    public const PUBLIC_CONST = 1;
    private const PRIVATE_CONST = 2;
    protected const PROTECTED_CONST = 3;
}"""
    assert should_skip_php(content) is True


def test_define_function():
    # Test define function for constants
    content = """<?php
define('MAX_SIZE', 100);
define('API_URL', 'https://api.example.com');"""
    assert should_skip_php(content) is True


def test_uppercase_constant():
    # Test uppercase constant pattern
    content = """<?php
const MAX_SIZE = 100;
const API_KEY = 'secret';"""
    assert should_skip_php(content) is True


def test_lowercase_constant():
    # Test lowercase constant (any case for PHP)
    content = """<?php
const maxSize = 100;
const apiKey = 'secret';"""
    assert should_skip_php(content) is True


def test_array_element_with_arrow():
    # Test array element with arrow notation
    content = """<?php
$config = [
    'key1' => 'value1',
    'key2' => 'value2'
];"""
    assert should_skip_php(content) is True


def test_array_element_with_quotes():
    # Test array element with various quote styles
    content = """<?php
$config = [
    "key1" => "value1",
    'key2' => 'value2',
    key3 => value3
];"""
    assert should_skip_php(content) is True


def test_nested_array_element_pattern():
    # Test nested array element pattern
    content = """<?php
$config = [
    'database' => [
        'host' => 'localhost'
    ]
];"""
    assert should_skip_php(content) is True


def test_closing_bracket_with_comma():
    # Test closing bracket with comma
    content = """<?php
$config = [
    'key' => [
        'nested' => 'value'
    ],
];"""
    assert should_skip_php(content) is True


def test_closing_statements():
    # Test various closing statements
    content = """<?php
class MyClass {
}
$array = [];
function_call();
?>"""


def test_branch_coverage_variable_assignment_multiline_array_start():
    # Explicitly test line 132 branch: variable assignment with [ but no ] on same line
    # This ensures in_array_initialization is set to True
    content = """<?php
$data = [
    'item1',
    'item2'
];"""
    assert should_skip_php(content) is True


def test_branch_coverage_return_multiline_array_start():
    # Explicitly test line 137 branch: return statement with [ but no ] on same line
    # This ensures in_array_initialization is set to True
    content = """<?php
return [
    'value1',
    'value2'
];"""
    assert should_skip_php(content) is True


def test_branch_coverage_variable_assignment_with_curly_multiline():
    # Test variable assignment with { but no closing on same line
    content = """<?php
$obj = {
    'prop' => 'value'
};"""
    assert should_skip_php(content) is True


def test_branch_coverage_return_with_curly_multiline():
    # Test return statement with { but no closing on same line
    content = """<?php
return {
    'prop' => 'value'
};"""
    assert should_skip_php(content) is True


def test_branch_coverage_array_closing_with_brace_semicolon():
    # Test line 142: array closing with }; pattern
    content = """<?php
$config = [
    'key' => 'value'
];"""
    assert should_skip_php(content) is True


def test_branch_coverage_in_array_initialization_flag():
    # Test that in_array_initialization flag works correctly across multiple lines
    content = """<?php
$config = [
    'database' => [
        'host' => 'localhost',
        'port' => 3306,
        'name' => 'mydb'
    ],
    'cache' => [
        'driver' => 'redis',
        'host' => 'localhost'
    ]
];
const MAX_SIZE = 100;"""
    assert should_skip_php(content) is True


def test_branch_coverage_return_array_initialization_flag():
    # Test that in_array_initialization flag works correctly for return statements
    content = """<?php
return [
    'users' => [
        'admin' => 'John',
        'guest' => 'Jane'
    ],
    'settings' => [
        'theme' => 'dark',
        'lang' => 'en'
    ]
];"""
    assert should_skip_php(content) is True


def test_function_detection_with_visibility():
    # Test function detection with visibility modifiers - should NOT be skipped
    content = """<?php
class MyClass {
    public function publicMethod() {
        return true;
    }

    private function privateMethod() {
        return false;
    }

    protected function protectedMethod() {
        return null;
    }
}"""
    assert should_skip_php(content) is False


def test_function_detection_without_visibility():
    # Test function detection without visibility modifier - should NOT be skipped
    content = """<?php
function myFunction() {
    return true;
}"""
    assert should_skip_php(content) is False


def test_edge_case_empty_lines_and_comments():
    # Test edge case with empty lines and comments
    content = """<?php

// Comment 1

/* Multi-line
   comment */

const MAX_SIZE = 100;

"""
    assert should_skip_php(content) is True


def test_edge_case_mixed_php_tags():
    # Test edge case with mixed PHP tags
    content = """<?php
const MAX_SIZE = 100;
?>
<?php
const MIN_SIZE = 10;
?>"""
    assert should_skip_php(content) is True


def test_edge_case_trait_with_opening_brace_on_same_line():
    # Test trait with opening brace on same line
    content = """<?php
trait MyTrait {
}"""
    assert should_skip_php(content) is True


def test_edge_case_class_with_opening_brace_on_same_line():
    # Test class with opening brace on same line
    content = """<?php
class MyClass {
    public $property;
}"""
    assert should_skip_php(content) is True


def test_edge_case_interface_method_with_private_visibility():
    # Test interface method with private visibility
    content = """<?php
interface MyInterface {
    private function method();
}"""
    assert should_skip_php(content) is True


def test_edge_case_interface_method_with_protected_visibility():
    # Test interface method with protected visibility
    content = """<?php
interface MyInterface {
    protected function method();
}"""
    assert should_skip_php(content) is True


def test_edge_case_standalone_opening_brace():
    # Test standalone opening brace
    content = """<?php
class MyClass
{
    public $property;
}"""
    assert should_skip_php(content) is True


def test_corner_case_variable_assignment_with_double_quote():
    # Test variable assignment starting with double quote
    content = """<?php
$message = "Hello";
const MAX_SIZE = 100;"""
    assert should_skip_php(content) is True


def test_corner_case_variable_assignment_with_single_quote():
    # Test variable assignment starting with single quote
    content = """<?php
$message = 'Hello';
const MAX_SIZE = 100;"""
    assert should_skip_php(content) is True


def test_corner_case_return_with_double_quote():
    # Test return statement starting with double quote
    content = """<?php
return "success";"""
    assert should_skip_php(content) is True


def test_corner_case_return_with_single_quote():
    # Test return statement starting with single quote
    content = """<?php
return 'success';"""
    assert should_skip_php(content) is True


def test_corner_case_multiline_array_with_closing_brace_semicolon():
    # Test multiline array with closing brace and semicolon
    content = """<?php
$config = [
    'key' => 'value'
];"""
    assert should_skip_php(content) is True


def test_corner_case_closing_parenthesis_semicolon():
    # Test closing parenthesis with semicolon
    content = """<?php
define('MAX_SIZE', 100);"""
    assert should_skip_php(content) is True


def test_error_case_unmatched_heredoc():
    # Test error case with unmatched heredoc (should still process)
    content = """<?php
const TEMPLATE = <<<EOT
This is a template
const MAX_SIZE = 100;"""
    assert should_skip_php(content) is True


def test_error_case_unmatched_multiline_comment():
    # Test error case with unmatched multiline comment (should still process)
    content = """<?php
/*
This is a comment
const MAX_SIZE = 100;"""
    assert should_skip_php(content) is True


def test_error_case_function_in_interface():
    # Test function in interface (should be skipped as it's just a signature)
    content = """<?php
interface MyInterface {
    public function method(): void;
}"""
    assert should_skip_php(content) is True


def test_error_case_function_outside_class():
    # Test function outside class - should NOT be skipped
    content = """<?php
function myFunction() {
    return true;
}"""
    assert should_skip_php(content) is False
