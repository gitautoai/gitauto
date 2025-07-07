from services.webhook.utils.extract_selected_files import extract_selected_files


def test_extract_selected_files_empty_string():
    """Test with empty string input."""
    result = extract_selected_files("")
    assert result == []


def test_extract_selected_files_no_checkboxes():
    """Test with comment body that has no checkboxes."""
    comment_body = "This is just a regular comment with no checkboxes."
    result = extract_selected_files(comment_body)
    assert result == []


def test_extract_selected_files_unchecked_boxes():
    """Test with unchecked checkboxes."""
    comment_body = """
    - [ ] `src/main.py`
    - [ ] `utils/helper.py`
    """
    result = extract_selected_files(comment_body)
    assert result == []


def test_extract_selected_files_single_checked_file():
    """Test with single checked file."""
    comment_body = "- [x] `src/main.py`"
    result = extract_selected_files(comment_body)
    assert result == ["src/main.py"]


def test_extract_selected_files_multiple_checked_files():
    """Test with multiple checked files."""
    comment_body = """
    - [x] `src/main.py`
    - [x] `utils/helper.py`
    - [x] `config/settings.py`
    """
    result = extract_selected_files(comment_body)
    assert result == ["src/main.py", "utils/helper.py", "config/settings.py"]


def test_extract_selected_files_mixed_checked_unchecked():
    """Test with mix of checked and unchecked files."""
    comment_body = """
    - [x] `src/main.py`
    - [ ] `utils/helper.py`
    - [x] `config/settings.py`
    - [ ] `tests/test_main.py`
    """
    result = extract_selected_files(comment_body)
    assert result == ["src/main.py", "config/settings.py"]


def test_extract_selected_files_filters_generate_tests():
    """Test that entries containing 'Generate Tests' are filtered out."""
    comment_body = """
    - [x] `src/main.py`
    - [x] Generate Tests
    - [x] `utils/helper.py`
    """
    result = extract_selected_files(comment_body)
    assert result == ["src/main.py", "utils/helper.py"]


def test_extract_selected_files_filters_generate_tests_with_backticks():
    """Test that entries containing 'Generate Tests' in backticks are filtered out."""
    comment_body = """
    - [x] `src/main.py`
    - [x] `Generate Tests - gitauto`
    - [x] `utils/helper.py`
    """
    result = extract_selected_files(comment_body)
    assert result == ["src/main.py", "utils/helper.py"]


def test_extract_selected_files_complex_file_paths():
    """Test with complex file paths including directories and extensions."""
    comment_body = """
    - [x] `services/webhook/utils/extract_selected_files.py`
    - [x] `src/components/Button/Button.tsx`
    - [x] `tests/unit/test_helper.spec.js`
    - [x] `config/database/migrations/001_initial.sql`
    """
    result = extract_selected_files(comment_body)
    assert result == [
        "services/webhook/utils/extract_selected_files.py",
        "src/components/Button/Button.tsx",
        "tests/unit/test_helper.spec.js",
        "config/database/migrations/001_initial.sql",
    ]


def test_extract_selected_files_with_extra_whitespace():
    """Test with extra whitespace around checkboxes."""
    comment_body = """
      - [x]   `src/main.py`  
    - [x] `utils/helper.py`
        - [x] `config/settings.py`
    """
    result = extract_selected_files(comment_body)
    assert result == ["src/main.py", "utils/helper.py", "config/settings.py"]


def test_extract_selected_files_with_other_markdown():
    """Test with other markdown content mixed in."""
    comment_body = """
    ## Test Selection
    
    Please select the files you want to test:
    
    - [x] `src/main.py`
    - [ ] `utils/helper.py`
    - [x] `config/settings.py`
    
    **Note**: This will generate tests for the selected files.
    """
    result = extract_selected_files(comment_body)
    assert result == ["src/main.py", "config/settings.py"]
