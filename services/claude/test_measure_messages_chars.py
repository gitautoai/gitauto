# pyright: reportGeneralTypeIssues=false
# pyright: reportTypedDictNotRequiredAccess=false
# pyright: reportIndexIssue=false
# pyright: reportAssignmentType=false
import json
import os

from services.claude.measure_messages_chars import measure_messages_chars

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
REAL_MESSAGES_PATH = os.path.join(FIXTURES_DIR, "real_verify_messages.json")


def load_real_messages():
    with open(REAL_MESSAGES_PATH, encoding="utf-8") as f:
        return json.load(f)


def test_measure_real_conversation():
    """Real 86-message conversation total chars."""
    messages = load_real_messages()

    result = measure_messages_chars(messages)

    assert result == 505094


def test_measure_empty():
    """Empty message list returns 0."""
    assert measure_messages_chars([]) == 0


def test_measure_after_forgetting_is_exact_diff():
    """After replacing a file read with placeholder, diff equals original - placeholder."""
    messages = load_real_messages()
    chars_before = measure_messages_chars(messages)

    # Replace .circleci/config.yml with placeholder
    config_block = messages[39]["content"]
    assert isinstance(config_block, list)
    original_content = config_block[0]["content"]
    assert original_content.startswith("```.circleci/config.yml")
    placeholder = "[Outdated '.circleci/config.yml' content removed]"
    config_block[0]["content"] = placeholder

    chars_after = measure_messages_chars(messages)

    assert chars_before - chars_after == len(original_content) - len(placeholder)
