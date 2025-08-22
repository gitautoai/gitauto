from utils.files.should_skip_rust import should_skip_rust


def test_export_only():
    # File with only pub use statements
    content = """pub use self::core::Core;
pub use self::utils::helper;
use std::io;

pub mod core;
pub mod utils;"""
    assert should_skip_rust(content) is True


def test_constants_only():
    # Constants only
    content = """pub const PI: f64 = 3.14159;
const MAX_SIZE: usize = 1024;
pub static VERSION: &str = "1.0.0";
static CONFIG: &str = "production";"""
    assert should_skip_rust(content) is True


def test_struct_definitions_only():
    # Struct definitions without implementation
    content = """pub struct User {
    id: u64,
    name: String,
    email: Option<String>,
}

struct Config {
    timeout: u32,
    retries: u8,
}"""
    assert should_skip_rust(content) is True


def test_enum_definitions_only():
    # Enum definitions only
    content = """pub enum Status {
    Active,
    Inactive,
    Pending,
}

enum Result<T, E> {
    Ok(T),
    Err(E),
}"""
    assert should_skip_rust(content) is True


def test_trait_definitions_only():
    # Trait definitions without implementation
    content = """pub trait Display {
    fn fmt(&self) -> String;
}

trait Clone {
    fn clone(&self) -> Self;
}"""
    assert should_skip_rust(content) is True


def test_mixed_uses_and_constants():
    # Mixed use statements and constants
    content = """use std::collections::HashMap;
pub use crate::types::*;

pub const DEFAULT_TIMEOUT: u64 = 30;
static CONFIG: &str = "production";"""
    assert should_skip_rust(content) is True


def test_function_with_logic():
    # Function definitions - should NOT be skipped
    content = """fn calculate_total(items: &[Item]) -> f64 {
    items.iter().map(|item| item.price).sum()
}

pub fn process_data(data: Vec<i32>) -> Vec<i32> {
    data.into_iter().map(|x| x * 2).collect()
}"""
    assert should_skip_rust(content) is False


def test_impl_blocks():
    # Implementation blocks - should NOT be skipped
    content = """struct Calculator;

impl Calculator {
    fn new() -> Self {
        Calculator
    }

    fn add(&self, a: i32, b: i32) -> i32 {
        a + b
    }
}"""
    assert should_skip_rust(content) is False


def test_mixed_struct_and_impl():
    # Mixed struct definition and implementation - should NOT be skipped
    content = """struct User {
    name: String,
}

impl User {
    fn new(name: String) -> Self {
        User { name }
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}"""
    assert should_skip_rust(content) is False


def test_macros_with_logic():
    # Macros with logic - should NOT be skipped
    content = """macro_rules! calculate {
    ($x:expr) => {
        $x * 2
    };
}

fn use_macro() {
    let result = calculate!(5);
}"""
    assert should_skip_rust(content) is False


def test_mixed_constants_and_logic():
    # Mixed constants and logic - should NOT be skipped
    content = """const MAX_SIZE: usize = 1024;
static VERSION: &str = "1.0.0";

fn get_max_size() -> usize {
    MAX_SIZE
}"""
    assert should_skip_rust(content) is False


def test_empty_file():
    # Empty content should be skipped
    assert should_skip_rust("") is True


def test_whitespace_only():
    # File with only whitespace should be skipped
    content = """




    """
    assert should_skip_rust(content) is True
