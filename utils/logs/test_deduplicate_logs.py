from utils.logs.deduplicate_logs import deduplicate_logs


def test_deduplicate_logs_passthrough():
    """
    Test that deduplicate_logs currently just passes through content unchanged.
    """
    input_text = "line 1\nline 2\nline 1\nline 3"
    result = deduplicate_logs(input_text)
    assert result == input_text, "deduplicate_logs should pass through unchanged"


if __name__ == "__main__":
    test_deduplicate_logs_passthrough()
    print("All deduplication tests passed!")
