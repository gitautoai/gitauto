import pytest

from services.webhook.utils.extract_selected_files import extract_selected_files


class TestExtractSelectedFiles:
    """Test cases for extract_selected_files function."""

    def test_empty_comment_body(self):
        """Test extracting files from empty comment body."""
        # Arrange
        comment_body = ""

        # Act
        result = extract_selected_files(comment_body)

        # Assert
        assert not result

    def test_comment_body_without_checkboxes(self):
        """Test extracting files from comment body without any checkboxes."""
        # Arrange
        comment_body = "This is a regular comment without any checkboxes."

        # Act
        result = extract_selected_files(comment_body)

        # Assert
        assert not result

    def test_comment_body_with_unchecked_boxes(self):
        """Test extracting files from comment body with unchecked boxes."""
        # Arrange
        comment_body = """
        - [ ] `src/file1.py`
        - [ ] `src/file2.py`
        - [ ] `tests/test_file.py`
        """

        # Act
        result = extract_selected_files(comment_body)

        # Assert
        assert not result

    def test_single_checked_file(self):
        """Test extracting single checked file."""
        # Arrange
        comment_body = "- [x] `src/main.py`"

        # Act
        result = extract_selected_files(comment_body)

        # Assert
        assert result == ["src/main.py"]

    def test_multiple_checked_files(self):
        """Test extracting multiple checked files."""
        # Arrange
        comment_body = """
        - [x] `src/file1.py`
        - [x] `src/file2.py`
        - [x] `tests/test_file.py`
        """

        # Act
        result = extract_selected_files(comment_body)

        # Assert
        assert result == ["src/file1.py", "src/file2.py", "tests/test_file.py"]

    def test_mixed_checked_and_unchecked_files(self):
        """Test extracting files with mixed checked and unchecked boxes."""
        # Arrange
        comment_body = """
        - [x] `src/selected1.py`
        - [ ] `src/unselected1.py`
        - [x] `src/selected2.py`
        - [ ] `src/unselected2.py`
        - [x] `tests/selected_test.py`
        """

        # Act
        result = extract_selected_files(comment_body)

        # Assert
        assert result == [
            "src/selected1.py",
            "src/selected2.py",
            "tests/selected_test.py",
        ]

    def test_generate_tests_entries_filtered_out(self):
        """Test that entries containing 'Generate Tests' are filtered out."""
        # Arrange
        comment_body = """
        - [x] `src/file1.py`
        - [x] `Generate Tests for src/file2.py`
        - [x] `src/file3.py`
        - [x] `Generate Tests - src/file4.py`
        """

        # Act
        result = extract_selected_files(comment_body)

        # Assert
        assert result == ["src/file1.py", "src/file3.py"]

    def test_various_file_path_formats(self):
        """Test extracting files with various path formats."""
        # Arrange
        comment_body = """
        - [x] `simple.py`
        - [x] `path/to/nested/file.py`
        - [x] `file-with-dashes.py`
        - [x] `file_with_underscores.py`
        - [x] `file.with.dots.py`
        - [x] `UPPERCASE.PY`
        - [x] `123numeric.py`
        - [x] `src/deep/nested/path/file.py`
        """

        # Act
        result = extract_selected_files(comment_body)

        # Assert
        expected = [
            "simple.py",
            "path/to/nested/file.py",
            "file-with-dashes.py",
            "file_with_underscores.py",
            "file.with.dots.py",
            "UPPERCASE.PY",
            "123numeric.py",
            "src/deep/nested/path/file.py",
        ]
        assert result == expected

    def test_files_with_special_characters(self):
        """Test extracting files with special characters in names."""
        # Arrange
        comment_body = """
        - [x] `file with spaces.py`
        - [x] `file@with#symbols$.py`
        - [x] `file(with)parentheses.py`
        - [x] `file[with]brackets.py`
        - [x] `file{with}braces.py`
        """

        # Act
        result = extract_selected_files(comment_body)

        # Assert
        expected = [
            "file with spaces.py",
            "file@with#symbols$.py",
            "file(with)parentheses.py",
            "file[with]brackets.py",
            "file{with}braces.py",
        ]
        assert result == expected

    def test_comment_with_extra_whitespace(self):
        """Test extracting files from comment with extra whitespace."""
        # Arrange
        comment_body = """
        
        - [x] `src/file1.py`
        
        - [x] `src/file2.py`
        
        """

        # Act
        result = extract_selected_files(comment_body)

        # Assert
        assert result == ["src/file1.py", "src/file2.py"]

    def test_comment_with_other_content(self):
        """Test extracting files from comment with other content mixed in."""
        # Arrange
        comment_body = """
        Here are the selected files:
        
        - [x] `src/main.py`
        - [ ] `src/unused.py`
        - [x] `tests/test_main.py`
        
        Please review these changes carefully.
        
        Additional notes:
        - This is important
        - Don't forget to test
        """

        # Act
        result = extract_selected_files(comment_body)

        # Assert
        assert result == ["src/main.py", "tests/test_main.py"]

    def test_case_sensitive_generate_tests_filter(self):
        """Test that 'Generate Tests' filter is case sensitive."""
        # Arrange
        comment_body = """
        - [x] `src/file1.py`
        - [x] `Generate Tests for file2.py`
        - [x] `generate tests for file3.py`
        - [x] `GENERATE TESTS for file4.py`
        - [x] `Generate tests for file5.py`
        """

        # Act
        result = extract_selected_files(comment_body)

        # Assert
        # Only exact case "Generate Tests" should be filtered out
        assert result == [
            "src/file1.py",
            "generate tests for file3.py",
            "GENERATE TESTS for file4.py",
            "Generate tests for file5.py",
        ]

    def test_large_number_of_files(self):
        """Test extracting a large number of files."""
        # Arrange
        num_files = 50
        comment_lines = []
        expected_files = []

        for i in range(num_files):
            filename = f"src/file_{i:03d}.py"
            comment_lines.append(f"- [x] `{filename}`")
            expected_files.append(filename)

        comment_body = "\n".join(comment_lines)

        # Act
        result = extract_selected_files(comment_body)

        # Assert
        assert len(result) == num_files
        assert result == expected_files

    def test_regex_pattern_edge_cases(self):
        """Test edge cases for the regex pattern matching."""
        # Arrange
        comment_body = """
        - [x] `normal_file.py`
        - [x] ``
        - [x] `file_with_backtick`.py`
        - [x] `file.py` extra text
        -[x] `no_space_before_bracket.py`
        - [x]`no_space_after_bracket.py`
        """

        # Act
        result = extract_selected_files(comment_body)

        # Assert
        # Entries matching the regex pattern should be extracted
        assert result == ["normal_file.py", "file_with_backtick", "file.py"]

    @pytest.mark.parametrize(
        "comment_body,expected",
        [
            ("- [x] `single.py`", ["single.py"]),
            ("- [x] `file1.py`\n- [x] `file2.py`", ["file1.py", "file2.py"]),
            ("- [ ] `unchecked.py`", []),
            ("- [x] `Generate Tests file.py`", []),
            ("", []),
            ("No checkboxes here", []),
        ],
    )
    def test_parametrized_scenarios(self, comment_body, expected):
        """Test various scenarios using parametrized tests."""
        # Act
        result = extract_selected_files(comment_body)

        # Assert
        assert result == expected

    def test_preserves_file_order(self):
        """Test that the function preserves the order of files as they appear."""
        # Arrange
        comment_body = """
        - [x] `zebra.py`
        - [x] `alpha.py`
        - [x] `beta.py`
        - [x] `gamma.py`
        """

        # Act
        result = extract_selected_files(comment_body)

        # Assert
        assert result == ["zebra.py", "alpha.py", "beta.py", "gamma.py"]

    def test_duplicate_files_preserved(self):
        """Test that duplicate file entries are preserved."""
        # Arrange
        comment_body = """
        - [x] `duplicate.py`
        - [x] `other.py`
        - [x] `duplicate.py`
        """

        # Act
        result = extract_selected_files(comment_body)

        # Assert
        assert result == ["duplicate.py", "other.py", "duplicate.py"]
