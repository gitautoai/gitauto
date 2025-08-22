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
    MaxSize = 100
    ApiURL = "https://api.example.com"
    Debug = true
)

var DefaultTimeout = 30
var (
    Version = "1.0.0"
    Build   = "abc123"
)"""
    assert should_skip_go(content) is True


def test_struct_definitions_only():
    # Struct definitions without methods
    content = """package types

type User struct {
    ID    int64
    Name  string
    Email *string
}

type Config struct {
    Timeout int
    Retries int
}"""
    assert should_skip_go(content) is True


def test_interface_definitions_only():
    # Interface definitions only
    content = """package interfaces

type Reader interface {
    Read([]byte) (int, error)
}

type Writer interface {
    Write([]byte) (int, error)
}

type ReadWriter interface {
    Reader
    Writer
}"""
    assert should_skip_go(content) is True


def test_type_aliases_only():
    # Type aliases only
    content = """package types

type ID string
type UserID ID
type Status int

const (
    StatusActive Status = iota
    StatusInactive
)"""
    assert should_skip_go(content) is True


def test_mixed_imports_and_constants():
    # Mixed imports and constants
    content = """package config

import "os"

const (
    DefaultPort = 8080
    MaxRetries  = 3
)

var (
    Environment = os.Getenv("ENV")
    Debug       = true
)"""
    assert should_skip_go(content) is True


def test_function_with_logic():
    # Function definitions - should NOT be skipped
    content = """package utils

func CalculateTotal(items []Item) float64 {
    total := 0.0
    for _, item := range items {
        total += item.Price
    }
    return total
}

func ProcessData(data []int) []int {
    result := make([]int, len(data))
    for i, v := range data {
        result[i] = v * 2
    }
    return result
}"""
    assert should_skip_go(content) is False


def test_methods_with_logic():
    # Method definitions - should NOT be skipped
    content = """package calculator

type Calculator struct{}

func (c *Calculator) Add(a, b int) int {
    return a + b
}

func (c *Calculator) Multiply(a, b int) int {
    return a * b
}"""
    assert should_skip_go(content) is False


def test_mixed_struct_and_methods():
    # Mixed struct definition and methods - should NOT be skipped
    content = """package user

type User struct {
    Name string
}

func (u *User) GetName() string {
    return u.Name
}

func (u *User) SetName(name string) {
    u.Name = name
}"""
    assert should_skip_go(content) is False


def test_init_function():
    # Init function - should NOT be skipped
    content = """package config

var GlobalConfig Config

func init() {
    GlobalConfig = Config{
        Timeout: 30,
        Retries: 3,
    }
}"""
    assert should_skip_go(content) is False


def test_mixed_constants_and_logic():
    # Mixed constants and logic - should NOT be skipped
    content = """package utils

const MaxSize = 1024

func GetMaxSize() int {
    return MaxSize
}"""
    assert should_skip_go(content) is False


def test_empty_file():
    # Empty content should be skipped
    assert should_skip_go("") is True


def test_whitespace_only():
    # File with only whitespace should be skipped
    content = """




    """
    assert should_skip_go(content) is True
