"""Unit tests for remove_duplicate_get_remote_file_content_results function."""

# Test the import
try:
    from services.anthropic.remove_duplicate_get_remote_file_content_results import \
        remove_duplicate_get_remote_file_content_results
    IMPORT_SUCCESS = True
except Exception as e:
    IMPORT_SUCCESS = False
    IMPORT_ERROR = str(e)


def test_import_works():
    """Test that the import works."""
    if not IMPORT_SUCCESS:
        pytest.fail(f"Import failed: {IMPORT_ERROR}")
    assert IMPORT_SUCCESS


def test_empty_messages():
    """Test with empty messages list."""
    if not IMPORT_SUCCESS:
        pytest.skip("Import failed")

    result = remove_duplicate_get_remote_file_content_results([])
    assert result == []


def test_basic_functionality():
    """Test basic functionality."""
    if not IMPORT_SUCCESS:
        pytest.skip("Import failed")

    messages = [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello"},
    ]
    result = remove_duplicate_get_remote_file_content_results(messages)
    assert result == messages
