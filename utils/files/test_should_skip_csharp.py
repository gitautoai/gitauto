from utils.files.should_skip_csharp import should_skip_csharp


def test_export_only():
    content = """using System;
using System.Collections.Generic;
using System.Linq;
using MyApp.Types;"""
    assert should_skip_csharp(content) is True


def test_constants_only():
    content = """public const int MaxRetries = 3;
private const string ApiUrl = "https://api.example.com";
internal const bool Debug = true;
protected const int StatusCode = 200;"""
    assert should_skip_csharp(content) is True


def test_multiline_string_constants():
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
    content = """public class CustomError : Exception
{
}

class AuthenticationError : Exception
{
}"""
    assert should_skip_csharp(content) is True


def test_class_with_methods():
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
    content = """public const int MaxSize = 100;
private const string ApiUrl = "https://api.com";

public static int CalculateSize()
{
    return MaxSize * 2;
}"""
    assert should_skip_csharp(content) is False


def test_constants_with_function_calls():
    content = """using System;
using System.IO;

public static readonly bool IsPrd = Environment.GetEnvironmentVariable("ENV") == "prod";
private static readonly string BasePath = Path.Combine("/", "app");"""
    assert should_skip_csharp(content) is False


def test_empty_file():
    assert should_skip_csharp("") is True


def test_whitespace_only():
    content = """



    """
    assert should_skip_csharp(content) is True


def test_empty_class_single_line_braces():
    content = """// Base class for components
public class MyComponent {}

interface IMyInterface {}"""
    assert should_skip_csharp(content) is True


def test_static_readonly_with_function_call():
    content = """public class Config
{
    public static readonly string ConnectionString = Environment.GetEnvironmentVariable("DB_CONNECTION");
    public static readonly int MaxConnections = int.Parse(Environment.GetEnvironmentVariable("MAX_CONN"));
}"""
    assert should_skip_csharp(content) is False


def test_constructor_with_logic():
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
    content = """namespace Example
{
    public record Point(int X, int Y);

    public record User(string Name, int Age);
}"""
    assert should_skip_csharp(content) is True


def test_auto_properties_only():
    content = """public class Config
{
    public string Name { get; init; }
    public int Value { get; private set; }
    public bool IsEnabled { get; }
}"""
    assert should_skip_csharp(content) is True


def test_enum_declarations():
    content = """public enum Status
{
    Active,
    Inactive,
    Pending
}"""
    assert should_skip_csharp(content) is True


def test_interface_with_method_signatures():
    content = """public interface IRepository
{
    Task<User> GetUserAsync(int id);
    Task SaveUserAsync(User user);
    void Delete(int id);
}"""
    assert should_skip_csharp(content) is True


def test_assembly_attributes():
    content = """[assembly: System.Reflection.AssemblyTitle("MyApp")]
[assembly: System.Reflection.AssemblyVersion("1.0.0")]
public const int CONSTANT = 100;"""
    assert should_skip_csharp(content) is True


def test_constructor_exact_pattern():
    content = """MyClass(int x) {
    this.x = x;
}"""
    assert should_skip_csharp(content) is False


def test_method_call_standalone_pattern():
    content = """methodCall();"""
    assert should_skip_csharp(content) is False


def test_standalone_control_statements():
    content = """if (globalCondition)
    doGlobalAction();"""
    assert should_skip_csharp(content) is False


def test_comprehensive_control_flow():
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
    content = """/* This is a multi-line comment
    that spans multiple lines
    and should be ignored */
public const int VALUE = 42;"""
    assert should_skip_csharp(content) is True


def test_static_readonly_without_function_calls():
    content = """public static readonly string ApiUrl = "https://api.com";
public static readonly int MaxRetries = 3;"""
    assert should_skip_csharp(content) is True


def test_method_with_braces():
    content = """public class Service
{
    public void ProcessData() {
        DoWork();
    }
}"""
    assert should_skip_csharp(content) is False


def test_return_statement_exact():
    content = """return obj.Property;"""
    assert should_skip_csharp(content) is False


def test_assignment_exact():
    content = """value = GetValue();"""
    assert should_skip_csharp(content) is False


def test_other_executable_code():
    content = """SomeExecutableStatement;"""
    assert should_skip_csharp(content) is False


def test_preprocessor_directives():
    content = """#define DEBUG
#if DEBUG
public const int LogLevel = 1;
#else
public const int LogLevel = 0;
#endif
#region Configuration
public const string AppName = "MyApp";
#endregion"""
    assert should_skip_csharp(content) is True


def test_verbatim_string_complete_on_same_line():
    content = """public const string Path = @"C:\Users\Documents";
public const string Query = @"SELECT * FROM Users";"""
    assert should_skip_csharp(content) is True


def test_verbatim_string_multiline_without_semicolon():
    content = """public const string Template = @"
Line 1
Line 2
Line 3
";"""
    assert should_skip_csharp(content) is True


def test_vb_net_single_quote_comments():
    content = """' This is a VB.NET comment
Imports System
' Another comment
Public Const MaxValue As Integer = 100"""
    assert should_skip_csharp(content) is True


def test_global_using_statements():
    content = """global using System;
global using System.Collections.Generic;
global using Microsoft.Extensions.DependencyInjection;"""
    assert should_skip_csharp(content) is True


def test_fsharp_open_statements():
    content = """open System
open System.IO
open Microsoft.FSharp.Core"""
    assert should_skip_csharp(content) is True


def test_fsharp_module_declarations():
    content = """module MyModule
open System
let constant = 42"""
    assert should_skip_csharp(content) is False


def test_vb_net_imports():
    content = """Imports System
Imports System.Collections.Generic
Imports Microsoft.VisualBasic"""
    assert should_skip_csharp(content) is True


def test_partial_interface():
    content = """public partial interface IMyInterface
{
    void Method1();
    int Method2(string param);
}"""
    assert should_skip_csharp(content) is True


def test_abstract_class_declaration():
    content = """public abstract class BaseClass
{
}"""
    assert should_skip_csharp(content) is True


def test_sealed_class_declaration():
    content = """public sealed class FinalClass
{
}"""
    assert should_skip_csharp(content) is True


def test_struct_declaration():
    content = """public struct Point
{
    public int X;
    public int Y;
}"""
    assert should_skip_csharp(content) is True


def test_field_with_function_call():
    content = """public class Config
{
    private string path = GetDefaultPath();
}"""
    assert should_skip_csharp(content) is False


def test_enum_with_explicit_values():
    content = """public enum ErrorCode
{
    Success = 0,
    NotFound = 404,
    ServerError = 500
}"""
    assert should_skip_csharp(content) is True


def test_readonly_const_combinations():
    content = """public readonly int ReadonlyField = 10;
private static const double PI = 3.14159;
protected const string Name = "Test";"""
    assert should_skip_csharp(content) is True


def test_method_signature_without_braces():
    content = """public class MyClass
{
    public void MethodName(int param)
    {
        DoSomething();
    }
}"""
    assert should_skip_csharp(content) is False


def test_virtual_method():
    content = """public class BaseClass
{
    public virtual void Process()
    {
        DoWork();
    }
}"""
    assert should_skip_csharp(content) is False


def test_override_method():
    content = """public class DerivedClass : BaseClass
{
    public override void Process()
    {
        base.Process();
    }
}"""
    assert should_skip_csharp(content) is False


def test_abstract_method():
    content = """public abstract class BaseClass
{
    public abstract void Process()
    {
        Initialize();
    }
}"""
    assert should_skip_csharp(content) is False


def test_return_with_literal_array():
    content = """public int[] GetValues()
{
    return [1, 2, 3];
}"""
    assert should_skip_csharp(content) is False


def test_return_with_literal_object():
    content = """public object GetConfig()
{
    return { Name = "Test" };
}"""
    assert should_skip_csharp(content) is False


def test_return_with_string_literal():
    content = """public string GetName()
{
    return "John";
}"""
    assert should_skip_csharp(content) is False


def test_return_with_numeric_literal():
    content = """public int GetValue()
{
    return 42;
}"""
    assert should_skip_csharp(content) is False


def test_while_loop():
    content = """while (condition)
{
    DoWork();
}"""
    assert should_skip_csharp(content) is False


def test_foreach_loop():
    content = """foreach (var item in collection)
{
    Process(item);
}"""
    assert should_skip_csharp(content) is False


def test_switch_statement():
    content = """switch (value)
{
    case 1:
        break;
}"""
    assert should_skip_csharp(content) is False


def test_try_catch():
    content = """try
{
    RiskyOperation();
}
catch (Exception ex)
{
    HandleError(ex);
}"""
    assert should_skip_csharp(content) is False


def test_internal_enum():
    content = """internal enum Priority
{
    Low,
    Medium,
    High
}"""
    assert should_skip_csharp(content) is True


def test_private_record():
    content = """private record InternalData(int Id, string Name);"""
    assert should_skip_csharp(content) is True


def test_protected_interface():
    content = """protected interface IInternalService
{
    void Execute();
}"""
    assert should_skip_csharp(content) is True


def test_internal_class_empty():
    content = """internal class InternalHelper {}"""
    assert should_skip_csharp(content) is True


def test_private_struct():
    content = """private struct InternalPoint
{
    public int X;
    public int Y;
}"""
    assert should_skip_csharp(content) is True


def test_class_with_base_class():
    content = """public class MyClass : BaseClass
{
}"""
    assert should_skip_csharp(content) is True


def test_class_with_interfaces():
    content = """public class MyClass : IDisposable, IComparable
{
}"""
    assert should_skip_csharp(content) is True


def test_generic_interface():
    content = """public interface IRepository<T>
{
    Task<T> GetAsync(int id);
}"""
    assert should_skip_csharp(content) is True


def test_auto_property_with_internal_set():
    content = """public class Config
{
    public string Name { get; internal set; }
}"""
    assert should_skip_csharp(content) is True


def test_auto_property_with_protected_init():
    content = """public class Config
{
    public string Name { get; protected init; }
}"""
    assert should_skip_csharp(content) is True


def test_multiline_comment_with_code_inside():
    content = """/* Comment with code
public void Method() {
    DoWork();
}
End of comment */
public const int Value = 42;"""
    assert should_skip_csharp(content) is True


def test_nested_multiline_comments():
    content = """/* Outer comment
/* Inner comment */
Still in comment */
public const string Name = "Test";"""
    assert should_skip_csharp(content) is True


def test_verbatim_string_with_escaped_quotes():
    content = """public const string Message = @"He said ""Hello""";"""
    assert should_skip_csharp(content) is True


def test_closing_braces_and_semicolons():
    content = """public class MyClass
{
    public int Value { get; set; }
};"""
    assert should_skip_csharp(content) is True


def test_array_brackets():
    content = """public class MyClass
{
    private int[] values;
}"""
    assert should_skip_csharp(content) is True


def test_opening_brace_alone():
    content = """public class MyClass
{
    public void Method()
    {
        if (condition)
        {
            DoWork();
        }
    }
}"""
    assert should_skip_csharp(content) is False


def test_private_constructor():
    content = """private MyClass()
{
    Initialize();
}"""
    assert should_skip_csharp(content) is False


def test_protected_constructor():
    content = """protected MyClass(int value)
{
    this.value = value;
}"""
    assert should_skip_csharp(content) is False


def test_internal_constructor():
    content = """internal MyClass()
{
    Setup();
}"""
    assert should_skip_csharp(content) is False


def test_static_method():
    content = """public static void Process()
{
    DoWork();
}"""
    assert should_skip_csharp(content) is False


def test_private_method():
    content = """private void Helper()
{
    DoSomething();
}"""
    assert should_skip_csharp(content) is False


def test_internal_method():
    content = """internal void InternalProcess()
{
    Execute();
}"""
    assert should_skip_csharp(content) is False


def test_protected_method():
    content = """protected void ProtectedMethod()
{
    BaseOperation();
}"""
    assert should_skip_csharp(content) is False


def test_assignment_without_const():
    content = """x = 10;"""
    assert should_skip_csharp(content) is False


def test_assignment_with_expression():
    content = """result = Calculate(a, b);"""
    assert should_skip_csharp(content) is False


def test_complex_return_statement():
    content = """return user.Name;"""
    assert should_skip_csharp(content) is False


def test_return_with_method_call():
    content = """return GetValue();"""
    assert should_skip_csharp(content) is False


def test_return_with_property_access():
    content = """return this.Value;"""
    assert should_skip_csharp(content) is False


def test_method_call_with_parameters():
    content = """ProcessData(param1, param2);"""
    assert should_skip_csharp(content) is False


def test_method_call_without_semicolon():
    content = """DoWork()"""
    assert should_skip_csharp(content) is False


def test_for_loop():
    content = """for (int i = 0; i < 10; i++)
{
    Process(i);
}"""
    assert should_skip_csharp(content) is False


def test_if_statement():
    content = """if (condition)
{
    DoWork();
}"""
    assert should_skip_csharp(content) is False


def test_mixed_comments_and_code():
    content = """// Single line comment
/* Multi-line
comment */
public const int Value = 42;
// Another comment"""
    assert should_skip_csharp(content) is True


def test_namespace_declaration():
    content = """namespace MyApp.Services
{
    public const int Version = 1;
}"""
    assert should_skip_csharp(content) is True


def test_multiple_namespaces():
    content = """namespace MyApp.Models
{
}

namespace MyApp.Services
{
}"""
    assert should_skip_csharp(content) is True


def test_field_declaration_with_assignment():
    content = """public class MyClass
{
    private int value = 42;
    private string name = "Test";
}"""
    assert should_skip_csharp(content) is True


def test_static_field_declaration():
    content = """public class MyClass
{
    private static int counter = 0;
}"""
    assert should_skip_csharp(content) is True


def test_readonly_field_declaration():
    content = """public class MyClass
{
    private readonly int maxValue = 100;
}"""
    assert should_skip_csharp(content) is True


def test_enum_member_with_comma():
    content = """public enum Status
{
    Active = 1,
    Inactive = 2,
    Pending = 3,
}"""
    assert should_skip_csharp(content) is True


def test_enum_member_without_value():
    content = """public enum Color
{
    Red,
    Green,
    Blue
}"""
    assert should_skip_csharp(content) is True


def test_interface_method_with_generic_return():
    content = """public interface IService
{
    Task<List<User>> GetUsersAsync();
}"""
    assert should_skip_csharp(content) is True


def test_interface_method_with_multiple_parameters():
    content = """public interface ICalculator
{
    int Calculate(int a, int b, string operation);
}"""
    assert should_skip_csharp(content) is True


def test_private_interface_method():
    content = """private interface IHelper
{
    void Help();
}"""
    assert should_skip_csharp(content) is True


def test_protected_interface_method():
    content = """protected interface IProtected
{
    void Execute();
}"""
    assert should_skip_csharp(content) is True


def test_internal_interface_method():
    content = """internal interface IInternal
{
    void Process();
}"""
    assert should_skip_csharp(content) is True


def test_verbatim_string_with_zero_quotes():
    content = """public const string NoQuotes = @;
public const int Value = 42;"""
    assert should_skip_csharp(content) is False


def test_verbatim_string_with_three_quotes():
    content = """public const string ThreeQuotes = @"test"extra";
public const int Value = 42;"""
    assert should_skip_csharp(content) is False


def test_preprocessor_with_double_slash_comment():
    content = """#define DEBUG
// This is a comment
#if DEBUG
public const int LogLevel = 1;
#endif"""
    assert should_skip_csharp(content) is True


def test_line_with_only_hash():
    content = """#
public const int Value = 42;"""
    assert should_skip_csharp(content) is True


def test_line_with_only_double_slash():
    content = """//
public const int Value = 42;"""
    assert should_skip_csharp(content) is True


def test_verbatim_string_multiline_start():
    content = """public const string Template = @"
Line 1
Line 2
";
public const int Value = 42;"""
    assert should_skip_csharp(content) is True


def test_verbatim_string_multiline_middle():
    content = """public const string Template = @"
Line 1
Line 2
Line 3
";"""
    assert should_skip_csharp(content) is True


def test_verbatim_string_multiline_end():
    content = """public const string Template = @"
Line 1
Line 2
";
public const int Value = 42;"""
    assert should_skip_csharp(content) is True


def test_multiline_comment_start_and_end_same_line():
    content = """/* Comment */ public const int Value = 42;"""
    assert should_skip_csharp(content) is True


def test_multiline_comment_multiple_lines():
    content = """/* Start
Middle
End */
public const int Value = 42;"""
    assert should_skip_csharp(content) is True


def test_static_readonly_with_only_opening_paren():
    content = """public static readonly string Value = GetValue(;"""
    assert should_skip_csharp(content) is False


def test_static_readonly_with_only_closing_paren():
    content = """public static readonly string Value = GetValue);"""
    assert should_skip_csharp(content) is False


def test_field_declaration_with_only_opening_paren():
    content = """private string value = GetValue(;"""
    assert should_skip_csharp(content) is False


def test_field_declaration_with_only_closing_paren():
    content = """private string value = GetValue);"""
    assert should_skip_csharp(content) is False


def test_return_statement_with_array_literal():
    content = """return [1, 2, 3];"""
    assert should_skip_csharp(content) is False


def test_return_statement_with_object_literal():
    content = """return { Name = "Test" };"""
    assert should_skip_csharp(content) is False


def test_return_statement_with_string_literal():
    content = """return "test";"""
    assert should_skip_csharp(content) is False


def test_return_statement_with_numeric_literal():
    content = """return 42;"""
    assert should_skip_csharp(content) is False


def test_return_statement_with_single_quote_string():
    content = """return 'c';"""
    assert should_skip_csharp(content) is False


def test_assignment_with_equals_in_const():
    content = """public const int Value = 42;"""
    assert should_skip_csharp(content) is True


def test_assignment_with_equals_not_const():
    content = """value = 42;"""
    assert should_skip_csharp(content) is False


def test_method_call_pattern():
    content = """MethodName();"""
    assert should_skip_csharp(content) is False


def test_method_call_with_params():
    content = """MethodName(param1, param2);"""
    assert should_skip_csharp(content) is False


def test_method_call_without_semicolon_pattern():
    content = """MethodName()"""
    assert should_skip_csharp(content) is False


def test_executable_code_not_starting_with_hash_or_slash():
    content = """SomeStatement;"""
    assert should_skip_csharp(content) is False


def test_executable_code_starting_with_letter():
    content = """statement;"""
    assert should_skip_csharp(content) is False


def test_all_control_flow_keywords():
    content = """if (condition) { }
for (int i = 0; i < 10; i++) { }
while (true) { }
foreach (var item in items) { }
switch (value) { }
try { } catch { }"""
    assert should_skip_csharp(content) is False


def test_mixed_imports_and_constants():
    content = """using System;
using System.Collections.Generic;

public const int MaxRetries = 3;
private const string ApiUrl = "https://api.example.com";"""
    assert should_skip_csharp(content) is True


def test_empty_init_file():
    content = ""
    assert should_skip_csharp(content) is True


def test_comment_with_simple_class():
    content = """/**
 * Base class for application components
 */
public class BaseComponent
{
}"""
    assert should_skip_csharp(content) is True


def test_single_line_constant():
    content = """public const string API_KEY = "abc123";"""
    assert should_skip_csharp(content) is True


def test_complex_class_transitions():
    content = """public class MyException : Exception
{
}

public record DataClass(int Id, string Name);

public const int MAX_RETRIES = 5;"""
    assert should_skip_csharp(content) is True


def test_mixed_assignment_patterns():
    content = """public const string SIMPLE_VAR = "value";
public const int NUM_VAR = 42;
public const bool BOOL_VAR = true;
public const double FLOAT_VAR = 3.14;"""
    assert should_skip_csharp(content) is True


def test_bare_string_continuation():
    content = """/**
 * This is a module documentation
 * that spans multiple lines
 */

public const string CONSTANT = "value";"""
    assert should_skip_csharp(content) is True


def test_autoload_statements():
    content = """using System;
using System.Collections.Generic;
public const string CONSTANT = "value";"""
    assert should_skip_csharp(content) is True


def test_field_definition_with_complex_types():
    content = """public class Config
{
    public string Handler()
    {
        return "error";
    }

    public List<string> ProcessData(List<string> items)
    {
        return items;
    }
}"""
    assert should_skip_csharp(content) is False


def test_inside_exception_class_to_typeddict():
    content = """public class MyError : Exception
{
}
public interface IConfig
{
    string Name { get; }
}"""
    assert should_skip_csharp(content) is True


def test_inside_typeddict_class_to_exception():
    content = """public interface IConfig
{
    string Name { get; }
}
public class MyError : Exception
{
}"""
    assert should_skip_csharp(content) is True


def test_inside_exception_class_to_namedtuple():
    content = """public class MyError : Exception
{
}
public record Point(int X, int Y);"""
    assert should_skip_csharp(content) is True


def test_extern_declarations():
    content = """using System;
using System.Collections.Generic;
public const int MAX_SIZE = 100;"""
    assert should_skip_csharp(content) is True


def test_static_extern_const():
    content = """private static int internalVar = 42;
public static readonly string VERSION = "1.0.0";
public const int MAX_SIZE = 100;"""
    assert should_skip_csharp(content) is True


def test_enum_and_macro_declarations():
    content = """public const bool DEBUG_MODE = true;
public const int BUFFER_SIZE = 1024;
public const int MAX_SIZE = 100;"""
    assert should_skip_csharp(content) is True


def test_macro_constants_only():
    content = """public const int MAX_SIZE = 1024;
public const int BUFFER_SIZE = 512;
public const int VALUE = 42;"""
    assert should_skip_csharp(content) is True


def test_standalone_closing_braces():
    content = """public class MyClass
{
    public const int VALUE = 42;
}
public const int MAX_SIZE = 100;"""
    assert should_skip_csharp(content) is True


def test_standalone_closing_brace_only():
    content = """}
public const int MAX_SIZE = 100;"""
    assert should_skip_csharp(content) is True


def test_class_without_opening_brace():
    content = """public class Config
{
}
public const int MAX_SIZE = 100;"""
    assert should_skip_csharp(content) is True


def test_static_variable_with_function_call():
    content = """private static int config = LoadConfig();


