import pytest

from services.openai.instructions.resolve_feedback import RESOLVE_FEEDBACK


def test_resolve_feedback_exists():
    """Test that RESOLVE_FEEDBACK constant exists and is accessible."""
    assert RESOLVE_FEEDBACK is not None


def test_resolve_feedback_is_string():
    """Test that RESOLVE_FEEDBACK is a string."""
    assert isinstance(RESOLVE_FEEDBACK, str)


def test_resolve_feedback_not_empty():
    """Test that RESOLVE_FEEDBACK is not empty."""
    assert len(RESOLVE_FEEDBACK) > 0
    assert RESOLVE_FEEDBACK.strip() != ""


def test_resolve_feedback_contains_expected_content():
    """Test that RESOLVE_FEEDBACK contains expected instructional content."""
    # Check for key phrases that should be in the instruction
    expected_phrases = [
        "top-class software engineer",
        "pull request title",
        "body",
        "changes",
        "workflow file content",
        "check run error log",
        "resolve the feedback",
        "write a plan",
        "fix the error"
    ]
    
    for phrase in expected_phrases:
        assert phrase in RESOLVE_FEEDBACK, f"Expected phrase '{phrase}' not found in RESOLVE_FEEDBACK"


def test_resolve_feedback_contains_output_format():
    """Test that RESOLVE_FEEDBACK contains the expected output format structure."""
    expected_sections = [
        "## What the feedback is",
        "## Where to change", 
        "## How to change"
    ]
    
    for section in expected_sections:
        assert section in RESOLVE_FEEDBACK, f"Expected section '{section}' not found in RESOLVE_FEEDBACK"


def test_resolve_feedback_language_instruction():
    """Test that RESOLVE_FEEDBACK contains language adaptation instructions."""
    language_phrases = [
        "language that is used in the input",
        "plan should be in English",
        "mainly in Japanese",
        "plan should be in Japanese"
    ]
    
    for phrase in language_phrases:
        assert phrase in RESOLVE_FEEDBACK, f"Expected language phrase '{phrase}' not found in RESOLVE_FEEDBACK"


def test_resolve_feedback_conciseness_instruction():
    """Test that RESOLVE_FEEDBACK contains instructions about being concise."""
    conciseness_phrases = [
        "concise and to the point",
        "Should not be long"
    ]
    
    for phrase in conciseness_phrases:
        assert phrase in RESOLVE_FEEDBACK, f"Expected conciseness phrase '{phrase}' not found in RESOLVE_FEEDBACK"


def test_resolve_feedback_multiline_string():
    """Test that RESOLVE_FEEDBACK is a multiline string."""
    assert "\n" in RESOLVE_FEEDBACK
    lines = RESOLVE_FEEDBACK.split("\n")
    assert len(lines) > 1


def test_resolve_feedback_immutable():
    """Test that RESOLVE_FEEDBACK behaves as an immutable constant."""
    original_value = RESOLVE_FEEDBACK
    # Attempt to modify (this should not affect the original constant)
    modified = RESOLVE_FEEDBACK + " modified"
    assert RESOLVE_FEEDBACK == original_value
    assert modified != original_value


def test_resolve_feedback_string_operations():
    """Test various string operations on RESOLVE_FEEDBACK."""
    # Test string methods work correctly
    assert RESOLVE_FEEDBACK.upper() != RESOLVE_FEEDBACK  # Should contain lowercase
    assert RESOLVE_FEEDBACK.lower() != RESOLVE_FEEDBACK  # Should contain uppercase
    assert len(RESOLVE_FEEDBACK.strip()) <= len(RESOLVE_FEEDBACK)


def test_resolve_feedback_contains_triple_quotes():
    """Test that the instruction is properly formatted as a triple-quoted string."""
    # The constant should not contain the triple quotes themselves
    assert '"""' not in RESOLVE_FEEDBACK


def test_resolve_feedback_startswith_expected_content():
    """Test that RESOLVE_FEEDBACK starts with the expected introduction."""
    assert RESOLVE_FEEDBACK.strip().startswith("You are an top-class software engineer")


def test_resolve_feedback_endswith_expected_content():
    """Test that RESOLVE_FEEDBACK ends with the expected conclusion."""
    assert RESOLVE_FEEDBACK.strip().endswith("Should not be long.")


def test_resolve_feedback_word_count():
    """Test that RESOLVE_FEEDBACK has a reasonable word count for an instruction."""
    words = RESOLVE_FEEDBACK.split()
    # Should have a reasonable number of words for an instruction
    assert len(words) > 10  # At least 10 words
    assert len(words) < 200  # But not too verbose (less than 200 words)
