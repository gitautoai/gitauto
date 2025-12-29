from utils.files.merge_test_file_headers import merge_test_file_headers


def test_merge_test_file_headers_pattern1_no_ignore_lines():
    file_content = """import { render } from '@testing-library/react';

describe('Test', () => {});
"""
    result = merge_test_file_headers(file_content, "Component.test.tsx")
    expected = """/* eslint-disable @typescript-eslint/no-unused-vars, @typescript-eslint/no-var-requires */
import { render } from '@testing-library/react';

describe('Test', () => {});
"""
    assert result == expected


def test_merge_test_file_headers_pattern2_has_some_ignore_lines():
    file_content = """/* eslint-disable no-console */
import { render } from '@testing-library/react';

describe('Test', () => {});
"""
    result = merge_test_file_headers(file_content, "Component.test.tsx")
    expected = """/* eslint-disable @typescript-eslint/no-unused-vars, @typescript-eslint/no-var-requires, no-console */
import { render } from '@testing-library/react';

describe('Test', () => {});
"""
    assert result == expected


def test_merge_test_file_headers_pattern3_already_has_exact_rules():
    file_content = """/* eslint-disable @typescript-eslint/no-unused-vars, @typescript-eslint/no-var-requires */
import { render } from '@testing-library/react';

describe('Test', () => {});
"""
    result = merge_test_file_headers(file_content, "Component.test.tsx")
    assert result == file_content


def test_merge_test_file_headers_python():
    file_content = """import pytest

def test_function():
    assert True
"""
    result = merge_test_file_headers(file_content, "test_module.py")
    expected = """# pylint: disable=redefined-outer-name, unused-argument
import pytest

def test_function():
    assert True
"""
    assert result == expected


def test_merge_test_file_headers_comma_separated_existing():
    file_content = """/* eslint-disable no-console, no-debugger */
import { render } from '@testing-library/react';
"""
    result = merge_test_file_headers(file_content, "Component.test.tsx")
    expected = """/* eslint-disable @typescript-eslint/no-unused-vars, @typescript-eslint/no-var-requires, no-console, no-debugger */
import { render } from '@testing-library/react';
"""
    assert result == expected


def test_merge_test_file_headers_non_test_file():
    file_content = """import React from 'react';
"""
    result = merge_test_file_headers(file_content, "Component.tsx")
    assert result == file_content


def test_merge_test_file_headers_invalid_input():
    result = merge_test_file_headers(None, "test.tsx")
    assert result is None

    result = merge_test_file_headers("content", None)
    assert result == "content"


def test_merge_test_file_headers_multiple_ignore_lines():
    file_content = """/* eslint-disable no-console */
import { render } from '@testing-library/react';
/* eslint-disable no-debugger */

describe('Test', () => {});
"""
    result = merge_test_file_headers(file_content, "Component.test.tsx")
    expected = """/* eslint-disable @typescript-eslint/no-unused-vars, @typescript-eslint/no-var-requires, no-console, no-debugger */
import { render } from '@testing-library/react';

describe('Test', () => {});
"""
    assert result == expected


def test_merge_test_file_headers_has_extra_rules():
    file_content = """/* eslint-disable @typescript-eslint/no-unused-vars, @typescript-eslint/no-var-requires, no-console, no-debugger */
import { render } from '@testing-library/react';

describe('Test', () => {});
"""
    result = merge_test_file_headers(file_content, "Component.test.tsx")
    assert result == file_content


def test_merge_test_file_headers_javascript():
    file_content = """const render = require('@testing-library/react').render;

describe('Test', () => {});
"""
    result = merge_test_file_headers(file_content, "Component.test.js")
    expected = """/* eslint-disable no-unused-vars */
const render = require('@testing-library/react').render;

describe('Test', () => {});
"""
    assert result == expected


def test_merge_test_file_headers_php():
    file_content = r"""<?php
use PHPUnit\Framework\TestCase;

class MyTest extends TestCase {
    public function testSomething() {
        $this->assertTrue(true);
    }
}
"""
    result = merge_test_file_headers(file_content, "MyTest.php")
    expected = r"""// phpcs:disable unused-variable
<?php
use PHPUnit\Framework\TestCase;

class MyTest extends TestCase {
    public function testSomething() {
        $this->assertTrue(true);
    }
}
"""
    assert result == expected
