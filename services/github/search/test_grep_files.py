import os

from services.github.search.grep_files import grep_files


def _create_file(base: str, rel_path: str, content: str = ""):
    full = os.path.join(base, rel_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)


def test_finds_matching_files(tmp_path):
    _create_file(tmp_path, "src/main.py", "def hello_world(): pass")
    _create_file(tmp_path, "src/utils.py", "import os")
    result = grep_files("hello_world", str(tmp_path))
    assert "src/main.py" in result
    assert "src/utils.py" not in result


def test_returns_empty_for_no_matches(tmp_path):
    _create_file(tmp_path, "main.py", "def foo(): pass")
    result = grep_files("nonexistent", str(tmp_path))
    assert result == []


def test_returns_empty_for_missing_dir():
    result = grep_files("query", "/nonexistent/path")
    assert result == []


def test_excludes_node_modules(tmp_path):
    _create_file(tmp_path, "node_modules/pkg/index.js", "const unique_var = 1")
    _create_file(tmp_path, "src/app.js", "const unique_var = 2")
    result = grep_files("unique_var", str(tmp_path))
    assert "src/app.js" in result
    assert len(result) == 1


def test_finds_multiple_files(tmp_path):
    _create_file(tmp_path, "a.py", "shared = 1")
    _create_file(tmp_path, "b.py", "shared = 2")
    _create_file(tmp_path, "c.py", "shared = 3")
    result = grep_files("shared", str(tmp_path))
    assert len(result) == 3


def test_strips_dot_slash_prefix(tmp_path):
    _create_file(tmp_path, "main.py", "target_func = 1")
    result = grep_files("target_func", str(tmp_path))
    assert result == ["main.py"]
