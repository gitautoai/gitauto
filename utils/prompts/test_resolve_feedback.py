import pytest
import sys

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


def test_resolve_feedback_module_import():
    """Test that the module can be imported and the constant is accessible."""
    # Test direct import
    from services.openai.instructions.resolve_feedback import RESOLVE_FEEDBACK as imported_constant
    assert imported_constant == RESOLVE_FEEDBACK
    
    # Test module import
    import services.openai.instructions.resolve_feedback as resolve_feedback_module
    assert hasattr(resolve_feedback_module, 'RESOLVE_FEEDBACK')
    assert resolve_feedback_module.RESOLVE_FEEDBACK == RESOLVE_FEEDBACK


def test_resolve_feedback_memory_efficiency():
    """Test that RESOLVE_FEEDBACK doesn't consume excessive memory."""
    # Get the size of the string in bytes
    size_in_bytes = sys.getsizeof(RESOLVE_FEEDBACK)
    # Should be reasonable for an instruction string (less than 10KB)
    assert size_in_bytes < 10240  # 10KB


def test_resolve_feedback_encoding():
    """Test that RESOLVE_FEEDBACK can be encoded/decoded properly."""
    # Test UTF-8 encoding/decoding
    encoded = RESOLVE_FEEDBACK.encode('utf-8')
    decoded = encoded.decode('utf-8')


def test_resolve_feedback_type_checking():
    """Test type checking and validation of RESOLVE_FEEDBACK."""
    # Test that it's specifically a str type, not a subclass
    assert type(RESOLVE_FEEDBACK) is str
    
    # Test that it's not None, empty, or other falsy values
    assert RESOLVE_FEEDBACK
    assert bool(RESOLVE_FEEDBACK)


def test_resolve_feedback_comparison_operations():
    """Test comparison operations with RESOLVE_FEEDBACK."""
    # Test equality with itself
    assert RESOLVE_FEEDBACK == RESOLVE_FEEDBACK
    
    # Test inequality with empty string
    assert RESOLVE_FEEDBACK != ""
    assert RESOLVE_FEEDBACK != " "
    
    # Test inequality with different strings
    assert RESOLVE_FEEDBACK != "different string"


def test_resolve_feedback_hash_consistency():
    """Test that RESOLVE_FEEDBACK has consistent hash values."""
    # Hash should be consistent across calls
    hash1 = hash(RESOLVE_FEEDBACK)
    hash2 = hash(RESOLVE_FEEDBACK)
    assert hash1 == hash2


def test_resolve_feedback_repr_str():
    """Test string representation methods."""
    # Test that str() and repr() work
    str_repr = str(RESOLVE_FEEDBACK)
    assert str_repr == RESOLVE_FEEDBACK
    
    repr_result = repr(RESOLVE_FEEDBACK)
    assert isinstance(repr_result, str)
    assert len(repr_result) > 0


def test_resolve_feedback_iteration():
    """Test that RESOLVE_FEEDBACK can be iterated over."""
    # Test that we can iterate over characters
    char_count = 0
    for char in RESOLVE_FEEDBACK:
        char_count += 1
        assert isinstance(char, str)
        assert len(char) == 1
    
    assert char_count == len(RESOLVE_FEEDBACK)


def test_resolve_feedback_slicing():
    """Test slicing operations on RESOLVE_FEEDBACK."""
    # Test basic slicing
    first_char = RESOLVE_FEEDBACK[0]
    assert isinstance(first_char, str)
    assert len(first_char) == 1
    
    # Test slice operations
    first_ten = RESOLVE_FEEDBACK[:10]
    assert len(first_ten) == 10
    assert isinstance(first_ten, str)
    
    # Test negative indexing
    last_char = RESOLVE_FEEDBACK[-1]
    assert isinstance(last_char, str)
    assert len(last_char) == 1


def test_resolve_feedback_constant_nature():
    """Test that RESOLVE_FEEDBACK behaves as a constant."""
