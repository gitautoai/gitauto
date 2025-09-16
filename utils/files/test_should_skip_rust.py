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


def test_multiline_comment_spanning_lines():
    # Test multiline comment that spans multiple lines
    content = """/* This is a multiline comment
that spans multiple lines
and should be ignored */
const VALUE: i32 = 42;"""
    assert should_skip_rust(content) is True


def test_multiline_comment_with_code():
    # Test multiline comment mixed with code
    content = """const BEFORE: i32 = 1;
/* This is a multiline comment
that spans multiple lines */
const AFTER: i32 = 2;"""
    assert should_skip_rust(content) is True


def test_multiline_raw_string_spanning_lines():
    # Test multiline raw string that spans multiple lines
    content = """const TEMPLATE: &str = r#"
This is a multiline
raw string template
that spans multiple lines
"#;
const OTHER: i32 = 42;"""
    assert should_skip_rust(content) is True


def test_multiline_raw_string_with_code():
    # Test multiline raw string mixed with other code
    content = """const BEFORE: i32 = 1;
const TEMPLATE: &str = r#"
This is a multiline template
"#;
const AFTER: i32 = 2;"""
    assert should_skip_rust(content) is True


def test_crate_level_attributes():
    # Test crate-level attributes with #![
    content = """#![allow(dead_code)]
#![warn(missing_docs)]
const VALUE: i32 = 42;
struct MyStruct {
    field: String,
}"""
    assert should_skip_rust(content) is True


def test_struct_with_opening_brace_on_next_line():
    # Test struct where opening brace is on next line
    content = """struct MyStruct
{
    field1: i32,
    field2: String,
}
const VALUE: i32 = 42;"""
    assert should_skip_rust(content) is True


def test_enum_with_opening_brace_on_next_line():
    # Test enum where opening brace is on next line
    content = """enum Status
{
    Active,
    Inactive,
    Pending,
}
const VALUE: i32 = 42;"""
    assert should_skip_rust(content) is True


def test_trait_with_opening_brace_on_next_line():
    # Test trait where opening brace is on next line
    content = """trait MyTrait
{
    fn method(&self) -> String;
}
const VALUE: i32 = 42;"""
    assert should_skip_rust(content) is True


def test_pub_struct_with_opening_brace_on_next_line():
    # Test pub struct where opening brace is on next line
    content = """pub struct MyStruct
{
    field: i32,
}
const VALUE: i32 = 42;"""
    assert should_skip_rust(content) is True


def test_pub_enum_with_opening_brace_on_next_line():
    # Test pub enum where opening brace is on next line
    content = """pub enum Status
{
    Active,
    Inactive,
}
const VALUE: i32 = 42;"""
    assert should_skip_rust(content) is True


def test_pub_trait_with_opening_brace_on_next_line():
    # Test pub trait where opening brace is on next line
    content = """pub trait MyTrait
{
    fn method(&self) -> String;
}
const VALUE: i32 = 42;"""
    assert should_skip_rust(content) is True


def test_const_with_struct_constructor():
    # Test const with struct constructor (should be allowed)
    content = """struct Point { x: i32, y: i32 }
const ORIGIN: Point = Point { x: 0, y: 0 };
const DEFAULT_CONFIG: Config = Config {};"""
    assert should_skip_rust(content) is True


def test_static_with_struct_constructor():
    # Test static with struct constructor (should be allowed)
    content = """struct Config { debug: bool }
static DEFAULT_CONFIG: Config = Config { debug: false };
static EMPTY_CONFIG: Config = Config {};"""
    assert should_skip_rust(content) is True


def test_const_with_function_call_and_struct_constructor():
    # Test const with both function call and struct constructor - function call should make it return False
    content = """struct Config { value: String }
const CONFIG: Config = Config { value: env::var("VALUE").unwrap() };"""
    assert should_skip_rust(content) is False


def test_single_line_comment_with_multiline_marker():
    # Test single line comment that looks like multiline but isn't
    content = """/* This is actually a single line comment */
const VALUE: i32 = 42;"""
    assert should_skip_rust(content) is True


def test_nested_multiline_comments():
    # Test nested multiline comments
    content = """/* Outer comment start
/* Inner comment */
Still in outer comment */
const VALUE: i32 = 42;"""
    assert should_skip_rust(content) is True


def test_multiline_comment_with_closing_on_same_line():
    # Test multiline comment that starts and ends on different lines
    content = """const BEFORE: i32 = 1;
/* Start of comment
End of comment */
const AFTER: i32 = 2;"""
    assert should_skip_rust(content) is True


def test_raw_string_ending_without_semicolon():
    # Test raw string that doesn't end with semicolon
    content = """const TEMPLATE: &str = r#"
This is a template
"#"""
    assert should_skip_rust(content) is True


def test_complex_const_with_double_colon_but_no_function_call():
    # Test const with :: but no function call (should be allowed)
    content = """const TYPE_NAME: &str = "std::collections::HashMap";
const PATH_SEP: &str = "::";"""
    assert should_skip_rust(content) is True


def test_complex_static_with_double_colon_but_no_function_call():
    # Test static with :: but no function call (should be allowed)
    content = """static TYPE_NAME: &str = "std::collections::HashMap";
static NAMESPACE: &str = "crate::module::submodule";"""
    assert should_skip_rust(content) is True


def test_const_with_array_access_pattern_in_string():
    # Test const with array-like pattern in string (should be allowed)
    content = """const TEMPLATE: &str = "array[index] access pattern";
const EXAMPLE: &str = "variable[0] in string";"""
    assert should_skip_rust(content) is True


def test_mixed_multiline_constructs():
    # Test file with multiple multiline constructs
    content = """/* Multiline comment
spanning lines */
const TEMPLATE: &str = r#"
Multiline raw string
"#;


def test_function_definition_should_not_skip():
    # Test function definition - should NOT be skipped (hits line 121)
    content = """const VALUE: i32 = 42;
fn my_function() {
    println!("Hello");
}"""
    assert should_skip_rust(content) is False


def test_impl_block_should_not_skip():
    # Test impl block - should NOT be skipped (hits line 121)
    content = """struct MyStruct;
impl MyStruct {
    fn new() -> Self {
        MyStruct
    }
}"""
    assert should_skip_rust(content) is False


def test_macro_definition_should_not_skip():
    # Test macro definition - should NOT be skipped (hits line 121)
    content = """const VALUE: i32 = 42;
macro_rules! my_macro {
    () => {
        println!("Hello");
    };
}"""
    assert should_skip_rust(content) is False


def test_let_statement_should_not_skip():
    # Test let statement - should NOT be skipped (hits line 121)
    content = """const VALUE: i32 = 42;
let x = 10;"""
    assert should_skip_rust(content) is False


def test_match_statement_should_not_skip():
    # Test match statement - should NOT be skipped (hits line 121)
    content = """enum Status { Active, Inactive }
match status {
    Status::Active => println!("Active"),
    Status::Inactive => println!("Inactive"),
}"""
    assert should_skip_rust(content) is False


def test_if_statement_should_not_skip():
    # Test if statement - should NOT be skipped (hits line 121)
    content = """const DEBUG: bool = true;
if DEBUG {
    println!("Debug mode");
}"""
    assert should_skip_rust(content) is False


def test_loop_statement_should_not_skip():
    # Test loop statement - should NOT be skipped (hits line 121)
    content = """const MAX: i32 = 10;
for i in 0..MAX {
    println!("{}", i);
}"""
    assert should_skip_rust(content) is False


def test_return_statement_should_not_skip():
    # Test return statement - should NOT be skipped (hits line 121)
    content = """const VALUE: i32 = 42;
return VALUE;"""
    assert should_skip_rust(content) is False


def test_expression_statement_should_not_skip():
    # Test expression statement - should NOT be skipped (hits line 121)
    content = """const VALUE: i32 = 42;
println!("Value: {}", VALUE);"""
    assert should_skip_rust(content) is False


def test_multiline_comment_starting_mid_line():
    # Test multiline comment that starts in the middle of a line
    content = """const VALUE: i32 = 42; /* This comment starts mid-line
and continues on next line */
const OTHER: i32 = 24;"""
    assert should_skip_rust(content) is True


def test_multiline_raw_string_starting_mid_line():
    # Test multiline raw string that starts in the middle of a line
    content = """const TEMPLATE: &str = r#"
This is a template
"#;
const OTHER: i32 = 42;"""
    assert should_skip_rust(content) is True


def test_raw_string_with_ending_pattern_in_middle():
    # Test raw string that has "#; pattern in middle but not at end
    content = """const TEMPLATE: &str = r#"
This template has "#; in the middle
but continues here
"#;"""
    assert should_skip_rust(content) is True


def test_const_with_parentheses_but_no_double_colon():
    # Test const with parentheses but no :: (should be allowed)
    content = """const TUPLE: (i32, i32) = (1, 2);
const ARRAY: [i32; 3] = [1, 2, 3];"""
    assert should_skip_rust(content) is True


def test_static_with_parentheses_but_no_double_colon():
    # Test static with parentheses but no :: (should be allowed)
    content = """static TUPLE: (i32, i32) = (1, 2);
static ARRAY: [i32; 3] = [1, 2, 3];"""
    assert should_skip_rust(content) is True


def test_const_with_double_colon_but_no_parentheses():
    # Test const with :: but no parentheses (should be allowed)
    content = """const TYPE_PATH: &str = "std::collections::HashMap";
const MODULE_PATH: &str = "crate::utils::helper";"""
    assert should_skip_rust(content) is True


def test_static_with_double_colon_but_no_parentheses():
    # Test static with :: but no parentheses (should be allowed)
    content = """static TYPE_PATH: &str = "std::collections::HashMap";
static MODULE_PATH: &str = "crate::utils::helper";"""
    assert should_skip_rust(content) is True


def test_empty_lines_and_whitespace_mixed():
    # Test file with various empty lines and whitespace
    content = """

