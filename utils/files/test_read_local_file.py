import os

from utils.files.read_local_file import read_local_file


def test_reads_existing_file(tmp_path):
    file_path = os.path.join(tmp_path, "hello.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("hello world")
    result = read_local_file("hello.txt", base_dir=str(tmp_path))
    assert result == "hello world"


def test_reads_nested_file(tmp_path):
    os.makedirs(os.path.join(tmp_path, "src", "lib"), exist_ok=True)
    file_path = os.path.join(tmp_path, "src", "lib", "utils.py")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("def foo(): pass")
    result = read_local_file("src/lib/utils.py", base_dir=str(tmp_path))
    assert result == "def foo(): pass"


def test_returns_none_for_missing_file(tmp_path):
    result = read_local_file("nonexistent.py", base_dir=str(tmp_path))
    assert result is None


def test_returns_none_for_missing_dir():
    result = read_local_file("foo.py", base_dir="/nonexistent/path")
    assert result is None
