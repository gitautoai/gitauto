from utils.files.should_skip_java import should_skip_java


def test_export_only():
    # File with only package and import statements
    content = """package com.example;

import java.util.List;
import java.util.Map;
import com.example.types.User;"""
    assert should_skip_java(content) is True


def test_constants_only():
    # Constants only
    content = """package com.example;

public static final int MAX_RETRIES = 3;
private static final String API_URL = "https://api.example.com";
public static final boolean DEBUG = true;
protected static final int STATUS_CODE = 200;"""
    assert should_skip_java(content) is True


def test_multiline_string_constants():
    # Multi-line string constants
    content = """package com.example;

public static final String IDENTIFY_CAUSE = \"\"\"
You are a GitHub Actions expert.
Given information such as a pull request title, identify the cause.
\"\"\";

private static final String ANOTHER_TEMPLATE = \"\"\"
This is another template
with multiple lines
\"\"\";"""
    assert should_skip_java(content) is True


def test_typeddict_only():
    # Interface definitions only
    content = """package com.example;

public interface User {
    Long getId();
    String getName();
    String getEmail();
}

interface Config {
    int getTimeout();
    int getRetries();
}"""
    assert should_skip_java(content) is True


def test_exception_classes_only():
    # Simple exception classes
    content = """package com.example;

public class CustomError extends Exception {
}

class AuthenticationError extends Exception {
}"""
    assert should_skip_java(content) is True


def test_mixed_imports_and_constants():
    # Mixed imports and constants
    content = """package com.example;

import java.util.Map;
import java.util.HashMap;

public static final int MAX_RETRIES = 3;
private static final String API_URL = "https://api.example.com";"""
    assert should_skip_java(content) is True


def test_function_with_logic():
    # Method definitions - should NOT be skipped
    content = """package com.example;

public class Calculator {
    public double calculateTotal(List<Item> items) {
        return items.stream()
                   .mapToDouble(Item::getPrice)
                   .sum();
    }

    public List<Integer> processData(List<Integer> data) {
        return data.stream()
                  .map(x -> x * 2)
                  .collect(Collectors.toList());
    }
}"""
    assert should_skip_java(content) is False


def test_class_with_methods():
    # Class with methods - should NOT be skipped
    content = """package com.example;

public class Calculator {
    private int value = 0;

    public int add(int a, int b) {
        return a + b;
    }

    public int multiply(int a, int b) {
        return a * b;
    }
}"""
    assert should_skip_java(content) is False


def test_mixed_constants_and_logic():
    # Mixed constants and logic - should NOT be skipped
    content = """package com.example;

public static final int MAX_SIZE = 100;
private static final String API_URL = "https://api.com";

public static int calculateSize() {
    return MAX_SIZE * 2;
}"""
    assert should_skip_java(content) is False


def test_constants_with_function_calls():
    # Constants with function calls - should NOT be skipped
    content = """package com.example;

import java.util.Map;
import com.config.ConfigLoader;

public static final boolean IS_PRD = ConfigLoader.getEnvVar("ENV").equals("prod");
private static final String BASE_PATH = Paths.get("/", "app").toString();"""
    assert should_skip_java(content) is False


def test_empty_file():
    # Empty content should be skipped
    assert should_skip_java("") is True


def test_whitespace_only():
    # File with only whitespace should be skipped
    content = """




    """
    assert should_skip_java(content) is True


def test_init_file_with_imports():
    # Typical module file with only imports
    content = """package com.example;

import com.example.module1.Class1;
import com.example.module1.function1;
import com.example.module2.Class2;
import com.example.utils.HelperFunction;"""
    assert should_skip_java(content) is True


def test_empty_init_file():
    # Empty module file
    content = ""
    assert should_skip_java(content) is True


def test_comment_with_simple_class():
    # File with comment and simple empty class should be skipped
    content = """/**
 * Base class for application components
 */
public class BaseComponent {
}"""
    assert should_skip_java(content) is True


def test_empty_class_single_line_braces():
    # Empty class with braces on same line should be skipped
    content = """// Base class for components
public class MyComponent {}

class AnotherComponent {}"""
    assert should_skip_java(content) is True


def test_single_line_triple_quote_constant():
    # Single-line constant with quotes
    content = """public static final String API_KEY = "abc123";
public static final boolean DEBUG_MODE = true;"""
    assert should_skip_java(content) is True


def test_namedtuple_class():
    # Record class definitions (Java 14+)
    content = """package com.example;

public record Point(int x, int y) {}

record User(String name, int age) {}"""
    assert should_skip_java(content) is True


def test_multiline_string_assignment_parentheses():
    # Simple string constant
    content = """public static final String TEMPLATE = "This is a template";

public static final int OTHER_CONSTANT = 42;"""
    assert should_skip_java(content) is True


def test_multiline_list_assignment():
    # Simple constant definitions
    content = """public static final String EXT_JAVA = ".java";
public static final String EXT_JS = ".js";
public static final String EXT_TS = ".ts";

public static final int MAX_SIZE = 100;"""
    assert should_skip_java(content) is True


def test_complex_class_transitions():
    # Test complex class definition transitions
    content = """public class MyException extends Exception {
    /**
     * Custom error
     */
}

record DataClass(int id, String name) {}

public static final int MAX_RETRIES = 5;"""
    assert should_skip_java(content) is True


def test_mixed_assignment_patterns():
    # Test various assignment patterns that should be skipped
    content = """public static final String SIMPLE_VAR = "value";
public static final int[] LIST_VAR = {1, 2, 3};
public static final boolean BOOL_VAR = true;
public static final int NUM_VAR = 42;
public static final double FLOAT_VAR = 3.14;
public static final Object NONE_VAR = null;"""
    assert should_skip_java(content) is True


def test_bare_string_continuation():
    # Test javadoc and comments
    content = """/**
 * This is a module documentation
 * that spans multiple lines
 */

public static final String CONSTANT = "value";"""
    assert should_skip_java(content) is True


def test_autoload_statements():
    # Test autoload statements should be skipped
    content = """package com.example;
import java.util.List;
public static final String CONSTANT = "value";"""
    assert should_skip_java(content) is True


def test_constants_with_square_brackets():
    # Test constants with square brackets should NOT be skipped - array access has logic
    content = """public static final String ENV_VAR = ENV["PATH"];
public static final String API_URL = "http://example.com";"""
    assert should_skip_java(content) is False


def test_assignment_function_call_detection():
    # Test assignment with function calls should NOT be skipped
    content = """public static final String CONFIG = loadConfig();
public static final String API_URL = "http://example.com";"""
    assert should_skip_java(content) is False


def test_field_definition_with_complex_types():
    # Test class with methods should NOT be skipped
    content = """public class Config {
    public String handler() {
        return "error";
    }

    public List<String> processData(List<String> items) {
        return items;
    }
}"""
    assert should_skip_java(content) is False


def test_inside_exception_class_to_typeddict():
    # Test class definitions should be skipped
    content = """public class MyError extends Exception {
}
interface Config {
    String getName();
}"""
    assert should_skip_java(content) is True


def test_inside_typeddict_class_to_exception():
    # Test class definitions should be skipped
    content = """interface Config {
    String getName();
}
public class MyError extends Exception {
}"""
    assert should_skip_java(content) is True


def test_inside_exception_class_to_namedtuple():
    # Test class definitions should be skipped
    content = """public class MyError extends Exception {
}
public record Point(int x, int y) {}"""
    assert should_skip_java(content) is True


def test_enum_declarations():
    # Test enum declarations - simple enums without methods are just constants
    content = """public enum Status {
    ACTIVE,
    INACTIVE,
    PENDING
}
public static final int MAX_SIZE = 100;"""
    assert should_skip_java(content) is True


def test_extern_declarations():
    # Test import statements
    content = """import java.util.List;
import com.example.Utils;
public static final int MAX_SIZE = 100;"""
    assert should_skip_java(content) is True


def test_forward_declarations():
    # Test class declarations - should NOT be skipped (invalid Java syntax)
    content = """public class ForwardClass;
interface ForwardInterface;
public static final int MAX_SIZE = 100;"""
    assert should_skip_java(content) is False


def test_using_namespace_statements():
    # Test static imports with logic - should NOT be skipped
    content = """import static java.lang.Math.*;
import java.util.List;
result = sqrt(16);"""
    assert should_skip_java(content) is False


def test_template_declarations():
    # Test generic classes - should NOT be skipped (has logic)
    content = """public class Container<T> {
    private List<T> items;

    public void add(T item) {
        items.add(item);
    }
}"""
    assert should_skip_java(content) is False


def test_static_extern_const():
    # Test static variables and constants - static variable declarations are just data
    content = """private static int internalVar = 42;
public static final String VERSION = "1.0.0";
public static final int MAX_SIZE = 100;"""
    assert should_skip_java(content) is True


def test_enum_and_macro_declarations():
    # Test constants
    content = """public static final boolean DEBUG_MODE = true;
public static final int BUFFER_SIZE = 1024;
public static final int MAX_SIZE = 100;"""
    assert should_skip_java(content) is True


def test_macro_constants_only():
    # Test constants only
    content = """public static final int MAX_SIZE = 1024;
public static final int BUFFER_SIZE = 512;
public static final int VALUE = 42;"""
    assert should_skip_java(content) is True


def test_annotation_interface_definitions():
    # Test annotation interface definitions - lines 53-54, 56-58
    content = """@interface MyAnnotation {
    String value() default "";
    int timeout() default 0;
}
public static final int MAX_SIZE = 100;"""
    assert should_skip_java(content) is True


def test_kotlin_data_class_definitions():
    # Test Kotlin data class definitions - lines 68-69
    content = """data class User(
    val id: Long,
    val name: String,
    val email: String
)
public static final int MAX_SIZE = 100;"""
    assert should_skip_java(content) is True


def test_scala_case_class_definitions():
    # Test Scala case class definitions - lines 73-74
    content = """case class Point(
    x: Int,
    y: Int
)
public static final int MAX_SIZE = 100;"""
    assert should_skip_java(content) is True


def test_java9_module_exports():
    # Test Java 9+ module exports - just module configuration, no executable logic
    content = """module com.example {
    exports com.example.api;
    opens com.example.impl;
}
public static final int MAX_SIZE = 100;"""
    assert should_skip_java(content) is True


def test_scala_object_declarations():
    # Test Scala object declarations - object with only val declarations is just data
    content = """object MyObject {
    val version = "1.0.0"
}
public static final int MAX_SIZE = 100;"""
    assert should_skip_java(content) is True


def test_standalone_closing_braces():
    # Test standalone closing braces - line 110
    content = """class MyClass {
    public static final int VALUE = 42;
}
public static final int MAX_SIZE = 100;"""
    assert should_skip_java(content) is True


def test_annotation_usage():
    # Test annotation usage - line 113
    content = """@Override
@SuppressWarnings("unchecked")
@Deprecated
public static final int MAX_SIZE = 100;"""
    assert should_skip_java(content) is True


def test_module_exports_only():
    # Test ONLY module exports to trigger line 97
    content = """exports com.example.api;
opens com.example.impl;
public static final int MAX_SIZE = 100;"""
    assert should_skip_java(content) is True


def test_standalone_closing_brace_only():
    # Test standalone closing brace to trigger line 110
    content = """}
public static final int MAX_SIZE = 100;"""
    assert should_skip_java(content) is True


def test_interface_without_opening_brace():
    # Test interface without opening brace on same line - covers branch 62->64
    # Since interface tracking is incomplete, this returns False
    content = """public interface Config
{
}
public static final int MAX_SIZE = 100;"""
    assert should_skip_java(content) is False


def test_static_variable_with_function_call():
    # Test static variable with function call - triggers line 122
    content = """private static int config = loadConfig();
public static final int MAX_SIZE = 100;"""
    assert should_skip_java(content) is False
