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
    # Create a string longer than OPENAI_MAX_STRING_LENGTH
    input_message = "x" * (OPENAI_MAX_STRING_LENGTH + 1000)
    result = truncate_message(input_message=input_message)
    assert len(result) == OPENAI_MAX_STRING_LENGTH
    assert result == "x" * OPENAI_MAX_STRING_LENGTH


def test_truncate_message_token_count():
    # Create a string that will exceed token limit
    # Each token is roughly 4 chars in English, so we'll create a string
    # that should exceed the token limit
    input_message = "token " * (OPENAI_MAX_CONTEXT_TOKENS + 1000)
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
    input_message = "🌟" * (OPENAI_MAX_STRING_LENGTH + 100)
    result = truncate_message(input_message=input_message)
    
    # Should truncate to max length while preserving unicode characters
    assert len(result) == OPENAI_MAX_STRING_LENGTH