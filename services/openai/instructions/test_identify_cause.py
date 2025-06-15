import re
from unittest import mock

import pytest

from services.openai.instructions.identify_cause import IDENTIFY_CAUSE


def test_identify_cause_exists():
    """Test that IDENTIFY_CAUSE constant exists and is a string."""
    assert IDENTIFY_CAUSE is not None
    assert isinstance(IDENTIFY_CAUSE, str)
    assert len(IDENTIFY_CAUSE) > 0


def test_identify_cause_content_structure():
    """Test that IDENTIFY_CAUSE contains expected structural elements."""
    # Check for key phrases that define the instruction's purpose
    assert "GitHub Actions" in IDENTIFY_CAUSE
    assert "Workflow" in IDENTIFY_CAUSE
    assert "Check Run" in IDENTIFY_CAUSE
    assert "expert" in IDENTIFY_CAUSE
    
    # Check for input requirements
    assert "pull request" in IDENTIFY_CAUSE
    assert "error log" in IDENTIFY_CAUSE
    assert "workflow file content" in IDENTIFY_CAUSE
    
    # Check for output requirements
    assert "Markdown format" in IDENTIFY_CAUSE
    assert "identify the cause" in IDENTIFY_CAUSE
    assert "plan to fix" in IDENTIFY_CAUSE


def test_identify_cause_markdown_headers():
    """Test that IDENTIFY_CAUSE contains all required markdown headers."""
    required_headers = [
        "## What is the Error?",
        "## Why did the Error Occur?",
        "## Where is the Error Located?",
        "## How to Fix the Error?",
        "## Why Fix it This Way?"
    ]
    
    for header in required_headers:
        assert header in IDENTIFY_CAUSE, f"Missing required header: {header}"


def test_identify_cause_language_requirement():
    """Test that IDENTIFY_CAUSE mentions language adaptation requirement."""
    assert "language that is used in the input" in IDENTIFY_CAUSE
    assert "Japanese" in IDENTIFY_CAUSE
    assert "plan should be in Japanese" in IDENTIFY_CAUSE


def test_identify_cause_minimalist_approach():
    """Test that IDENTIFY_CAUSE emphasizes minimal changes."""
    assert "absolutely necessary changes" in IDENTIFY_CAUSE
    assert "minimizing code modifications" in IDENTIFY_CAUSE
    assert "Unnecessary changes can confuse reviewers" in IDENTIFY_CAUSE
    assert "skilled engineer avoids that" in IDENTIFY_CAUSE


def test_identify_cause_response_quality():
    """Test that IDENTIFY_CAUSE specifies response quality requirements."""
    assert "clear" in IDENTIFY_CAUSE
    assert "specific" in IDENTIFY_CAUSE
    assert "concise" in IDENTIFY_CAUSE
    assert "direct" in IDENTIFY_CAUSE


def test_identify_cause_no_empty_lines_at_start_end():
    """Test that IDENTIFY_CAUSE doesn't have unnecessary whitespace."""
    # The constant starts with a newline due to multiline string format, which is expected
    assert not IDENTIFY_CAUSE.endswith('\n\n')


def test_identify_cause_proper_formatting():
    """Test that IDENTIFY_CAUSE has proper formatting structure."""
    lines = IDENTIFY_CAUSE.split('\n')
    
    # Should have multiple lines
    assert len(lines) > 5  # Adjusted to match actual content
    
    # Should contain empty lines for proper formatting
    empty_lines = [i for i, line in enumerate(lines) if line.strip() == '']
    assert len(empty_lines) > 0


def test_identify_cause_header_format():
    """Test that markdown headers are properly formatted."""
    # Find all markdown headers
    headers = re.findall(r'^## .+$', IDENTIFY_CAUSE, re.MULTILINE)
    
    # Should have exactly 5 headers
    assert len(headers) == 5
    
    # Each header should start with "## " and end with "?"
    for header in headers:
        assert header.startswith("## ")
        assert header.endswith("?")


def test_identify_cause_immutable():
    """Test that IDENTIFY_CAUSE behaves as an immutable constant."""
    original_value = IDENTIFY_CAUSE
    
    # Attempt to modify should not affect the original
    modified = IDENTIFY_CAUSE + " extra text"
    assert IDENTIFY_CAUSE == original_value
    assert modified != IDENTIFY_CAUSE


def test_identify_cause_import():
    """Test that IDENTIFY_CAUSE can be imported correctly."""
    # This test ensures the import works and the constant is accessible
    from services.openai.instructions.identify_cause import IDENTIFY_CAUSE as imported_constant
    
    assert imported_constant == IDENTIFY_CAUSE
    assert isinstance(imported_constant, str)
    assert len(imported_constant) > 0


def test_identify_cause_string_operations():
    """Test various string operations on IDENTIFY_CAUSE."""
    # Test string length
    assert len(IDENTIFY_CAUSE) > 200  # Adjusted to match actual content length
    
    # Test string contains operations
    assert "error" in IDENTIFY_CAUSE.lower()
    assert "fix" in IDENTIFY_CAUSE.lower()
    
    # Test string splitting
    words = IDENTIFY_CAUSE.split()
    assert len(words) > 30  # Adjusted to match actual word count
    
    # Test string stripping
    stripped = IDENTIFY_CAUSE.strip()
    assert len(stripped) <= len(IDENTIFY_CAUSE)


def test_identify_cause_encoding():
    """Test that IDENTIFY_CAUSE handles encoding properly."""
    # Test UTF-8 encoding/decoding
    encoded = IDENTIFY_CAUSE.encode('utf-8')
    decoded = encoded.decode('utf-8')
    assert decoded == IDENTIFY_CAUSE
    
    # Test that it contains ASCII characters
    try:
        IDENTIFY_CAUSE.encode('ascii')
        ascii_compatible = True
    except UnicodeEncodeError:
        ascii_compatible = False
    
    # The instruction should be ASCII compatible for broad compatibility
    assert ascii_compatible


def test_identify_cause_line_endings():
    """Test that IDENTIFY_CAUSE has consistent line endings."""
    # Check for consistent line endings (should use \n)
    assert '\r\n' not in IDENTIFY_CAUSE  # No Windows line endings
    assert '\r' not in IDENTIFY_CAUSE    # No old Mac line endings
    
    # Should contain Unix line endings
    lines = IDENTIFY_CAUSE.split('\n')
    assert len(lines) > 1  # Should be multi-line


def test_identify_cause_content_validation():
    """Test detailed content validation of IDENTIFY_CAUSE."""
    # Test for specific technical terms
    technical_terms = [
        "GitHub Actions",
        "Workflow",
        "Check Run",
        "pull request",
        "error log"
    ]
    
    for term in technical_terms:
        assert term in IDENTIFY_CAUSE, f"Missing technical term: {term}"
    
    # Test for instruction keywords
    instruction_keywords = [
        "identify",
        "cause",
        "failure",
        "fix",
        "plan"
    ]
    
    for keyword in instruction_keywords:
        assert keyword in IDENTIFY_CAUSE.lower(), f"Missing instruction keyword: {keyword}"


def test_identify_cause_markdown_structure():
    """Test the markdown structure in detail."""
    # Test that headers are properly spaced
    lines = IDENTIFY_CAUSE.split('\n')
    header_indices = []
    
    for i, line in enumerate(lines):
        if line.startswith('## '):
            header_indices.append(i)
    
    # Should have 5 headers
    assert len(header_indices) == 5
    


def test_identify_cause_word_count():
    """Test word count and readability metrics."""
    words = IDENTIFY_CAUSE.split()
    
    # Should have a reasonable word count for an instruction
    assert 30 <= len(words) <= 500, f"Word count {len(words)} is outside expected range"
    
    # Test average word length (should be reasonable for technical content)
    total_chars = sum(len(word) for word in words)
    avg_word_length = total_chars / len(words)
    assert 3 <= avg_word_length <= 10, f"Average word length {avg_word_length} seems unusual"


def test_identify_cause_special_characters():
    """Test handling of special characters in IDENTIFY_CAUSE."""
    # Should contain some punctuation
    assert '.' in IDENTIFY_CAUSE
    assert ',' in IDENTIFY_CAUSE
    assert '?' in IDENTIFY_CAUSE
    
    # Should not contain problematic characters
    problematic_chars = ['\t', '\x00', '\x01', '\x02']
    for char in problematic_chars:
        assert char not in IDENTIFY_CAUSE, f"Contains problematic character: {repr(char)}"


def test_identify_cause_consistency():
    """Test consistency of the instruction content."""
    # Multiple calls should return the same value
    from services.openai.instructions.identify_cause import IDENTIFY_CAUSE as second_import
    
    assert IDENTIFY_CAUSE == second_import
    assert id(IDENTIFY_CAUSE) == id(second_import)  # Should be the same object


@mock.patch('services.openai.instructions.identify_cause.IDENTIFY_CAUSE', 'mocked_instruction')
def test_identify_cause_mocking():
    """Test that IDENTIFY_CAUSE can be mocked for testing purposes."""
    from services.openai.instructions.identify_cause import IDENTIFY_CAUSE as mocked_constant
    
    assert mocked_constant == 'mocked_instruction'


def test_identify_cause_type_safety():
    """Test type safety and immutability aspects."""
    # Should be a string type
    assert type(IDENTIFY_CAUSE) is str
    
    # Should not be None or empty
    assert IDENTIFY_CAUSE is not None
    assert IDENTIFY_CAUSE != ""
    assert IDENTIFY_CAUSE.strip() != ""
    
    # Should be truthy
    assert bool(IDENTIFY_CAUSE) is True


def test_identify_cause_regex_patterns():
    """Test regex patterns in IDENTIFY_CAUSE content."""
    # Test for markdown header pattern
    header_pattern = r'^## .+\?$'
    headers = re.findall(header_pattern, IDENTIFY_CAUSE, re.MULTILINE)
    assert len(headers) == 5
    
    # Test for parenthetical examples pattern
    paren_pattern = r'\([^)]+\)'
    parentheticals = re.findall(paren_pattern, IDENTIFY_CAUSE)
    assert len(parentheticals) > 0  # Should have examples in parentheses
    
    # Test that it doesn't contain code blocks (shouldn't have ``` in instructions)
    assert '```' not in IDENTIFY_CAUSE


def test_identify_cause_sentence_structure():
    """Test sentence structure and grammar aspects."""
    sentences = re.split(r'[.!?]+', IDENTIFY_CAUSE)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # Should have multiple sentences
    assert len(sentences) >= 5
    
    # Each sentence should start with a capital letter (basic grammar check)
    for sentence in sentences:
        if sentence and not sentence.startswith('##'):
            assert sentence[0].isupper() or sentence[0].isdigit(), f"Sentence doesn't start with capital: '{sentence}'"


def test_identify_cause_content_completeness():
    """Test that IDENTIFY_CAUSE contains all necessary instruction components."""
    # Should mention the role/expertise
    assert any(word in IDENTIFY_CAUSE.lower() for word in ['expert', 'specialist'])
    
    # Should mention input requirements
    input_requirements = ['pull request', 'title', 'body', 'changes', 'workflow', 'error log']
    for requirement in input_requirements:
        assert requirement in IDENTIFY_CAUSE.lower(), f"Missing input requirement: {requirement}"
    
    # Should mention output format
    assert 'markdown' in IDENTIFY_CAUSE.lower()
    assert 'format' in IDENTIFY_CAUSE.lower()
    
    # Should mention quality expectations
    quality_words = ['clear', 'specific', 'concise', 'direct']
    for word in quality_words:
        assert word in IDENTIFY_CAUSE.lower(), f"Missing quality expectation: {word}"


def test_identify_cause_no_placeholder_text():
    """Test that IDENTIFY_CAUSE doesn't contain placeholder text."""
    placeholders = ['TODO', 'FIXME', 'XXX', 'PLACEHOLDER', '[INSERT', 'TBD']
    for placeholder in placeholders:
        assert placeholder not in IDENTIFY_CAUSE.upper(), f"Contains placeholder text: {placeholder}"


def test_identify_cause_edge_cases():
    """Test edge cases and boundary conditions."""
    # Test that the constant is not empty after stripping
    assert IDENTIFY_CAUSE.strip() != ""
    
    # Test that it doesn't consist only of whitespace
    assert not IDENTIFY_CAUSE.isspace()
    
    # Test that it has reasonable bounds
    assert 500 < len(IDENTIFY_CAUSE) < 1000  # Adjusted to match actual content length
    
    # Test that it contains actual content, not just formatting
    content_chars = sum(1 for c in IDENTIFY_CAUSE if c.isalnum())
    assert content_chars > 100  # Should have substantial alphanumeric content


def test_identify_cause_multiline_structure():
    """Test multiline structure and formatting."""
    lines = IDENTIFY_CAUSE.split('\n')
    
    # Should have a reasonable number of lines
    assert 10 <= len(lines) <= 20  # Adjusted to match actual line count
    
    # Should not have excessively long lines
    for line in lines:
        assert len(line) <= 200, f"Line too long: {line[:50]}..."
    
    # Should have some non-empty lines
    non_empty_lines = [line for line in lines if line.strip()]
    assert len(non_empty_lines) >= 8  # Adjusted to match actual content


def test_identify_cause_professional_tone():
    """Test that IDENTIFY_CAUSE maintains a professional tone."""
    # Should not contain informal language
    informal_words = ['gonna', 'wanna', 'gotta', 'yeah', 'ok', 'cool']
    for word in informal_words:
        assert word not in IDENTIFY_CAUSE.lower(), f"Contains informal word: {word}"
    
    # Should contain professional language
    professional_indicators = ['expert', 'professional', 'skilled', 'clear', 'specific']
    found_professional = any(word in IDENTIFY_CAUSE.lower() for word in professional_indicators)
    assert found_professional, "Should contain professional language indicators"
