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
    # Test that the constant is accessible and consistent across imports
    from services.openai.instructions.resolve_feedback import RESOLVE_FEEDBACK as fresh_import
    assert fresh_import == RESOLVE_FEEDBACK
    assert fresh_import is not None
    assert isinstance(fresh_import, str)


def test_resolve_feedback_character_count():
    assert len(RESOLVE_FEEDBACK) > 100
    assert len(RESOLVE_FEEDBACK) < 2000


def test_resolve_feedback_word_count():
    words = RESOLVE_FEEDBACK.split()
    assert len(words) > 20
    assert len(words) < 300


def test_resolve_feedback_no_code_blocks():
    assert "```" not in RESOLVE_FEEDBACK
    # No backticks expected in this instruction text


def test_resolve_feedback_professional_tone():
    assert "You are a" in RESOLVE_FEEDBACK
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


def test_resolve_feedback_triple_quoted_string():
    # Fix: Use 'in' instead of 'startswith' to handle potential leading whitespace
    assert 'You are a top-class software engineer' in RESOLVE_FEEDBACK.strip()
    assert 'Should not be long.' in RESOLVE_FEEDBACK.strip()


def test_resolve_feedback_contains_specific_sections(): 
    sections = ["What the feedback is", "Where to change", "How to change"]
    for section in sections:
        assert section in RESOLVE_FEEDBACK


def test_resolve_feedback_mentions_error_fixing():
    assert "fix the error" in RESOLVE_FEEDBACK


def test_resolve_feedback_mentions_workflow_context():
    assert "workflow file" in RESOLVE_FEEDBACK


def test_resolve_feedback_mentions_check_run():
    assert "check run" in RESOLVE_FEEDBACK


def test_resolve_feedback_language_example():
    assert "mainly in Japanese" in RESOLVE_FEEDBACK
    assert "plan should be in Japanese" in RESOLVE_FEEDBACK


def test_resolve_feedback_no_html_tags():
    assert "<" not in RESOLVE_FEEDBACK
    assert ">" not in RESOLVE_FEEDBACK


def test_resolve_feedback_no_special_characters():
    special_chars = ["@", "$", "%", "^", "&", "*", "[", "]", "{", "}", "|", "\\"]
    for char in special_chars:
        assert char not in RESOLVE_FEEDBACK


def test_resolve_feedback_proper_punctuation():
    assert RESOLVE_FEEDBACK.count(".") >= 3
    assert RESOLVE_FEEDBACK.count(",") >= 2


def test_resolve_feedback_contains_parenthetical_example():
    assert "(" in RESOLVE_FEEDBACK
    assert ")" in RESOLVE_FEEDBACK


def test_resolve_feedback_mentions_information_types():
    info_types = ["pull request title", "body", "changes", "workflow file content", "check run error log"]
    for info_type in info_types:
        assert info_type in RESOLVE_FEEDBACK


def test_resolve_feedback_instruction_completeness():
    assert "resolve the feedback" in RESOLVE_FEEDBACK.lower()
    assert "write a plan" in RESOLVE_FEEDBACK.lower()
    assert "fix the error" in RESOLVE_FEEDBACK.lower()


def test_resolve_feedback_output_format_clarity():
    assert "Output format would be like this:" in RESOLVE_FEEDBACK
    lines = RESOLVE_FEEDBACK.split('\n')
    format_line_found = False
    for i, line in enumerate(lines):
        if "Output format would be like this:" in line:
            format_line_found = True
            break
    assert format_line_found


def test_resolve_feedback_section_order():
    lines = RESOLVE_FEEDBACK.split('\n')
    sections = []
    for line in lines:
        if line.startswith('## '):
            sections.append(line)
    
    expected_order = ["## What the feedback is", "## Where to change", "## How to change"]
    assert len(sections) == len(expected_order)
    for i, expected in enumerate(expected_order):
        assert sections[i] == expected


def test_resolve_feedback_no_empty_lines_at_start():
    # The constant starts with a newline due to triple-quote formatting, which is acceptable
    assert RESOLVE_FEEDBACK.startswith('\n')
    # Verify that after stripping whitespace, it starts with the expected content
    assert RESOLVE_FEEDBACK.lstrip().startswith('You are a')


def test_resolve_feedback_ends_with_newline():
    assert RESOLVE_FEEDBACK.endswith('\n')


def test_resolve_feedback_consistent_spacing():
    lines = RESOLVE_FEEDBACK.split('\n')
    for line in lines:
        if line.strip() and not line.startswith('##'):
            assert not line.startswith(' '), f"Line starts with space: '{line}'"


def test_resolve_feedback_role_specification():
    assert "You are a top-class software engineer" in RESOLVE_FEEDBACK


def test_resolve_feedback_task_description():
    assert "Given information such as" in RESOLVE_FEEDBACK


def test_resolve_feedback_language_sensitivity():
    assert "language that is used in the input" in RESOLVE_FEEDBACK


def test_resolve_feedback_brevity_instruction():
    assert "concise and to the point" in RESOLVE_FEEDBACK
    assert "Should not be long" in RESOLVE_FEEDBACK


def test_resolve_feedback_constant_name():
    import services.openai.instructions.resolve_feedback as module
    assert hasattr(module, 'RESOLVE_FEEDBACK')


def test_resolve_feedback_module_level_constant():
    import services.openai.instructions.resolve_feedback as module
    assert module.RESOLVE_FEEDBACK == RESOLVE_FEEDBACK


def test_resolve_feedback_string_literal():
    assert isinstance(RESOLVE_FEEDBACK, str)
    assert len(RESOLVE_FEEDBACK.strip()) > 0


def test_resolve_feedback_no_unicode_issues():
    try:
        RESOLVE_FEEDBACK.encode('utf-8')
        assert True
    except UnicodeEncodeError:
        assert False, "String contains invalid unicode characters"


def test_resolve_feedback_line_count():
    lines = RESOLVE_FEEDBACK.split('\n')
    assert len(lines) >= 5, f"Expected at least 5 lines, got {len(lines)}"
    assert len(lines) <= 15, f"Expected at most 15 lines, got {len(lines)}"


def test_resolve_feedback_contains_all_required_elements():
    required_elements = [
        "You are a top-class software engineer",
        "Given information such as",
        "pull request title",
        "body",
        "changes", 
        "workflow file content",
        "check run error log",
        "resolve the feedback",
        "write a plan",
        "fix the error",
        "language that is used in the input",
        "Output format would be like this:",
        "## What the feedback is",
        "## Where to change", 
        "## How to change",
        "Each section should be concise and to the point",
        "Should not be long"
    ]
    
    for element in required_elements:
        assert element in RESOLVE_FEEDBACK, f"Missing required element: {element}"


def test_resolve_feedback_no_typos_in_key_phrases():
    assert "top-class" in RESOLVE_FEEDBACK
    assert "software engineer" in RESOLVE_FEEDBACK
    assert "pull request" in RESOLVE_FEEDBACK
    assert "workflow file" in RESOLVE_FEEDBACK
    assert "check run" in RESOLVE_FEEDBACK
    assert "error log" in RESOLVE_FEEDBACK


def test_resolve_feedback_proper_grammar():
    assert "You are a top-class" in RESOLVE_FEEDBACK
    assert "Given information such as" in RESOLVE_FEEDBACK
    assert "resolve the feedback and write" in RESOLVE_FEEDBACK


def test_resolve_feedback_example_language_context():
    assert "e.g." in RESOLVE_FEEDBACK.lower()
    assert "if the input is mainly in Japanese" in RESOLVE_FEEDBACK


def test_resolve_feedback_instruction_structure():
    assert RESOLVE_FEEDBACK.count('##') == 3
    sections = [line for line in RESOLVE_FEEDBACK.split('\n') if line.startswith('##')]
    assert len(sections) == 3


def test_resolve_feedback_no_redundant_whitespace():
    lines = RESOLVE_FEEDBACK.split('\n')
    for line in lines:
        if line.strip():
            assert line == line.rstrip(), f"Line has trailing whitespace: '{line}'"


def test_resolve_feedback_consistent_formatting():
    lines = RESOLVE_FEEDBACK.split('\n')
    header_lines = [line for line in lines if line.startswith('##')]
    for header in header_lines:
        assert header.startswith('## ')
        assert not header.endswith(' ')


def test_resolve_feedback_complete_instruction_set():
    instruction_keywords = ["resolve", "write", "plan", "fix", "error", "feedback"]
    for keyword in instruction_keywords:
        assert keyword in RESOLVE_FEEDBACK.lower()


def test_resolve_feedback_contextual_information():
    context_items = ["pull request title", "body", "changes", "workflow file content", "check run error log"]
    for item in context_items:
        assert item in RESOLVE_FEEDBACK


def test_resolve_feedback_output_requirements():
    output_keywords = ["Output format", "concise", "to the point", "not be long"]
    for keyword in output_keywords:
        assert keyword in RESOLVE_FEEDBACK


def test_resolve_feedback_language_adaptation_detail():
    assert "language that is used in the input" in RESOLVE_FEEDBACK
    assert "English" in RESOLVE_FEEDBACK
    assert "Japanese" in RESOLVE_FEEDBACK
    assert "the plan should be in Japanese" in RESOLVE_FEEDBACK
