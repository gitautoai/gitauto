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


def test_identify_cause_contains_specific_keywords():
    keywords = ["error", "fix", "failure", "plan", "changes"]
    for keyword in keywords:
        assert keyword.lower() in IDENTIFY_CAUSE.lower()


def test_identify_cause_string_length():
    assert len(IDENTIFY_CAUSE) > 100
    assert len(IDENTIFY_CAUSE) < 2000


def test_identify_cause_line_count():
    lines = IDENTIFY_CAUSE.split("\n")
    assert len(lines) >= 10
    assert len(lines) <= 20


def test_identify_cause_consistent_value():
    original_value = IDENTIFY_CAUSE
    from services.openai.instructions.identify_cause import IDENTIFY_CAUSE as reimported
    assert reimported == original_value
    assert IDENTIFY_CAUSE == original_value


def test_identify_cause_contains_reviewer_consideration():
    assert "confuse reviewers" in IDENTIFY_CAUSE
    assert "skilled engineer" in IDENTIFY_CAUSE


def test_identify_cause_contains_check_run_context():
    assert "Check Run" in IDENTIFY_CAUSE
    assert "failure" in IDENTIFY_CAUSE


def test_identify_cause_japanese_example():
    assert "e.g." in IDENTIFY_CAUSE
    assert "mainly in Japanese" in IDENTIFY_CAUSE


def test_identify_cause_output_format_specificity():
    assert "following headers:" in IDENTIFY_CAUSE


def test_identify_cause_no_html_tags():
    assert "<" not in IDENTIFY_CAUSE
    assert ">" not in IDENTIFY_CAUSE


def test_identify_cause_proper_sentence_structure():
    sentences = [s.strip() for s in IDENTIFY_CAUSE.split('.') if s.strip()]
    assert len(sentences) >= 3


def test_identify_cause_contains_workflow_reference():
    assert "workflow" in IDENTIFY_CAUSE.lower()


def test_identify_cause_header_order():
    headers = re.findall(r'^## .+$', IDENTIFY_CAUSE, re.MULTILINE)
    expected_order = [
        "## What is the Error?",
        "## Why did the Error Occur?", 
        "## Where is the Error Located?",
        "## How to Fix the Error?",
        "## Why Fix it This Way?"
    ]
    assert headers == expected_order


def test_identify_cause_no_trailing_newlines():
    assert not IDENTIFY_CAUSE.endswith("\n\n")


def test_identify_cause_contains_action_words():
    action_words = ["identify", "write", "fix", "output"]
    for word in action_words:
        assert word in IDENTIFY_CAUSE.lower()


def test_identify_cause_professional_tone():
    professional_indicators = ["expert", "skilled", "necessary", "specific"]
    for indicator in professional_indicators:
        assert indicator in IDENTIFY_CAUSE.lower()


def test_identify_cause_instruction_clarity():
    clarity_words = ["clear", "specific", "concise", "direct"]
    for word in clarity_words:
        assert word in IDENTIFY_CAUSE.lower()


def test_identify_cause_string_immutability():
    original_length = len(IDENTIFY_CAUSE)
    original_content = str(IDENTIFY_CAUSE)
    assert len(IDENTIFY_CAUSE) == original_length
    assert IDENTIFY_CAUSE == original_content


def test_identify_cause_contains_parenthetical_example():
    assert "(" in IDENTIFY_CAUSE
    assert ")" in IDENTIFY_CAUSE
    assert "e.g." in IDENTIFY_CAUSE


def test_identify_cause_markdown_headers_complete():
    header_count = IDENTIFY_CAUSE.count("##")
    assert header_count == 5


def test_identify_cause_no_code_blocks():
    assert "```" not in IDENTIFY_CAUSE
    assert "`" not in IDENTIFY_CAUSE


def test_identify_cause_contains_github_context():
    github_terms = ["GitHub", "pull request", "workflow"]
    for term in github_terms:
        assert term in IDENTIFY_CAUSE


def test_identify_cause_error_focus():
    error_related = ["error", "failure", "fix", "cause"]
    for term in error_related:
        assert term.lower() in IDENTIFY_CAUSE.lower()


def test_identify_cause_instruction_completeness():
    instruction_elements = ["Given", "identify", "write", "Output", "Always"]
    for element in instruction_elements:
        assert element in IDENTIFY_CAUSE


def test_identify_cause_no_special_characters():
    special_chars = ["@", "#", "$", "%", "^", "&", "*"]
    for char in special_chars:
        assert char not in IDENTIFY_CAUSE


def test_identify_cause_proper_capitalization():
    lines = IDENTIFY_CAUSE.split("\n")
    non_empty_lines = [line.strip() for line in lines if line.strip()]
    for line in non_empty_lines:
        if line.startswith("##"):
            assert line[2:].strip()[0].isupper()


def test_identify_cause_contains_engineering_best_practices():
    best_practices = ["minimal", "necessary", "skilled", "avoid"]
    for practice in best_practices:
        assert practice in IDENTIFY_CAUSE.lower()