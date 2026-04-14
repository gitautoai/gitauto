import pytest

from utils.files.is_python_test_file import is_python_test_file


@pytest.mark.parametrize(
    "file_path, expected",
    [
        ("tests/test_utils.py", True),
        ("tests/test_client.py", True),
        ("src/test_helper.py", True),
        ("test_main.py", True),
        ("deep/nested/dir/test_foo.py", True),
        ("src/main.py", False),
        ("src/utils.py", False),
        ("README.md", False),
        ("config.json", False),
        ("src/index.test.ts", False),
        ("tests/conftest.py", False),
        ("tests/test_utils.txt", False),
        ("test_something/helper.py", False),
    ],
)
def test_is_python_test_file(file_path, expected):
    assert is_python_test_file(file_path) == expected
