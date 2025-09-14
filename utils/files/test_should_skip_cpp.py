from utils.files.should_skip_cpp import should_skip_cpp


def test_export_only():
    # File with only include statements
    content = """#include <iostream>
#include <vector>
#include <map>
#include "user.h\""""
    assert should_skip_cpp(content) is True


def test_constants_only():
    # Constants only
    content = """const int MAX_RETRIES = 3;
const char* API_URL = "https://api.example.com";
const bool DEBUG = true;
static const int STATUS_CODE = 200;"""
    assert should_skip_cpp(content) is True


def test_multiline_string_constants():
    # Multi-line string constants
    content = """const char* IDENTIFY_CAUSE = R"(
You are a GitHub Actions expert.
Given information such as a pull request title, identify the cause.
)";

const char* ANOTHER_TEMPLATE = R"(
This is another template
with multiple lines
)";"""
    assert should_skip_cpp(content) is True


def test_typeddict_only():
    # Struct definitions only
    content = """struct User {
    int id;
    std::string name;
    std::string email;
};

struct Config {
    int timeout;
    int retries;
};"""
    assert should_skip_cpp(content) is True


def test_exception_classes_only():
    # Simple empty classes
    content = """class CustomError : public std::exception {
};

class AuthenticationError : public std::exception {
};"""
    assert should_skip_cpp(content) is True


def test_mixed_imports_and_constants():
    # Mixed includes and constants
    content = """#include <iostream>
#include <string>

const int MAX_RETRIES = 3;
const char* API_URL = "https://api.example.com";

static const char* VERSION = "1.0.0";"""
    assert should_skip_cpp(content) is True


def test_function_with_logic():
    # Function definitions - should NOT be skipped
    content = """double calculateTotal(const std::vector<Item>& items) {
    double total = 0.0;
    for (const auto& item : items) {
        total += item.price;
    }
    return total;
}

std::vector<int> processData(const std::vector<int>& data) {
    std::vector<int> result;
    for (int x : data) {
        result.push_back(x * 2);
    }
    return result;
}"""
    assert should_skip_cpp(content) is False


def test_class_with_methods():
    # Class with methods - should NOT be skipped
    content = """class Calculator {
private:
    int value;

public:
    Calculator() : value(0) {}

    int add(int a, int b) {
        return a + b;
    }

    int multiply(int a, int b) {
        return a * b;
    }
};"""
    assert should_skip_cpp(content) is False


def test_mixed_constants_and_logic():
    # Mixed constants and logic - should NOT be skipped
    content = """const int MAX_SIZE = 100;
const char* API_URL = "https://api.com";

int calculateSize() {
    return MAX_SIZE * 2;
}"""
    assert should_skip_cpp(content) is False


def test_constants_with_function_calls():
    # Constants with function calls - should NOT be skipped
    content = """#include <cstdlib>
#include <filesystem>

bool IS_PRD = std::getenv("ENV") && std::string(std::getenv("ENV")) == "prod";
std::string BASE_PATH = std::filesystem::path("/") / "app";"""
    assert should_skip_cpp(content) is False


def test_empty_file():
    # Empty content should be skipped
    assert should_skip_cpp("") is True


def test_whitespace_only():
    # File with only whitespace should be skipped
    content = """




    """
    assert should_skip_cpp(content) is True


def test_init_file_with_imports():
    # Typical header file with only includes
    content = """#include "module1/class1.h"
#include "module2/class2.h"
#include "utils/helper.h"

#include <vector>
#include <string>"""
    assert should_skip_cpp(content) is True


def test_empty_init_file():
    # Empty header file
    content = ""
    assert should_skip_cpp(content) is True


def test_comment_with_simple_class():
    # File with comment and simple empty class should be skipped
    content = """/*
Base class for application components
*/
class BaseComponent {
};"""
    assert should_skip_cpp(content) is True


def test_empty_class_single_line_braces():
    # Empty class with braces on same line should be skipped
    content = """// Base class for components
class MyComponent {};

struct MyStruct {};"""
    assert should_skip_cpp(content) is True


def test_single_line_triple_quote_constant():
    # Single-line constant definition
    content = """const char* API_KEY = "abc123";
const bool DEBUG_MODE = true;"""
    assert should_skip_cpp(content) is True


def test_namedtuple_class():
    # Simple struct definitions
    content = """struct Point {
    int x;
    int y;
};

struct User {
    std::string name;
    int age;
};"""
    assert should_skip_cpp(content) is True


def test_multiline_string_assignment_parentheses():
    # Multi-line string constant
    content = """const std::string TEMPLATE = "This is a very long template";

const int OTHER_CONSTANT = 42;"""
    assert should_skip_cpp(content) is True


def test_multiline_list_assignment():
    # Simple constant definitions
    content = """const std::string EXT_CPP = ".cpp";
const std::string EXT_H = ".h";
const std::string EXT_HPP = ".hpp";

const int MAX_SIZE = 100;"""
    assert should_skip_cpp(content) is True


def test_complex_class_transitions():
    # Test complex class definition transitions - contains method implementation
    content = """class MyException : public std::exception {
public:
    const char* what() const noexcept override {
        return "Custom error";
    }
};

struct DataStruct {
    int id;
    std::string name;
};

const int MAX_RETRIES = 5;"""
    assert should_skip_cpp(content) is False


def test_mixed_assignment_patterns():
    # Test various assignment patterns that should be skipped
    content = """const std::string SIMPLE_VAR = "value";
const std::vector<int> LIST_VAR = {1, 2, 3};
const bool BOOL_VAR = true;
const int NUM_VAR = 42;
const double FLOAT_VAR = 3.14;
const void* NULL_VAR = nullptr;"""
    assert should_skip_cpp(content) is True


def test_bare_string_continuation():
    # Test comments and documentation
    content = """/*
 * This is a module documentation
 * that spans multiple lines
 */

const std::string CONSTANT = "value";"""
    assert should_skip_cpp(content) is True


def test_autoload_statements():
    # Test include statements should be skipped
    content = """#include <iostream>
#include "myheader.h"
const std::string CONSTANT = "value";"""
    assert should_skip_cpp(content) is True


def test_constants_with_square_brackets():
    # Test constants with square brackets should NOT be skipped
    content = """const std::string ENV_VAR = ENV["PATH"];
const std::string API_URL = "http://example.com";"""
    assert should_skip_cpp(content) is True


def test_assignment_function_call_detection():
    # Test assignment with function calls should NOT be skipped (function calls have logic)
    content = """const std::string CONFIG = loadConfig();
const std::string API_URL = "http://example.com";"""
    assert should_skip_cpp(content) is False


def test_field_definition_with_complex_types():
    # Test class with methods should NOT be skipped
    content = """class Config {
public:
    std::string handler() {
        return "error";
    }

    std::vector<std::string> processData(const std::vector<std::string>& items) {
        return items;
    }
};"""
    assert should_skip_cpp(content) is False


def test_inside_exception_class_to_typeddict():
    # Test class definitions should be skipped
    content = """class MyError : public std::exception {
};
class Config {
    std::string name;
};"""
    assert should_skip_cpp(content) is True


def test_inside_typeddict_class_to_exception():
    # Test class definitions should be skipped
    content = """struct Config {
    std::string name;
};
class MyError : public std::exception {
};"""
    assert should_skip_cpp(content) is True


def test_inside_exception_class_to_namedtuple():
    # Test class definitions should be skipped
    content = """class MyError : public std::exception {
};
struct Point {
    int x;
    int y;
};"""
    assert should_skip_cpp(content) is True


def test_enum_declarations():
    # Test enum declarations - triggers lines 62-63
    content = """enum Status {
    ACTIVE,
    INACTIVE,
    PENDING
};
const int MAX_SIZE = 100;"""
    assert should_skip_cpp(content) is True


def test_extern_declarations():
    # Test extern declarations - triggers line 75
    content = """extern int global_var;
extern void some_function();
const int MAX_SIZE = 100;"""
    assert should_skip_cpp(content) is True


def test_forward_declarations():
    # Test forward declarations - triggers lines 78, 80, 83
    content = """class ForwardClass;
struct ForwardStruct;
typedef struct SomeStruct MyStruct;
const int MAX_SIZE = 100;"""
    assert should_skip_cpp(content) is True


def test_using_namespace_statements():
    # Test using and namespace statements - triggers lines 86, 89
    content = """using std::vector;
using namespace std;
namespace MyNamespace {
    const int INTERNAL_CONST = 42;
}
const int MAX_SIZE = 100;"""
    assert should_skip_cpp(content) is True


def test_template_declarations():
    # Test template declarations - triggers line 92
    content = """template<typename T>
class MyTemplate;
const int MAX_SIZE = 100;"""
    assert should_skip_cpp(content) is True


def test_static_extern_const():
    # Test static and extern const - triggers line 97
    content = """static int internal_var = 42;
extern const int EXTERNAL_CONST = 100;
const int MAX_SIZE = 100;"""
    assert should_skip_cpp(content) is True


def test_enum_and_macro_declarations():
    # Test enum and macro - triggers lines 100, 103
    content = """enum Color;
#define MAX_BUFFER_SIZE 1024
#define DEBUG_MODE 1
const int MAX_SIZE = 100;"""
    assert should_skip_cpp(content) is True


def test_macro_constants_only():
    # Test macro constants with exact pattern - triggers line 103
    content = """#define MAX_SIZE 1024
#define BUFFER_SIZE 512
const int value = 42;"""
    assert should_skip_cpp(content) is True


def test_only_macros_nothing_else():
    # Test ONLY macros that should hit line 103
    content = """#define MAX_BUFFER 1024
#define MIN_BUFFER 64
#define DEBUG_FLAG 1"""
    assert should_skip_cpp(content) is True


def test_annotation_interface_definitions():
    # Test annotation-like definitions (C++ attributes) - just data declarations
    content = """[[deprecated]] struct MyStruct {
    int value;
};
const int MAX_SIZE = 100;"""
    assert should_skip_cpp(content) is True


def test_kotlin_data_class_definitions():
    # Test simple struct definitions
    content = """struct Data {
    int id;
    std::string name;
    std::string email;
};
const int MAX_SIZE = 100;"""
    assert should_skip_cpp(content) is True


def test_scala_case_class_definitions():
    # Test struct definitions
    content = """struct Point {
    int x;
    int y;
};
const int MAX_SIZE = 100;"""
    assert should_skip_cpp(content) is True


def test_module_exports_only():
    # Test preprocessor directives
    content = """#pragma once
#include "exports.h"
const int MAX_SIZE = 100;"""
    assert should_skip_cpp(content) is True


def test_standalone_closing_brace_only():
    # Test standalone closing brace
    content = """struct MyStruct {
    int value;
};
const int MAX_SIZE = 100;"""
    assert should_skip_cpp(content) is True
