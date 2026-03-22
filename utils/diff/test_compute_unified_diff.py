from utils.diff.compute_unified_diff import compute_unified_diff


def test_returns_diff_for_changed_content():
    old = "line 1\nline 2\nline 3\n"
    new = "line 1\nmodified\nline 3\n"
    result = compute_unified_diff(old, new, "test.py")
    assert "-line 2\n" in result
    assert "+modified\n" in result


def test_returns_empty_for_identical_content():
    content = "line 1\nline 2\n"
    result = compute_unified_diff(content, content, "test.py")
    assert result == ""


def test_includes_file_path_in_header():
    old = "old\n"
    new = "new\n"
    result = compute_unified_diff(old, new, "src/app.ts")
    assert "src/app.ts" in result
