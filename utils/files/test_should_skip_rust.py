import sys
sys.path.append('.')
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


def test_empty_class_single_line_braces():
    # Empty struct with braces on same line should be skipped
    content = """// Base struct for components
struct MyComponent {}

const _: MyComponent = MyComponent {};"""
    assert should_skip_rust(content) is True


def test_single_line_triple_quote_constant():
    # Single-line constant definition
    content = """const API_KEY: &str = "abc123";
const DEBUG_MODE: bool = true;"""
    assert should_skip_rust(content) is True


def test_namedtuple_class():
    # Struct definitions
    content = """struct Point {
    x: i32,
    y: i32,
}

struct User {
    name: String,
    age: u32,
}"""
    assert should_skip_rust(content) is True


def test_multiline_string_assignment_parentheses():
    # Simple string constant
    content = """const TEMPLATE: &str = "This is a template";

const OTHER_CONSTANT: i32 = 42;"""
    assert should_skip_rust(content) is True


def test_multiline_list_assignment():
    # Simple constant definitions
    content = """const EXT_RS: &str = ".rs";
const EXT_JS: &str = ".js";
const EXT_TS: &str = ".ts";

const MAX_SIZE: usize = 100;"""
    assert should_skip_rust(content) is True


def test_complex_class_transitions():
    # Simple struct definitions and constants
    content = """struct MyError {
    message: String,
}

struct DataStruct {
    id: u32,
    name: String,
}

const MAX_RETRIES: u32 = 5;"""
    assert should_skip_rust(content) is True


def test_mixed_assignment_patterns():
    # Test various assignment patterns that should be skipped
    content = """const SIMPLE_VAR: &str = "value";
const LIST_VAR: &[i32] = &[1, 2, 3];
const BOOL_VAR: bool = true;
const NUM_VAR: i32 = 42;
const FLOAT_VAR: f64 = 3.14;
static NULL_VAR: Option<()> = None;"""
    assert should_skip_rust(content) is True


def test_bare_string_continuation():
    # Test comments and documentation
    content = """/// This is a module documentation
/// that spans multiple lines

const CONSTANT: &str = "value";"""
    assert should_skip_rust(content) is True


def test_autoload_statements():
    # Test use statements should be skipped
    content = """use std::collections::HashMap;
use serde::Serialize;
const CONSTANT: &str = "value";"""
    assert should_skip_rust(content) is True


def test_constants_with_square_brackets():
    # Test constants with array indexing should NOT be skipped - has executable logic
    content = """const ENV_VAR: &str = &ENV_ARRAY[0];
const API_URL: &str = "http://example.com";"""
    assert should_skip_rust(content) is False


def test_assignment_function_call_detection():
    # Test assignment with function calls should NOT be skipped - contains executable logic
    content = """static CONFIG: String = utils::load_config();
const API_URL: &str = "http://example.com";"""
    assert should_skip_rust(content) is False


def test_field_definition_with_complex_types():
    # Test impl blocks with methods should NOT be skipped
    content = """struct Config {}

impl Config {
    fn handler(&self) -> &str {
        "error"
    }

    fn process_data(&self, items: Vec<String>) -> Vec<String> {
        items
    }
}"""
    assert should_skip_rust(content) is False

def test_debug_struct_config():
    # Debug test for the specific failing case
    content = """struct Config {}"""
    result = should_skip_rust(content)
    print(f"Debug: struct Config {{}} returned {result}")
    assert result is True

def test_inside_exception_class_to_typeddict():
    # Test struct definitions should be skipped
    content = """struct MyError {
    message: String,
}
struct Config {
    name: String,
}"""
    assert should_skip_rust(content) is True


def test_inside_typeddict_class_to_exception():
    # Test struct definitions should be skipped
    content = """struct Config {
    name: String,
}
struct MyError {
    message: String,
}"""
    assert should_skip_rust(content) is True


def test_inside_exception_class_to_namedtuple():
    # Test struct definitions should be skipped
    content = """struct MyError {
    message: String,
}
struct Point {
    x: i32,
    y: i32,
}"""
    assert should_skip_rust(content) is True


def test_enum_declarations():
    # Test enum declarations
    content = """enum Status {
    Active,
    Inactive,
    Pending,
}
const MAX_SIZE: i32 = 100;"""
    assert should_skip_rust(content) is True


def test_extern_declarations():
    # Test use statements
    content = """use std::collections::HashMap;
use crate::utils::helper;
const MAX_SIZE: i32 = 100;"""
    assert should_skip_rust(content) is True


def test_forward_declarations():
    # Test struct declarations
    content = """struct ForwardStruct;
trait ForwardTrait;
const MAX_SIZE: i32 = 100;"""
    assert should_skip_rust(content) is True


def test_using_namespace_statements():
    # Test use with logic - should NOT be skipped
    content = """use std::collections::HashMap;
use crate::utils::process;
let result = process();"""
    assert should_skip_rust(content) is False


def test_template_declarations():
    # Test generic structs - should NOT be skipped (has logic)
    content = """struct Container<T> {
    items: Vec<T>,
}

impl<T> Container<T> {
    fn new() -> Self {
        Container { items: Vec::new() }
    }
}"""
    assert should_skip_rust(content) is False


def test_static_extern_const():
    # Test static variables and constants
    content = """static INTERNAL_VAR: i32 = 42;
const VERSION: &str = "1.0.0";
const MAX_SIZE: i32 = 100;"""
    assert should_skip_rust(content) is True


def test_enum_and_macro_declarations():
    # Test constants
    content = """const DEBUG_MODE: bool = true;
const BUFFER_SIZE: usize = 1024;
const MAX_SIZE: i32 = 100;"""
    assert should_skip_rust(content) is True


def test_macro_constants_only():
    # Test constants only
    content = """const MAX_SIZE: usize = 1024;
const BUFFER_SIZE: usize = 512;
const VALUE: i32 = 42;"""
    assert should_skip_rust(content) is True


def test_annotation_interface_definitions():
    # Test trait definitions
    content = """trait MyTrait {
    fn method(&self) -> String;
}
const CONSTANT: &str = "value";"""
    assert should_skip_rust(content) is True


def test_kotlin_data_class_definitions():
    # Test struct definitions
    content = """#[derive(Debug, Clone)]
struct User {
    id: i64,
    name: String,
    email: String,
}
const CONSTANT: &str = "value";"""
    assert should_skip_rust(content) is True


def test_scala_case_class_definitions():
    # Test struct definitions
    content = """struct Point {
    x: i32,
    y: i32,
}
const CONSTANT: &str = "value";"""
    assert should_skip_rust(content) is True


def test_module_exports_only():
    # Test use statements
    content = """use std::collections::HashMap;
pub use crate::exports::*;
const CONSTANT: &str = "value";"""
    assert should_skip_rust(content) is True


def test_standalone_closing_brace_only():
    # Test struct with closing brace
    content = """struct MyStruct {
    value: i32,
}
const CONSTANT: &str = "value";"""
    assert should_skip_rust(content) is True


def test_type_alias():
    # Test type alias to hit line 83
    content = """pub type MyString = String;
type UserId = u64;
const CONSTANT: &str = "value";"""
    assert should_skip_rust(content) is True


def test_mod_statements():
    # Test mod statements to hit line 90
    content = """pub mod utils;
mod internal;
const CONSTANT: &str = "value";"""
    assert should_skip_rust(content) is True


def test_extern_crate():
    # Test extern crate to hit line 93
    content = """extern crate serde;
extern crate tokio;
const CONSTANT: &str = "value";"""
    assert should_skip_rust(content) is True


def test_const_with_function_calls():
    # Test const with function calls to hit line 102
    content = """const CONFIG: &str = env::var("CONFIG").unwrap_or("default");
const PATH: PathBuf = Path::new("/tmp");"""
    assert should_skip_rust(content) is False


def test_static_with_function_calls():
    # Test static with function calls to hit line 112
    content = """static CONFIG: Lazy<String> = Lazy::new(|| env::var("CONFIG").unwrap());
static INSTANCE: Arc<Mutex<State>> = Arc::new(Mutex::new(State::new()));"""
    assert should_skip_rust(content) is False


def test_static_with_array_indexing():
    # Test static with array indexing to hit line 118
    content = """static CONFIG: &str = &DEFAULT_CONFIG[0];
static VERSION: &str = "1.0.0";"""
    assert should_skip_rust(content) is False


# Additional tests for 100% coverage


def test_multiline_comment_handling():
    # Test multiline comment handling (lines 30-36)
    content = """/* This is a multiline comment
that spans multiple lines
and should be ignored */
const CONSTANT: &str = "value";"""
    assert should_skip_rust(content) is True


def test_multiline_comment_incomplete():
    # Test incomplete multiline comment (starts but doesn't end in same line)
    content = """/* This is a multiline comment
that continues on next line
const CONSTANT: &str = "value";
and ends here */
const ANOTHER: i32 = 42;"""
    assert should_skip_rust(content) is True


def test_multiline_raw_string_handling():
    # Test multiline raw string handling (lines 39-45)
    content = """const TEMPLATE: &str = r#"
This is a multiline raw string
that spans multiple lines
"#;
const ANOTHER: &str = "value";"""
    assert should_skip_rust(content) is True


def test_multiline_raw_string_incomplete():
    # Test incomplete multiline raw string (starts but doesn't end properly)
    content = """const TEMPLATE: &str = r#"
This is a multiline raw string
that continues
const HIDDEN: &str = "hidden";
and ends here
"#;
const VISIBLE: i32 = 42;"""
    assert should_skip_rust(content) is True


def test_single_line_multiline_comment():
    # Test single-line multiline comment (line 48)
    content = """/* single line comment */ const CONSTANT: &str = "value";
const ANOTHER: i32 = 42;"""
    assert should_skip_rust(content) is True


def test_attributes_handling():
    # Test attributes handling (lines 51-52)
    content = """#[derive(Debug, Clone)]
#![allow(dead_code)]
struct MyStruct {
    value: i32,
}
const CONSTANT: &str = "value";"""
    assert should_skip_rust(content) is True


def test_struct_with_braces_on_same_line():
    # Test struct with opening brace on same line (line 59)
    content = """pub struct Config {
    timeout: u32,
}
const CONSTANT: &str = "value";"""
    assert should_skip_rust(content) is True


def test_struct_without_braces_on_same_line():
    # Test struct without opening brace on same line
    content = """pub struct Config
{
    timeout: u32,
}
const CONSTANT: &str = "value";"""
    assert should_skip_rust(content) is True


def test_enum_with_braces_on_same_line():
    # Test enum with opening brace on same line (line 63)
    content = """pub enum Status {
    Active,
    Inactive,
}
const CONSTANT: &str = "value";"""
    assert should_skip_rust(content) is True


def test_enum_without_braces_on_same_line():
    # Test enum without opening brace on same line
    content = """pub enum Status
{
    Active,
    Inactive,
}
const CONSTANT: &str = "value";"""
    assert should_skip_rust(content) is True


def test_trait_with_braces_on_same_line():
    # Test trait with opening brace on same line (line 73)
    content = """pub trait MyTrait {
    fn method(&self) -> String;
}
const CONSTANT: &str = "value";"""
    assert should_skip_rust(content) is True


def test_trait_without_braces_on_same_line():
    # Test trait without opening brace on same line
    content = """pub trait MyTrait
{
    fn method(&self) -> String;
}
const CONSTANT: &str = "value";"""
    assert should_skip_rust(content) is True


def test_const_with_struct_constructor():
    # Test const with struct constructor (should be allowed - line 100)
    content = """const DEFAULT_CONFIG: Config = Config {};
const ANOTHER: &str = "value";"""
    assert should_skip_rust(content) is True


def test_static_with_struct_constructor():
    # Test static with struct constructor (should be allowed - line 113)
    content = """static DEFAULT_STATE: State = State {};
const ANOTHER: &str = "value";"""
    assert should_skip_rust(content) is True


def test_const_with_array_indexing():
    # Test const with array indexing (line 104)
    content = """const VALUE: &str = &ARRAY[0];
const ANOTHER: &str = "value";"""
    assert should_skip_rust(content) is False


def test_unknown_code_line():
    # Test unknown code that should cause function to return False (line 121)
    content = """const CONSTANT: &str = "value";
let variable = 42;  // This is executable code
const ANOTHER: &str = "value";"""
    assert should_skip_rust(content) is False


def test_nested_struct_enum_handling():
    # Test nested struct/enum state tracking
    content = """struct Outer {
    inner: Inner,
}

enum Status {
    Active {
        timestamp: u64,
    },
    Inactive,
}

const CONSTANT: &str = "value";"""
    assert should_skip_rust(content) is True


def test_nested_trait_handling():
    # Test nested trait state tracking
    content = """trait OuterTrait {
    type AssociatedType;

    fn method(&self) -> Self::AssociatedType;
}

const CONSTANT: &str = "value";"""
    assert should_skip_rust(content) is True


def test_mixed_comments_and_strings():
    # Test combination of comments and multiline strings
    content = """// Single line comment
/* Multiline comment */
const TEMPLATE: &str = r#"
Raw string content
"#;
#[derive(Debug)]
struct Config {}
const CONSTANT: &str = "value";"""
    assert should_skip_rust(content) is True


def test_complex_multiline_scenarios():
    # Test complex multiline comment and string scenarios
    content = """/*
 * Complex multiline comment
 * with multiple lines
 */
const FIRST: &str = r#"
First multiline string
"#;

/* Another comment */
const SECOND: &str = r#"
Second multiline string
with more content
"#;

struct SimpleStruct {
    field: i32,
}"""
    assert should_skip_rust(content) is True


def test_edge_case_empty_lines_and_whitespace():
    # Test edge cases with empty lines and whitespace
    content = """

    // Comment with leading whitespace

    const CONSTANT: &str = "value";


    struct EmptyStruct {}

    """
    assert should_skip_rust(content) is True
