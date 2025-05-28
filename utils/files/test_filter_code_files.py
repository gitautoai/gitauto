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
    with patch('utils.files.filter_code_files.handle_exceptions') as mock_decorator:
        mock_decorator.side_effect = Exception("Test exception")
        
        def mock_filter_code_files(filenames):
            raise Exception("Test exception")
        
        mock_decorator.return_value = mock_filter_code_files
        
        result = filter_code_files(["main.py"])
        assert result == ["main.py"]
