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


def test_empty_class_single_line_braces():
    # Empty class with braces on same line should be skipped
    content = """// Base class for components
public class MyComponent {}

interface IMyInterface {}"""
    assert should_skip_csharp(content) is True


def test_static_readonly_with_function_call():
    # Static readonly with function calls - has testing value
    content = """public class Config
{
    public static readonly string ConnectionString = Environment.GetEnvironmentVariable("DB_CONNECTION");
    public static readonly int MaxConnections = int.Parse(Environment.GetEnvironmentVariable("MAX_CONN"));
}"""
    assert should_skip_csharp(content) is False


def test_constructor_with_logic():
    # Constructor - HAS TESTING VALUE
    content = """public class MyClass
{
    public MyClass(string name)
    {
        Name = name ?? throw new ArgumentNullException(nameof(name));
    }

    public string Name { get; }
}"""
    assert should_skip_csharp(content) is False


def test_method_with_control_flow():
    # Method with control flow - HAS TESTING VALUE
    content = """public class Validator
{
    public bool IsValid(string input)
    {
        if (string.IsNullOrEmpty(input))
            return false;

        for (int i = 0; i < input.Length; i++)
        {
            if (!char.IsLetterOrDigit(input[i]))
                return false;
        }

        return true;
    }
}"""
    assert should_skip_csharp(content) is False


def test_namedtuple_class():
    # Record definitions (C# 9+) - just data, no testing value
    content = """namespace Example
{
    public record Point(int X, int Y);

    public record User(string Name, int Age);
}"""
    assert should_skip_csharp(content) is True


def test_auto_properties_only():
    # Auto-properties are just data declarations, no logic to test
    content = """public class Config
{
    public string Name { get; init; }
    public int Value { get; private set; }
    public bool IsEnabled { get; }
}"""
    assert should_skip_csharp(content) is True


def test_enum_declarations():
    # Enum declarations - just constants, no testing value
    content = """public enum Status
{
    Active,
    Inactive,
    Pending
}"""
    assert should_skip_csharp(content) is True


def test_interface_with_method_signatures():
    # Interface with method signatures - no testing value (just contracts)
    content = """public interface IRepository
{
    Task<User> GetUserAsync(int id);
    Task SaveUserAsync(User user);
    void Delete(int id);
}"""
    assert should_skip_csharp(content) is True


def test_assembly_attributes():
    # Test assembly attributes
    content = """[assembly: System.Reflection.AssemblyTitle("MyApp")]
[assembly: System.Reflection.AssemblyVersion("1.0.0")]
public const int CONSTANT = 100;"""
    assert should_skip_csharp(content) is True


def test_constructor_exact_pattern():
    # Test exact constructor pattern
    content = """MyClass(int x) {
    this.x = x;
}"""
    assert should_skip_csharp(content) is False


def test_method_call_standalone_pattern():
    # Test standalone method call pattern
    content = """methodCall();"""
    assert should_skip_csharp(content) is False


def test_standalone_control_statements():
    # Test control statements not inside methods
    content = """if (globalCondition)
    doGlobalAction();"""
    assert should_skip_csharp(content) is False


def test_comprehensive_control_flow():
    # Single comprehensive test covering all control flow patterns for coverage
    content = """public class Service
{
    public void Process()
    {
        if (condition) return;
        while (running) { doWork(); }
        for (int i = 0; i < 10; i++) process(i);
        foreach (var item in items) processItem(item);
        switch (status) { case 1: break; }
        try { riskyOperation(); } catch { handleError(); }
        value = GetValue();
        ProcessData();
        someExecutableStatement;
    }
}"""
    assert should_skip_csharp(content) is False


def test_multiline_comments():
    # Test multi-line comments to hit lines 43, 45-47
    content = """/* This is a multi-line comment
    that spans multiple lines
    and should be ignored */
public const int VALUE = 42;"""
    assert should_skip_csharp(content) is True


def test_static_readonly_without_function_calls():
    # Test static readonly without function calls to hit line 74
    content = """public static readonly string ApiUrl = "https://api.com";
public static readonly int MaxRetries = 3;"""
    assert should_skip_csharp(content) is True


def test_method_with_braces():
    # Test method definition with braces to hit line 122
    content = """public class Service
{
    public void ProcessData() {
        DoWork();
    }
}"""
    assert should_skip_csharp(content) is False


def test_return_statement_exact():
    # Test return statement that starts with "return " but not literals to hit line 140
    # Must not match field declaration pattern, use property access
    content = """return obj.Property;"""
    assert should_skip_csharp(content) is False


def test_assignment_exact():
    # Test assignment with = but not const to hit line 144
    content = """value = GetValue();"""
    assert should_skip_csharp(content) is False


def test_other_executable_code():
    # Test other executable code to hit lines 151-152
    content = """SomeExecutableStatement;"""
    assert should_skip_csharp(content) is False
