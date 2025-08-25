from unittest.mock import patch

import pytest

from utils.issue_templates.merge import (
    get_issue_title_for_pr_merged,
    get_issue_body_for_pr_merged,
)


class TestGetIssueTitleForPrMerged:
    """Test cases for get_issue_title_for_pr_merged function."""

    def test_get_issue_title_for_pr_merged_basic(self):
        """Test generating issue title with a basic PR number."""
        pr_number = 123
        result = get_issue_title_for_pr_merged(pr_number)
        expected = "Add unit tests for files changed in PR #123"
        assert result == expected

    def test_get_issue_title_for_pr_merged_single_digit(self):
        """Test generating issue title with a single digit PR number."""
        pr_number = 5
        result = get_issue_title_for_pr_merged(pr_number)
        expected = "Add unit tests for files changed in PR #5"
        assert result == expected

    def test_get_issue_title_for_pr_merged_large_number(self):
        """Test generating issue title with a large PR number."""
        pr_number = 99999
        result = get_issue_title_for_pr_merged(pr_number)
        expected = "Add unit tests for files changed in PR #99999"
        assert result == expected

    def test_get_issue_title_for_pr_merged_zero(self):
        """Test generating issue title with PR number zero."""
        pr_number = 0
        result = get_issue_title_for_pr_merged(pr_number)
        expected = "Add unit tests for files changed in PR #0"
        assert result == expected

    def test_get_issue_title_for_pr_merged_negative_number(self):
        """Test generating issue title with a negative PR number."""
        pr_number = -1
        result = get_issue_title_for_pr_merged(pr_number)
        expected = "Add unit tests for files changed in PR #-1"
        assert result == expected

    def test_get_issue_title_for_pr_merged_return_type(self):
        """Test that the function returns a string."""
        pr_number = 42
        result = get_issue_title_for_pr_merged(pr_number)
        assert isinstance(result, str)

    def test_get_issue_title_for_pr_merged_format_consistency(self):
        """Test that the title format is consistent across different PR numbers."""
        test_cases = [1, 10, 100, 1000, 10000]
        for pr_number in test_cases:
            result = get_issue_title_for_pr_merged(pr_number)
            assert result.startswith("Add unit tests for files changed in PR #")
            assert result.endswith(str(pr_number))
            assert f"#{pr_number}" in result


class TestGetIssueBodyForPrMerged:
    """Test cases for get_issue_body_for_pr_merged function."""

    @pytest.fixture
    def mock_settings_links(self):
        """Mock the SETTINGS_LINKS constant."""
        with patch(
            "utils.issue_templates.merge.SETTINGS_LINKS", "MOCK_SETTINGS_LINKS"
        ) as mock:
            yield mock

    def test_get_issue_body_for_pr_merged_single_file(self, mock_settings_links):
        """Test generating issue body with a single file."""
        pr_number = 123
        file_list = ["src/main.py"]
        result = get_issue_body_for_pr_merged(pr_number, file_list)

        expected_lines = [
            "Add unit tests for files changed in PR #123:",
            "- src/main.py",
            "",
            "MOCK_SETTINGS_LINKS",
        ]
        expected = "\n".join(expected_lines)
        assert result == expected

    def test_get_issue_body_for_pr_merged_multiple_files(self, mock_settings_links):
        """Test generating issue body with multiple files."""
        pr_number = 456
        file_list = ["src/main.py", "src/utils.py", "tests/test_main.py"]
        result = get_issue_body_for_pr_merged(pr_number, file_list)

        expected_lines = [
            "Add unit tests for files changed in PR #456:",
            "- src/main.py",
            "- src/utils.py",
            "- tests/test_main.py",
            "",
            "MOCK_SETTINGS_LINKS",
        ]
        expected = "\n".join(expected_lines)
        assert result == expected

    def test_get_issue_body_for_pr_merged_empty_file_list(self, mock_settings_links):
        """Test generating issue body with an empty file list."""
        pr_number = 789
        file_list = []
        result = get_issue_body_for_pr_merged(pr_number, file_list)

        expected_lines = [
            "Add unit tests for files changed in PR #789:",
            "",
            "",
            "MOCK_SETTINGS_LINKS",
        ]
        expected = "\n".join(expected_lines)
        assert result == expected

    def test_get_issue_body_for_pr_merged_files_with_special_characters(
        self, mock_settings_links
    ):
        """Test generating issue body with files containing special characters."""
        pr_number = 101
        file_list = [
            "src/file-with-dashes.py",
            "src/file_with_underscores.py",
            "src/file.with.dots.py",
            "src/file with spaces.py",
        ]
        result = get_issue_body_for_pr_merged(pr_number, file_list)

        expected_lines = [
            "Add unit tests for files changed in PR #101:",
            "- src/file-with-dashes.py",
            "- src/file_with_underscores.py",
            "- src/file.with.dots.py",
            "- src/file with spaces.py",
            "",
            "MOCK_SETTINGS_LINKS",
        ]
        expected = "\n".join(expected_lines)
        assert result == expected

    def test_get_issue_body_for_pr_merged_nested_paths(self, mock_settings_links):
        """Test generating issue body with deeply nested file paths."""
        pr_number = 202
        file_list = [
            "very/deeply/nested/path/to/file.py",
            "another/deep/path/structure/file.js",
            "simple.py",
        ]
        result = get_issue_body_for_pr_merged(pr_number, file_list)

        expected_lines = [
            "Add unit tests for files changed in PR #202:",
            "- very/deeply/nested/path/to/file.py",
            "- another/deep/path/structure/file.js",
            "- simple.py",
            "",
            "MOCK_SETTINGS_LINKS",
        ]
        expected = "\n".join(expected_lines)
        assert result == expected

    def test_get_issue_body_for_pr_merged_return_type(self, mock_settings_links):
        """Test that the function returns a string."""
        pr_number = 303
        file_list = ["test.py"]
        result = get_issue_body_for_pr_merged(pr_number, file_list)
        assert isinstance(result, str)

    def test_get_issue_body_for_pr_merged_structure_consistency(
        self, mock_settings_links
    ):
        """Test that the body structure is consistent across different inputs."""
        test_cases = [
            (1, ["file1.py"]),
            (100, ["file1.py", "file2.py"]),
            (999, ["path/to/file.py", "another/file.js", "third.txt"]),
        ]

        for pr_number, file_list in test_cases:
            result = get_issue_body_for_pr_merged(pr_number, file_list)
            lines = result.split("\n")

            # Check that it starts with the PR description
            assert lines[0] == f"Add unit tests for files changed in PR #{pr_number}:"

            # Check that each file is listed with a bullet point
            for i, file_path in enumerate(file_list):
                assert lines[i + 1] == f"- {file_path}"

            # Check that there's an empty line before settings links
            assert lines[len(file_list) + 1] == ""

            # Check that settings links are at the end
            assert lines[len(file_list) + 2] == "MOCK_SETTINGS_LINKS"

    def test_get_issue_body_for_pr_merged_integration_without_mocking(self):
        """Test the function with actual SETTINGS_LINKS import."""
        pr_number = 404
        file_list = ["src/example.py"]
        result = get_issue_body_for_pr_merged(pr_number, file_list)

        # Verify the structure without mocking SETTINGS_LINKS
        assert f"Add unit tests for files changed in PR #{pr_number}:" in result
        assert "- src/example.py" in result
        # The actual SETTINGS_LINKS should be present at the end
        assert "You can [turn off triggers]" in result
        assert "update coding rules" in result
        assert "exclude files" in result
