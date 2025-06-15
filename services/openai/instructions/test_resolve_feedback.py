from services.openai.instructions.resolve_feedback import RESOLVE_FEEDBACK


def test_resolve_feedback_exists():
    assert RESOLVE_FEEDBACK is not None


def test_resolve_feedback_is_string():
    assert isinstance(RESOLVE_FEEDBACK, str)


def test_resolve_feedback_not_empty():
    assert len(RESOLVE_FEEDBACK) > 0
    assert RESOLVE_FEEDBACK.strip() != ""


def test_resolve_feedback_contains_key_phrases():
    assert "software engineer" in RESOLVE_FEEDBACK
    assert "pull request" in RESOLVE_FEEDBACK
    assert "feedback" in RESOLVE_FEEDBACK
    assert "plan" in RESOLVE_FEEDBACK


def test_resolve_feedback_contains_output_format():
    assert "## What the feedback is" in RESOLVE_FEEDBACK
    assert "## Where to change" in RESOLVE_FEEDBACK
    assert "## How to change" in RESOLVE_FEEDBACK


def test_resolve_feedback_mentions_language_adaptation():
    assert "language that is used in the input" in RESOLVE_FEEDBACK
    assert "English" in RESOLVE_FEEDBACK
    assert "Japanese" in RESOLVE_FEEDBACK


def test_resolve_feedback_mentions_conciseness():
    assert "concise" in RESOLVE_FEEDBACK
    assert "not be long" in RESOLVE_FEEDBACK


def test_resolve_feedback_starts_with_role_definition():
    lines = RESOLVE_FEEDBACK.strip().split('\n')
    first_line = lines[0] if lines else ""
    assert "software engineer" in first_line.lower()


def test_resolve_feedback_has_proper_structure():
    assert RESOLVE_FEEDBACK.count("##") >= 3
    assert "Output format would be like this:" in RESOLVE_FEEDBACK


def test_resolve_feedback_mentions_required_inputs():
    assert "pull request title" in RESOLVE_FEEDBACK
    assert "body" in RESOLVE_FEEDBACK
    assert "changes" in RESOLVE_FEEDBACK
    assert "workflow file content" in RESOLVE_FEEDBACK
    assert "check run error log" in RESOLVE_FEEDBACK


def test_resolve_feedback_multiline_string():
    assert '\n' in RESOLVE_FEEDBACK
    lines = RESOLVE_FEEDBACK.split('\n')
    assert len(lines) > 1


def test_resolve_feedback_no_trailing_whitespace():
    lines = RESOLVE_FEEDBACK.split('\n')
    for line in lines[:-1]:
        assert not line.endswith(' '), f"Line has trailing whitespace: '{line}'"


def test_resolve_feedback_proper_markdown_headers():
    lines = RESOLVE_FEEDBACK.split('\n')
    header_lines = [line for line in lines if line.startswith('##')]
    assert len(header_lines) == 3
    for header in header_lines:
        assert header.startswith('## ')
        assert len(header) > 3


def test_resolve_feedback_contains_example_scenario():
    assert "e.g." in RESOLVE_FEEDBACK or "for example" in RESOLVE_FEEDBACK


def test_resolve_feedback_immutable():
    original_content = RESOLVE_FEEDBACK
    try:
        RESOLVE_FEEDBACK = "modified"
    except:
        pass
    from services.openai.instructions.resolve_feedback import RESOLVE_FEEDBACK as fresh_import
    assert fresh_import == original_content


def test_resolve_feedback_character_count():
    assert len(RESOLVE_FEEDBACK) > 100
    assert len(RESOLVE_FEEDBACK) < 2000


def test_resolve_feedback_word_count():
    words = RESOLVE_FEEDBACK.split()
    assert len(words) > 20
    assert len(words) < 300


def test_resolve_feedback_no_code_blocks():
    assert "```" not in RESOLVE_FEEDBACK
    assert "`" not in RESOLVE_FEEDBACK or RESOLVE_FEEDBACK.count("`") == 0


def test_resolve_feedback_professional_tone():
    assert "You are an" in RESOLVE_FEEDBACK
    assert "top-class" in RESOLVE_FEEDBACK


def test_resolve_feedback_instruction_clarity():
    assert "Given information" in RESOLVE_FEEDBACK
    assert "resolve the feedback" in RESOLVE_FEEDBACK
    assert "write a plan" in RESOLVE_FEEDBACK


def test_resolve_feedback_format_specification():
    assert "Output format" in RESOLVE_FEEDBACK
    assert "would be like this" in RESOLVE_FEEDBACK


def test_resolve_feedback_section_guidelines():
    assert "Each section should be" in RESOLVE_FEEDBACK
    assert "to the point" in RESOLVE_FEEDBACK


def test_resolve_feedback_import_accessibility():
    from services.openai.instructions.resolve_feedback import RESOLVE_FEEDBACK as imported_constant
    assert imported_constant == RESOLVE_FEEDBACK
    assert imported_constant is not None
    assert isinstance(imported_constant, str)
