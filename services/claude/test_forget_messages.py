# pyright: reportGeneralTypeIssues=false
# pyright: reportTypedDictNotRequiredAccess=false
# pyright: reportIndexIssue=false
# pyright: reportAssignmentType=false
import json
import os

from services.claude.forget_messages import forget_messages

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
REAL_MESSAGES_PATH = os.path.join(FIXTURES_DIR, "real_verify_messages.json")


def load_real_messages():
    with open(REAL_MESSAGES_PATH, encoding="utf-8") as f:
        return json.load(f)


def test_forget_single_file_from_real_conversation():
    """Forget .circleci/config.yml from real 86-message conversation.

    General optimization removes 23 messages (fully-emptied; text-only assistant
    messages are preserved by the remove_tool_pairs fix). config.yml adds 1
    more popped pair. 86 - 23 - 1 = 62.
    """
    messages = load_real_messages()
    assert len(messages) == 86

    forget_messages(
        file_paths=[".circleci/config.yml"],
        messages=messages,
        base_args={},
    )

    assert len(messages) == 62


def test_forget_multiple_files_preserves_others():
    """Forget 3 files from real conversation.

    General optimization pops 23 fully-emptied messages. The 3 files add 3 more
    popped pairs (config.yml, package.json, App.test.tsx — each 1 read pair).
    86 - 23 - 3 = 60.
    """
    messages = load_real_messages()
    # These non-outdated tool_results should survive
    assert messages[27]["content"][0]["tool_use_id"] == "toolu_01EGQHGYZ1yvZJgS6HcKs2Ke"
    assert messages[63]["content"][0]["tool_use_id"] == "toolu_01RS7iEjJfRY1pbbzKunXMFV"

    forget_messages(
        file_paths=["package.json", ".circleci/config.yml", "src/App.test.tsx"],
        messages=messages,
        base_args={},
    )

    assert len(messages) == 60


def test_forget_nonexistent_path_still_optimizes():
    """Forgetting a nonexistent path still runs general optimization.

    Same as verify test: 86 - 23 fully-emptied = 63.
    """
    messages = load_real_messages()
    assert len(messages) == 86

    forget_messages(
        file_paths=["src/nonexistent.py"],
        messages=messages,
        base_args={},
    )

    assert len(messages) == 63


def test_forget_empty_list_still_optimizes():
    """Forgetting zero files still runs general optimization.

    Same as verify test: 86 - 23 fully-emptied = 63.
    """
    messages = load_real_messages()
    assert len(messages) == 86

    forget_messages(file_paths=[], messages=messages, base_args={})

    assert len(messages) == 63
