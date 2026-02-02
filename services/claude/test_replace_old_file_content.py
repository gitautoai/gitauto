# pyright: reportGeneralTypeIssues=false
# pyright: reportTypedDictNotRequiredAccess=false
# pyright: reportIndexIssue=false
# pyright: reportAssignmentType=false
from anthropic.types import MessageParam

from services.claude.replace_old_file_content import replace_old_file_content


def test_replace_old_file_content_replaces_matching_file():
    messages: list[MessageParam] = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "tool_1",
                    "content": "```src/main.py\n1\tprint('hello')\n```",
                }
            ],
        },
        {"role": "assistant", "content": "I see the file content."},
    ]

    replace_old_file_content(messages, "src/main.py")

    content = messages[0]["content"]
    assert isinstance(content, list)
    assert content[0]["content"] == "[Outdated 'src/main.py' content removed]"


def test_replace_old_file_content_no_change_when_different_file():
    messages: list[MessageParam] = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "tool_1",
                    "content": "```src/other.py\n1\tprint('other')\n```",
                }
            ],
        },
    ]

    original_content = "```src/other.py\n1\tprint('other')\n```"
    replace_old_file_content(messages, "src/main.py")

    content = messages[0]["content"]
    assert isinstance(content, list)
    assert content[0]["content"] == original_content


def test_replace_old_file_content_ignores_assistant_messages():
    messages: list[MessageParam] = [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "tool_1",
                    "name": "get_remote_file_content",
                    "input": {"file_path": "src/main.py"},
                }
            ],
        },
    ]

    replace_old_file_content(messages, "src/main.py")

    content = messages[0]["content"]
    assert isinstance(content, list)
    assert content[0]["type"] == "tool_use"


def test_replace_old_file_content_ignores_string_content():
    messages: list[MessageParam] = [
        {"role": "user", "content": "Please read src/main.py"},
    ]

    replace_old_file_content(messages, "src/main.py")

    assert messages[0]["content"] == "Please read src/main.py"


def test_replace_old_file_content_ignores_non_tool_result_blocks():
    messages: list[MessageParam] = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "```src/main.py\n1\tprint('hello')\n```"},
            ],
        },
    ]

    replace_old_file_content(messages, "src/main.py")

    content = messages[0]["content"]
    assert isinstance(content, list)
    assert content[0]["text"] == "```src/main.py\n1\tprint('hello')\n```"


def test_replace_old_file_content_handles_multiple_tool_results():
    messages: list[MessageParam] = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "tool_1",
                    "content": "```src/main.py\n1\tprint('first')\n```",
                },
                {
                    "type": "tool_result",
                    "tool_use_id": "tool_2",
                    "content": "```src/other.py\n1\tprint('other')\n```",
                },
            ],
        },
    ]

    replace_old_file_content(messages, "src/main.py")

    content = messages[0]["content"]
    assert isinstance(content, list)
    assert content[0]["content"] == "[Outdated 'src/main.py' content removed]"
    assert content[1]["content"] == "```src/other.py\n1\tprint('other')\n```"


def test_replace_old_file_content_replaces_all_occurrences():
    messages: list[MessageParam] = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "tool_1",
                    "content": "```src/main.py\n1\tprint('first')\n```",
                }
            ],
        },
        {"role": "assistant", "content": "I see version 1."},
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "tool_2",
                    "content": "```src/main.py\n1\tprint('second')\n```",
                }
            ],
        },
    ]

    replace_old_file_content(messages, "src/main.py")

    content_0 = messages[0]["content"]
    content_2 = messages[2]["content"]
    assert isinstance(content_0, list)
    assert isinstance(content_2, list)
    assert content_0[0]["content"] == "[Outdated 'src/main.py' content removed]"
    assert content_2[0]["content"] == "[Outdated 'src/main.py' content removed]"


def test_replace_old_file_content_handles_empty_messages():
    messages: list[MessageParam] = []

    replace_old_file_content(messages, "src/main.py")

    assert not messages


def test_replace_old_file_content_ignores_list_content():
    """Test that list content (list of content blocks) is ignored - only string content is handled."""
    original_content = [
        {"type": "text", "text": "```src/main.py\n1\tprint('hello')\n```"}
    ]
    messages: list[MessageParam] = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "tool_1",
                    "content": original_content,
                }
            ],
        },
    ]

    replace_old_file_content(messages, "src/main.py")

    content = messages[0]["content"]
    assert isinstance(content, list)
    # List content is ignored, only string content is handled
    assert content[0]["content"] == original_content


def test_replace_old_file_content_ignores_list_content_without_text_block():
    """Test that list content without text block is ignored."""
    messages: list[MessageParam] = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "tool_1",
                    "content": [{"type": "image", "source": {"data": "..."}}],
                }
            ],
        },
    ]

    replace_old_file_content(messages, "src/main.py")

    content = messages[0]["content"]
    assert isinstance(content, list)
    # Content should remain unchanged since it's an image block
    assert content[0]["content"] == [{"type": "image", "source": {"data": "..."}}]


def test_replace_old_file_content_ignores_empty_list_content():
    """Test that empty list content is ignored."""
    messages: list[MessageParam] = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "tool_1",
                    "content": [],
                }
            ],
        },
    ]

    replace_old_file_content(messages, "src/main.py")

    content = messages[0]["content"]
    assert isinstance(content, list)
    assert not content[0]["content"]
