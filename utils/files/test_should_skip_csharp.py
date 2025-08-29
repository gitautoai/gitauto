from utils.files.should_skip_csharp import should_skip_csharp


def test_export_only():
    # File with only using statements
    content = """using System;
using System.Collections.Generic;
using System.Linq;
using MyApp.Types;"""
    assert should_skip_csharp(content) is True


def test_constants_only():
    # Constants only
    content = """public const int MaxRetries = 3;
private const string ApiUrl = "https://api.example.com";
internal const bool Debug = true;
protected const int StatusCode = 200;"""
    assert should_skip_csharp(content) is True


def test_multiline_string_constants():
    # Multi-line string constants
    content = """public const string IdentifyCause = @"
You are a GitHub Actions expert.
Given information such as a pull request title, identify the cause.
";

private const string AnotherTemplate = @"
This is another template
with multiple lines
";"""
    assert should_skip_csharp(content) is True


def test_typeddict_only():
    # Interface definitions only
    content = """public interface IUser
{
    int Id { get; set; }
    string Name { get; set; }
    string Email { get; set; }
}

interface IConfig
{
    int Timeout { get; set; }
    int Retries { get; set; }
}"""
    assert should_skip_csharp(content) is True


def test_exception_classes_only():
    # Simple empty classes
    content = """public class CustomError : Exception
{
}

class AuthenticationError : Exception
{
}"""
    assert should_skip_csharp(content) is True


def test_mixed_imports_and_constants():
    # Mixed using statements and constants
    content = """using System;
using System.Collections.Generic;

public const int MaxRetries = 3;
private const string ApiUrl = "https://api.example.com";

internal const string Version = "1.0.0";"""
    assert should_skip_csharp(content) is True


def test_function_with_logic():
    # Method definitions - should NOT be skipped
    content = """public static class Calculator
{
    public static double CalculateTotal(List<Item> items)
    {
        return items.Sum(item => item.Price);
    }

    public static List<int> ProcessData(List<int> data)
    {
        return data.Select(x => x * 2).ToList();
    }
}"""
    assert should_skip_csharp(content) is False


def test_class_with_methods():
    # Class with methods - should NOT be skipped
    content = """public class Calculator
{
    private int _value = 0;

    public int Add(int a, int b)
    {
        return a + b;
    }

    public int Multiply(int a, int b)
    {
        return a * b;
    }
}"""
    assert should_skip_csharp(content) is False


def test_mixed_constants_and_logic():
    # Mixed constants and logic - should NOT be skipped
    content = """public const int MaxSize = 100;
private const string ApiUrl = "https://api.com";

public static int CalculateSize()
{
    return MaxSize * 2;
}"""
    assert should_skip_csharp(content) is False


def test_constants_with_function_calls():
    # Constants with function calls - should NOT be skipped
    content = """using System;
using System.IO;

public static readonly bool IsPrd = Environment.GetEnvironmentVariable("ENV") == "prod";
private static readonly string BasePath = Path.Combine("/", "app");"""
    assert should_skip_csharp(content) is False


def test_empty_file():
    # Empty content should be skipped
    assert should_skip_csharp("") is True


def test_whitespace_only():
    # File with only whitespace should be skipped
    content = """




    """
    assert should_skip_csharp(content) is True


def test_init_file_with_imports():
    # Typical module file with only using statements
    content = """using MyApp.Module1;
using MyApp.Module2;
using MyApp.Utils;

using System.Collections.Generic;
using System.Linq;"""
    assert should_skip_csharp(content) is True


def test_empty_init_file():
    # Empty module file
    content = ""
    assert should_skip_csharp(content) is True


def test_comment_with_simple_class():
    # File with comment and simple empty class should be skipped
    content = """/*
Base class for application components
*/
public class BaseComponent
{
}"""
    assert should_skip_csharp(content) is True


def test_empty_class_single_line_braces():
    # Empty class with braces on same line should be skipped
    content = """// Base class for components
public class MyComponent {}

interface IMyInterface {}"""
    assert should_skip_csharp(content) is True
