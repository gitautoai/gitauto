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
