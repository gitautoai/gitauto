from utils.files.should_skip_go import should_skip_go


def test_export_only():
    # File with only package and import statements
    content = '''package types

import (
    "fmt"
    "encoding/json"
)

import "net/http"'''
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
    content = '''package main

import "os"
import "fmt"

const MaxRetries = 3
const ApiURL = "https://api.example.com"

var Version = "1.0.0"'''
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


def test_multiline_comments():
    # File with multiline comments should be skipped
    content = """package main

/*
This is a multiline comment
that spans multiple lines
*/

const MaxRetries = 3

/*
Another multiline comment
*/"""
    assert should_skip_go(content) is True


def test_multiline_comments_with_function():
    # File with multiline comments and function should NOT be skipped
    content = """package main

/*
This is a multiline comment
*/

func doSomething() {
    // implementation
}"""
    assert should_skip_go(content) is False


def test_interface_definitions():
    # Interface definitions only should be skipped
    content = """package main

type Reader interface {
    Read([]byte) (int, error)
}

type Writer interface {
    Write([]byte) (int, error)
}"""
    assert should_skip_go(content) is True


def test_interface_with_methods():
    # Interface with method implementations should NOT be skipped
    content = """package main

type Reader interface {
    Read([]byte) (int, error)
}

func (r *MyReader) Read(data []byte) (int, error) {
    return 0, nil
}"""
    assert should_skip_go(content) is False


def test_type_aliases():
    # Type aliases should be skipped
    content = """package main

type UserID int64
type Username string
type Config map[string]interface{}"""
    assert should_skip_go(content) is True


def test_type_aliases_with_assignment():
    # Type aliases with assignment should be skipped
    content = """package main

type UserID = int64
type Username = string"""
    assert should_skip_go(content) is False


def test_import_block_variations():
    # Various import block formats should be skipped
    content = '''package main

import (
    "fmt"
    "os"
    "github.com/example/pkg"
)

import "net/http"
import "encoding/json"'''
    assert should_skip_go(content) is True


def test_bare_const_declarations():
    # Bare const declarations without assignment should be skipped
    content = """package main

const (
    StatusActive
    StatusInactive
    StatusPending
)

const MaxRetries = 10"""
    assert should_skip_go(content) is True


def test_struct_field_definitions():
    # Struct with various field types should be skipped
    content = """package main

type User struct {
    ID       int64
    Name     string
    Email    *string
    Tags     []string
    Metadata map[string]interface{}
    Config   *Config
}"""
    assert should_skip_go(content) is True


def test_complex_multiline_string():
    # Complex multiline string with backticks should be skipped
    content = """package main

const Template = `
SELECT * FROM users
WHERE id = ?
AND status = 'active'
`

const AnotherTemplate = `{
    "name": "test",
    "value": 123
}`"""
    assert should_skip_go(content) is True


def test_multiline_string_with_single_backtick():
    # Multiline string that starts and ends on same line should be skipped
    content = """package main

const Query = `SELECT * FROM users`
const Message = `Hello World`"""
    assert should_skip_go(content) is True


def test_nested_struct_definitions():
    # Nested struct definitions should be skipped
    content = """package main

type Outer struct {
    Inner struct {
        Value string
        Count int
    }
    Name string
}"""
    assert should_skip_go(content) is True


def test_mixed_struct_and_interface():
    # Mixed struct and interface definitions should be skipped
    content = """package main

type User struct {
    ID   int64
    Name string
}

type UserService interface {
    GetUser(id int64) (*User, error)
    CreateUser(user *User) error
}"""
    assert should_skip_go(content) is True


def test_const_with_function_call_in_block():
    # Const block with function call should NOT be skipped
    content = """package main

const (
    MaxRetries = 3
    ApiURL     = "https://api.com"
    Timestamp  = time.Now().Unix()
)"""
    assert should_skip_go(content) is False


def test_var_with_function_call_in_block():
    # Var block with function call should NOT be skipped
    content = """package main

var (
    Version = "1.0.0"
    BuildID = generateBuildID()
)"""
    assert should_skip_go(content) is False


def test_single_line_comments():
    # File with single line comments should be skipped
    content = """package main

// This is a comment
const MaxRetries = 3

// Another comment
type User struct {
    ID   int64  // User ID
    Name string // User name
}"""
    assert should_skip_go(content) is True


def test_mixed_comments_and_multiline_strings():
    # Mixed comments and multiline strings should be skipped
    content = """package main

// Configuration template
const ConfigTemplate = `
{
    "timeout": 30,
    "retries": 3
}
`

/*
Default configuration values
*/
const DefaultTimeout = 30"""
    assert should_skip_go(content) is True


def test_struct_with_closing_brace_on_same_line():
    # Struct with closing brace on same line as field should be skipped
    content = """package main

type Config struct {
    Timeout int
    Retries int }"""
    assert should_skip_go(content) is True


def test_interface_with_closing_brace_on_same_line():
    # Interface with closing brace on same line should be skipped
    content = """package main

type Reader interface {
    Read([]byte) (int, error) }"""
    assert should_skip_go(content) is True


def test_empty_const_and_var_blocks():
    # Empty const and var blocks should be skipped
    content = """package main

const (
)

var (
)

type User struct {
    ID int64
}"""
    assert should_skip_go(content) is True


def test_complex_field_types():
    # Struct with complex field types should be skipped
    content = """package main

type ComplexStruct struct {
    SimpleField    string
    PointerField   *int
    SliceField     []string
    MapField       map[string]int
    ChanField      chan int
    FuncField      func(int) string
    InterfaceField interface{}
}"""
    assert should_skip_go(content) is True


def test_multiline_comment_edge_cases():
    # Multiline comment that starts and ends on same line
    content = """package main

/* single line comment */ const MaxRetries = 3

type User struct {
    ID int64
}"""
    assert should_skip_go(content) is True


def test_function_keyword_in_comments():
    # Function keyword in comments should not affect result
    content = """package main

// This function does something
const MaxRetries = 3

/*
func example() {
    // This is in a comment
}
*/

type User struct {
    ID int64
}"""
    assert should_skip_go(content) is True


def test_executable_code_detection():
    # Any executable code should cause function to return False
    content = """package main

const MaxRetries = 3

x := 5  // This is executable code"""
    assert should_skip_go(content) is False


def test_function_call_in_const_assignment():
    # Function call in const assignment should return False
    content = """package main

const Timestamp = getCurrentTime()"""
    assert should_skip_go(content) is False


def test_go_directive_and_build_tags():
    # Go directives and build tags should be skipped
    content = """//go:build linux
// +build linux

package main

const MaxRetries = 3

type Config struct {
    Timeout int
}"""
    assert should_skip_go(content) is True
