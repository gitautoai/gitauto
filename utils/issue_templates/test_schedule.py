from unittest.mock import patch

import pytest

from utils.issue_templates.schedule import get_issue_title, get_issue_body


class TestGetIssueTitle:
    """Test cases for get_issue_title function."""

    def test_get_issue_title_basic_file_path(self):
        """Test generating issue title with a basic file path."""
        file_path = "src/main.py"
        result = get_issue_title(file_path)
        expected = "Schedule: Add unit tests to src/main.py"
        assert result == expected

    def test_get_issue_title_nested_file_path(self):
        """Test generating issue title with a nested file path."""
        file_path = "utils/helpers/database.py"
        result = get_issue_title(file_path)
        expected = "Schedule: Add unit tests to utils/helpers/database.py"
        assert result == expected

    def test_get_issue_title_single_file_name(self):
        """Test generating issue title with just a file name."""
        file_path = "config.py"
        result = get_issue_title(file_path)
        expected = "Schedule: Add unit tests to config.py"
        assert result == expected

    def test_get_issue_title_with_special_characters(self):
        """Test generating issue title with file paths containing special characters."""
        test_cases = [
            "src/file-with-dashes.py",
            "src/file_with_underscores.py",
            "src/file.with.dots.py",
            "src/file with spaces.py",
        ]

        for file_path in test_cases:
            result = get_issue_title(file_path)
            expected = f"Schedule: Add unit tests to {file_path}"
            assert result == expected

    def test_get_issue_title_deeply_nested_path(self):
        """Test generating issue title with a deeply nested file path."""
        file_path = "very/deeply/nested/path/to/some/file.py"
        result = get_issue_title(file_path)
        expected = "Schedule: Add unit tests to very/deeply/nested/path/to/some/file.py"
        assert result == expected

    def test_get_issue_title_different_file_extensions(self):
        """Test generating issue title with different file extensions."""
        test_cases = [
            "script.py",
            "component.js",
            "styles.css",
            "config.json",
            "README.md",
            "Dockerfile",
        ]

        for file_path in test_cases:
            result = get_issue_title(file_path)
            expected = f"Schedule: Add unit tests to {file_path}"
            assert result == expected

    def test_get_issue_title_empty_string(self):
        """Test generating issue title with an empty string."""
        file_path = ""
        result = get_issue_title(file_path)
        expected = "Schedule: Add unit tests to "
        assert result == expected

    def test_get_issue_title_return_type(self):
        """Test that the function returns a string."""
        file_path = "test.py"
        result = get_issue_title(file_path)
        assert isinstance(result, str)

    def test_get_issue_title_format_consistency(self):
        """Test that the title format is consistent across different file paths."""
        test_cases = [
            "a.py",
            "src/b.py",
            "very/long/path/c.py",
            "file-name.js",
        ]

        for file_path in test_cases:
            result = get_issue_title(file_path)
            assert result.startswith("Schedule: Add unit tests to ")
            assert result.endswith(file_path)
            assert file_path in result


class TestGetIssueBody:
    """Test cases for get_issue_body function."""

    @pytest.fixture
    def _(self):
        """Mock the imported constants."""
        with patch(
            "utils.issue_templates.schedule.GH_BASE_URL", "https://github.com"
        ) as mock_gh_url, patch(
            "utils.issue_templates.schedule.SETTINGS_LINKS", "MOCK_SETTINGS_LINKS"
        ) as mock_settings:
            yield mock_gh_url, mock_settings

    def test_get_issue_body_with_coverage(self, _):
        """Test generating issue body with coverage percentage."""
        owner = "testowner"
        repo = "testrepo"
        branch = "main"
        file_path = "src/main.py"
        statement_coverage = 75.5
        function_coverage = 80.0
        branch_coverage = 65.0
        line_coverage = 70.0
        uncovered_lines = "10,15,20"
        uncovered_functions = "func1,func2"
        uncovered_branches = "branch1,branch2"

        result = get_issue_body(
            owner,
            repo,
            branch,
            file_path,
            statement_coverage,
            function_coverage,
            branch_coverage,
            line_coverage,
            uncovered_lines,
            uncovered_functions,
            uncovered_branches,
        )

        expected_url = "https://github.com/testowner/testrepo/blob/main/src/main.py"
        assert f"Add unit tests for [src/main.py]({expected_url})" in result
        assert "Line Coverage: 70% (Uncovered Lines: 10,15,20)" in result
        assert "Statement Coverage: 75%" in result
        assert "Function Coverage: 80% (Uncovered Functions: func1,func2)" in result
        assert "Branch Coverage: 65% (Uncovered Branches: branch1,branch2)" in result
        assert "MOCK_SETTINGS_LINKS" in result

    def test_get_issue_body_without_coverage(self, _):
        """Test generating issue body without coverage percentage."""
        owner = "testowner"
        repo = "testrepo"
        branch = "main"
        file_path = "src/main.py"
        statement_coverage = None

        result = get_issue_body(
            owner,
            repo,
            branch,
            file_path,
            statement_coverage,
            None,
            None,
            None,
            None,
            None,
            None,
        )

        expected_url = "https://github.com/testowner/testrepo/blob/main/src/main.py"
        expected = (
            f"Add unit tests for [src/main.py]({expected_url}).\n\nMOCK_SETTINGS_LINKS"
        )
        assert result == expected

    def test_get_issue_body_zero_coverage(self, _):
        """Test generating issue body with zero coverage."""
        owner = "owner"
        repo = "repo"
        branch = "develop"
        file_path = "utils/helper.py"
        statement_coverage = 0.0
        function_coverage = 0.0
        branch_coverage = 0.0
        line_coverage = 0.0
        uncovered_lines = "1,2,3,4,5"
        uncovered_functions = "helper_func1,helper_func2"
        uncovered_branches = "if_branch1,else_branch1"

        result = get_issue_body(
            owner,
            repo,
            branch,
            file_path,
            statement_coverage,
            function_coverage,
            branch_coverage,
            line_coverage,
            uncovered_lines,
            uncovered_functions,
            uncovered_branches,
        )

        expected_url = "https://github.com/owner/repo/blob/develop/utils/helper.py"
        assert f"Add unit tests for [utils/helper.py]({expected_url})" in result
        assert "Line Coverage: 0% (Uncovered Lines: 1,2,3,4,5)" in result
        assert "Statement Coverage: 0%" in result
        assert (
            "Function Coverage: 0% (Uncovered Functions: helper_func1,helper_func2)"
            in result
        )
        assert (
            "Branch Coverage: 0% (Uncovered Branches: if_branch1,else_branch1)"
            in result
        )
        assert "MOCK_SETTINGS_LINKS" in result

    def test_get_issue_body_full_coverage(self, _):
        """Test generating issue body with 100% coverage."""
        owner = "owner"
        repo = "repo"
        branch = "feature/test"
        file_path = "src/complete.py"
        statement_coverage = 100.0
        function_coverage = 100.0
        branch_coverage = 100.0
        line_coverage = 100.0
        uncovered_lines = None
        uncovered_functions = None
        uncovered_branches = None

        result = get_issue_body(
            owner,
            repo,
            branch,
            file_path,
            statement_coverage,
            function_coverage,
            branch_coverage,
            line_coverage,
            uncovered_lines,
            uncovered_functions,
            uncovered_branches,
        )

        expected_url = "https://github.com/owner/repo/blob/feature/test/src/complete.py"
        assert f"Add unit tests for [src/complete.py]({expected_url})" in result
        assert "Line Coverage: 100%" in result
        assert "Statement Coverage: 100%" in result
        assert "Function Coverage: 100%" in result
        assert "Branch Coverage: 100%" in result
        assert "MOCK_SETTINGS_LINKS" in result

    def test_get_issue_body_different_branches(self, _):
        """Test generating issue body with different branch names."""
        owner = "owner"
        repo = "repo"
        file_path = "test.py"
        statement_coverage = 50.0

        test_branches = [
            "main",
            "develop",
            "feature/new-feature",
            "bugfix/fix-123",
            "release/v1.0.0",
            "hotfix/urgent-fix",
        ]

        for branch in test_branches:
            result = get_issue_body(
                owner,
                repo,
                branch,
                file_path,
                statement_coverage,
                45.0,
                55.0,
                48.0,
                "5,10,15",
                "test_func",
                "if_branch",
            )
            expected_url = f"https://github.com/owner/repo/blob/{branch}/test.py"
            assert expected_url in result
            assert "Statement Coverage: 50%" in result

    def test_get_issue_body_special_characters_in_paths(self, _):
        """Test generating issue body with special characters in file paths."""
        owner = "test-owner"
        repo = "test_repo"
        branch = "main"
        statement_coverage = 42.5

        test_files = [
            "src/file-with-dashes.py",
            "src/file_with_underscores.py",
            "src/file.with.dots.py",
            "src/file with spaces.py",
        ]

        for file_path in test_files:
            result = get_issue_body(
                owner,
                repo,
                branch,
                file_path,
                statement_coverage,
                40.0,
                45.0,
                41.0,
                "1,5,9",
                "setup_func",
                "error_branch",
            )
            expected_url = (
                f"https://github.com/test-owner/test_repo/blob/main/{file_path}"
            )
            assert f"[{file_path}]({expected_url})" in result
            assert "Statement Coverage: 42%" in result

    def test_get_issue_body_nested_file_paths(self, _):
        """Test generating issue body with deeply nested file paths."""
        owner = "owner"
        repo = "repo"
        branch = "main"
        file_path = "very/deeply/nested/path/to/file.py"
        statement_coverage = 33.3

        result = get_issue_body(
            owner,
            repo,
            branch,
            file_path,
            statement_coverage,
            30.0,
            35.0,
            32.0,
            "8,12,16,20",
            "nested_func",
            "deep_branch",
        )

        expected_url = (
            "https://github.com/owner/repo/blob/main/very/deeply/nested/path/to/file.py"
        )
        assert (
            f"Add unit tests for [very/deeply/nested/path/to/file.py]({expected_url})"
            in result
        )
        assert "Statement Coverage: 33%" in result
        assert "MOCK_SETTINGS_LINKS" in result

    def test_get_issue_body_decimal_coverage_values(self, _):
        """Test generating issue body with various decimal coverage values."""
        owner = "owner"
        repo = "repo"
        branch = "main"
        file_path = "test.py"

        test_coverages = [0.1, 25.75, 50.0, 99.99, 100.0]

        for coverage in test_coverages:
            result = get_issue_body(
                owner,
                repo,
                branch,
                file_path,
                coverage,
                coverage - 5,
                coverage + 5,
                coverage - 2,
                "1,2",
                "test_func",
                "branch1",
            )
            assert f"Statement Coverage: {int(coverage)}%" in result
            expected_url = "https://github.com/owner/repo/blob/main/test.py"
            assert expected_url in result

    def test_get_issue_body_url_construction(self, _):
        """Test that the GitHub URL is constructed correctly."""
        owner = "myowner"
        repo = "myrepo"
        branch = "mybranch"
        file_path = "myfile.py"
        statement_coverage = 80.0

        result = get_issue_body(
            owner,
            repo,
            branch,
            file_path,
            statement_coverage,
            75.0,
            85.0,
            78.0,
            "3,7,11",
            "main_func",
            "url_branch",
        )

        expected_url = "https://github.com/myowner/myrepo/blob/mybranch/myfile.py"
        assert expected_url in result

    def test_get_issue_body_return_type(self, _):
        """Test that the function returns a string."""
        result = get_issue_body(
            "owner",
            "repo",
            "main",
            "test.py",
            50.0,
            45.0,
            55.0,
            48.0,
            "1,2",
            "func",
            "branch",
        )
        assert isinstance(result, str)

        result = get_issue_body(
            "owner", "repo", "main", "test.py", None, None, None, None, None, None, None
        )
        assert isinstance(result, str)

    def test_get_issue_body_structure_with_coverage(self, _):
        """Test the structure of the issue body with coverage."""
        owner = "owner"
        repo = "repo"
        branch = "main"
        file_path = "test.py"
        statement_coverage = 75.0

        result = get_issue_body(
            owner,
            repo,
            branch,
            file_path,
            statement_coverage,
            70.0,
            80.0,
            73.0,
            "5,10",
            "test_func",
            "test_branch",
        )

        assert "Add unit tests for [test.py]" in result
        assert "Statement Coverage: 75%" in result
        assert "MOCK_SETTINGS_LINKS" in result

    def test_get_issue_body_structure_without_coverage(self, _):
        """Test the structure of the issue body without coverage."""
        owner = "owner"
        repo = "repo"
        branch = "main"
        file_path = "test.py"
        statement_coverage = None

        result = get_issue_body(
            owner,
            repo,
            branch,
            file_path,
            statement_coverage,
            None,
            None,
            None,
            None,
            None,
            None,
        )

        assert "Add unit tests for [test.py]" in result
        assert "Coverage:" not in result
        assert "MOCK_SETTINGS_LINKS" in result

    def test_get_issue_body_integration_without_mocking(self):
        """Test the function with actual imported constants."""
        owner = "testowner"
        repo = "testrepo"
        branch = "main"
        file_path = "src/example.py"
        statement_coverage = 60.0

        result = get_issue_body(
            owner,
            repo,
            branch,
            file_path,
            statement_coverage,
            55.0,
            65.0,
            58.0,
            "2,6,10",
            "example_func",
            "main_branch",
        )

        # Verify the structure without mocking constants
        assert "Add unit tests for [src/example.py]" in result
        assert (
            "https://github.com/testowner/testrepo/blob/main/src/example.py" in result
        )
        assert "Statement Coverage: 60%" in result
        # The actual SETTINGS_LINKS should be present
        assert "You can [turn off triggers]" in result
        assert "update coding rules" in result
        assert "exclude files" in result

    def test_get_issue_body_edge_cases(self, _):
        """Test edge cases for get_issue_body function."""
        # Test with empty strings
        result = get_issue_body(
            "", "", "", "", None, None, None, None, None, None, None
        )
        expected_url = "https://github.com///blob//"
        assert expected_url in result

        # Test with very small coverage
        result = get_issue_body(
            "owner",
            "repo",
            "main",
            "test.py",
            0.01,
            0.02,
            0.03,
            0.01,
            "1",
            "func",
            "branch",
        )
        assert "Statement Coverage: 0%" in result

        # Test with very large coverage (edge case, shouldn't happen in practice)
        result = get_issue_body(
            "owner",
            "repo",
            "main",
            "test.py",
            999.99,
            998.0,
            997.0,
            999.0,
            None,
            None,
            None,
        )
        assert "Statement Coverage: 999%" in result
