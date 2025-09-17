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


def test_heredoc_multiline_detection():
    # Test heredoc string detection - covers lines 33-39
    content = """<?php
const TEMPLATE = <<<EOT
This is a heredoc string
with multiple lines
and special characters
EOT;

const ANOTHER = "simple string";"""
    assert should_skip_php(content) is True


def test_heredoc_without_semicolon():
    # Test heredoc without ending semicolon - edge case for line 37
    content = """<?php
const TEMPLATE = <<<EOT
This is a heredoc string
without ending semicolon
EOT

const ANOTHER = "simple string";"""
    assert should_skip_php(content) is True


def test_multiline_comment_detection():
    # Test multiline comment detection - covers lines 42-47
    content = """<?php
/* This is a multiline comment
   that spans several lines
   and contains various text */
const MAX_SIZE = 100;

/* Another comment */
const MIN_SIZE = 10;"""
    assert should_skip_php(content) is True


def test_multiline_comment_with_asterisk_in_middle():
    # Test multiline comment with asterisk in content
    content = """<?php
/* This comment has * asterisks * in the middle
   but should still be handled correctly */
const VALUE = 42;"""
    assert should_skip_php(content) is True


def test_single_line_comments():
    # Test single line comment detection - covers lines 50-51
    content = """<?php
// This is a single line comment
# This is also a comment
const MAX_SIZE = 100;
// Another comment
const MIN_SIZE = 10;"""
    assert should_skip_php(content) is True


def test_php_tags_detection():
    # Test PHP tag detection - covers lines 53-54
    content = """<?php
const VALUE = 42;
?>
<?
const ANOTHER = 24;
?>"""
    assert should_skip_php(content) is True


def test_abstract_interface():
    # Test abstract interface - covers line 60
    content = """<?php
abstract interface BaseInterface
{
    public function method(): string;
}"""
    assert should_skip_php(content) is True


def test_final_interface():
    # Test final interface - covers line 60
    content = """<?php
final interface ConfigInterface
{
    public function getValue(): int;
}"""
    assert should_skip_php(content) is True


def test_opening_brace_detection():
    # Test opening brace detection - covers line 63-64
    content = """<?php
class MyClass
{
    public $property;
}"""
    assert should_skip_php(content) is True


def test_abstract_class():
    # Test abstract class - covers line 88
    content = """<?php
abstract class BaseClass
{
    public $property;
}"""
    assert should_skip_php(content) is True


def test_final_class():
    # Test final class - covers line 88
    content = """<?php
final class FinalClass
{
    public $property;
}"""
    assert should_skip_php(content) is True


def test_class_with_opening_brace_same_line():
    # Test class with opening brace on same line - covers line 89-90
    content = """<?php
class MyClass {
    public $property;
}"""
    assert should_skip_php(content) is True


def test_private_property_in_class():
    # Test private property detection - covers line 102
    content = """<?php
class MyClass
{
    private $privateProperty;
    protected $protectedProperty;
    public $publicProperty;
}"""
    assert should_skip_php(content) is True


def test_include_statements():
    # Test include statements - covers lines 107-117
    content = """<?php
include 'file1.php';
include_once 'file2.php';
require 'file3.php';
require_once 'file4.php';
use App\\Models\\User;
use App\\Services\\Logger;"""
    assert should_skip_php(content) is True


def test_namespace_declaration():
    # Test namespace declaration - covers lines 119-120
    content = """<?php
namespace App\\Controllers;
namespace App\\Models\\User;
const VALUE = 42;"""
    assert should_skip_php(content) is True


def test_private_const():
    # Test private const - covers line 123
    content = """<?php
class MyClass
{
    private const PRIVATE_CONST = 'value';
    protected const PROTECTED_CONST = 42;
    public const PUBLIC_CONST = true;
}"""
    assert should_skip_php(content) is True


def test_define_function():
    # Test define function - covers line 123
    content = """<?php
define('CONSTANT_NAME', 'value');
define('ANOTHER_CONSTANT', 42);
define('BOOL_CONSTANT', true);"""
    assert should_skip_php(content) is True


def test_global_const_any_case():
    # Test global const with any case - covers line 128
    content = """<?php
const myConstant = 'value';
const AnotherConstant = 42;
const UPPER_CASE = true;"""
    assert should_skip_php(content) is True


def test_variable_assignment_with_quotes():
    # Test variable assignment with different quote types - covers line 131
    content = """<?php
$stringVar = "double quotes";
$singleVar = 'single quotes';
$arrayVar = ['array', 'values'];
$objectVar = {'key': 'value'};"""
    assert should_skip_php(content) is True


def test_return_with_quotes():
    # Test return statement with different quote types - covers line 136
    content = """<?php
return "simple string";
return 'another string';
return ['array', 'return'];
return {'object': 'return'};"""
    assert should_skip_php(content) is True


def test_array_closing_with_semicolon():
    # Test array closing with semicolon - covers line 142
    content = """<?php
$config = [
    'key' => 'value'
};"""
    assert should_skip_php(content) is True


def test_array_element_patterns():
    # Test various array element patterns - covers line 146
    content = """<?php
$config = [
    'simple' => 'value',
    "double" => "quotes",
    key => value,
    'number' => 42,
    'boolean' => true,
];"""
    assert should_skip_php(content) is True


def test_nested_array_pattern():
    # Test nested array pattern - covers line 149
    content = """<?php
$config = [
    'database' => [
        'host' => 'localhost'
    ],
    "cache" => [
        "driver" => "redis"
    ]
];"""
    assert should_skip_php(content) is True


def test_closing_statements():
    # Test various closing statements - covers line 155
    content = """<?php
class MyClass {
    public $prop;
}

$array = [
    'value'
];

?>"""
    assert should_skip_php(content) is True


def test_for_loop_detection():
    # Test for loop detection - covers line 163-165
    content = """<?php
for ($i = 0; $i < 10; $i++) {
    echo $i;
}"""
    assert should_skip_php(content) is False


def test_while_loop_detection():
    # Test while loop detection - covers line 163-165
    content = """<?php
while ($condition) {
    doSomething();
}"""
    assert should_skip_php(content) is False


def test_unknown_code_detection():
    # Test unknown code detection - covers line 169
    content = """<?php
echo "Hello World";"""
    assert should_skip_php(content) is False


def test_complex_mixed_content():
    # Test complex mixed content that should be skipped
    content = """<?php
namespace App\\Models;

use App\\Contracts\\UserInterface;
use App\\Traits\\Timestampable;

/* Multi-line comment
   with documentation */

// Single line comment

const MAX_USERS = 1000;
const API_VERSION = '2.0';

define('DEBUG_MODE', false);

interface UserRepositoryInterface
{
    public function findById(int $id): ?User;
    public function save(User $user): bool;
}

trait Loggable
{
    public $logLevel = 'info';
}

class User
{
    public string $name;
    private int $id;
    protected string $email;
}

class UserNotFoundException extends Exception
{
}

$config = [
    'database' => [
        'host' => 'localhost',
        'port' => 3306
    ],
    'cache' => [
        'driver' => 'redis'
    ]
];

return [
    'settings' => $config,
    'version' => API_VERSION
];
?>"""
    assert should_skip_php(content) is True


def test_complex_mixed_content_with_logic():
    # Test complex mixed content with logic that should NOT be skipped
    content = """<?php
namespace App\\Services;

use App\\Models\\User;

const MAX_RETRIES = 3;

class UserService
{
    private $repository;

    public function __construct(UserRepository $repo)
    {
        $this->repository = $repo;
    }

    public function createUser(array $data): User
    {
        if (empty($data['name'])) {
            throw new InvalidArgumentException('Name is required');
        }

        return $this->repository->create($data);
    }
}"""
    assert should_skip_php(content) is False


def test_heredoc_with_starting_marker():
    # Test heredoc detection with starting marker - edge case for line 33
    content = """<?php
const TEMPLATE = <<<EOT
This line starts with <<<INNER but should not trigger new heredoc
EOT;"""
    assert should_skip_php(content) is True


def test_multiline_comment_start_end_same_line():
    # Test multiline comment that starts and ends on same line
    content = """<?php
/* single line multiline comment */ const VALUE = 42;
const ANOTHER = 24;"""
    assert should_skip_php(content) is True


def test_interface_method_with_private_protected():
    # Test interface method with private/protected modifiers - covers line 71
    content = """<?php
interface TestInterface
{
    private function privateMethod(): void;
    protected function protectedMethod(): string;
    public function publicMethod(): int;
}"""
    assert should_skip_php(content) is True


def test_trait_with_opening_brace_same_line():
    # Test trait with opening brace on same line - covers line 79
    content = """<?php
trait MyTrait {
    public $property;
}"""
    assert should_skip_php(content) is True


def test_class_without_opening_brace_same_line():
    # Test class without opening brace on same line - covers line 88-91
    content = """<?php
class MyClass
{
    public $property;
}"""
    assert should_skip_php(content) is True


def test_variable_assignment_without_array_bracket():
    # Test variable assignment that doesn't trigger array detection - covers line 131-134
    content = """<?php
$stringVar = "simple string";
$numberVar = 42;
$boolVar = true;"""
    assert should_skip_php(content) is True


def test_return_statement_without_array_bracket():
    # Test return statement that doesn't trigger array detection - covers line 136-139
    content = """<?php
return "simple string";
return 42;
return true;"""
    assert should_skip_php(content) is True


def test_array_initialization_without_closing_bracket():
    # Test array initialization that spans multiple lines - covers line 132-133
    content = """<?php
$config = [
    'key1' => 'value1',
    'key2' => 'value2'
];"""
    assert should_skip_php(content) is True


def test_return_array_without_closing_bracket():
    # Test return array that spans multiple lines - covers line 137-138
    content = """<?php
return [
    'status' => 'success',
    'data' => 'result'
];"""
    assert should_skip_php(content) is True


def test_edge_case_empty_lines_and_comments():
    # Test file with only empty lines, comments, and PHP tags
    content = """<?php

// Comment only

/* Another comment */


?>"""
    assert should_skip_php(content) is True
