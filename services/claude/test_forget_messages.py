# pyright: reportGeneralTypeIssues=false
# pyright: reportTypedDictNotRequiredAccess=false
# pyright: reportIndexIssue=false
# pyright: reportAssignmentType=false
import json
import os

from services.claude.forget_messages import forget_messages
from services.claude.measure_messages_chars import measure_messages_chars

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
REAL_MESSAGES_PATH = os.path.join(FIXTURES_DIR, "real_verify_messages.json")


def load_real_messages():
    with open(REAL_MESSAGES_PATH, encoding="utf-8") as f:
        return json.load(f)


def test_forget_single_file_from_real_conversation():
    """Forget .circleci/config.yml (21K chars) from real 86-message conversation."""
    messages = load_real_messages()

    # Capture before state
    config_block = messages[39]["content"]
    assert isinstance(config_block, list)
    original_content = config_block[0]["content"]
    assert isinstance(original_content, str)
    assert original_content.startswith("```.circleci/config.yml")
    chars_before = measure_messages_chars(messages)

    result = forget_messages(
        file_paths=[".circleci/config.yml"],
        messages=messages,
        base_args={},
    )

    placeholder = "['.circleci/config.yml' content removed because agent already extracted needed patterns]"
    assert config_block[0]["content"] == placeholder
    chars_after = measure_messages_chars(messages)
    chars_saved = chars_before - chars_after
    pct = chars_saved / chars_before * 100
    assert (
        result
        == f"Forgot 1 file(s) from context. Saved {chars_saved:,} chars ({pct:.2g}%, {chars_before:,} → {chars_after:,})."
    )


def test_forget_multiple_files_preserves_others():
    """Forget 3 files from real conversation, verify others untouched."""
    messages = load_real_messages()

    # Capture before state
    keep_msg_17 = messages[17]["content"][0]["content"]
    keep_msg_27 = messages[27]["content"][0]["content"]
    keep_msg_63 = messages[63]["content"][0]["content"]
    chars_before = measure_messages_chars(messages)

    result = forget_messages(
        file_paths=["package.json", ".circleci/config.yml", "src/App.test.tsx"],
        messages=messages,
        base_args={},
    )

    chars_after = measure_messages_chars(messages)
    chars_saved = chars_before - chars_after
    pct = chars_saved / chars_before * 100
    assert (
        result
        == f"Forgot 3 file(s) from context. Saved {chars_saved:,} chars ({pct:.2g}%, {chars_before:,} → {chars_after:,})."
    )
    # Forgotten files replaced
    assert (
        messages[13]["content"][0]["content"]
        == "['package.json' content removed because agent already extracted needed patterns]"
    )
    assert (
        messages[39]["content"][0]["content"]
        == "['.circleci/config.yml' content removed because agent already extracted needed patterns]"
    )
    assert (
        messages[41]["content"][0]["content"]
        == "['src/App.test.tsx' content removed because agent already extracted needed patterns]"
    )
    # Kept files untouched
    assert messages[17]["content"][0]["content"] == keep_msg_17
    assert messages[27]["content"][0]["content"] == keep_msg_27
    assert messages[63]["content"][0]["content"] == keep_msg_63


def test_forget_nonexistent_path_no_change():
    """Forgetting a path not in real messages doesn't modify anything."""
    messages = load_real_messages()
    snapshot = json.dumps(messages)
    chars_before = measure_messages_chars(messages)

    result = forget_messages(
        file_paths=["src/nonexistent.py"],
        messages=messages,
        base_args={},
    )

    assert (
        result
        == f"Forgot 1 file(s) from context. Saved 0 chars (0%, {chars_before:,} → {chars_before:,})."
    )
    assert json.dumps(messages) == snapshot


def test_forget_empty_list_no_change():
    """Forgetting zero files from real messages changes nothing."""
    messages = load_real_messages()
    snapshot = json.dumps(messages)
    chars_before = measure_messages_chars(messages)

    result = forget_messages(file_paths=[], messages=messages, base_args={})

    assert (
        result
        == f"Forgot 0 file(s) from context. Saved 0 chars (0%, {chars_before:,} → {chars_before:,})."
    )
    assert json.dumps(messages) == snapshot
