import re
from services.openai.instructions.identify_cause import IDENTIFY_CAUSE


def test_identify_cause_exists():
    assert IDENTIFY_CAUSE is not None


def test_identify_cause_is_string():
    assert isinstance(IDENTIFY_CAUSE, str)


def test_identify_cause_not_empty():
    assert len(IDENTIFY_CAUSE.strip()) > 0


def test_identify_cause_contains_expert_role():
    assert "GitHub Actions, Workflow, and Check Run expert" in IDENTIFY_CAUSE


def test_identify_cause_contains_input_description():
    assert "pull request title, body, changes, workflow file content, and check run error log" in IDENTIFY_CAUSE


def test_identify_cause_contains_language_instruction():
    assert "language that is used in the input" in IDENTIFY_CAUSE
    assert "Japanese" in IDENTIFY_CAUSE


def test_identify_cause_contains_minimal_changes_instruction():
    assert "absolutely necessary changes" in IDENTIFY_CAUSE
    assert "minimizing code modifications" in IDENTIFY_CAUSE


def test_identify_cause_contains_markdown_format_instruction():
    assert "Markdown format" in IDENTIFY_CAUSE


def test_identify_cause_contains_required_headers():
    required_headers = [
        "## What is the Error?",
        "## Why did the Error Occur?",
        "## Where is the Error Located?",
        "## How to Fix the Error?",
        "## Why Fix it This Way?"
    ]
    for header in required_headers:
        assert header in IDENTIFY_CAUSE


def test_identify_cause_contains_response_guidelines():
    assert "clear, specific, concise, and direct" in IDENTIFY_CAUSE


def test_identify_cause_multiline_string():
    assert "\n" in IDENTIFY_CAUSE
    lines = IDENTIFY_CAUSE.split("\n")
    assert len(lines) > 1


def test_identify_cause_starts_with_role_definition():
    stripped = IDENTIFY_CAUSE.strip()
    assert stripped.startswith("You are a GitHub Actions")


def test_identify_cause_ends_with_response_guidelines():
    stripped = IDENTIFY_CAUSE.strip()
    assert stripped.endswith("responses.")


def test_identify_cause_header_format():
    headers = re.findall(r'^## .+$', IDENTIFY_CAUSE, re.MULTILINE)
    assert len(headers) == 5
    for header in headers:
        assert header.startswith("## ")
        assert header.endswith("?")


def test_identify_cause_no_extra_whitespace_at_start():
    assert not IDENTIFY_CAUSE.startswith(" ")
    assert not IDENTIFY_CAUSE.startswith("\t")


def test_identify_cause_no_extra_whitespace_at_end():
    assert not IDENTIFY_CAUSE.endswith(" ")
    assert not IDENTIFY_CAUSE.endswith("\t")
