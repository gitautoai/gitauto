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


def test_raw_string_literals():
    # Raw string literals should be skipped
    content = """const char* SQL_QUERY = R"(
SELECT * FROM users 
WHERE id = ?
AND status = 'active'
)";

const char* JSON_TEMPLATE = R"(
{
    "name": "test",
    "value": 123
}
)";"""
    assert should_skip_cpp(content) is True


def test_raw_string_with_parentheses():
    # Raw string with complex content including parentheses
    content = """const char* COMPLEX_STRING = R"(
This string contains (parentheses) and other symbols
function() { return true; }
)";"""
    assert should_skip_cpp(content) is True


def test_multiline_comments():
    # File with multiline comments should be skipped
    content = """/*
This is a multiline comment
that spans multiple lines
*/

/* Another comment */
const int VALUE = 42;"""
    assert should_skip_cpp(content) is True


def test_multiline_comment_with_code():
    # Multiline comment followed by actual code
    content = """/*
Header comment
*/

int calculate() {
    return 42;
}"""
    assert should_skip_cpp(content) is False


def test_single_line_comments():
    # File with only single-line comments and constants
    content = """// Configuration constants
const int MAX_CONNECTIONS = 100;
// API endpoint
const char* API_URL = "https://api.example.com";
// Debug flag
const bool DEBUG_MODE = false;"""
    assert should_skip_cpp(content) is True


def test_struct_with_inheritance():
    # Struct with inheritance should be skipped if no implementation
    content = """struct Base {
    int id;
    std::string name;
};

struct Derived : public Base {
    int value;
    double score;
};"""
    assert should_skip_cpp(content) is True


def test_class_with_inheritance():
    # Class with inheritance should be skipped if no implementation
    content = """class Animal {
public:
    std::string name;
    int age;
};

class Dog : public Animal {
public:
    std::string breed;
};"""
    assert should_skip_cpp(content) is True


def test_enum_declarations():
    # Enum declarations should be skipped
    content = """enum Color {
    RED,
    GREEN,
    BLUE
};

enum class Status {
    PENDING,
    APPROVED,
    REJECTED
};"""
    assert should_skip_cpp(content) is True


def test_enum_forward_declaration():
    # Enum forward declarations should be skipped
    content = """enum Color;
enum class Status;

const int DEFAULT_COLOR = 1;"""
    assert should_skip_cpp(content) is True


def test_class_with_method_implementation():
    # Class with method implementation should NOT be skipped
    content = """class Calculator {
private:
    int value;

public:
    int getValue() {
        return value;
    }
};"""
    assert should_skip_cpp(content) is False


def test_struct_with_method_implementation():
    # Struct with method implementation should NOT be skipped
    content = """struct Point {
    int x, y;
    
    double distance() {
        return sqrt(x*x + y*y);
    }
};"""
    assert should_skip_cpp(content) is False


def test_extern_declarations():
    # Extern declarations should be skipped
    content = """extern int global_counter;
extern const char* version_string;
extern void external_function();

const int LOCAL_CONSTANT = 42;"""
    assert should_skip_cpp(content) is True


def test_forward_declarations():
    # Forward declarations should be skipped
    content = """class Database;
struct Configuration;
class Logger;

typedef int UserId;
typedef std::string UserName;"""
    assert should_skip_cpp(content) is True


def test_using_statements():
    # Using statements should be skipped
    content = """using std::string;
using std::vector;
using namespace std;

using UserId = int;
using UserMap = std::map<int, std::string>;"""
    assert should_skip_cpp(content) is True


def test_namespace_declarations():
    # Namespace declarations should be skipped
    content = """namespace utils {
    const int MAX_SIZE = 1000;
}

namespace config {
    const char* VERSION = "1.0.0";
}"""
    assert should_skip_cpp(content) is True


def test_template_declarations():
    # Template declarations should be skipped
    content = """template<typename T>
class Container;

template<class T, int N>
struct Array {
    T data[N];
};"""
    assert should_skip_cpp(content) is True


def test_static_declarations():
    # Static declarations should be skipped
    content = """static const int MAX_BUFFER = 1024;
static int counter = 0;
static const char* DEFAULT_NAME = "unknown";"""
    assert should_skip_cpp(content) is True


def test_preprocessor_directives():
    # Various preprocessor directives should be skipped
    content = """#ifndef HEADER_H
#define HEADER_H

#include <iostream>
#include <vector>

#define MAX_SIZE 100
#define API_VERSION "1.0"

#ifdef DEBUG
#define LOG(x) std::cout << x << std::endl
#else
#define LOG(x)
#endif

#endif // HEADER_H"""
    assert should_skip_cpp(content) is True


def test_macro_definitions():
    # Macro definitions should be skipped
    content = """#define PI 3.14159
#define MAX_RETRIES 5
#define API_ENDPOINT "https://api.com"
#define BUFFER_SIZE 1024"""
    assert should_skip_cpp(content) is True


def test_complex_mixed_declarations():
    # Complex mix of declarations that should be skipped
    content = """#include <iostream>
#include <memory>

// Forward declarations
class Database;
struct Config;

// Using statements
using std::string;
using std::shared_ptr;

// Constants
const int MAX_CONNECTIONS = 100;
static const char* VERSION = "2.0.0";

// Extern declarations
extern Database* g_database;

// Template declarations
template<typename T>
class Repository;

// Namespace
namespace utils {
    const bool DEBUG = true;
}

// Empty structs
struct Point {
    int x, y;
};

// Enums
enum Status {
    ACTIVE,
    INACTIVE
};"""
    assert should_skip_cpp(content) is True


def test_mixed_comments_and_raw_strings():
    # Mix of comments and raw strings
    content = """/*
Configuration file
*/

// SQL queries
const char* SELECT_QUERY = R"(
SELECT id, name FROM users
WHERE active = 1
)";

/* Another comment */
const char* UPDATE_QUERY = R"(
UPDATE users SET last_login = NOW()
WHERE id = ?
)";"""
    assert should_skip_cpp(content) is True


def test_edge_case_empty_braces():


def test_nested_raw_strings():
    # Test nested or complex raw string scenarios
    content = """const char* NESTED = R"(
This contains R"( but not a real nested raw string
)";

const char* WITH_QUOTES = R"(
String with "quotes" and 'apostrophes'
)";"""
    assert should_skip_cpp(content) is True


def test_multiline_comment_edge_cases():
    # Test multiline comment edge cases
    content = """/* Start comment
   continues here
   */ const int VALUE = 42;

/* Another /* nested-looking */ comment */
static const bool FLAG = true;"""
    assert should_skip_cpp(content) is True


def test_class_with_constructor_only():
    # Class with only constructor/destructor declarations (no implementation)
    content = """class MyClass {
public:
    MyClass();
    ~MyClass();
    
private:
    int value;
    std::string name;
};"""
    assert should_skip_cpp(content) is True


def test_class_with_inline_constructor():
    # Class with inline constructor implementation should NOT be skipped
    content = """class MyClass {
public:
    MyClass() : value(0) {
        // initialization code
    }
    
private:
    int value;
};"""
    assert should_skip_cpp(content) is False


def test_typedef_complex():
    # Complex typedef declarations
    content = """typedef int (*FunctionPtr)(int, int);
typedef struct {
    int x, y;
} Point;

typedef enum {
    RED, GREEN, BLUE
} Color;"""
    assert should_skip_cpp(content) is True


def test_function_pointer_declarations():
    # Function pointer declarations should be skipped
    content = """extern int (*operation)(int, int);
typedef void (*Callback)(const std::string&);

const Callback default_callback = nullptr;"""
    assert should_skip_cpp(content) is True


def test_variable_with_function_call():
    # Variables initialized with function calls should NOT be skipped
    content = """const int SIZE = calculateSize();
static bool initialized = initialize();"""
    assert should_skip_cpp(content) is False
