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
