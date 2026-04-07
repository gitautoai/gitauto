# pylint: disable=too-many-lines
# pyright: reportIndexIssue=false, reportArgumentType=false

import json
from pathlib import Path
from typing import cast
from unittest.mock import patch

from anthropic.types import MessageParam

from services.claude.remove_outdated_file_edit_attempts import (
    remove_outdated_file_edit_attempts,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_remove_outdated_file_edit_attempts_empty_list():
    result = remove_outdated_file_edit_attempts([])
    assert not result


def test_remove_outdated_file_edit_attempts_no_diff_results():
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {"role": "assistant", "content": "Hello"},
            {"role": "user", "content": [{"type": "text", "text": "Hi there"}]},
        ],
    )
    result = remove_outdated_file_edit_attempts(messages)
    assert result == messages


def test_remove_outdated_file_edit_attempts_successful_diff_ignored():
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "content": "diff applied to the file: test.py successfully by apply_diff_to_file().",
                    }
                ],
            }
        ],
    )
    result = remove_outdated_file_edit_attempts(messages)
    # Successful diffs should be ignored (not deduplicated)
    assert result == messages


def test_remove_outdated_file_edit_attempts_multiple_failed_same_file():
    failed_diff_content = 'diff partially applied to the file: test.py. But, some changes were rejected. Review rejected changes, modify the diff, and try again.\n\ndiff="--- a/test.py\\n+++ b/test.py\\n@@ -1,3 +1,3 @@\\n-old line\\n+new line"\n\nrej_text="Failed to apply patch"'

    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
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
        ],
    )
    result = remove_outdated_file_edit_attempts(messages)

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


def test_remove_outdated_file_edit_attempts_different_failed_files():
    failed_diff1 = 'diff partially applied to the file: test1.py. But, some changes were rejected. Review rejected changes, modify the diff, and try again.\n\ndiff="--- a/test1.py\\n+++ b/test1.py"\n\nrej_text="Failed"'
    failed_diff2 = 'diff partially applied to the file: test2.py. But, some changes were rejected. Review rejected changes, modify the diff, and try again.\n\ndiff="--- a/test2.py\\n+++ b/test2.py"\n\nrej_text="Failed"'

    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
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
        ],
    )
    result = remove_outdated_file_edit_attempts(messages)

    expected = messages  # Both should remain unchanged since they're different files
    assert result == expected


def test_remove_outdated_file_edit_attempts_mixed_content():
    failed_diff = 'diff partially applied to the file: utils.py. But, some changes were rejected. Review rejected changes, modify the diff, and try again.\n\ndiff="--- a/utils.py\\n+++ b/utils.py"\n\nrej_text="Failed"'

    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
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
        ],
    )
    result = remove_outdated_file_edit_attempts(messages)

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


def test_remove_outdated_file_edit_attempts_non_tool_result_content():
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {
                "role": "user",
                "content": [
                    {
                        "type": "other",
                        "content": "diff applied to the file: test.py successfully by apply_diff_to_file().",
                    }
                ],
            }
        ],
    )
    result = remove_outdated_file_edit_attempts(messages)

    # Should remain unchanged since it's not a tool_result
    assert result == messages


def test_remove_outdated_file_edit_attempts_partial_match():
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "content": "diff applied to the file: test.py but failed",
                    }
                ],
            }
        ],
    )
    result = remove_outdated_file_edit_attempts(messages)

    # Should remain unchanged since it doesn't match the full pattern
    assert result == messages


def test_remove_outdated_file_edit_attempts_three_failed_occurrences():
    failed_diff = 'diff partially applied to the file: main.py. But, some changes were rejected. Review rejected changes, modify the diff, and try again.\n\ndiff="--- a/main.py\\n+++ b/main.py"\n\nrej_text="Failed"'

    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
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
        ],
    )
    result = remove_outdated_file_edit_attempts(messages)

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


def test_remove_outdated_file_edit_attempts_preserves_other_tool_results():
    failed_diff = 'diff partially applied to the file: test.py. But, some changes were rejected. Review rejected changes, modify the diff, and try again.\n\ndiff="--- a/test.py\\n+++ b/test.py"\n\nrej_text="Failed"'

    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
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
        ],
    )
    result = remove_outdated_file_edit_attempts(messages)

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


def test_remove_outdated_file_edit_attempts_failed_then_successful():
    failed_diff = 'diff partially applied to the file: test.py. But, some changes were rejected. Review rejected changes, modify the diff, and try again.\n\ndiff="--- a/test.py\\n+++ b/test.py"\n\nrej_text="Failed"'
    successful_diff = (
        "diff applied to the file: test.py successfully by apply_diff_to_file()."
    )

    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
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
        ],
    )
    result = remove_outdated_file_edit_attempts(messages)

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


def test_remove_outdated_file_edit_attempts_successful_then_failed():
    successful_diff = (
        "diff applied to the file: test.py successfully by apply_diff_to_file()."
    )
    failed_diff = 'diff partially applied to the file: test.py. But, some changes were rejected. Review rejected changes, modify the diff, and try again.\n\ndiff="--- a/test.py\\n+++ b/test.py"\n\nrej_text="Failed"'

    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
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
        ],
    )
    result = remove_outdated_file_edit_attempts(messages)

    # When successful → failed, keep BOTH (successful is tiny, failed shows what went wrong)
    expected = messages
    assert result == expected


def test_remove_outdated_file_edit_attempts_tool_use_then_failed():
    """Test that tool_use diffs are removed when followed by failed result"""
    diff_content = (
        "--- a/test.py\\n+++ b/test.py\\n@@ -1,3 +1,3 @@\\n-old line\\n+new line"
    )
    failed_diff = 'diff partially applied to the file: test.py. But, some changes were rejected. Review rejected changes, modify the diff, and try again.\n\ndiff="--- a/test.py\\n+++ b/test.py"\n\nrej_text="Failed"'

    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
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
        ],
    )
    result = remove_outdated_file_edit_attempts(messages)

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


def test_remove_outdated_file_edit_attempts_tool_use_then_successful():
    """Test that tool_use diffs are removed when followed by successful result"""
    diff_content = (
        "--- a/test.py\\n+++ b/test.py\\n@@ -1,3 +1,3 @@\\n-old line\\n+new line"
    )
    successful_diff = (
        "diff applied to the file: test.py successfully by apply_diff_to_file()."
    )

    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
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
        ],
    )
    result = remove_outdated_file_edit_attempts(messages)

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


def test_remove_outdated_file_edit_attempts_multiple_tool_use_same_file():
    """Test multiple tool_use diffs for the same file"""
    diff_content_1 = "--- a/test.py\\n+++ b/test.py\\n@@ -1,3 +1,3 @@\\n-old1\\n+new1"
    diff_content_2 = "--- a/test.py\\n+++ b/test.py\\n@@ -5,3 +5,3 @@\\n-old2\\n+new2"
    diff_content_3 = "--- a/test.py\\n+++ b/test.py\\n@@ -10,3 +10,3 @@\\n-old3\\n+new3"

    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
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
        ],
    )
    result = remove_outdated_file_edit_attempts(messages)

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


def test_remove_outdated_file_edit_attempts_tool_use_different_files():
    """Test tool_use diffs for different files should all be kept"""
    diff_content_1 = "--- a/file1.py\\n+++ b/file1.py\\n@@ -1,3 +1,3 @@\\n-old\\n+new"
    diff_content_2 = "--- a/file2.py\\n+++ b/file2.py\\n@@ -1,3 +1,3 @@\\n-old\\n+new"

    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
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
        ],
    )
    result = remove_outdated_file_edit_attempts(messages)

    # Different files, so both should be kept
    expected = messages
    assert result == expected


def test_remove_outdated_file_edit_attempts_tool_use_mixed_with_failed():
    """Test tool_use followed by failed, then another tool_use"""
    diff_content_1 = "--- a/test.py\\n+++ b/test.py\\n@@ -1,3 +1,3 @@\\n-old1\\n+new1"
    failed_diff = 'diff partially applied to the file: test.py. But, some changes were rejected. Review rejected changes, modify the diff, and try again.\n\ndiff="--- a/test.py\\n+++ b/test.py"\n\nrej_text="Failed"'
    diff_content_2 = "--- a/test.py\\n+++ b/test.py\\n@@ -1,3 +1,3 @@\\n-old2\\n+new2"

    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
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
        ],
    )
    result = remove_outdated_file_edit_attempts(messages)

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


def test_remove_outdated_file_edit_attempts_tool_use_without_diff_field():
    """Test tool_use without diff field should be kept as-is"""
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
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
        ],
    )
    result = remove_outdated_file_edit_attempts(messages)

    # First one has no diff field, so only its structure is preserved
    expected = messages
    assert result == expected


def test_remove_outdated_file_edit_attempts_complex_pattern_1():
    """Test pattern: tool_use → failed → successful → tool_use"""
    diff_content_1 = "--- a/test.py\\n+++ b/test.py\\n@@ -1,3 +1,3 @@\\n-old1\\n+new1"
    failed_diff = 'diff partially applied to the file: test.py. But, some changes were rejected. Review rejected changes, modify the diff, and try again.\n\ndiff="--- a/test.py\\n+++ b/test.py"\n\nrej_text="Failed"'
    successful_diff = (
        "diff applied to the file: test.py successfully by apply_diff_to_file()."
    )
    diff_content_2 = "--- a/test.py\\n+++ b/test.py\\n@@ -5,3 +5,3 @@\\n-old2\\n+new2"

    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
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
        ],
    )

    result = remove_outdated_file_edit_attempts(messages)

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


def test_remove_outdated_file_edit_attempts_complex_pattern_2():
    """Test pattern with irrelevant content mixed in"""
    diff_content = "--- a/test.py\\n+++ b/test.py\\n@@ -1,3 +1,3 @@\\n-old\\n+new"
    failed_diff = 'diff partially applied to the file: test.py. But, some changes were rejected. Review rejected changes, modify the diff, and try again.\n\ndiff="--- a/test.py\\n+++ b/test.py"\n\nrej_text="Failed"'

    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
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
                    {
                        "type": "tool_result",
                        "content": "File content here...",
                    }  # Irrelevant
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
        ],
    )

    result = remove_outdated_file_edit_attempts(messages)

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


def test_remove_outdated_file_edit_attempts_interleaved_files():
    """Test pattern: file1 → file2 → file1 → file2 (interleaved)"""
    diff_1a = "--- a/file1.py\\n+++ b/file1.py\\n@@ -1,3 +1,3 @@\\n-1a\\n+new1a"
    diff_2a = "--- a/file2.py\\n+++ b/file2.py\\n@@ -1,3 +1,3 @@\\n-2a\\n+new2a"
    diff_1b = "--- a/file1.py\\n+++ b/file1.py\\n@@ -5,3 +5,3 @@\\n-1b\\n+new1b"
    diff_2b = "--- a/file2.py\\n+++ b/file2.py\\n@@ -5,3 +5,3 @@\\n-2b\\n+new2b"

    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
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
        ],
    )

    result = remove_outdated_file_edit_attempts(messages)

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
    # Test by mocking enumerate to raise an exception during first pass

    messages: list[MessageParam] = cast(
        list[MessageParam], [{"role": "user", "content": []}]
    )

    with patch(
        "services.claude.remove_outdated_file_edit_attempts.enumerate",
        side_effect=RuntimeError("Simulated failure"),
    ):
        result = remove_outdated_file_edit_attempts(messages)
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

    messages: list[MessageParam] = cast(list[MessageParam], [BadDict()])

    result = remove_outdated_file_edit_attempts(messages)
    # Should return original messages unchanged when exception occurs
    assert result == messages


def test_search_and_replace_multiple_same_file():
    """Older search_and_replace for same file gets pruned, latest kept."""
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_1",
                        "name": "search_and_replace",
                        "input": {
                            "file_path": "test.py",
                            "old_string": "old_code_1",
                            "new_string": "new_code_1",
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
                        "name": "search_and_replace",
                        "input": {
                            "file_path": "test.py",
                            "old_string": "old_code_2",
                            "new_string": "new_code_2",
                        },
                    }
                ],
            },
        ],
    )
    result = remove_outdated_file_edit_attempts(messages)

    expected = [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_1",
                    "name": "search_and_replace",
                    "input": {
                        "file_path": "test.py",
                        "old_string": "[Outdated search text removed]",
                        "new_string": "[Outdated replacement text removed]",
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
                    "name": "search_and_replace",
                    "input": {
                        "file_path": "test.py",
                        "old_string": "old_code_2",
                        "new_string": "new_code_2",
                    },
                }
            ],
        },
    ]
    assert result == expected


def test_search_and_replace_different_files():
    """search_and_replace for different files are both kept."""
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_1",
                        "name": "search_and_replace",
                        "input": {
                            "file_path": "file1.py",
                            "old_string": "old1",
                            "new_string": "new1",
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
                        "name": "search_and_replace",
                        "input": {
                            "file_path": "file2.py",
                            "old_string": "old2",
                            "new_string": "new2",
                        },
                    }
                ],
            },
        ],
    )
    result = remove_outdated_file_edit_attempts(messages)

    # Different files, both should be kept unchanged
    assert result == messages


def test_search_and_replace_mixed_with_apply_diff():
    """Cross-tool pruning: apply_diff followed by search_and_replace for same file."""
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_1",
                        "name": "apply_diff_to_file",
                        "input": {
                            "file_path": "test.py",
                            "diff": "--- a/test.py\n+++ b/test.py\n@@ -1 +1 @@\n-old\n+new",
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
                        "name": "search_and_replace",
                        "input": {
                            "file_path": "test.py",
                            "old_string": "old_code",
                            "new_string": "new_code",
                        },
                    }
                ],
            },
        ],
    )
    result = remove_outdated_file_edit_attempts(messages)

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
                    "name": "search_and_replace",
                    "input": {
                        "file_path": "test.py",
                        "old_string": "old_code",
                        "new_string": "new_code",
                    },
                }
            ],
        },
    ]
    assert result == expected


def test_tool_result_stripped_for_outdated_search_and_replace():
    """Test that tool_results for search_and_replace are stripped when outdated via tool_use_id."""
    big_result = (
        "Successfully replaced in test.py\n\nDiff:\n```\n- old\n+ new```\n\n"
        + "x" * 10000
    )

    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_1",
                        "name": "search_and_replace",
                        "input": {
                            "file_path": "test.py",
                            "old_string": "old",
                            "new_string": "new",
                        },
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_1",
                        "content": big_result,
                    }
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_2",
                        "name": "search_and_replace",
                        "input": {
                            "file_path": "test.py",
                            "old_string": "new",
                            "new_string": "newer",
                        },
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_2",
                        "content": big_result,
                    }
                ],
            },
        ],
    )
    result = remove_outdated_file_edit_attempts(messages)

    # First tool_use input: stripped (outdated)
    assert (
        result[0]["content"][0]["input"]["old_string"]
        == "[Outdated search text removed]"
    )
    # First tool_result: stripped (outdated)
    assert (
        result[1]["content"][0]["content"]
        == "[Outdated edit result for 'test.py' removed]"
    )
    # Second tool_use input: kept (latest)
    assert result[2]["content"][0]["input"]["old_string"] == "new"
    # Second tool_result: kept (latest)
    assert result[3]["content"][0]["content"] == big_result


def test_tool_result_kept_when_latest():
    """Test that the latest tool_result is kept even when earlier ones are stripped."""
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_1",
                        "name": "search_and_replace",
                        "input": {
                            "file_path": "test.py",
                            "old_string": "a",
                            "new_string": "b",
                        },
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_1",
                        "content": "Result with full file content here",
                    }
                ],
            },
        ],
    )
    result = remove_outdated_file_edit_attempts(messages)

    # Single edit — both tool_use and tool_result should be kept as-is
    assert result == messages


def test_write_and_commit_file_input_stripped_when_outdated():
    """Test that write_and_commit_file file_content is stripped when outdated."""
    big_content = "def main():\n    pass\n" * 500

    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_1",
                        "name": "write_and_commit_file",
                        "input": {
                            "file_path": "test.py",
                            "file_content": big_content,
                        },
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_1",
                        "content": "Written successfully",
                    }
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_2",
                        "name": "write_and_commit_file",
                        "input": {
                            "file_path": "test.py",
                            "file_content": big_content + "\n# updated",
                        },
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_2",
                        "content": "Written successfully",
                    }
                ],
            },
        ],
    )
    result = remove_outdated_file_edit_attempts(messages)

    # First write_and_commit input: stripped
    assert (
        result[0]["content"][0]["input"]["file_content"]
        == "[Outdated file content removed]"
    )
    # First tool_result: stripped
    assert (
        result[1]["content"][0]["content"]
        == "[Outdated edit result for 'test.py' removed]"
    )
    # Second write_and_commit input: kept (latest)
    assert (
        result[2]["content"][0]["input"]["file_content"] == big_content + "\n# updated"
    )
    # Second tool_result: kept (latest)
    assert result[3]["content"][0]["content"] == "Written successfully"


def test_tool_result_without_tool_use_id_falls_through():
    """Test that tool_results without tool_use_id use the text-based fallback."""
    failed_diff = 'diff partially applied to the file: test.py. But, some changes were rejected. Review rejected changes, modify the diff, and try again.\n\ndiff="--- a/test.py"\n\nrej_text="Failed"'

    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
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
        ],
    )
    result = remove_outdated_file_edit_attempts(messages)

    # First: stripped via text-based fallback
    assert (
        result[0]["content"][0]["content"]
        == "[Outdated failed diff for 'test.py' removed]"
    )
    # Second: kept (latest)
    assert result[1]["content"][0]["content"] == failed_diff


def test_mixed_edit_tools_tool_results_stripped():
    """Test search_and_replace then write_and_commit for same file strips outdated results."""
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_1",
                        "name": "search_and_replace",
                        "input": {
                            "file_path": "test.py",
                            "old_string": "a",
                            "new_string": "b",
                        },
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_1",
                        "content": "Result 1 with full file " + "x" * 5000,
                    }
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_2",
                        "name": "write_and_commit_file",
                        "input": {
                            "file_path": "test.py",
                            "file_content": "full new content",
                        },
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_2",
                        "content": "Final result",
                    }
                ],
            },
        ],
    )
    result = remove_outdated_file_edit_attempts(messages)

    # search_and_replace input: stripped (outdated)
    assert (
        result[0]["content"][0]["input"]["old_string"]
        == "[Outdated search text removed]"
    )
    # First tool_result: stripped (outdated)
    assert (
        result[1]["content"][0]["content"]
        == "[Outdated edit result for 'test.py' removed]"
    )
    # write_and_commit input: kept (latest)
    assert result[2]["content"][0]["input"]["file_content"] == "full new content"
    # Final tool_result: kept (latest)
    assert result[3]["content"][0]["content"] == "Final result"


def test_real_conversation_llm_97545():
    """Real production conversation (llm_requests id=97545) with 13 search_and_replace edits.

    60 messages, foxden-account.ts edited 6 times, foxden-account.spec.ts edited 7 times.
    Tool_use inputs were already stripped by old code. New code strips 11 outdated tool_results.
    Expected output built by manual analysis — not generated by the function under test.
    """
    input_path = FIXTURES_DIR / "llm_97545_input_content.json"
    expected_path = FIXTURES_DIR / "llm_97545_expected_output.json"
    with open(input_path, encoding="utf-8") as f:
        messages = json.loads(f.read())
    with open(expected_path, encoding="utf-8") as f:
        expected = json.loads(f.read())

    result = remove_outdated_file_edit_attempts(messages)

    assert result == expected
