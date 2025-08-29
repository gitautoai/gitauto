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
