from utils.files.should_skip_javascript import should_skip_javascript


def test_export_only():
    # File with only export statements
    content = """export * from './lib';
export { default } from './main';
export { Button, Input } from './components';"""
    assert should_skip_javascript(content) is True


def test_constants_only():
    # Constants only
    content = """const MAX_RETRIES = 3;
const API_URL = "https://api.example.com";
const DEFAULT_CONFIG = { debug: true };
const STATUS_CODES = [200, 201, 404];"""
    assert should_skip_javascript(content) is True


def test_multiline_string_constants():
    # Multi-line string constants
    content = """const IDENTIFY_CAUSE = `
You are a GitHub Actions expert.
Given information such as a pull request title, identify the cause.
`;

const ANOTHER_TEMPLATE = `
This is another template
with multiple lines
`;"""
    assert should_skip_javascript(content) is True


def test_typeddict_only():
    # TypeScript interface and type definitions only
    content = """interface User {
    id: number;
    name: string;
    email?: string;
}

interface Config {
    timeout: number;
    retries: number;
}"""
    assert should_skip_javascript(content) is True


def test_exception_classes_only():
    # Simple empty classes
    content = """class CustomError extends Error {
}

class AuthenticationError extends Error {
}"""
    assert should_skip_javascript(content) is True


def test_mixed_imports_and_constants():
    # Mixed imports and constants
    content = """import os from 'os';
import { Dict } from 'typing';

const MAX_RETRIES = 3;
const API_URL = "https://api.example.com";

export { MAX_RETRIES, API_URL };"""
    assert should_skip_javascript(content) is True


def test_function_with_logic():
    # Function definitions - should NOT be skipped
    content = """function calculateTotal(items) {
    return items.reduce((sum, item) => sum + item.price, 0);
}

function processData(data) {
    return data.map(x => x * 2);
}"""
    assert should_skip_javascript(content) is False


def test_class_with_methods():
    # Class with methods - should NOT be skipped
    content = """class Calculator {
    constructor() {
        this.value = 0;
    }

    add(a, b) {
        return a + b;
    }

    multiply(a, b) {
        return a * b;
    }
}"""
    assert should_skip_javascript(content) is False


def test_mixed_constants_and_logic():
    # Mixed constants and logic - should NOT be skipped
    content = """const MAX_SIZE = 100;
const API_URL = "https://api.com";

function calculateSize() {
    return MAX_SIZE * 2;
}"""
    assert should_skip_javascript(content) is False


def test_constants_with_function_calls():
    # Constants with function calls - should NOT be skipped
    content = """import os from 'os';
import { getEnvVar } from './config';

const IS_PRD = getEnvVar("ENV") === "prod";
const BASE_PATH = os.path.join("/", "app");"""
    assert should_skip_javascript(content) is False


def test_empty_file():
    # Empty content should be skipped
    assert should_skip_javascript("") is True


def test_whitespace_only():
    # File with only whitespace should be skipped
    content = """




    """
    assert should_skip_javascript(content) is True


def test_init_file_with_imports():
    # Typical index.js file with only imports and exports
    content = """import { Class1, function1 } from './module1';
import { Class2 } from './module2';
import { helperFunction } from './utils';

export { Class1, Class2, function1, helperFunction };"""
    assert should_skip_javascript(content) is True


def test_empty_init_file():
    # Empty index.js file
    content = ""
    assert should_skip_javascript(content) is True


def test_comment_with_simple_class():
    # File with comment and simple empty class should be skipped
    content = """/**
 * Base class for application components
 */
class BaseComponent {
}

export default BaseComponent;"""
    assert should_skip_javascript(content) is True


def test_empty_class_single_line_braces():
    # Empty class with braces on same line should be skipped
    content = """/**
 * Base class for components
 */
class MyComponent {}

export default MyComponent;"""
    assert should_skip_javascript(content) is True


def test_single_line_triple_quote_constant():
    # Single-line constant definition
    content = """const API_KEY = "abc123";
const DEBUG_MODE = true;"""
    assert should_skip_javascript(content) is True


def test_namedtuple_class():
    # Empty class definitions should be skipped
    content = """class Point {
}

class User {
}"""
    assert should_skip_javascript(content) is True


def test_multiline_string_assignment_parentheses():
    # Multi-line string assignment using template literals
    content = """const TEMPLATE = `
This is a very long template
that spans multiple lines
`;

const OTHER_CONSTANT = 42;"""
    assert should_skip_javascript(content) is True


def test_multiline_list_assignment():
    # Simple constant assignments
    content = """const EXT_JS = ".js";
const EXT_TS = ".ts";
const EXT_JSX = ".jsx";
const EXT_TSX = ".tsx";

const MAX_SIZE = 100;"""
    assert should_skip_javascript(content) is True


def test_complex_class_transitions():
    # Simple constants only - should be skipped
    content = """const ERROR_TYPE = 'MyError';

const DATA_TYPE = 'DataClass';

const MAX_RETRIES = 5;"""
    assert should_skip_javascript(content) is True


def test_mixed_assignment_patterns():
    # Test various assignment patterns that should be skipped
    content = """const SIMPLE_VAR = "value";
const LIST_VAR = [1, 2, 3];
const BOOL_VAR = true;
const NUM_VAR = 42;
const FLOAT_VAR = 3.14;
const NULL_VAR = null;"""
    assert should_skip_javascript(content) is True


def test_bare_string_continuation():
    # Test comments and documentation
    content = """/**
 * This is a module documentation
 * that spans multiple lines
 */

const CONSTANT = "value";"""
    assert should_skip_javascript(content) is True


def test_autoload_statements():
    # Test import/require statements should be skipped
    content = """import { Component } from "react";
const fs = require("fs");
const CONSTANT = "value";"""
    assert should_skip_javascript(content) is True


def test_constants_with_direct_function_calls():
    # Test constants with function calls should NOT be skipped
    content = """const CONFIG = loadConfig();
const API_URL = "http://example.com";"""
    assert should_skip_javascript(content) is False


def test_constants_with_square_brackets():
    # Test constants with square brackets should NOT be skipped
    content = """const ENV_VAR = ENV["PATH"];
const API_URL = "http://example.com";"""
    assert should_skip_javascript(content) is False


def test_assignment_function_call_detection():
    # Test assignment with function calls should NOT be skipped
    content = """const config = loadConfig();
const apiUrl = "http://example.com";"""
    assert should_skip_javascript(content) is False


def test_field_definition_with_complex_types():
    # Test class with methods should NOT be skipped
    content = """class Config {
    handler() {
        return "error";
    }

    processData(items) {
        return items;
    }
}"""
    assert should_skip_javascript(content) is False


def test_inside_exception_class_to_typeddict():
    # Test class definitions should NOT be skipped (JS treats classes with constructors as logic)
    content = """class MyError extends Error {
}
class Config {
    constructor() {}
}"""
    assert should_skip_javascript(content) is False


def test_inside_typeddict_class_to_exception():
    # Test class definitions should NOT be skipped (JS treats classes with constructors as logic)
    content = """class Config {
    constructor() {}
}
class MyError extends Error {
}"""
    assert should_skip_javascript(content) is False


def test_inside_exception_class_to_namedtuple():
    # Test class definitions should NOT be skipped (JS treats classes with constructors as logic)
    content = """class MyError extends Error {
}
class Point {
    constructor(x, y) {
        this.x = x;
        this.y = y;
    }
}"""
    assert should_skip_javascript(content) is False


def test_enum_declarations():
    # Test constants - should NOT be skipped (object assignment)
    content = """const Status = {
    ACTIVE: 'active',
    INACTIVE: 'inactive',
    PENDING: 'pending'
};
const MAX_SIZE = 100;"""
    assert should_skip_javascript(content) is False


def test_extern_declarations():
    # Test import/require statements
    content = """import { List } from 'immutable';
const utils = require('./utils');
const MAX_SIZE = 100;"""
    assert should_skip_javascript(content) is True


def test_forward_declarations():
    # Test class declarations without implementation
    content = """class ForwardClass {}
class AnotherClass {}
const MAX_SIZE = 100;"""
    assert should_skip_javascript(content) is True


def test_using_namespace_statements():
    # Test import with logic - should NOT be skipped
    content = """import * as utils from './utils';
import { process } from './processor';
const result = process();"""
    assert should_skip_javascript(content) is False


def test_template_declarations():
    # Test class with methods - should NOT be skipped
    content = """class Container {
    constructor() {
        this.items = [];
    }

    add(item) {
        this.items.push(item);
    }
}"""
    assert should_skip_javascript(content) is False


def test_static_extern_const():
    # Test variables and constants - should NOT be skipped (let variables are mutable)
    content = """let internalVar = 42;
const VERSION = "1.0.0";
const MAX_SIZE = 100;"""
    assert should_skip_javascript(content) is False


def test_enum_and_macro_declarations():
    # Test constants
    content = """const DEBUG_MODE = true;
const BUFFER_SIZE = 1024;
const MAX_SIZE = 100;"""
    assert should_skip_javascript(content) is True


def test_macro_constants_only():
    # Test constants only
    content = """const MAX_SIZE = 1024;
const BUFFER_SIZE = 512;
const VALUE = 42;"""
    assert should_skip_javascript(content) is True


def test_annotation_interface_definitions():
    # Test class definitions
    content = """@deprecated
class MyClass {
    constructor() {}
}
const CONSTANT = "value";"""
    assert should_skip_javascript(content) is False


def test_kotlin_data_class_definitions():
    # Test class definitions
    content = """class User {
    constructor(id, name, email) {
        this.id = id;
        this.name = name;
        this.email = email;
    }
}
const CONSTANT = "value";"""
    assert should_skip_javascript(content) is False


def test_scala_case_class_definitions():
    # Test object definitions
    content = """const Point = {
    x: 0,
    y: 0
};
const CONSTANT = "value";"""
    assert should_skip_javascript(content) is False


def test_module_exports_only():
    # Test import/export statements
    content = """import { List } from 'immutable';
export { CONSTANT };
const CONSTANT = "value";"""
    assert should_skip_javascript(content) is True


def test_standalone_closing_brace_only():
    # Test object with closing brace
    content = """const MyObject = {
    value: 42
};
const CONSTANT = "value";"""
    assert should_skip_javascript(content) is False


def test_single_line_comments():
    # Test single line comments - line 39
    content = """// This is a comment
// Another comment
const CONSTANT = "value";"""
    assert should_skip_javascript(content) is True


def test_typescript_type_imports():
    # Test TypeScript type imports - line 61
    content = """import type { User } from './types';
import { type Config } from './config';
const CONSTANT = "value";"""
    assert should_skip_javascript(content) is True


def test_destructured_requires():
    # Test destructured require statements - line 67
    content = """const { readFile, writeFile } = require('fs');
let { join, resolve } = require('path');
const CONSTANT = "value";"""
    assert should_skip_javascript(content) is True


def test_module_exports_statements():
    # Test module.exports statements - line 73
    content = """module.exports = { value: 42 };
exports.helper = function() {};
const CONSTANT = "value";"""
    assert should_skip_javascript(content) is True


def test_simple_object_properties():
    # Test simple property names in objects - line 76
    content = """const config = {
    development,
    production,
    test
};
const CONSTANT = "value";"""
    assert should_skip_javascript(content) is False


def test_export_all_statements():
    # Test export all statements - line 81
    content = """export * from './utils';
export * from './types';
const CONSTANT = "value";"""
    assert should_skip_javascript(content) is True


def test_export_with_braces():
    # Test export with braces - line 84
    content = """export { User, Config } from './types';
export { helper } from './utils';
const CONSTANT = "value";"""
    assert should_skip_javascript(content) is True


def test_default_exports_from_modules():
    # Test default exports from other modules - line 87
    content = """export { default as User } from './User';
export { default as Config } from './Config';
const CONSTANT = "value";"""
    assert should_skip_javascript(content) is True


def test_class_definition_closing():
    # Test class definition closing logic - lines 102-103
    # Empty class + constants = declarations only, should be skipped
    content = """class EmptyClass {
}
const CONSTANT = "value";"""
    assert should_skip_javascript(content) is True


def test_class_with_content():
    # Test content inside class definitions - line 106
    content = """class MyClass {
    constructor() {
        this.value = 42;
    }
}
const CONSTANT = "value";"""
    assert should_skip_javascript(content) is False


def test_multiline_type_definitions():
    # Test multi-line type definitions - lines 111-113
    content = """type User = {
    id: number;
    name: string;
};
const CONSTANT = "value";"""
    assert should_skip_javascript(content) is True


def test_enum_definitions():
    # Test enum definitions - lines 119-121
    content = """enum Status {
    Active = 1,
    Inactive = 2
}
const CONSTANT = "value";"""
    assert should_skip_javascript(content) is True


def test_interface_enum_closing():
    # Test interface/enum closing logic - lines 124-125
    content = """interface Config {
    timeout: number;
}
enum Status {
    Active
}
const CONSTANT = "value";"""
    assert should_skip_javascript(content) is True


def test_type_annotations():
    # Test type annotations - line 129
    content = """interface User {
    id: number;
    name?: string;
    email: string;
}
const CONSTANT = "value";"""
    assert should_skip_javascript(content) is True


def test_closing_braces_semicolon():
    # Test closing braces with semicolon - line 132
    content = """interface Config {
    timeout: number;
};
type Status = 'active' | 'inactive';
const CONSTANT = "value";"""
    assert should_skip_javascript(content) is True


def test_uppercase_constant_only():
    # Test to hit line 134: uppercase constant continue
    content = """const API_URL = "https://api.example.com";"""
    assert should_skip_javascript(content) is True


def test_regular_constant_only():
    # Test to hit line 145: regular constant continue (without function calls)
    content = """const flag = true;"""
    assert should_skip_javascript(content) is True


def test_multiline_type_definition():
    # Test lines 100-102: multi-line type definition opening
    content = """type User = {
    name: string;
    age: number;
}"""
    assert should_skip_javascript(content) is True


def test_interface_opening():
    # Test lines 104-106: interface opening detection
    content = """interface Config {
    timeout: number;
}"""
    assert should_skip_javascript(content) is True


def test_enum_opening():
    # Test lines 108-110: enum opening detection
    content = """enum Status {
    Active,
    Inactive
}"""
    assert should_skip_javascript(content) is True


def test_interface_and_enum_together():
    # Test interface and enum in same file
    content = """interface User {
    id: number;
}
enum Status {
    Active
}"""
    assert should_skip_javascript(content) is True


def test_template_literal_with_expressions():
    # Test template literals with expressions should NOT be skipped - has executable logic
    content = """const message = `Hello ${name}!`;
const greeting = `Welcome ${user.name}`;"""
    assert should_skip_javascript(content) is False


def test_closing_braces_with_semicolon():
    # Test line 121: closing braces with semicolon
    content = """interface Config {
    timeout: number;
};"""
    assert should_skip_javascript(content) is True


def test_uppercase_constant_detection():
    # Test lines 127-134: uppercase constant pattern
    content = 'const API_URL = "https://api.example.com";'
    assert should_skip_javascript(content) is True


def test_lowercase_literal_constant():
    # Test lines 136-143: lowercase constant with literal
    content = "const flag = true;"
    assert should_skip_javascript(content) is True


def test_interface_closing_line():
    # Test lines 114-115: specific interface closing
    content = """interface Config {
    timeout: number;
}
const API_URL = "test";"""
    assert should_skip_javascript(content) is True


def test_enum_closing_line():
    # Test lines 114-115: specific enum closing
    content = """enum Status {
    Active,
    Inactive
}
const MAX_SIZE = 100;"""
    assert should_skip_javascript(content) is True


def test_standalone_braces():
    # Test line 121: standalone closing braces
    content = """};
}"""
    assert should_skip_javascript(content) is True


def test_mixed_case_return_false():
    # Test line 145: force return False for non-matching patterns
    content = "const result = someFunction();"
    assert should_skip_javascript(content) is False


def test_class_closing_logic():
    # Test lines 91-92: class closing when in_class_definition is True
    content = """class MyClass {
}"""
    assert should_skip_javascript(content) is True


def test_interface_enum_closing_logic():
    # Test lines 114-115: interface/enum closing when in state
    content = """interface User {
    id: number;
}
enum Status {
    Active
}
const CONSTANT = "value";"""
    assert should_skip_javascript(content) is True


def test_type_annotation_pattern():
    # Test line 119: type annotation pattern with colon
    content = """interface Config {
    timeout?: number;
    retries: string;
}"""
    assert should_skip_javascript(content) is True


def test_standalone_closing_brace_semicolon():
    # Test line 122: standalone closing braces and semicolons
    content = """interface Config {
    timeout: number;
};
}
const value = "test";"""
    assert should_skip_javascript(content) is True


def test_multiline_template_literal():
    # Test lines 42->47, 44->46: multiline template literal start
    content = """const TEMPLATE = `multiline template
continues here
`;
const OTHER = "value";"""
    assert should_skip_javascript(content) is True


def test_empty_class_with_closing():
    # Test lines 91-92: empty class closing
    content = """class Empty {
}
const VALUE = "test";"""
    assert should_skip_javascript(content) is True


def test_interface_with_opening_brace():
    # Test lines 104->106: interface with opening brace
    content = """interface Config {
    name: string;
}"""
    assert should_skip_javascript(content) is True


def test_enum_with_opening_brace():
    # Test lines 108->110: enum with opening brace
    content = """enum Status {
    ACTIVE = 1,
    INACTIVE = 2
}"""
    assert should_skip_javascript(content) is True


def test_interface_enum_with_values():
    # Test interface/enum with assigned values
    content = """interface Config {
    value: number;
}
enum Status {
    ACTIVE = 1
}"""
    assert should_skip_javascript(content) is True


def test_type_annotations_with_optional():
    # Test type annotations with optional fields
    content = """interface Config {
    optional?: string;
    required: number;
}"""
    assert should_skip_javascript(content) is True


def test_closing_braces_only():
    # Test line 124: closing braces outside interface/enum
    content = """}
};
const VALUE = "test";"""
    assert should_skip_javascript(content) is True


def test_interface_without_opening_brace():
    # Test lines 106->108 negative case: interface without opening brace on same line
    content = """interface Config
{
    name: string;
}"""
    assert should_skip_javascript(content) is True


def test_enum_without_opening_brace():
    # Test lines 110->112 negative case: enum without opening brace on same line
    content = """enum Status
{
    ACTIVE = 1,
    INACTIVE = 2
}"""
    assert should_skip_javascript(content) is True


def test_type_annotations_outside_interface():
    # Test line 121: type annotations outside interface/enum context
    content = """name: string;
value: number;
const TEST = "value";"""
    assert should_skip_javascript(content) is True


def test_template_literal_single_backtick():
    # Test lines 42->47: template literal start (count == 1)
    content = """const TEMPLATE = `start
content here
end`;
const OTHER = "value";"""
    assert should_skip_javascript(content) is True


def test_template_literal_multiple_backticks():
    # Test opposite branch of line 42: template literal with multiple backticks (count != 1)
    content = """const TEMPLATE = `single line template`;
const OTHER = "value";"""
    assert should_skip_javascript(content) is True


def test_template_literal_with_empty_lines():
    # Test negative branch: template literal with empty lines inside
    content = """const TEMPLATE = `


`;
const OTHER = "value";"""
    assert should_skip_javascript(content) is True


def test_interface_multiline_closing():
    # Test interface with multiline structure to force lines 122-123
    content = """interface Config
{
    timeout: number;
    retries: number;
}
const API_URL = 'http://example.com';"""
    assert should_skip_javascript(content) is True


def test_interface_closing_flags():
    # Test to hit lines 122-123: setting flags to False inside interface
    content = """interface User {
    name: string;
}"""
    assert should_skip_javascript(content) is True


def test_standalone_closing_brace():
    # Test to hit line 128: standalone closing brace
    content = """}"""
    assert should_skip_javascript(content) is True


def test_closing_brace_with_semicolon():
    # Test to hit line 128: closing brace with semicolon
    content = """};"""
    assert should_skip_javascript(content) is True


def test_enum_multiline_closing():
    # Test enum with multiline structure to force lines 122-123
    content = """enum Status
{
    ACTIVE,
    INACTIVE,
    PENDING
}
const MAX_SIZE = 100;"""
    assert should_skip_javascript(content) is True
