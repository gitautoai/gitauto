from unittest.mock import patch
from utils.text.sort_imports_py import sort_python_imports


def test_sort_python_imports_basic():
    """Test basic Python import sorting."""
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
    result = sort_python_imports(content)
    # isort preserves comments but may place them semantically incorrectly
    assert result == expected


def test_sort_python_imports_empty():
    """Test empty Python content."""
    content = ""
    result = sort_python_imports(content)
    assert result == ""


def test_sort_python_imports_no_imports():
    """Test Python file with no imports."""
    content = """def hello():
    print('world')"""
    expected = """def hello():
    print('world')"""
    result = sort_python_imports(content)
    # Should return exactly the same content when no imports
    assert result == expected


def test_sort_python_imports_messy():
    """Test with a real messy Python file with unsorted imports."""
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

    result = sort_python_imports(messy_code)
    assert result == expected


def test_sort_python_imports_multiline():
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

    result = sort_python_imports(code)
    assert result == expected


def test_sort_python_imports_with_docstring():
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

    result = sort_python_imports(code)
    assert result == expected


def test_sort_python_imports_with_future():
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

    result = sort_python_imports(code)
    assert result == expected


def test_sort_python_imports_error_handling():
    """Test that sort_python_imports returns original content on error"""
    content = "import os\nimport sys\nfrom typing import Any"

    # Mock isort.code to raise an exception
    with patch(
        "utils.text.sort_imports_py.isort.code", side_effect=ValueError("Test error")
    ):
        result = sort_python_imports(content)
        # Should return original content unchanged on error
        assert result == content

    # Test with empty content - should handle gracefully
    assert sort_python_imports("") == ""


def test_sort_python_imports_failure_scenarios():
    """Test various isort failure scenarios"""
    # Test with malformed Python that might cause isort to fail
    malformed_content = "import os\nimport sys\nthis is not valid python import"

    # Even with malformed content, isort usually handles it, but if it fails,
    # we should get the original back
    result = sort_python_imports(malformed_content)
    # Either sorted or original, but never None or empty (unless input was empty)
    assert result is not None
    assert len(result) > 0
