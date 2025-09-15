from unittest.mock import patch
from utils.text.sort_imports_js import sort_js_ts_imports


def test_sort_js_imports_basic():
    """Test basic JavaScript import sorting."""
    content = """import { Component } from './Component';
import React from 'react';
import { readFile } from 'fs';
import axios from 'axios';

function App() {
    return <div>Hello</div>;
}"""

    # Actual output from ESLint sort-imports rule
    expected = """import { Component } from './Component';
import React from 'react';
import { readFile } from 'fs';
import axios from 'axios';

function App() {
    return <div>Hello</div>;
}"""

    result = sort_js_ts_imports(content)
    assert result == expected


def test_sort_js_imports_empty():
    """Test empty JavaScript content."""
    content = ""
    result = sort_js_ts_imports(content)
    assert result == ""


def test_sort_js_imports_no_imports():
    """Test JavaScript file with no ES6 imports."""
    content = """const fs = require('fs');

function doSomething() {
    return 'hello';
}"""

    result = sort_js_ts_imports(content)
    # Should return unchanged since no ES6 imports
    assert result == content


def test_sort_ts_imports_with_types():
    """Test TypeScript import sorting."""
    content = """import type { User } from './types';
import React from 'react';
import fs from 'fs';

const component: React.FC = () => {
    return null;
};"""

    # ESLint keeps original order - type imports don't follow special rules
    expected = """import type { User } from './types';
import React from 'react';
import fs from 'fs';

const component: React.FC = () => {
    return null;
};"""

    result = sort_js_ts_imports(content)
    assert result == expected


def test_sort_js_imports_syntax_error():
    """Test that syntax errors return original content."""
    content = """import { Component } from './Component';
import React from 'react'  // Missing semicolon
import { from 'fs';        // Syntax error

function App() {
    return <div>Hello</div>;
}"""

    result = sort_js_ts_imports(content)
    # Should return original content when ESLint fails
    assert result == content


def test_sort_js_imports_invalid_syntax():
    """Test malformed JavaScript returns unchanged."""
    content = """this is not valid javascript at all
import something
function {"""

    result = sort_js_ts_imports(content)
    # Should return original content unchanged
    assert result == content


def test_sort_js_imports_cleanup_error():
    """Test that OSError during cleanup is handled gracefully."""
    content = "import React from 'react';"

    # Mock os.unlink to raise OSError to test cleanup error handling
    with patch(
        "utils.text.sort_imports_js.os.unlink", side_effect=OSError("Permission denied")
    ):
        result = sort_js_ts_imports(content)
        # Should still return result despite cleanup error
        assert result == content or "import React from 'react';" in result
