from utils.files.should_skip_go import should_skip_go


def test_export_only():
    # File with only package and import statements
    content = """package types

import (
    "fmt"
    "encoding/json"
)

import "net/http\""""
    assert should_skip_go(content) is True


def test_constants_only():
    # Constants only
    content = """package main

const (
    MaxRetries = 3
    ApiURL = "https://api.example.com"
    Debug = true
)

var DefaultTimeout = 30
var (
    Version = "1.0.0"
    Build   = "abc123"
)"""
    assert should_skip_go(content) is True


def test_multiline_string_constants():
    # Multi-line string constants
    content = """package main

const IdentifyCause = `
You are a GitHub Actions expert.
Given information such as a pull request title, identify the cause.
`

const AnotherTemplate = `
This is another template
with multiple lines
`"""
    assert should_skip_go(content) is True


def test_typeddict_only():
    # Struct and interface definitions only
    content = """package main

type User struct {
    ID    int64
    Name  string
    Email string
}

type Config struct {
    Timeout int
    Retries int
}"""
    assert should_skip_go(content) is True


def test_exception_classes_only():
    # Simple empty structs
    content = """package main

type CustomError struct {
}

type AuthenticationError struct {
}"""
    assert should_skip_go(content) is True


def test_mixed_imports_and_constants():
    # Mixed imports and constants
    content = """package main

import "os"
import "fmt"

const MaxRetries = 3
const ApiURL = "https://api.example.com"

var Version = "1.0.0\""""
    assert should_skip_go(content) is True


def test_function_with_logic():
    # Function definitions - should NOT be skipped
    content = """package main

func calculateTotal(items []Item) float64 {
    total := 0.0
    for _, item := range items {
        total += item.Price
    }
    return total
}

func processData(data []int) []int {
    result := make([]int, len(data))
    for i, x := range data {
        result[i] = x * 2
    }
    return result
}"""
    assert should_skip_go(content) is False


def test_class_with_methods():
    # Struct with methods - should NOT be skipped
    content = """package main

type Calculator struct {
    value int
}

func (c *Calculator) Add(a, b int) int {
    return a + b
}

func (c *Calculator) Multiply(a, b int) int {
    return a * b
}"""
    assert should_skip_go(content) is False


def test_mixed_constants_and_logic():
    # Mixed constants and logic - should NOT be skipped
    content = """package main

const MaxSize = 100
const ApiURL = "https://api.com"

func calculateSize() int {
    return MaxSize * 2
}"""
    assert should_skip_go(content) is False


def test_constants_with_function_calls():
    # Constants with function calls - should NOT be skipped
    content = """package main

import "os"
import "path/filepath"

var IsPrd = os.Getenv("ENV") == "prod"
var BasePath = filepath.Join("/", "app")"""
    assert should_skip_go(content) is False


def test_empty_file():
    # Empty content should be skipped
    assert should_skip_go("") is True


def test_whitespace_only():
    # File with only whitespace should be skipped
    content = """




    """
    assert should_skip_go(content) is True


def test_init_file_with_imports():
    # Typical module file with only imports
    content = """package main

import (
    "github.com/example/module1"
    "github.com/example/module2"
    "github.com/example/utils"
)"""
    assert should_skip_go(content) is True


def test_empty_init_file():
    # Empty module file
    content = ""
    assert should_skip_go(content) is True


def test_comment_with_simple_class():
    # File with comment and simple empty struct should be skipped
    content = """/*
Base struct for application components
*/
type BaseComponent struct {
}

var _ = BaseComponent{}"""
    assert should_skip_go(content) is True


def test_empty_class_single_line_braces():
    # Empty struct with braces on same line should be skipped
    content = """// Base struct for components
type MyComponent struct{}

var _ = MyComponent{}"""
    assert should_skip_go(content) is True


def test_single_line_triple_quote_constant():
    # Single-line constant definition
    content = """const APIKey = "abc123"
const DebugMode = true"""
    assert should_skip_go(content) is True


def test_namedtuple_class():
    # Struct type definitions
    content = """package main

type Point struct {
    X int
    Y int
}

type User struct {
    Name string
    Age  int
}"""
    assert should_skip_go(content) is True


def test_multiline_string_assignment_parentheses():
    # Multi-line string constant without function calls
    content = """const Template = `
This is a very long template
that spans multiple lines
`

const OtherConstant = 42"""
    assert should_skip_go(content) is True


def test_multiline_list_assignment():
    # Multi-line slice assignment - should NOT skip due to var declaration with complex type
    content = """const Extension1 = ".go"
const Extension2 = ".js"
const Extension3 = ".ts"
const Extension4 = ".py"

const MaxSize = 100"""
    assert should_skip_go(content) is True


def test_complex_class_transitions():
    # Test complex struct definition transitions
    content = """type MyError struct {
    message string
}

type DataStruct struct {
    ID   int
    Name string
}

const MaxRetries = 5"""
    assert should_skip_go(content) is True


def test_mixed_assignment_patterns():
    # Test various assignment patterns that should be skipped
    content = """const SimpleVar = "value"
var ListVar = []int{1, 2, 3}
const BoolVar = true
const NumVar = 42
const FloatVar = 3.14
var NilVar interface{} = nil"""
    assert should_skip_go(content) is True


def test_bare_string_continuation():
    # Test comments
    content = '''/*
 * This is a module documentation
 * that spans multiple lines
 */

const Constant = "value"'''
    assert should_skip_go(content) is True


def test_autoload_statements():
    # Test autoload statements should be skipped
    content = '''package main
import "fmt"
const CONSTANT = "value"'''
    assert should_skip_go(content) is True


def test_constants_with_square_brackets():
    # Test constants with square brackets should NOT be skipped - array/map access has logic
    content = '''var ENV_VAR = ENV["PATH"]
const API_URL = "http://example.com"'''
    assert should_skip_go(content) is False


def test_interface_with_brace():
    # Test interface definitions with opening brace - triggers lines 61-63
    content = '''type MyInterface interface {
    Method() error
}
const VALUE = "test"'''
    assert should_skip_go(content) is True


def test_type_aliases():
    # Test type aliases - triggers line 72
    content = '''type MyString string
type MyInt int64
const VALUE = "test"'''
    assert should_skip_go(content) is True


def test_assignment_with_function_calls():
    # Test assignment with function calls should NOT be skipped - triggers line 94
    content = '''var config = loadConfig()
const API_URL = "http://example.com"'''
    assert should_skip_go(content) is False


def test_bare_const_declarations():
    # Test bare const declarations - triggers line 98
    content = """const (
    StatusActive
    StatusInactive
    StatusPending
)"""
    assert should_skip_go(content) is True


def test_struct_field_definitions():
    # Test struct field definitions - triggers line 101
    content = """type User struct {
    Name string
    Age  int
    Tags []string
}"""
    assert should_skip_go(content) is True


def test_assignment_function_call_detection():
    # Test assignment with function calls in parentheses - triggers line 94
    content = """const (
    config = loadConfig()
    value  = "test"
)"""
    assert should_skip_go(content) is False


def test_assignment_with_array_access_in_block():
    # Test assignment with array access inside const/var block - triggers line 106
    content = """const (
    envPath = ENV["PATH"]
    value   = "test"
)"""
    assert should_skip_go(content) is False


def test_field_definition_with_complex_types():
    # Test field definitions with complex types - just data structure declarations
    content = """type Config struct {
    handler func() error
    data    map[string]interface{}
    items   []*Item
}"""
    assert should_skip_go(content) is True


def test_inside_exception_class_to_typeddict():
    # Test struct definitions should be skipped
    content = """type MyError struct {
    message string
}
type Config struct {
    name string
}"""
    assert should_skip_go(content) is True


def test_inside_typeddict_class_to_exception():
    # Test struct definitions should be skipped
    content = """type Config struct {
    name string
}
type MyError struct {
    message string
}"""
    assert should_skip_go(content) is True


def test_inside_exception_class_to_namedtuple():
    # Test struct definitions should be skipped
    content = """type MyError struct {
    message string
}
type Point struct {
    X int
    Y int
}"""
    assert should_skip_go(content) is True


def test_enum_declarations():
    # Test const block declarations
    content = """const (
    ACTIVE = iota
    INACTIVE
    PENDING
)
const MAX_SIZE = 100"""
    assert should_skip_go(content) is True


def test_extern_declarations():
    # Test import statements
    content = """import "fmt"
import "os"
const MAX_SIZE = 100"""
    assert should_skip_go(content) is True


def test_forward_declarations():
    # Test type declarations
    content = """type MyInterface interface{}
type MyStruct struct{}
const MAX_SIZE = 100"""
    assert should_skip_go(content) is True


def test_using_namespace_statements():
    # Test import with alias and function call - should NOT be skipped
    content = """import f "fmt"
import "os"
result := f.Sprintf("hello")"""
    assert should_skip_go(content) is False


def test_template_declarations():
    # Test generic types - should NOT be skipped (has logic)
    content = """type Container[T any] struct {
    items []T
}
func (c *Container[T]) Add(item T) {
    c.items = append(c.items, item)
}"""
    assert should_skip_go(content) is False


def test_static_extern_const():
    # Test variables and constants
    content = """var internalVar = 42
const VERSION = "1.0.0"
const MAX_SIZE = 100"""
    assert should_skip_go(content) is True


def test_enum_and_macro_declarations():
    # Test constants
    content = """const DEBUG_MODE = true
const BUFFER_SIZE = 1024
const MAX_SIZE = 100"""
    assert should_skip_go(content) is True


def test_macro_constants_only():
    # Test constants only
    content = """const MAX_SIZE = 1024
const BUFFER_SIZE = 512
const VALUE = 42"""
    assert should_skip_go(content) is True


def test_annotation_interface_definitions():
    # Test interface definitions
    content = '''type MyInterface interface {
    Method() error
}
const CONSTANT = "value"'''
    assert should_skip_go(content) is True


def test_kotlin_data_class_definitions():
    # Test struct definitions
    content = '''type User struct {
    ID    int64
    Name  string
    Email string
}
const CONSTANT = "value"'''
    assert should_skip_go(content) is True


def test_scala_case_class_definitions():
    # Test struct definitions
    content = '''type Point struct {
    X int
    Y int
}
const CONSTANT = "value"'''
    assert should_skip_go(content) is True


def test_module_exports_only():
    # Test package and import statements
    content = '''package main
import "fmt"
const CONSTANT = "value"'''
    assert should_skip_go(content) is True


def test_standalone_closing_brace_only():
    # Test struct with closing brace
    content = '''type MyStruct struct {
    Value int
}
const CONSTANT = "value"'''
    assert should_skip_go(content) is True


def test_raw_string_multiline():
    # Test raw string with single backtick - covers branch 40->43
    content = '''const TEMPLATE = `multiline
raw string
continues here`
const OTHER = "value"'''
    assert should_skip_go(content) is True


def test_struct_without_opening_brace():
    # Test struct without opening brace on same line - just type declaration
    content = '''type Config struct
{
    Name string
}
const CONSTANT = "value"'''
    assert should_skip_go(content) is True


def test_interface_without_opening_brace():
    # Test interface without opening brace on same line - just method signatures
    content = '''type Reader interface
{
    Read() error
}
const CONSTANT = "value"'''
    assert should_skip_go(content) is True
