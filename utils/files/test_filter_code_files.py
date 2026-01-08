from utils.files.filter_code_files import filter_code_files


def test_filter_code_files_empty_list():
    result = filter_code_files([])
    assert not result


def test_filter_code_files_code_files_only():
    filenames = [
        "main.py",
        "utils/helper.py",
        "src/app.js",
        "lib/module.rb",
        "package/file.go",
        "script.sh",
        "config.ini",
    ]
    result = filter_code_files(filenames)
    assert result == filenames


def test_filter_code_files_non_code_extensions():
    filenames = [
        "README.md",
        "notes.txt",
        "config.json",
        "data.xml",
        "settings.yml",
        "docker.yaml",
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
    ]
    result = filter_code_files(filenames)
    assert not result


def test_filter_code_files_test_patterns():
    filenames = [
        "test_main.py",
        "helper_test.py",
        "app.spec.js",
        "module.spec.rb",
        "tests/unit.py",
        "test/integration.py",
        "specs/behavior.py",
        "__tests__/component.js",
        "mock_data.py",
        "stub_service.py",
        "fixture_setup.py",
    ]
    result = filter_code_files(filenames)
    assert not result


def test_filter_code_files_mixed_files():
    filenames = [
        "main.py",
        "test_main.py",
        "README.md",
        "utils/helper.py",
        "utils/test_helper.py",
        "config.json",
        "src/app.js",
        "src/app.spec.js",
        "style.css",
        "script.sh",
    ]
    expected = ["main.py", "utils/helper.py", "src/app.js", "script.sh"]
    result = filter_code_files(filenames)
    assert result == expected


def test_filter_code_files_case_insensitive_test_patterns():
    filenames = [
        "TEST_main.py",
        "Helper_TEST.py",
        "App.SPEC.js",
        "TESTS/unit.py",
        "MOCK_data.py",
        "STUB_service.py",
        "FIXTURE_setup.py",
    ]
    result = filter_code_files(filenames)
    assert not result


def test_filter_code_files_partial_matches():
    filenames = [
        "testing.py",
        "contested.py",
        "specification.py",
        "mockingbird.py",
        "stubborn.py",
        "fixtures.py",
    ]
    result = filter_code_files(filenames)
    assert result == ["testing.py", "contested.py", "specification.py"]


def test_filter_code_files_edge_cases():
    filenames = [
        "",
        "file",
        "file.",
        ".hidden",
        "path/to/file.py",
        "very/long/path/to/deeply/nested/file.js",
    ]
    expected = [
        "",
        "file",
        "file.",
        ".hidden",
        "path/to/file.py",
        "very/long/path/to/deeply/nested/file.js",
    ]
    result = filter_code_files(filenames)
    assert result == expected


def test_filter_code_files_all_non_code_extensions():
    filenames = [
        f"file{ext}"
        for ext in [
            ".md",
            ".txt",
            ".json",
            ".xml",
            ".yml",
            ".yaml",
            ".csv",
            ".html",
            ".css",
            ".svg",
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".ico",
            ".pdf",
            ".lock",
            ".env",
        ]
    ]
    result = filter_code_files(filenames)
    assert not result


def test_filter_code_files_all_test_patterns():
    filenames = [
        "test_file.py",
        "file_test.py",
        "file.spec.py",
        "file.spec.js",
        "tests/file.py",
        "test/file.py",
        "specs/file.py",
        "__tests__/file.js",
        "mock_file.py",
        "stub_file.py",
        "fixture_file.py",
    ]
    result = filter_code_files(filenames)
    assert not result


def test_filter_code_files_complex_scenarios():
    filenames = [
        "src/main.py",
        "src/test_main.py.backup",
        "docs/README.md",
        "config/settings.json",
        "lib/utils.js",
        "tests/mock_data.json",
    ]
    expected = ["src/main.py", "lib/utils.js"]
    result = filter_code_files(filenames)
    assert result == expected
