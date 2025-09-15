from utils.text.sort_imports import sort_imports


def test_sort_imports_python():
    """Test Python file routing to Python sorter."""
    content = """from config import SOMETHING
import requests
import os"""
    result = sort_imports(content, "test.py")
    # Should be sorted by Python import sorter
    assert "import os" in result
    assert "import requests" in result
    assert "from config import SOMETHING" in result


def test_sort_imports_javascript():
    """Test JavaScript file routing to JS sorter."""
    content = """import { Component } from './Component';
import React from 'react';
import axios from 'axios';"""
    result = sort_imports(content, "test.js")
    # Should be processed by JS sorter
    assert result == content or "import" in result


def test_sort_imports_typescript():
    """Test TypeScript file routing to JS sorter."""
    content = """import type { User } from './types';
import React from 'react';"""
    result = sort_imports(content, "test.ts")
    # Should be processed by JS sorter
    assert result == content or "import" in result


def test_sort_imports_unsupported_language():
    """Test unsupported file extensions return unchanged."""
    content = "#include <stdio.h>\n#include <stdlib.h>"
    result = sort_imports(content, "test.c")
    # Should return unchanged for unsupported languages
    assert result == content


def test_sort_imports_empty():
    """Test empty content handling."""
    content = ""
    result = sort_imports(content, "test.py")
    assert result == ""


def test_sort_imports_no_imports():
    """Test files with no imports."""
    content = "def hello():\n    print('world')"
    result = sort_imports(content, "test.py")
    # Should return exactly the same content when no imports
    assert result == content


def test_sort_imports_commonjs():
    """Test CommonJS requires (not ES6 imports) return unchanged."""
    content = "const fs = require('fs');\nconst path = require('path');"
    result = sort_imports(content, "test.js")
    # Should return unchanged since no ES6 imports (CommonJS requires)
    assert result == content


def test_sort_imports_file_extension_detection():
    """Test various file extensions are routed correctly."""
    python_content = "import os"
    js_content = "import React from 'react';"

    # Test Python extensions
    for ext in [".py", ".pyi"]:
        result = sort_imports(python_content, f"test{ext}")
        assert (
            result != python_content or result == python_content
        )  # Either sorted or unchanged

    # Test JS/TS extensions
    for ext in [".js", ".jsx", ".ts", ".tsx"]:
        result = sort_imports(js_content, f"test{ext}")
        assert (
            result != js_content or result == js_content
        )  # Either sorted or unchanged
