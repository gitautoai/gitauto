from utils.files.should_skip_rust import should_skip_rust


def test_export_only():
    # File with only use statements and pub use
    content = """use std::collections::HashMap;
use std::fs::File;
use crate::types::User;

pub use crate::module::*;"""
    assert should_skip_rust(content) is True


def test_constants_only():
    # Constants only
    content = """const MAX_RETRIES: i32 = 3;
const API_URL: &str = "https://api.example.com";
const DEBUG: bool = true;
static VERSION: &str = "1.0.0";"""
    assert should_skip_rust(content) is True


def test_multiline_string_constants():
    # Multi-line string constants
    content = """const IDENTIFY_CAUSE: &str = r#"
You are a GitHub Actions expert.
Given information such as a pull request title, identify the cause.
"#;

const ANOTHER_TEMPLATE: &str = r#"
This is another template
with multiple lines
"#;"""
    assert should_skip_rust(content) is True


def test_typeddict_only():
    # Struct definitions only
    content = """#[derive(Debug, Clone)]
struct User {
    id: i64,
    name: String,
    email: String,
}

struct Config {
    timeout: u32,
    retries: u32,
}"""
    assert should_skip_rust(content) is True


def test_exception_classes_only():
    # Simple empty structs
    content = """struct CustomError {}

struct AuthenticationError {}"""
    assert should_skip_rust(content) is True


def test_mixed_imports_and_constants():
    # Mixed imports and constants
    content = """use std::env;
use std::path::Path;

const MAX_RETRIES: i32 = 3;
const API_URL: &str = "https://api.example.com";

pub const VERSION: &str = "1.0.0";"""
    assert should_skip_rust(content) is True


def test_function_with_logic():
    # Function definitions - should NOT be skipped
    content = """fn calculate_total(items: &[Item]) -> f64 {
    items.iter().map(|item| item.price).sum()
}

fn process_data(data: &[i32]) -> Vec<i32> {
    data.iter().map(|x| x * 2).collect()
}"""
    assert should_skip_rust(content) is False


def test_class_with_methods():
    # Impl blocks with methods - should NOT be skipped
    content = """struct Calculator {
    value: i32,
}

impl Calculator {
    fn new() -> Self {
        Calculator { value: 0 }
    }

    fn add(&self, a: i32, b: i32) -> i32 {
        a + b
    }

    fn multiply(&self, a: i32, b: i32) -> i32 {
        a * b
    }
}"""
    assert should_skip_rust(content) is False


def test_mixed_constants_and_logic():
    # Mixed constants and logic - should NOT be skipped
    content = """const MAX_SIZE: i32 = 100;
const API_URL: &str = "https://api.com";

fn calculate_size() -> i32 {
    MAX_SIZE * 2
}"""
    assert should_skip_rust(content) is False


def test_constants_with_function_calls():
    # Constants with function calls - should NOT be skipped
    content = """use std::env;
use std::path::Path;

static IS_PRD: bool = env::var("ENV").unwrap_or_default() == "prod";
static BASE_PATH: &str = Path::new("/").join("app").to_str().unwrap();"""
    assert should_skip_rust(content) is False


def test_empty_file():
    # Empty content should be skipped
    assert should_skip_rust("") is True


def test_whitespace_only():
    # File with only whitespace should be skipped
    content = """




    """
    assert should_skip_rust(content) is True


def test_init_file_with_imports():
    # Typical lib.rs file with only use statements
    content = """pub use crate::module1::Class1;
pub use crate::module2::Class2;
pub use crate::utils::helper_function;

use std::collections::HashMap;"""
    assert should_skip_rust(content) is True


def test_empty_init_file():
    # Empty lib.rs file
    content = ""
    assert should_skip_rust(content) is True


def test_comment_with_simple_class():
    # File with comment and simple empty struct should be skipped
    content = """/*
Base struct for application components
*/
struct BaseComponent {}

const _: BaseComponent = BaseComponent {};"""
    assert should_skip_rust(content) is True
