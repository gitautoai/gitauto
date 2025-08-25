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
