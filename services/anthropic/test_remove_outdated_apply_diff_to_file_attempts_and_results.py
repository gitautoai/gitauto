# pylint: disable=too-many-lines

from unittest.mock import patch

from services.anthropic.remove_outdated_apply_diff_to_file_attempts_and_results import (
    remove_outdated_apply_diff_to_file_attempts_and_results,
)


def test_remove_outdated_apply_diff_to_file_attempts_and_results_empty_list():
    result = remove_outdated_apply_diff_to_file_attempts_and_results([])
    assert result == []


def test_remove_outdated_apply_diff_to_file_attempts_and_results_no_diff_results():
    messages = [
        {"role": "assistant", "content": "Hello"},
        {"role": "user", "content": [{"type": "text", "text": "Hi there"}]},
    ]
    result = remove_outdated_apply_diff_to_file_attempts_and_results(messages)
    assert result == messages


def test_remove_outdated_apply_diff_to_file_attempts_and_results_successful_diff_ignored():
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "diff applied to the file: test.py successfully by apply_diff_to_file().",
                }
            ],
        }
    ]
    result = remove_outdated_apply_diff_to_file_attempts_and_results(messages)
    # Successful diffs should be ignored (not deduplicated)
    assert result == messages


def test_remove_outdated_apply_diff_to_file_attempts_and_results_multiple_failed_same_file():
    failed_diff_content = 'diff partially applied to the file: test.py. But, some changes were rejected. Review rejected changes, modify the diff, and try again.\n\ndiff="--- a/test.py\\n+++ b/test.py\\n@@ -1,3 +1,3 @@\\n-old line\\n+new line"\n\nrej_text="Failed to apply patch"'

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": failed_diff_content,
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": failed_diff_content,
                }
            ],
        },
    ]
    result = remove_outdated_apply_diff_to_file_attempts_and_results(messages)

    expected = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "[Outdated failed diff for 'test.py' removed]",
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": failed_diff_content,
                }
            ],
        },
    ]

    assert result == expected


def test_remove_outdated_apply_diff_to_file_attempts_and_results_different_failed_files():
    failed_diff1 = 'diff partially applied to the file: test1.py. But, some changes were rejected. Review rejected changes, modify the diff, and try again.\n\ndiff="--- a/test1.py\\n+++ b/test1.py"\n\nrej_text="Failed"'
    failed_diff2 = 'diff partially applied to the file: test2.py. But, some changes were rejected. Review rejected changes, modify the diff, and try again.\n\ndiff="--- a/test2.py\\n+++ b/test2.py"\n\nrej_text="Failed"'

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": failed_diff1,
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": failed_diff2,
                }
            ],
        },
    ]
    result = remove_outdated_apply_diff_to_file_attempts_and_results(messages)

    expected = messages  # Both should remain unchanged since they're different files
    assert result == expected


def test_remove_outdated_apply_diff_to_file_attempts_and_results_mixed_content():
    failed_diff = 'diff partially applied to the file: utils.py. But, some changes were rejected. Review rejected changes, modify the diff, and try again.\n\ndiff="--- a/utils.py\\n+++ b/utils.py"\n\nrej_text="Failed"'

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Some text"},
                {
                    "type": "tool_result",
                    "content": failed_diff,
                },
            ],
        },
        {"role": "assistant", "content": "Processing..."},
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": failed_diff,
                },
                {"type": "text", "text": "More text"},
            ],
        },
    ]
    result = remove_outdated_apply_diff_to_file_attempts_and_results(messages)

    expected = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Some text"},
                {
                    "type": "tool_result",
                    "content": "[Outdated failed diff for 'utils.py' removed]",
                },
            ],
        },
        {"role": "assistant", "content": "Processing..."},
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": failed_diff,
                },
                {"type": "text", "text": "More text"},
            ],
        },
    ]
    assert result == expected


def test_remove_outdated_apply_diff_to_file_attempts_and_results_non_tool_result_content():
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "other",
                    "content": "diff applied to the file: test.py successfully by apply_diff_to_file().",
                }
            ],
        }
    ]
    result = remove_outdated_apply_diff_to_file_attempts_and_results(messages)

    # Should remain unchanged since it's not a tool_result
    assert result == messages


def test_remove_outdated_apply_diff_to_file_attempts_and_results_partial_match():
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "diff applied to the file: test.py but failed",
                }
            ],
        }
    ]
    result = remove_outdated_apply_diff_to_file_attempts_and_results(messages)

    # Should remain unchanged since it doesn't match the full pattern
    assert result == messages


def test_remove_outdated_apply_diff_to_file_attempts_and_results_three_failed_occurrences():
    failed_diff = 'diff partially applied to the file: main.py. But, some changes were rejected. Review rejected changes, modify the diff, and try again.\n\ndiff="--- a/main.py\\n+++ b/main.py"\n\nrej_text="Failed"'

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": failed_diff,
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": failed_diff,
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": failed_diff,
                }
            ],
        },
    ]
    result = remove_outdated_apply_diff_to_file_attempts_and_results(messages)

    expected = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "[Outdated failed diff for 'main.py' removed]",
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "[Outdated failed diff for 'main.py' removed]",
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": failed_diff,
                }
            ],
        },
    ]
    assert result == expected


def test_remove_outdated_apply_diff_to_file_attempts_and_results_preserves_other_tool_results():
    failed_diff = 'diff partially applied to the file: test.py. But, some changes were rejected. Review rejected changes, modify the diff, and try again.\n\ndiff="--- a/test.py\\n+++ b/test.py"\n\nrej_text="Failed"'

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers for your information.",
                },
                {
                    "type": "tool_result",
                    "content": failed_diff,
                },
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": failed_diff,
                }
            ],
        },
    ]
    result = remove_outdated_apply_diff_to_file_attempts_and_results(messages)

    expected = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "Opened file: 'test.py' with line numbers for your information.",
                },
                {
                    "type": "tool_result",
                    "content": "[Outdated failed diff for 'test.py' removed]",
                },
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": failed_diff,
                }
            ],
        },
    ]
    assert result == expected


def test_remove_outdated_apply_diff_to_file_attempts_and_results_failed_then_successful():
    failed_diff = 'diff partially applied to the file: test.py. But, some changes were rejected. Review rejected changes, modify the diff, and try again.\n\ndiff="--- a/test.py\\n+++ b/test.py"\n\nrej_text="Failed"'
    successful_diff = (
        "diff applied to the file: test.py successfully by apply_diff_to_file()."
    )

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": failed_diff,
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": successful_diff,
                }
            ],
        },
    ]
    result = remove_outdated_apply_diff_to_file_attempts_and_results(messages)

    expected = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "[Outdated failed diff for 'test.py' removed]",
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": successful_diff,
                }
            ],
        },
    ]
    assert result == expected


def test_remove_outdated_apply_diff_to_file_attempts_and_results_successful_then_failed():
    successful_diff = (
        "diff applied to the file: test.py successfully by apply_diff_to_file()."
    )
    failed_diff = 'diff partially applied to the file: test.py. But, some changes were rejected. Review rejected changes, modify the diff, and try again.\n\ndiff="--- a/test.py\\n+++ b/test.py"\n\nrej_text="Failed"'

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": successful_diff,
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": failed_diff,
                }
            ],
        },
    ]
    result = remove_outdated_apply_diff_to_file_attempts_and_results(messages)

    # When successful → failed, keep BOTH (successful is tiny, failed shows what went wrong)
    expected = messages
    assert result == expected


def test_remove_outdated_apply_diff_to_file_attempts_and_results_tool_use_then_failed():
    """Test that tool_use diffs are removed when followed by failed result"""
    diff_content = (
        "--- a/test.py\\n+++ b/test.py\\n@@ -1,3 +1,3 @@\\n-old line\\n+new line"
    )
    failed_diff = 'diff partially applied to the file: test.py. But, some changes were rejected. Review rejected changes, modify the diff, and try again.\n\ndiff="--- a/test.py\\n+++ b/test.py"\n\nrej_text="Failed"'

    messages = [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_123",
                    "name": "apply_diff_to_file",
                    "input": {
                        "file_path": "test.py",
                        "diff": diff_content,
                    },
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "toolu_123",
                    "content": failed_diff,
                }
            ],
        },
    ]
    result = remove_outdated_apply_diff_to_file_attempts_and_results(messages)

    expected = [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_123",
                    "name": "apply_diff_to_file",
                    "input": {
                        "file_path": "test.py",
                        "diff": "[Outdated diff input removed]",
                    },
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "toolu_123",
                    "content": failed_diff,
                }
            ],
        },
    ]
    assert result == expected


def test_remove_outdated_apply_diff_to_file_attempts_and_results_tool_use_then_successful():
    """Test that tool_use diffs are removed when followed by successful result"""
    diff_content = (
        "--- a/test.py\\n+++ b/test.py\\n@@ -1,3 +1,3 @@\\n-old line\\n+new line"
    )
    successful_diff = (
        "diff applied to the file: test.py successfully by apply_diff_to_file()."
    )

    messages = [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_123",
                    "name": "apply_diff_to_file",
                    "input": {
                        "file_path": "test.py",
                        "diff": diff_content,
                    },
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "toolu_123",
                    "content": successful_diff,
                }
            ],
        },
    ]
    result = remove_outdated_apply_diff_to_file_attempts_and_results(messages)

    expected = [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_123",
                    "name": "apply_diff_to_file",
                    "input": {
                        "file_path": "test.py",
                        "diff": "[Outdated diff input removed]",
                    },
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "toolu_123",
                    "content": successful_diff,
                }
            ],
        },
    ]
    assert result == expected


def test_remove_outdated_apply_diff_to_file_attempts_and_results_multiple_tool_use_same_file():
    """Test multiple tool_use diffs for the same file"""
    diff_content_1 = "--- a/test.py\\n+++ b/test.py\\n@@ -1,3 +1,3 @@\\n-old1\\n+new1"
    diff_content_2 = "--- a/test.py\\n+++ b/test.py\\n@@ -5,3 +5,3 @@\\n-old2\\n+new2"
    diff_content_3 = "--- a/test.py\\n+++ b/test.py\\n@@ -10,3 +10,3 @@\\n-old3\\n+new3"

    messages = [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_1",
                    "name": "apply_diff_to_file",
                    "input": {
                        "file_path": "test.py",
                        "diff": diff_content_1,
                    },
                }
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_2",
                    "name": "apply_diff_to_file",
                    "input": {
                        "file_path": "test.py",
                        "diff": diff_content_2,
                    },
                }
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_3",
                    "name": "apply_diff_to_file",
                    "input": {
                        "file_path": "test.py",
                        "diff": diff_content_3,
                    },
                }
            ],
        },
    ]
    result = remove_outdated_apply_diff_to_file_attempts_and_results(messages)

    expected = [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_1",
                    "name": "apply_diff_to_file",
                    "input": {
                        "file_path": "test.py",
                        "diff": "[Outdated diff input removed]",
                    },
                }
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_2",
                    "name": "apply_diff_to_file",
                    "input": {
                        "file_path": "test.py",
                        "diff": "[Outdated diff input removed]",
                    },
                }
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_3",
                    "name": "apply_diff_to_file",
                    "input": {
                        "file_path": "test.py",
                        "diff": diff_content_3,
                    },
                }
            ],
        },
    ]
    assert result == expected


def test_remove_outdated_apply_diff_to_file_attempts_and_results_tool_use_different_files():
    """Test tool_use diffs for different files should all be kept"""
    diff_content_1 = "--- a/file1.py\\n+++ b/file1.py\\n@@ -1,3 +1,3 @@\\n-old\\n+new"
    diff_content_2 = "--- a/file2.py\\n+++ b/file2.py\\n@@ -1,3 +1,3 @@\\n-old\\n+new"

    messages = [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_1",
                    "name": "apply_diff_to_file",
                    "input": {
                        "file_path": "file1.py",
                        "diff": diff_content_1,
                    },
                }
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_2",
                    "name": "apply_diff_to_file",
                    "input": {
                        "file_path": "file2.py",
                        "diff": diff_content_2,
                    },
                }
            ],
        },
    ]
    result = remove_outdated_apply_diff_to_file_attempts_and_results(messages)

    # Different files, so both should be kept
    expected = messages
    assert result == expected


def test_remove_outdated_apply_diff_to_file_attempts_and_results_tool_use_mixed_with_failed():
    """Test tool_use followed by failed, then another tool_use"""
    diff_content_1 = "--- a/test.py\\n+++ b/test.py\\n@@ -1,3 +1,3 @@\\n-old1\\n+new1"
    failed_diff = 'diff partially applied to the file: test.py. But, some changes were rejected. Review rejected changes, modify the diff, and try again.\n\ndiff="--- a/test.py\\n+++ b/test.py"\n\nrej_text="Failed"'
    diff_content_2 = "--- a/test.py\\n+++ b/test.py\\n@@ -1,3 +1,3 @@\\n-old2\\n+new2"

    messages = [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_1",
                    "name": "apply_diff_to_file",
                    "input": {
                        "file_path": "test.py",
                        "diff": diff_content_1,
                    },
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": failed_diff,
                }
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_2",
                    "name": "apply_diff_to_file",
                    "input": {
                        "file_path": "test.py",
                        "diff": diff_content_2,
                    },
                }
            ],
        },
    ]
    result = remove_outdated_apply_diff_to_file_attempts_and_results(messages)

    expected = [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_1",
                    "name": "apply_diff_to_file",
                    "input": {
                        "file_path": "test.py",
                        "diff": "[Outdated diff input removed]",
                    },
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "[Outdated failed diff removed]",
                }
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_2",
                    "name": "apply_diff_to_file",
                    "input": {
                        "file_path": "test.py",
                        "diff": diff_content_2,
                    },
                }
            ],
        },
    ]
    assert result == expected


def test_remove_outdated_apply_diff_to_file_attempts_and_results_tool_use_without_diff_field():
    """Test tool_use without diff field should be kept as-is"""
    messages = [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_1",
                    "name": "apply_diff_to_file",
                    "input": {
                        "file_path": "test.py",
                        # Missing diff field
                    },
                }
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_2",
                    "name": "apply_diff_to_file",
                    "input": {
                        "file_path": "test.py",
                        "diff": "--- a/test.py\\n+++ b/test.py",
                    },
                }
            ],
        },
    ]
    result = remove_outdated_apply_diff_to_file_attempts_and_results(messages)

    # First one has no diff field, so only its structure is preserved
    expected = messages
    assert result == expected


def test_remove_outdated_apply_diff_to_file_attempts_and_results_complex_pattern_1():
    """Test pattern: tool_use → failed → successful → tool_use"""
    diff_content_1 = "--- a/test.py\\n+++ b/test.py\\n@@ -1,3 +1,3 @@\\n-old1\\n+new1"
    failed_diff = 'diff partially applied to the file: test.py. But, some changes were rejected. Review rejected changes, modify the diff, and try again.\n\ndiff="--- a/test.py\\n+++ b/test.py"\n\nrej_text="Failed"'
    successful_diff = (
        "diff applied to the file: test.py successfully by apply_diff_to_file()."
    )
    diff_content_2 = "--- a/test.py\\n+++ b/test.py\\n@@ -5,3 +5,3 @@\\n-old2\\n+new2"

    messages = [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_1",
                    "name": "apply_diff_to_file",
                    "input": {"file_path": "test.py", "diff": diff_content_1},
                }
            ],
        },
        {
            "role": "user",
            "content": [{"type": "tool_result", "content": failed_diff}],
        },
        {
            "role": "user",
            "content": [{"type": "tool_result", "content": successful_diff}],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_2",
                    "name": "apply_diff_to_file",
                    "input": {"file_path": "test.py", "diff": diff_content_2},
                }
            ],
        },
    ]

    result = remove_outdated_apply_diff_to_file_attempts_and_results(messages)

    expected = [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_1",
                    "name": "apply_diff_to_file",
                    "input": {
                        "file_path": "test.py",
                        "diff": "[Outdated diff input removed]",
                    },
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": "[Outdated failed diff removed]",
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "content": successful_diff,
                }  # Keep successful (tiny)
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_2",
                    "name": "apply_diff_to_file",
                    "input": {
                        "file_path": "test.py",
                        "diff": diff_content_2,
                    },  # Keep latest
                }
            ],
        },
    ]
    assert result == expected


def test_remove_outdated_apply_diff_to_file_attempts_and_results_complex_pattern_2():
    """Test pattern with irrelevant content mixed in"""
    diff_content = "--- a/test.py\\n+++ b/test.py\\n@@ -1,3 +1,3 @@\\n-old\\n+new"
    failed_diff = 'diff partially applied to the file: test.py. But, some changes were rejected. Review rejected changes, modify the diff, and try again.\n\ndiff="--- a/test.py\\n+++ b/test.py"\n\nrej_text="Failed"'

    messages = [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_1",
                    "name": "get_file",  # Different tool
                    "input": {"file_path": "test.py"},
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {"type": "tool_result", "content": "File content here..."}  # Irrelevant
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_2",
                    "name": "apply_diff_to_file",
                    "input": {"file_path": "test.py", "diff": diff_content},
                }
            ],
        },
        {
            "role": "user",
            "content": [{"type": "tool_result", "content": failed_diff}],
        },
    ]

    result = remove_outdated_apply_diff_to_file_attempts_and_results(messages)

    # Only the diff-related content should be affected
    expected = [
        messages[0],  # Keep irrelevant tool_use
        messages[1],  # Keep irrelevant result
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_2",
                    "name": "apply_diff_to_file",
                    "input": {
                        "file_path": "test.py",
                        "diff": "[Outdated diff input removed]",
                    },
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {"type": "tool_result", "content": failed_diff}  # Keep latest failed
            ],
        },
    ]
    assert result == expected


def test_remove_outdated_apply_diff_to_file_attempts_and_results_interleaved_files():
    """Test pattern: file1 → file2 → file1 → file2 (interleaved)"""
    diff_1a = "--- a/file1.py\\n+++ b/file1.py\\n@@ -1,3 +1,3 @@\\n-1a\\n+new1a"
    diff_2a = "--- a/file2.py\\n+++ b/file2.py\\n@@ -1,3 +1,3 @@\\n-2a\\n+new2a"
    diff_1b = "--- a/file1.py\\n+++ b/file1.py\\n@@ -5,3 +5,3 @@\\n-1b\\n+new1b"
    diff_2b = "--- a/file2.py\\n+++ b/file2.py\\n@@ -5,3 +5,3 @@\\n-2b\\n+new2b"

    messages = [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_1",
                    "name": "apply_diff_to_file",
                    "input": {"file_path": "file1.py", "diff": diff_1a},
                }
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_2",
                    "name": "apply_diff_to_file",
                    "input": {"file_path": "file2.py", "diff": diff_2a},
                }
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_3",
                    "name": "apply_diff_to_file",
                    "input": {"file_path": "file1.py", "diff": diff_1b},
                }
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_4",
                    "name": "apply_diff_to_file",
                    "input": {"file_path": "file2.py", "diff": diff_2b},
                }
            ],
        },
    ]

    result = remove_outdated_apply_diff_to_file_attempts_and_results(messages)

    expected = [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_1",
                    "name": "apply_diff_to_file",
                    "input": {
                        "file_path": "file1.py",
                        "diff": "[Outdated diff input removed]",
                    },
                }
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_2",
                    "name": "apply_diff_to_file",
                    "input": {
                        "file_path": "file2.py",
                        "diff": "[Outdated diff input removed]",
                    },
                }
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_3",
                    "name": "apply_diff_to_file",
                    "input": {
                        "file_path": "file1.py",
                        "diff": diff_1b,
                    },  # Keep latest for file1
                }
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_4",
                    "name": "apply_diff_to_file",
                    "input": {
                        "file_path": "file2.py",
                        "diff": diff_2b,
                    },  # Keep latest for file2
                }
            ],
        },
    ]
    assert result == expected


def test_handles_exception_gracefully():
    # Test by mocking deepcopy to raise an exception

    messages = [{"role": "user", "content": []}]

    with patch("copy.deepcopy", side_effect=RuntimeError("Simulated failure")):
        result = remove_outdated_apply_diff_to_file_attempts_and_results(messages)
        # Should return original messages unchanged when exception occurs
        assert result == messages


def test_handles_runtime_exception():
    # Test by making dict access fail
    class BadDict(dict):
        def get(self, key, default=None):
            if key == "role":
                return "user"
            if key == "content":
                raise KeyError("Simulated KeyError")
            return default

    messages: list[dict] = [BadDict()]

    result = remove_outdated_apply_diff_to_file_attempts_and_results(messages)
    # Should return original messages unchanged when exception occurs
    assert result == messages
