# pyright: reportIndexIssue=false, reportArgumentType=false
import json
import os
from typing import cast

from anthropic.types import MessageParam

from services.claude.detect_outdated_tool_ids import detect_outdated_tool_ids
from services.claude.remove_outdated_messages import remove_outdated_messages

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def load_fixture(name: str):
    with open(os.path.join(FIXTURES_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def test_empty_messages():
    messages: list[MessageParam] = []
    remove_outdated_messages(messages, file_paths_to_remove=set())
    assert len(messages) == 0


def test_no_outdated_content():
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_1",
                        "name": "get_local_file_content",
                        "input": {"file_path": "test.py"},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_1",
                        "content": "content",
                    }
                ],
            },
        ],
    )
    original = json.dumps(messages)
    remove_outdated_messages(messages, file_paths_to_remove=set())
    assert json.dumps(messages) == original


def test_removes_outdated_read_after_edit():
    """Read then edit: read tool pair is removed, edit kept."""
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_read",
                        "name": "get_local_file_content",
                        "input": {"file_path": "src/main.py"},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_read",
                        "content": "```src/main.py\n1\tprint('hello')\n```",
                    }
                ],
            },
            {"role": "assistant", "content": "I'll edit the file."},
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_edit",
                        "name": "search_and_replace",
                        "input": {
                            "file_path": "src/main.py",
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
                        "tool_use_id": "toolu_edit",
                        "content": "Updated src/main.py.",
                    }
                ],
            },
        ],
    )
    remove_outdated_messages(messages, file_paths_to_remove=set())
    # After strip: the read pair is fully popped. The text-only "I'll edit the file." assistant survives, followed by the edit tool_use assistant and its tool_result. The two adjacent assistants are accepted by both Anthropic (auto-merge) and Gemma (verified empirically).
    assert len(messages) == 3
    assert messages[0] == {"role": "assistant", "content": "I'll edit the file."}
    assert messages[1]["role"] == "assistant"
    content_1 = messages[1].get("content")
    assert isinstance(content_1, list)
    block_1 = content_1[0]
    assert isinstance(block_1, dict)
    assert block_1.get("id") == "toolu_edit"
    assert messages[2]["role"] == "user"
    content_2 = messages[2].get("content")
    assert isinstance(content_2, list)
    block_2 = content_2[0]
    assert isinstance(block_2, dict)
    assert block_2.get("tool_use_id") == "toolu_edit"


def test_removes_outdated_string_user_message():
    """String user message with file content is removed when file was re-read."""
    messages: list[MessageParam] = cast(
        list[MessageParam],
        [
            {"role": "user", "content": "```src/main.py\n1\tprint('v1')\n```"},
            {"role": "assistant", "content": "I see v1."},
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_1",
                        "name": "get_local_file_content",
                        "input": {"file_path": "src/main.py"},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_1",
                        "content": "```src/main.py\n1\tprint('v2')\n```",
                    }
                ],
            },
        ],
    )
    remove_outdated_messages(messages, file_paths_to_remove=set())
    # String user message popped; the "I see v1." assistant survives, followed by the assistant carrying toolu_1 and its tool_result.
    assert len(messages) == 3
    assert messages[0]["content"] == "I see v1."


def test_real_fixture_verify_messages():
    """Real 86-message conversation: 12 verify results, 2 multi-read files.

    18 outdated IDs: 11 verify results (all but latest) + 2 outdated reads
    (craco.config.js, amtrustCoverage.test.tsx) + 5 outdated tool_results.
    23 messages popped (fully emptied). 11 assistant messages keep their
    text after their tool_use is stripped — the agent's plan is preserved.
    """
    messages = load_fixture("real_verify_messages.json")
    assert len(messages) == 86

    remove_outdated_messages(messages, file_paths_to_remove=set())

    # 86 - 23 popped = 63
    assert len(messages) == 63


def test_real_fixture_llm_97545():
    """Real production conversation: 60 messages with 13 search_and_replace edits.

    foxden-account.ts edited 6 times, foxden-account.spec.ts edited 7 times.
    Outdated edits and reads should be removed.
    """
    messages = load_fixture("llm_97545_input_content.json")
    assert len(messages) == 60

    # First detect what's outdated
    ids_to_remove, positions = detect_outdated_tool_ids(
        messages, file_paths_to_remove=set()
    )

    # 21 outdated: 8 foxden-account.ts (latest edit at msg[46]) + 11 spec.ts (latest edit at msg[58]) + 2 verifies
    assert len(ids_to_remove) == 21
    assert positions["src/tenancy/foxden-account.ts"] == {
        "message_index": 46,
        "action": "edit",
    }
    assert positions["test/specs/tenancy/foxden-account.spec.ts"] == {
        "message_index": 58,
        "action": "edit",
    }

    # Now run the full orchestrator
    messages = load_fixture("llm_97545_input_content.json")
    remove_outdated_messages(messages, file_paths_to_remove=set())

    # 60 - 18 popped = 42. Only fully-emptied messages are popped; 16 assistant messages keep their text after the outdated tool_use is stripped.
    assert len(messages) == 42


def test_real_fixture_llm_97545_specific_ids():
    """Verify exact set of outdated tool IDs in the llm_97545 fixture."""
    messages = load_fixture("llm_97545_input_content.json")
    ids_to_remove, _ = detect_outdated_tool_ids(messages, file_paths_to_remove=set())

    assert ids_to_remove == {
        "toolu_011623K1NqkvigPgsR3nBeSp",
        "toolu_016VbxPb1G6UccDAW1Zap3VM",
        "toolu_0174bkCDktmPY5H17xiYJNYG",
        "toolu_019fEb18r8qJnLADKyB8JZtT",
        "toolu_01BFP9MqxyZYsVErWANLsPTH",
        "toolu_01Cee9tpfCGysyB1YgHG9c41",
        "toolu_01ChuEgLYRurnBx2ZTALm39S",
        "toolu_01DPaLS9Z3XY7g3HxkGPDApY",
        "toolu_01EDA4xx8X3UfjSYFV9MPtcz",
        "toolu_01EuLuDfX3JgWsgMB3zYCu7U",
        "toolu_01F8LY4zgLCiHwyjyroBqvCp",
        "toolu_01HWLmpjXSzCynMYQGmMjcXm",
        "toolu_01Ld6KmbJ8c9oZa61BwfBiNr",
        "toolu_01RN63nxX2n5oN8D9AXDsE1B",
        "toolu_01SE6LwnwLVhCUFen61nTr4h",
        "toolu_01SmsqAEHmhiGDJCvVHPoiKv",
        "toolu_01TcEYTixAPxMj767MtfPjDx",
        "toolu_01UA7769kd8TyGqqvSvETwKw",
        "toolu_01UYiyBU595tQbYuvCfHcQA2",
        "toolu_01VFomQ4MLYuCjrNLJbQPLUz",
        "toolu_01WYq1Ae9QLkX1tavef35nZE",
    }
