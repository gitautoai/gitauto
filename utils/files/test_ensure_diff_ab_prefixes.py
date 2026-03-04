from utils.files.ensure_diff_ab_prefixes import ensure_diff_ab_prefixes


def test_adds_ab_prefix_to_modification_diff():
    diff = "--- src/file.ts\n+++ src/file.ts\n@@ -1,1 +1,1 @@\n-old\n+new"
    result = ensure_diff_ab_prefixes(diff)
    assert "--- a/src/file.ts" in result
    assert "+++ b/src/file.ts" in result


def test_preserves_existing_ab_prefix():
    diff = "--- a/src/file.ts\n+++ b/src/file.ts\n@@ -1,1 +1,1 @@\n-old\n+new"
    result = ensure_diff_ab_prefixes(diff)
    assert result == diff


def test_preserves_dev_null():
    diff = "--- /dev/null\n+++ src/new_file.ts\n@@ -0,0 +1,1 @@\n+content"
    result = ensure_diff_ab_prefixes(diff)
    assert "--- /dev/null" in result
    assert "+++ b/src/new_file.ts" in result


def test_preserves_dev_null_for_deletion():
    diff = "--- src/old_file.ts\n+++ /dev/null\n@@ -1,1 +0,0 @@\n-content"
    result = ensure_diff_ab_prefixes(diff)
    assert "--- a/src/old_file.ts" in result
    assert "+++ /dev/null" in result


def test_does_not_modify_non_header_lines():
    diff = "--- /dev/null\n+++ b/file.ts\n@@ -0,0 +1,2 @@\n+--- some content\n++++ more content"
    result = ensure_diff_ab_prefixes(diff)
    assert result == diff


def test_new_file_with_nested_path_no_prefix():
    diff = "--- /dev/null\n+++ src/resolvers/getUserResolver.test.ts\n@@ -0,0 +1,1 @@\n+describe('test', () => {});"
    result = ensure_diff_ab_prefixes(diff)
    assert "--- /dev/null" in result
    assert "+++ b/src/resolvers/getUserResolver.test.ts" in result
