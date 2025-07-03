import pytest
import re
from utils.prompts.resolve_feedback import RESOLVE_FEEDBACK


def test_resolve_feedback_constant_exists():
    """Test that RESOLVE_FEEDBACK constant is defined and accessible."""
    assert RESOLVE_FEEDBACK is not None


def test_resolve_feedback_is_string():
    """Test that RESOLVE_FEEDBACK is a string type."""
    assert isinstance(RESOLVE_FEEDBACK, str)


def test_resolve_feedback_is_not_empty():
    """Test that RESOLVE_FEEDBACK is not an empty string."""
    assert len(RESOLVE_FEEDBACK.strip()) > 0


def test_resolve_feedback_contains_role_definition():
    """Test that the prompt contains role definition for the AI."""
    assert "software engineer" in RESOLVE_FEEDBACK.lower()


def test_resolve_feedback_contains_input_description():
    """Test that the prompt describes expected input types."""
    expected_inputs = [
        "pull request title",
        "body",
        "changes",
        "workflow file content",
        "check run error log"
    ]
    
    for input_type in expected_inputs:
        assert input_type in RESOLVE_FEEDBACK.lower()


def test_resolve_feedback_contains_output_format():
    """Test that the prompt specifies the expected output format."""
    expected_sections = [
        "## What the feedback is",
        "## Where to change", 
        "## How to change"
    ]
    
    for section in expected_sections:
        assert section in RESOLVE_FEEDBACK


def test_resolve_feedback_mentions_language_adaptation():
    """Test that the prompt mentions adapting to input language."""
    assert "language that is used in the input" in RESOLVE_FEEDBACK
    assert "japanese" in RESOLVE_FEEDBACK.lower()


def test_resolve_feedback_emphasizes_conciseness():
    """Test that the prompt emphasizes concise output."""
    conciseness_keywords = ["concise", "point", "not be long"]
    
    for keyword in conciseness_keywords:
        assert keyword in RESOLVE_FEEDBACK.lower()


def test_resolve_feedback_has_proper_structure():
    """Test that the prompt has proper markdown structure."""
    lines = RESOLVE_FEEDBACK.strip().split('\n')
    
    # Should have multiple lines
    assert len(lines) > 1
    
    # Should contain markdown headers
    header_lines = [line for line in lines if line.startswith('##')]
    assert len(header_lines) == 3


def test_resolve_feedback_multiline_format():
    """Test that the prompt is properly formatted as a multiline string."""
    assert '\n' in RESOLVE_FEEDBACK
    assert RESOLVE_FEEDBACK.startswith('\n')
    assert RESOLVE_FEEDBACK.endswith('\n')


def test_resolve_feedback_immutable():
    """Test that RESOLVE_FEEDBACK behaves as an immutable constant."""
    original_content = RESOLVE_FEEDBACK
    
    # Verify the constant hasn't changed after access
    assert RESOLVE_FEEDBACK == original_content
    assert id(RESOLVE_FEEDBACK) == id(original_content)


def test_resolve_feedback_contains_expected_keywords():
    """Test that the prompt contains all expected keywords for functionality."""
    expected_keywords = [
        "software engineer",
        "pull request",
        "feedback",
        "plan",
        "fix",
        "error"
    ]
    
    for keyword in expected_keywords:
        assert keyword in RESOLVE_FEEDBACK.lower(), f"Missing keyword: {keyword}"


def test_resolve_feedback_markdown_headers_format():
    """Test that markdown headers are properly formatted."""
    headers = re.findall(r'^## .+$', RESOLVE_FEEDBACK, re.MULTILINE)
    
    expected_headers = [
        "## What the feedback is",
        "## Where to change",
        "## How to change"
    ]
    
    assert len(headers) == 3
    for expected_header in expected_headers:
        assert expected_header in headers


def test_resolve_feedback_no_trailing_whitespace():
    """Test that the prompt doesn't have excessive trailing whitespace."""
    lines = RESOLVE_FEEDBACK.split('\n')
    
    # Check that no line has trailing whitespace (except the last empty line)
    for i, line in enumerate(lines[:-1]):  # Exclude the last line
        if line:  # Skip empty lines
            assert not line.endswith(' '), f"Line {i+1} has trailing whitespace: '{line}'"


def test_resolve_feedback_consistent_formatting():
    """Test that the prompt has consistent formatting throughout."""
    lines = RESOLVE_FEEDBACK.strip().split('\n')
    
    # Find header lines
    header_lines = [i for i, line in enumerate(lines) if line.startswith('##')]
    
    # Verify headers are properly spaced
    assert len(header_lines) == 3
    
    # Check that there's content between headers
    for i in range(len(header_lines) - 1):
        current_header_line = header_lines[i]
        next_header_line = header_lines[i + 1]
        # There should be at least one line between headers (even if empty)
        assert next_header_line > current_header_line


def test_resolve_feedback_encoding_compatibility():
    """Test that the prompt is compatible with common encodings."""
    # Test UTF-8 encoding/decoding
    encoded = RESOLVE_FEEDBACK.encode('utf-8')
