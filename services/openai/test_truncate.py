from config import OPENAI_MAX_CONTEXT_TOKENS, OPENAI_MAX_STRING_LENGTH
from services.openai.truncate import truncate_message


def test_truncate_message_within_limits():
    input_message = "This is a normal message"
    result = truncate_message(input_message=input_message)
    assert result == input_message


def test_truncate_message_empty_string():
    input_message = ""
    result = truncate_message(input_message=input_message)
    assert result == input_message


def test_truncate_message_string_length():
    # Create a string slightly longer than OPENAI_MAX_STRING_LENGTH
    # Using a reasonable size to avoid stack overflow
    test_length = min(OPENAI_MAX_STRING_LENGTH + 100, 50000)
    input_message = "x" * test_length
    result = truncate_message(input_message=input_message)
    assert len(result) == min(OPENAI_MAX_STRING_LENGTH, test_length)
    assert result == "x" * min(OPENAI_MAX_STRING_LENGTH, test_length)


def test_truncate_message_token_count():
    # Create a string that will exceed token limit
    # Using a simple repeating word pattern
    # Each word is about 1 token
    words = ["test", "token", "limit", "check"]
    input_message = " ".join(words * (OPENAI_MAX_CONTEXT_TOKENS + 10))
    result = truncate_message(input_message=input_message)
    
    # The result should be shorter than the input
    assert len(result) < len(input_message)


def test_truncate_message_error_handling():
    # Test the error handling decorator by passing None
    # which would normally raise an error when slicing
    result = truncate_message(input_message=None)  # type: ignore
    assert result == ""


def test_truncate_message_unicode():
    # Test with unicode characters to ensure proper handling
    # Using a smaller repeat count to avoid stack overflow
    test_length = min(OPENAI_MAX_STRING_LENGTH + 10, 1000)
    input_message = "🌟" * test_length
    result = truncate_message(input_message=input_message)
    
    # Should truncate to max length while preserving unicode characters
    assert len(result) <= OPENAI_MAX_STRING_LENGTH
    assert all(char == "🌟" for char in result)