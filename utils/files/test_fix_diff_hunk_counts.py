from utils.files.fix_diff_hunk_counts import fix_diff_hunk_counts


def test_correct_counts_unchanged():
    diff = (
        "--- a/file.py\n"
        "+++ b/file.py\n"
        "@@ -1,3 +1,3 @@\n"
        " line1\n"
        "-old\n"
        "+new\n"
        " line3\n"
    )
    result = fix_diff_hunk_counts(diff)
    assert result == diff


def test_overcounted_plus_lines_fixed():
    # Header claims +1,5 but only 3 addition lines exist
    diff = (
        "--- a/file.py\n"
        "+++ b/file.py\n"
        "@@ -1,2 +1,5 @@\n"
        " context\n"
        "-removed\n"
        "+added1\n"
        "+added2\n"
        "+added3\n"
    )
    result = fix_diff_hunk_counts(diff)
    assert "@@ -1,2 +1,4 @@" in result


def test_undercounted_minus_lines_fixed():
    # Header claims -1,1 but there are 2 removal lines + 1 context
    diff = (
        "--- a/file.py\n"
        "+++ b/file.py\n"
        "@@ -1,1 +1,1 @@\n"
        " context\n"
        "-removed1\n"
        "-removed2\n"
        "+added\n"
    )
    result = fix_diff_hunk_counts(diff)
    assert "@@ -1,3 +1,2 @@" in result


def test_multiple_hunks():
    diff = (
        "--- a/file.py\n"
        "+++ b/file.py\n"
        "@@ -1,2 +1,2 @@\n"
        " ctx\n"
        "-old1\n"
        "+new1\n"
        "@@ -10,1 +10,3 @@\n"
        "+add1\n"
        "+add2\n"
    )
    result = fix_diff_hunk_counts(diff)
    assert "@@ -1,2 +1,2 @@" in result
    assert "@@ -10,0 +10,2 @@" in result


def test_deletion_only_hunk():
    diff = (
        "--- a/file.py\n"
        "+++ b/file.py\n"
        "@@ -1,3 +1,0 @@\n"
        "-line1\n"
        "-line2\n"
        "-line3\n"
    )
    result = fix_diff_hunk_counts(diff)
    assert "@@ -1,3 +1,0 @@" in result


def test_addition_only_hunk():
    diff = (
        "--- a/file.py\n"
        "+++ b/file.py\n"
        "@@ -1,0 +1,2 @@\n"
        "+new1\n"
        "+new2\n"
    )
    result = fix_diff_hunk_counts(diff)
    assert "@@ -1,0 +1,2 @@" in result


def test_new_file_diff():
    diff = (
        "--- /dev/null\n"
        "+++ b/newfile.py\n"
        "@@ -0,0 +1,10 @@\n"
        "+line1\n"
        "+line2\n"
        "+line3\n"
    )
    result = fix_diff_hunk_counts(diff)
    assert "@@ -0,0 +1,3 @@" in result


def test_preserves_function_name_after_header():
    diff = (
        "--- a/file.py\n"
        "+++ b/file.py\n"
        "@@ -10,3 +10,3 @@ def my_function():\n"
        " ctx\n"
        "-old\n"
        "+new\n"
    )
    result = fix_diff_hunk_counts(diff)
    assert "@@ -10,2 +10,2 @@ def my_function():" in result


def test_no_hunk_header_returns_unchanged():
    text = "not a diff at all\njust some text\n"
    result = fix_diff_hunk_counts(text)
    assert result == text


def test_no_newline_at_end_of_file_marker():
    diff = (
        "--- a/file.py\n"
        "+++ b/file.py\n"
        "@@ -1,2 +1,2 @@\n"
        "-old\n"
        "+new\n"
        "\\ No newline at end of file\n"
    )
    result = fix_diff_hunk_counts(diff)
    # The "\ No newline" marker should not count as a line
    assert "@@ -1,1 +1,1 @@" in result


def test_large_overcounted_hunk():
    # Simulates the real-world LLM error: header says +26,138 but only 130 + lines
    additions = "".join(f"+line{i}\n" for i in range(130))
    diff = (
        "--- a/big.py\n"
        "+++ b/big.py\n"
        f"@@ -26,5 +26,138 @@\n"
        " ctx1\n"
        " ctx2\n"
        "-old1\n"
        "-old2\n"
        "-old3\n"
        f"{additions}"
    )
    result = fix_diff_hunk_counts(diff)
    # old_count = 2 context + 3 removals = 5
    # new_count = 2 context + 130 additions = 132
    assert "@@ -26,5 +26,132 @@" in result
