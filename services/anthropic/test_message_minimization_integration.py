import json

from config import UTF8
from services.anthropic.remove_duplicate_get_remote_file_content_results import (
    remove_duplicate_get_remote_file_content_results,
)
from services.anthropic.remove_get_remote_file_content_before_replace_remote_file_content import (
    remove_get_remote_file_content_before_replace_remote_file_content,
)
from services.anthropic.remove_outdated_apply_diff_to_file_attempts_and_results import (
    remove_outdated_apply_diff_to_file_attempts_and_results,
)


def test_all_three_functions_with_real_payload():
    # Load the original payload
    with open(
        "payloads/anthropic/llm_request_8144_9808_input_content_raw.json",
        "r",
        encoding=UTF8,
    ) as f:
        original_messages = json.load(f)

    # Load the expected minimized result
    with open(
        "payloads/anthropic/llm_request_8144_9808_input_content_minimized.json",
        "r",
        encoding=UTF8,
    ) as f:
        expected_messages = json.load(f)

    # Apply all three functions in sequence (same order as chat_with_functions.py)
    messages = remove_duplicate_get_remote_file_content_results(original_messages)
    messages = remove_get_remote_file_content_before_replace_remote_file_content(
        messages
    )
    messages = remove_outdated_apply_diff_to_file_attempts_and_results(messages)

    # Should match the expected minimized result
    assert messages == expected_messages
