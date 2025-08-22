from utils.files.should_skip_javascript import should_skip_javascript


def test_export_only():
    # File with only export statements
    content = """export * from './lib';
export { default } from './main';
export { Button, Input } from './components';"""
    assert should_skip_javascript(content) is True


def test_constants_only():
    # Constants only
    content = """const MAX_SIZE = 100;
const API_URL = "https://api.example.com";
const CONFIG = { timeout: 5000 };
const COLORS = ["red", "blue", "green"];"""
    assert should_skip_javascript(content) is True


def test_typescript_types_only():
    # TypeScript interface and type definitions only
    content = """interface User {
    id: number;
    name: string;
    email?: string;
}

type Status = "active" | "inactive" | "pending";

enum Color {
    Red = "red",
    Green = "green",
    Blue = "blue"
}"""
    assert should_skip_javascript(content) is True


def test_imports_and_exports():
    # File with imports and exports only
    content = """import { Something } from './lib';
import React from 'react';

export * from './lib';
export { Something };
export default MyComponent;"""
    assert should_skip_javascript(content) is True


def test_commonjs_requires():
    # CommonJS require statements
    content = """const fs = require('fs');
const { spawn } = require('child_process');
const config = require('./config.json');

module.exports = {
    fs,
    spawn,
    config
};"""
    assert should_skip_javascript(content) is True


def test_mixed_constants_and_exports():
    # Mixed constants and exports
    content = """export * from './lib';

const MAX_SIZE = 100;
const API_URL = "https://api.com";

export { MAX_SIZE, API_URL };"""
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


def test_arrow_functions():
    # Arrow functions - should NOT be skipped
    content = """const MAX_SIZE = 100;

const calculate = () => MAX_SIZE * 2;
const multiply = (a, b) => a * b;"""
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


def test_typescript_with_logic():
    # TypeScript with function logic - should NOT be skipped
    content = """interface User {
    id: number;
    name: string;
}

function createUser(id: number, name: string): User {
    return { id, name };
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


def test_empty_file():
    # Empty content should be skipped
    assert should_skip_javascript("") is True


def test_whitespace_only():
    # File with only whitespace should be skipped
    content = """




    """
    assert should_skip_javascript(content) is True
