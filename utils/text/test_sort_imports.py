import tempfile
import os
from unittest.mock import patch
from utils.text.sort_imports import sort_imports


def test_sort_imports_python():
    content = """# Local imports
from config import SOMETHING
# Third party imports
import requests
# Standard imports
import os
from typing import Any
"""
    expected = """# Local imports
# Standard imports
import os
from typing import Any

# Third party imports
import requests

from config import SOMETHING
"""
    result = sort_imports(content, "test.py")
    # isort preserves comments but may place them semantically incorrectly
    assert result == expected


def test_sort_imports_non_python():
    content = "const fs = require('fs');\nconst path = require('path');"
    result = sort_imports(content, "test.js")
    # Should return unchanged for now
    assert result == content


def test_sort_imports_empty():
    content = ""
    result = sort_imports(content, "test.py")
    assert result == ""


def test_sort_imports_no_imports():
    content = "def hello():\n    print('world')"
    expected = "def hello():\n    print('world')"
    result = sort_imports(content, "test.py")
    # Should return exactly the same content when no imports
    assert result == expected


def test_sort_imports_real_messy_file():
    """Test with a real messy Python file with unsorted imports"""
    messy_code = """#!/usr/bin/env python
from utils.error.handle_exceptions import handle_exceptions
import sys
from typing import Any, Dict, List
import requests
from config import GITHUB_API_URL, TIMEOUT
import os
from services.github.types.github_types import BaseArgs
import json
from pathlib import Path
import base64

class MyClass:
    def __init__(self):
        self.data = {}

def main():
    print("Hello World")
"""

    expected = """#!/usr/bin/env python
import base64
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import requests

from config import GITHUB_API_URL, TIMEOUT
from services.github.types.github_types import BaseArgs
from utils.error.handle_exceptions import handle_exceptions


class MyClass:
    def __init__(self):
        self.data = {}

def main():
    print("Hello World")
"""

    result = sort_imports(messy_code, "messy.py")
    assert result == expected


def test_sort_imports_multiline():
    """Test with multiline imports"""
    code = """
from services.openai.functions.functions import (
    TOOLS_TO_COMMIT_CHANGES,
    TOOLS_TO_EXPLORE_REPO,
    tools_to_call,
)
import os
from typing import Any, Dict, List

def foo():
    pass
"""

    expected = """
import os
from typing import Any, Dict, List

from services.openai.functions.functions import (TOOLS_TO_COMMIT_CHANGES,
                                                 TOOLS_TO_EXPLORE_REPO,
                                                 tools_to_call)


def foo():
    pass
"""

    result = sort_imports(code, "test.py")
    assert result == expected


def test_sort_imports_with_docstring():
    """Test file with module docstring remains at top"""
    code = '''"""Module docstring."""

from utils.test import something
import sys
import os

def main():
    pass
'''

    expected = '''"""Module docstring."""

import os
import sys

from utils.test import something


def main():
    pass
'''

    result = sort_imports(code, "test.py")
    assert result == expected


def test_sort_imports_with_future():
    """Test __future__ imports come first"""
    code = """
from config import SOMETHING
from __future__ import annotations
import os

def process():
    pass
"""

    expected = """
from __future__ import annotations

import os

from config import SOMETHING


def process():
    pass
"""

    result = sort_imports(code, "test.py")
    assert result == expected


def test_sort_imports_with_real_file():
    """Test with an actual file from our codebase"""
    # Create a temporary file to test file path handling
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        code = """
from config import TIMEOUT
import requests
import os
from typing import Any

def fetch_data():
    pass
"""
        f.write(code)
        temp_file = f.name

    try:
        expected = """
import os
from typing import Any

import requests

from config import TIMEOUT


def fetch_data():
    pass
"""
        result = sort_imports(code, temp_file)
        assert result == expected
    finally:
        os.unlink(temp_file)


def test_sort_imports_error_handling():
    """Test that sort_imports returns original content on error"""
    content = "import os\nimport sys\nfrom typing import Any"

    # Mock isort.code to raise an exception
    with patch(
        "utils.text.sort_imports.isort.code", side_effect=ValueError("Test error")
    ):
        result = sort_imports(content, "test.py")
        # Should return original content unchanged on error
        assert result == content

    # Test with empty content - should handle gracefully
    assert sort_imports("", "test.py") == ""

    # Test with non-Python file - should return unchanged
    js_content = "const fs = require('fs');"
    assert sort_imports(js_content, "test.js") == js_content


def test_sort_imports_with_isort_failure():
    """Test various isort failure scenarios"""
    # Test with malformed Python that might cause isort to fail
    malformed_content = "import os\nimport sys\nthis is not valid python import"

    # Even with malformed content, isort usually handles it, but if it fails,
    # we should get the original back
    result = sort_imports(malformed_content, "test.py")
    # Either sorted or original, but never None or empty (unless input was empty)
    assert result is not None
    assert len(result) > 0
def test_sort_imports_whitespace_only():
    """Test with whitespace-only content"""
    whitespace_content = "   \n  \t  \n   "
    result = sort_imports(whitespace_content, "test.py")
    # Should return original content for whitespace-only
    assert result == whitespace_content


def test_sort_imports_javascript_extensions():
    """Test all JavaScript/TypeScript file extensions return unchanged"""
    js_content = "import React from 'react';\nimport { useState } from 'react';"

    # Test .js extension
    result = sort_imports(js_content, "component.js")
    assert result == js_content
    # Test .jsx extension
    result = sort_imports(js_content, "component.jsx")
    assert result == js_content

    # Test .ts extension
    result = sort_imports(js_content, "component.ts")
    assert result == js_content

    # Test .tsx extension
    result = sort_imports(js_content, "component.tsx")
    assert result == js_content


def test_sort_imports_java_extension():
    """Test Java file extension returns unchanged"""
    java_content = """import java.util.List;
import java.io.File;
import java.util.ArrayList;

public class MyClass {
    public static void main(String[] args) {
        System.out.println("Hello World");
    }
}"""
    result = sort_imports(java_content, "MyClass.java")
    assert result == java_content


def test_sort_imports_unknown_extension():
    """Test unknown file extension returns unchanged"""
    content = "some random content\nwith multiple lines"

    result = sort_imports(content, "file.unknown")
    assert result == content

    result = sort_imports(content, "file.txt")
    assert result == content


def test_sort_imports_comments_only():
    """Test Python file with only comments"""
    comments_only = """# This is a comment
# Another comment
# Yet another comment"""
    result = sort_imports(comments_only, "test.py")
    assert result == comments_only

    result = sort_imports(content, "file")  # No extension
    assert result == content
