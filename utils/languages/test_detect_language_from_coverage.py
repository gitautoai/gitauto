# Standard imports
import json

# Third-party imports
import pytest

# Local imports
from services.coverages.parse_lcov_coverage import parse_lcov_coverage
from utils.languages.detect_language_from_coverage import detect_language_from_coverage


def test_detect_language_from_python_coverage():
    """Test language detection using real Python LCOV file"""
    with open("payloads/lcov/lcov-python-sample.info", "r", encoding="utf-8") as f:
        lcov_content = f.read()

    coverage_data = parse_lcov_coverage(lcov_content)
    detected_language = detect_language_from_coverage(coverage_data)

    assert detected_language == "python"


def test_detect_language_from_javascript_coverage():
    """Test language detection using real JavaScript LCOV file"""
    with open("payloads/lcov/lcov-javascript-sample.info", "r", encoding="utf-8") as f:
        lcov_content = f.read()

    coverage_data = parse_lcov_coverage(lcov_content)
    detected_language = detect_language_from_coverage(coverage_data)

    assert detected_language == "javascript"


def test_detect_language_with_mixed_extensions():
    """Test language detection with mixed file extensions"""
    mixed_coverage = [
        {"level": "file", "full_path": "src/main.py"},
        {"level": "file", "full_path": "src/utils.py"},
        {"level": "file", "full_path": "src/helper.js"},
        {"level": "directory", "full_path": "src"},
        {"level": "repository", "full_path": "All"},
    ]

    detected_language = detect_language_from_coverage(mixed_coverage)

    # Python files are more common (2 vs 1), so should return python
    assert detected_language == "python"


def test_detect_language_with_typescript():
    """Test language detection with TypeScript files"""
    ts_coverage = [
        {"level": "file", "full_path": "src/components/Button.tsx"},
        {"level": "file", "full_path": "src/utils/api.ts"},
        {"level": "file", "full_path": "src/types/user.ts"},
    ]

    detected_language = detect_language_from_coverage(ts_coverage)

    assert detected_language == "javascript"


def test_detect_language_with_no_files():
    """Test language detection with no file-level coverage"""
    no_files_coverage = [
        {"level": "directory", "full_path": "src"},
        {"level": "repository", "full_path": "All"},
    ]

    detected_language = detect_language_from_coverage(no_files_coverage)

    assert detected_language == "unknown"


def test_detect_language_with_empty_coverage():
    """Test language detection with empty coverage data"""
    detected_language = detect_language_from_coverage([])

    assert detected_language == "unknown"


def test_detect_language_with_unknown_extension():
    """Test language detection with unrecognized file extensions"""
    unknown_coverage = [
        {"level": "file", "full_path": "src/config.yaml"},
        {"level": "file", "full_path": "src/data.xml"},
    ]

    detected_language = detect_language_from_coverage(unknown_coverage)

    assert detected_language == "unknown"


def test_detect_language_with_multiple_same_extension():
    """Test language detection when all files have same extension"""
    java_coverage = [
        {"level": "file", "full_path": "src/Main.java"},
        {"level": "file", "full_path": "src/Utils.java"},
        {"level": "file", "full_path": "src/Controller.java"},
    ]

    detected_language = detect_language_from_coverage(java_coverage)

    assert detected_language == "java"
