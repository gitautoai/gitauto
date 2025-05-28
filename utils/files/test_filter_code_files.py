import pytest
from unittest.mock import patch
from utils.files.filter_code_files import filter_code_files


def test_filter_code_files_empty_list():
    result = filter_code_files([])
    assert result == []


def test_filter_code_files_only_code_files():
    filenames = [
        "main.py",
        "utils/helper.py",
        "src/app.js",
        "lib/module.rb",
        "package/file.go",
        "script.sh"
    ]
    result = filter_code_files(filenames)
    assert result == filenames


def test_filter_code_files_removes_non_code_extensions():
    filenames = [
        "main.py",
        "README.md",
        "config.json",
        "data.xml",
        "settings.yml",
        "config.yaml",
        "data.csv",
        "index.html",
        "style.css",
        "icon.svg",
        "image.png",
        "photo.jpg",
        "picture.jpeg",
        "animation.gif",
        "favicon.ico",
        "document.pdf",
        "package.lock",
        "environment.env",
        "notes.txt"
    ]
    result = filter_code_files(filenames)
    assert result == ["main.py"]


def test_filter_code_files_removes_test_patterns():
    filenames = [
        "main.py",
        "test_main.py",
        "main_test.py",
        "spec.py",
        "main.spec.py",
        "tests/helper.py",
        "test/utils.py",
        "specs/validation.py",
        "__tests__/component.py",
        "mock_data.py",
        "stub_service.py",
        "fixture_setup.py"
    ]
    result = filter_code_files(filenames)
    assert result == ["main.py"]


def test_filter_code_files_case_insensitive_test_patterns():
    filenames = [
        "main.py",
        "TEST_main.py",
        "Main_TEST.py",
        "SPEC.py",
        "main.SPEC.py",
        "TESTS/helper.py",
        "TEST/utils.py",
        "SPECS/validation.py",
        "__TESTS__/component.py",
        "MOCK_data.py",
        "STUB_service.py",
        "FIXTURE_setup.py"
    ]
    result = filter_code_files(filenames)
    assert result == ["main.py"]


def test_filter_code_files_mixed_valid_and_invalid():
    filenames = [
        "main.py",
        "utils.py",
        "test_main.py",
        "config.json",
        "helper.js",
        "README.md",
        "mock_data.py",
        "style.css"
    ]
    result = filter_code_files(filenames)
    assert result == ["main.py", "utils.py", "helper.js"]


def test_filter_code_files_all_filtered_out():
    filenames = [
        "test_main.py",
        "config.json",
        "README.md",
        "mock_data.py",
        "style.css"
    ]
    result = filter_code_files(filenames)
    assert result == []


def test_filter_code_files_with_exception():
    # Test that the function handles exceptions gracefully due to the @handle_exceptions decorator
    # The decorator should return the default_return_value (empty list) when an exception occurs
    # Patch the str.endswith method to raise an exception
    with patch.object(str, 'endswith', side_effect=Exception("Test exception")):
        result = filter_code_files(["main.py"])
        assert result == []  # Should return default_return_value=[] when exception occurs


def test_filter_code_files_partial_pattern_matches():
    filenames = [
        "main.py",
        "testing.py",
        "contest.py",
        "respect.py",
        "mockingbird.py",
        "stubborn.py",
        "fixtures.py"
    ]
    result = filter_code_files(filenames)
    assert result == ["main.py", "testing.py", "contest.py", "respect.py"]


def test_filter_code_files_edge_case_extensions():
    filenames = [
        "file.py",
        "file.PY",
        "file.Py",
        "file.pY"
    ]
    result = filter_code_files(filenames)
    assert result == filenames


def test_filter_code_files_single_file():
    result = filter_code_files(["main.py"])
    assert result == ["main.py"]
    
    result = filter_code_files(["test_main.py"])
    assert result == []


def test_filter_code_files_all_test_patterns():
    filenames = [
        "test_file.py",
        "file_test.py", 
        "spec.py",
        "file.spec.py",
        "tests/file.py",
        "test/file.py",
        "specs/file.py",
        "__tests__/file.py",
        "mock.py",
        "stub.py",
        "fixture.py"
    ]
    result = filter_code_files(filenames)
    assert result == []


def test_filter_code_files_all_non_code_extensions():
    filenames = [
        "file.md",
        "file.txt", 
        "file.json",
        "file.xml",
        "file.yml",
        "file.yaml",
        "file.csv",
        "file.html",
        "file.css",
        "file.svg",
        "file.png",
        "file.jpg",
        "file.jpeg",
        "file.gif",
        "file.ico",
        "file.pdf",
        "file.lock",
        "file.env"
    ]
    result = filter_code_files(filenames)
    assert result == []


def test_filter_code_files_complex_paths():
    filenames = [
        "src/main.py",
        "src/test_main.py",
        "lib/utils.js",
        "lib/mock_utils.js",
        "docs/README.md",
        "config/settings.json",
        "tests/unit/helper.py",
        "__tests__/integration/api.py"
    ]
    result = filter_code_files(filenames)
    assert result == ["src/main.py", "lib/utils.js"]


def test_filter_code_files_boundary_cases():
    filenames = [
        "test",
        "spec",
        "mock",
        "stub", 
        "fixture",
        "test.py",
        "spec.py",
        "mock.py",
        "stub.py",
        "fixture.py"
    ]
    result = filter_code_files(filenames)
    assert result == ["test", "spec", "mock", "stub", "fixture"]


def test_filter_code_files_mixed_extensions():
    filenames = [
        "script.py.md",  # Should be filtered out
        "readme.md.py",  # Should be kept
        "test.py.js",   # Should be kept
        "mock.js.py",   # Should be filtered out (mock prefix)
        "fixture.py.rb" # Should be kept
    ]
    result = filter_code_files(filenames)
    assert result == ["readme.md.py", "test.py.js", "fixture.py.rb"]


def test_filter_code_files_special_python_cases():
    filenames = [
        "mockup.py",      # Should be kept (not exact match)
        "stubbed.py",     # Should be kept (not exact match)
        "fixtures_db.py", # Should be kept (not exact match)
        "mock_test.py",   # Should be filtered out (mock_ prefix)
        "stub_data.py",   # Should be filtered out (stub_ prefix)
        "fixture_db.py",  # Should be filtered out (fixture_ prefix)
        "mock.py",        # Should be filtered out (exact match)
        "stub.py",        # Should be filtered out (exact match)
        "fixture.py"      # Should be filtered out (exact match)
    ]
    result = filter_code_files(filenames)
    assert result == [
        "mockup.py",
        "stubbed.py",
        "fixtures_db.py"
    ]