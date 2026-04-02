from utils.text.reset_command import create_reset_command_message


def test_basic_branch_name():
    # Verify the message contains the branch name in both git commands
    result = create_reset_command_message("feature/add-login")
    assert "git checkout feature/add-login" in result
    assert "git push --force-with-lease origin feature/add-login" in result


def test_message_contains_product_name():
    # Verify the message references GitAuto so users know the source
    result = create_reset_command_message("main")
    assert "GitAuto" in result


def test_message_structure():
    # Verify the full message matches the expected template exactly
    result = create_reset_command_message("my-branch")
    expected = """If GitAuto's commits are not satisfactory, you can reset to your original state from your local branch:

```bash
git checkout my-branch
git push --force-with-lease origin my-branch
```
"""
    assert result == expected


def test_branch_with_slashes():
    # Branches like feature/foo/bar with nested slashes must be preserved verbatim
    result = create_reset_command_message("feature/foo/bar")
    assert "git checkout feature/foo/bar" in result
    assert "git push --force-with-lease origin feature/foo/bar" in result


def test_branch_with_special_characters():
    # Branch names can contain dots, underscores, hyphens — all must pass through
    result = create_reset_command_message("fix/issue-123_v2.0")
    assert "git checkout fix/issue-123_v2.0" in result
    assert "git push --force-with-lease origin fix/issue-123_v2.0" in result


def test_empty_branch_name():
    # Empty string is technically valid input; verify it doesn't crash and produces the template
    result = create_reset_command_message("")
    assert "git checkout " in result
    assert "git push --force-with-lease origin " in result


def test_branch_with_spaces():
    # Spaces in branch names are unusual but the function should not crash
    result = create_reset_command_message("branch with spaces")
    assert "git checkout branch with spaces" in result
    assert "git push --force-with-lease origin branch with spaces" in result


def test_branch_with_unicode():
    # Unicode characters in branch names should be preserved
    result = create_reset_command_message("feature/日本語-branch")
    assert "git checkout feature/日本語-branch" in result
    assert "git push --force-with-lease origin feature/日本語-branch" in result


def test_branch_with_shell_injection_attempt():
    # Malicious input should be rendered literally, not interpreted
    malicious = "main; rm -rf /"
    result = create_reset_command_message(malicious)
    assert "git checkout main; rm -rf /" in result
    assert "git push --force-with-lease origin main; rm -rf /" in result


def test_branch_with_backtick_injection():
    # Backticks could cause command substitution in a shell; verify they pass through literally
    malicious = "main`whoami`"
    result = create_reset_command_message(malicious)
    assert "git checkout main`whoami`" in result


def test_branch_with_newline_injection():
    # Newlines in branch name could break the markdown code block structure
    result = create_reset_command_message("main\necho hacked")
    assert "git checkout main\necho hacked" in result


def test_very_long_branch_name():
    # Git allows branch names up to ~256 chars; verify no truncation
    long_name = "a" * 256
    result = create_reset_command_message(long_name)
    assert f"git checkout {long_name}" in result
    assert f"git push --force-with-lease origin {long_name}" in result


def test_return_type_is_string():
    # Verify the return type annotation is honored at runtime
    result = create_reset_command_message("main")
    assert isinstance(result, str)


def test_message_ends_with_newline():
    # The triple-quoted string should end with a trailing newline
    result = create_reset_command_message("main")
    assert result.endswith("\n")


def test_message_contains_bash_code_block():
    # Verify the markdown code fence is present for proper rendering
    result = create_reset_command_message("main")
    assert "```bash" in result
    assert result.count("```") == 2
