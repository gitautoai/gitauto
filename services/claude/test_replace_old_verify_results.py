# pyright: reportArgumentType=false
import json
import os

from services.claude.replace_old_verify_results import (
    VERIFY_PLACEHOLDER,
    replace_old_verify_results,
)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

# Full 86-message real conversation from foxcom-forms PR#1146 (2026-04-10).
# 12 verify_task_is_complete results (31K each), 31 non-verify tool results, assistant messages.
REAL_MESSAGES_PATH = os.path.join(FIXTURES_DIR, "real_verify_messages.json")


def load_real_messages():
    with open(REAL_MESSAGES_PATH, encoding="utf-8") as f:
        return json.load(f)


def test_replaces_real_verify_results():
    """Real data: 12 verify results (31K each) should be replaced, 31 others untouched."""
    messages = load_real_messages()

    # Verify precondition: messages have 12 verify results and 31 non-verify
    verify_count = 0
    non_verify_count = 0
    for msg in messages:
        if msg.get("role") != "user":
            continue
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if block.get("type") != "tool_result":
                continue
            c = block.get("content", "")
            if isinstance(c, str) and c.startswith("Task NOT complete"):
                verify_count += 1
            elif isinstance(c, str) and not c.startswith("Task"):
                non_verify_count += 1
    assert verify_count == 12
    assert non_verify_count == 31

    replace_old_verify_results(messages)

    # After replacement: all 12 verify results should be placeholders
    replaced_count = 0
    surviving_non_verify = 0
    for msg in messages:
        if msg.get("role") != "user":
            continue
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if block.get("type") != "tool_result":
                continue
            c = block.get("content", "")
            if c == VERIFY_PLACEHOLDER:
                replaced_count += 1
            elif isinstance(c, str):
                # Non-verify results must NOT be replaced
                assert not c.startswith("Task NOT complete")
                surviving_non_verify += 1
    assert replaced_count == 12
    assert surviving_non_verify == 31


def test_skips_already_replaced_results():
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "t1",
                    "content": VERIFY_PLACEHOLDER,
                }
            ],
        },
    ]

    replace_old_verify_results(messages)
    assert messages[0]["content"][0]["content"] == VERIFY_PLACEHOLDER


def test_no_verify_results_is_noop():
    messages = load_real_messages()
    # Remove verify results, keep only non-verify
    for msg in messages:
        if msg.get("role") != "user":
            continue
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        msg["content"] = [
            block
            for block in content
            if not (
                block.get("type") == "tool_result"
                and isinstance(block.get("content"), str)
                and block["content"].startswith("Task ")
            )
        ]

    # Snapshot content before
    before = json.dumps(messages)
    replace_old_verify_results(messages)
    after = json.dumps(messages)
    assert before == after
