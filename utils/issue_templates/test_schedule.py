from unittest.mock import patch

import pytest
from utils.issue_templates.schedule import get_issue_body, get_issue_title


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

    def test_get_issue_title_empty_string(self):
        """Test generating issue title with an empty string."""
        file_path = ""
        result = get_issue_title(file_path)
        expected = "Schedule: Add unit tests to "
        assert result == expected

    def test_get_issue_title_special_characters(self):
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


class TestGetIssueBody:
    """Test cases for get_issue_body function."""

    @pytest.fixture
    def mock_constants(self):
        """Mock the imported constants."""
        with patch(
            "utils.issue_templates.schedule.GH_BASE_URL", "https://github.com"
        ) as mock_gh_url, patch(
            "utils.issue_templates.schedule.SETTINGS_LINKS", "MOCK_SETTINGS_LINKS"
        ) as mock_settings:
            yield mock_gh_url, mock_settings

    def test_get_issue_body_no_coverage_data(self, mock_constants):
        """Test early return when all coverage data is None."""
        result = get_issue_body(
            owner="testowner",
            repo="testrepo",
            branch="main",
            file_path="src/main.py",
            statement_coverage=None,
            function_coverage=None,
            branch_coverage=None,
            line_coverage=None,
            uncovered_lines=None,
            uncovered_functions=None,
            uncovered_branches=None,
        )

        expected_url = "https://github.com/testowner/testrepo/blob/main/src/main.py"
        expected = f"Add unit tests for [src/main.py]({expected_url}).\n\nMOCK_SETTINGS_LINKS"
        assert result == expected

    def test_get_issue_body_line_coverage_with_uncovered_lines(self, mock_constants):
        """Test line coverage branch (line 33) with uncovered lines."""
        result = get_issue_body(
            owner="testowner",
            repo="testrepo",
            branch="main",
            file_path="src/main.py",
            statement_coverage=None,
            function_coverage=None,
            branch_coverage=None,
            line_coverage=85.5,
            uncovered_lines="10,15,20",
            uncovered_functions=None,
            uncovered_branches=None,
        )

        expected_url = "https://github.com/testowner/testrepo/blob/main/src/main.py"
        assert f"Add unit tests for [src/main.py]({expected_url})" in result
        assert "- Line Coverage: 85% (Uncovered Lines: 10,15,20)" in result
        assert "Statement Coverage" not in result
        assert "Function Coverage" not in result
        assert "Branch Coverage" not in result
        assert "MOCK_SETTINGS_LINKS" in result

    def test_get_issue_body_line_coverage_without_uncovered_lines(self, mock_constants):
        """Test line coverage branch (line 33) without uncovered lines."""
        result = get_issue_body(
            owner="testowner",
            repo="testrepo",
            branch="main",
            file_path="src/main.py",
            statement_coverage=None,
            function_coverage=None,
            branch_coverage=None,
            line_coverage=100.0,
            uncovered_lines=None,
            uncovered_functions=None,
            uncovered_branches=None,
        )

        expected_url = "https://github.com/testowner/testrepo/blob/main/src/main.py"
        assert f"Add unit tests for [src/main.py]({expected_url})" in result
        assert "- Line Coverage: 100%" in result
        assert "(Uncovered Lines:" not in result
        assert "MOCK_SETTINGS_LINKS" in result

    def test_get_issue_body_line_coverage_with_empty_uncovered_lines(self, mock_constants):
        """Test line coverage branch (line 33) with empty uncovered lines string."""
        result = get_issue_body(
            owner="testowner",
            repo="testrepo",
            branch="main",
            file_path="src/main.py",
            statement_coverage=None,
            function_coverage=None,
            branch_coverage=None,
            line_coverage=90.0,
            uncovered_lines="",
            uncovered_functions=None,
            uncovered_branches=None,
        )

        expected_url = "https://github.com/testowner/testrepo/blob/main/src/main.py"
        assert f"Add unit tests for [src/main.py]({expected_url})" in result
        assert "- Line Coverage: 90%" in result
        assert "(Uncovered Lines:" not in result
        assert "MOCK_SETTINGS_LINKS" in result

    def test_get_issue_body_statement_coverage_only(self, mock_constants):
        """Test statement coverage branch (line 41)."""
        result = get_issue_body(
            owner="testowner",
            repo="testrepo",
            branch="main",
            file_path="src/main.py",
            statement_coverage=75.5,
            function_coverage=None,
            branch_coverage=None,
            line_coverage=None,
            uncovered_lines=None,
            uncovered_functions=None,
            uncovered_branches=None,
        )

        expected_url = "https://github.com/testowner/testrepo/blob/main/src/main.py"
        assert f"Add unit tests for [src/main.py]({expected_url})" in result
        assert "- Statement Coverage: 75%" in result
        assert "Line Coverage" not in result
        assert "Function Coverage" not in result
        assert "Branch Coverage" not in result
        assert "MOCK_SETTINGS_LINKS" in result

    def test_get_issue_body_function_coverage_with_uncovered_functions(self, mock_constants):
        """Test function coverage branch (line 44) with uncovered functions."""
        result = get_issue_body(
            owner="testowner",
            repo="testrepo",
            branch="main",
            file_path="src/main.py",
            statement_coverage=None,
            function_coverage=80.0,
            branch_coverage=None,
            line_coverage=None,
            uncovered_lines=None,
            uncovered_functions="func1,func2",
            uncovered_branches=None,
        )

        expected_url = "https://github.com/testowner/testrepo/blob/main/src/main.py"
        assert f"Add unit tests for [src/main.py]({expected_url})" in result
        assert "- Function Coverage: 80% (Uncovered Functions: func1,func2)" in result
        assert "Line Coverage" not in result
        assert "Statement Coverage" not in result
        assert "Branch Coverage" not in result
        assert "MOCK_SETTINGS_LINKS" in result

    def test_get_issue_body_function_coverage_without_uncovered_functions(self, mock_constants):
        """Test function coverage branch (line 44) without uncovered functions."""
        result = get_issue_body(
            owner="testowner",
            repo="testrepo",
            branch="main",
            file_path="src/main.py",
            statement_coverage=None,
            function_coverage=100.0,
            branch_coverage=None,
            line_coverage=None,
            uncovered_lines=None,
            uncovered_functions=None,
            uncovered_branches=None,
        )

        expected_url = "https://github.com/testowner/testrepo/blob/main/src/main.py"
        assert f"Add unit tests for [src/main.py]({expected_url})" in result
        assert "- Function Coverage: 100%" in result
        assert "(Uncovered Functions:" not in result
        assert "MOCK_SETTINGS_LINKS" in result

    def test_get_issue_body_function_coverage_with_empty_uncovered_functions(self, mock_constants):
        """Test function coverage branch (line 44) with empty uncovered functions string."""
        result = get_issue_body(
            owner="testowner",
            repo="testrepo",
            branch="main",
            file_path="src/main.py",
            statement_coverage=None,
            function_coverage=85.0,
            branch_coverage=None,
            line_coverage=None,
            uncovered_lines=None,
            uncovered_functions="",
            uncovered_branches=None,
        )

        expected_url = "https://github.com/testowner/testrepo/blob/main/src/main.py"
        assert f"Add unit tests for [src/main.py]({expected_url})" in result
        assert "- Function Coverage: 85%" in result
        assert "(Uncovered Functions:" not in result
        assert "MOCK_SETTINGS_LINKS" in result

    def test_get_issue_body_branch_coverage_with_uncovered_branches(self, mock_constants):
        """Test branch coverage branch (line 54) with uncovered branches."""
        result = get_issue_body(
            owner="testowner",
            repo="testrepo",
            branch="main",
            file_path="src/main.py",
            statement_coverage=None,
            function_coverage=None,
            branch_coverage=65.0,
            line_coverage=None,
            uncovered_lines=None,
            uncovered_functions=None,
            uncovered_branches="branch1,branch2",
        )

        expected_url = "https://github.com/testowner/testrepo/blob/main/src/main.py"
        assert f"Add unit tests for [src/main.py]({expected_url})" in result
        assert "- Branch Coverage: 65% (Uncovered Branches: branch1,branch2)" in result
        assert "Line Coverage" not in result
        assert "Statement Coverage" not in result
        assert "Function Coverage" not in result
        assert "MOCK_SETTINGS_LINKS" in result

    def test_get_issue_body_branch_coverage_without_uncovered_branches(self, mock_constants):
        """Test branch coverage branch (line 54) without uncovered branches."""
        result = get_issue_body(
            owner="testowner",
            repo="testrepo",
            branch="main",
            file_path="src/main.py",
            statement_coverage=None,
            function_coverage=None,
            branch_coverage=100.0,
            line_coverage=None,
            uncovered_lines=None,
            uncovered_functions=None,
            uncovered_branches=None,
        )

        expected_url = "https://github.com/testowner/testrepo/blob/main/src/main.py"
        assert f"Add unit tests for [src/main.py]({expected_url})" in result
        assert "- Branch Coverage: 100%" in result
        assert "(Uncovered Branches:" not in result
        assert "MOCK_SETTINGS_LINKS" in result

    def test_get_issue_body_branch_coverage_with_empty_uncovered_branches(self, mock_constants):
        """Test branch coverage branch (line 54) with empty uncovered branches string."""
        result = get_issue_body(
            owner="testowner",
            repo="testrepo",
            branch="main",
            file_path="src/main.py",
            statement_coverage=None,
            function_coverage=None,
            branch_coverage=70.0,
            line_coverage=None,
            uncovered_lines=None,
            uncovered_functions=None,
            uncovered_branches="",
        )

        expected_url = "https://github.com/testowner/testrepo/blob/main/src/main.py"
        assert f"Add unit tests for [src/main.py]({expected_url})" in result
        assert "- Branch Coverage: 70%" in result
        assert "(Uncovered Branches:" not in result
        assert "MOCK_SETTINGS_LINKS" in result

    def test_get_issue_body_all_coverage_types_with_uncovered_items(self, mock_constants):
        """Test with all coverage types and uncovered items."""
        result = get_issue_body(
            owner="testowner",
            repo="testrepo",
            branch="main",
            file_path="src/main.py",
            statement_coverage=75.5,
            function_coverage=80.0,
            branch_coverage=65.0,
            line_coverage=70.0,
            uncovered_lines="10,15,20",
            uncovered_functions="func1,func2",
            uncovered_branches="branch1,branch2",
        )

        expected_url = "https://github.com/testowner/testrepo/blob/main/src/main.py"
        assert f"Add unit tests for [src/main.py]({expected_url})" in result
        assert "- Line Coverage: 70% (Uncovered Lines: 10,15,20)" in result
        assert "- Statement Coverage: 75%" in result
        assert "- Function Coverage: 80% (Uncovered Functions: func1,func2)" in result
        assert "- Branch Coverage: 65% (Uncovered Branches: branch1,branch2)" in result
        assert "Focus on covering the uncovered areas, including both happy paths, error cases, edge cases, and corner cases." in result
        assert "MOCK_SETTINGS_LINKS" in result

    def test_get_issue_body_all_coverage_types_without_uncovered_items(self, mock_constants):
        """Test with all coverage types but no uncovered items."""
        result = get_issue_body(
            owner="testowner",
            repo="testrepo",
            branch="main",
            file_path="src/main.py",
            statement_coverage=100.0,
            function_coverage=100.0,
            branch_coverage=100.0,
            line_coverage=100.0,
            uncovered_lines=None,
            uncovered_functions=None,
            uncovered_branches=None,
        )

        expected_url = "https://github.com/testowner/testrepo/blob/main/src/main.py"
        assert f"Add unit tests for [src/main.py]({expected_url})" in result
        assert "- Line Coverage: 100%" in result
        assert "- Statement Coverage: 100%" in result
        assert "- Function Coverage: 100%" in result
        assert "- Branch Coverage: 100%" in result
        assert "(Uncovered" not in result
        assert "MOCK_SETTINGS_LINKS" in result

    def test_get_issue_body_zero_coverage(self, mock_constants):
        """Test with zero coverage values."""
        result = get_issue_body(
            owner="owner",
            repo="repo",
            branch="develop",
            file_path="utils/helper.py",
            statement_coverage=0.0,
            function_coverage=0.0,
            branch_coverage=0.0,
            line_coverage=0.0,
            uncovered_lines="1,2,3,4,5",
            uncovered_functions="helper_func1,helper_func2",
            uncovered_branches="if_branch1,else_branch1",
        )

        expected_url = "https://github.com/owner/repo/blob/develop/utils/helper.py"
        assert f"Add unit tests for [utils/helper.py]({expected_url})" in result
        assert "- Line Coverage: 0% (Uncovered Lines: 1,2,3,4,5)" in result
        assert "- Statement Coverage: 0%" in result
        assert "- Function Coverage: 0% (Uncovered Functions: helper_func1,helper_func2)" in result
        assert "- Branch Coverage: 0% (Uncovered Branches: if_branch1,else_branch1)" in result
        assert "MOCK_SETTINGS_LINKS" in result

    def test_get_issue_body_decimal_coverage_values(self, mock_constants):
        """Test with decimal coverage values that get converted to integers."""
        result = get_issue_body(
            owner="owner",
            repo="repo",
            branch="main",
            file_path="test.py",
            statement_coverage=75.75,
            function_coverage=80.99,
            branch_coverage=65.01,
            line_coverage=70.50,
            uncovered_lines="1,2",
            uncovered_functions="test_func",
            uncovered_branches="branch1",
        )

        assert "- Line Coverage: 70% (Uncovered Lines: 1,2)" in result
        assert "- Statement Coverage: 75%" in result
        assert "- Function Coverage: 80% (Uncovered Functions: test_func)" in result
        assert "- Branch Coverage: 65% (Uncovered Branches: branch1)" in result

    def test_get_issue_body_coverage_order(self, mock_constants):
        """Test that coverage details appear in the correct order."""
        result = get_issue_body(
            owner="owner",
            repo="repo",
            branch="main",
            file_path="test.py",
            statement_coverage=75.0,
            function_coverage=80.0,
            branch_coverage=65.0,
            line_coverage=70.0,
            uncovered_lines="1,2",
            uncovered_functions="func1",
            uncovered_branches="branch1",
        )

        lines = result.split('\n')
        coverage_lines = [line for line in lines if 'Coverage:' in line]

        assert len(coverage_lines) == 4
        assert "Line Coverage:" in coverage_lines[0]
        assert "Statement Coverage:" in coverage_lines[1]
        assert "Function Coverage:" in coverage_lines[2]
        assert "Branch Coverage:" in coverage_lines[3]

    def test_get_issue_body_url_construction(self, mock_constants):
        """Test that the GitHub URL is constructed correctly."""
        result = get_issue_body(
            owner="myowner",
            repo="myrepo",
            branch="mybranch",
            file_path="myfile.py",
            statement_coverage=80.0,
            function_coverage=None,
            branch_coverage=None,
            line_coverage=None,
            uncovered_lines=None,
            uncovered_functions=None,
            uncovered_branches=None,
        )

        expected_url = "https://github.com/myowner/myrepo/blob/mybranch/myfile.py"
        assert expected_url in result

    def test_get_issue_body_special_characters_in_paths(self, mock_constants):
        """Test with special characters in file paths."""
        test_files = [
            "src/file-with-dashes.py",
            "src/file_with_underscores.py",
            "src/file.with.dots.py",
            "src/file with spaces.py",
        ]

        for file_path in test_files:
            result = get_issue_body(
                owner="test-owner",
                repo="test_repo",
                branch="main",
                file_path=file_path,
                statement_coverage=42.5,
                function_coverage=None,
                branch_coverage=None,
                line_coverage=None,
                uncovered_lines=None,
                uncovered_functions=None,
                uncovered_branches=None,
            )
            expected_url = f"https://github.com/test-owner/test_repo/blob/main/{file_path}"
            assert f"[{file_path}]({expected_url})" in result
            assert "- Statement Coverage: 42%" in result

    def test_get_issue_body_different_branches(self, mock_constants):
        """Test with different branch names."""
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
                owner="owner",
                repo="repo",
                branch=branch,
                file_path="test.py",
                statement_coverage=50.0,
                function_coverage=None,
                branch_coverage=None,
                line_coverage=None,
                uncovered_lines=None,
                uncovered_functions=None,
                uncovered_branches=None,
            )
            expected_url = f"https://github.com/owner/repo/blob/{branch}/test.py"
            assert expected_url in result
            assert "- Statement Coverage: 50%" in result

    def test_get_issue_body_edge_cases(self, mock_constants):
        """Test edge cases."""
        # Test with empty strings for owner, repo, branch, file_path
        result = get_issue_body(
            owner="",
            repo="",
            branch="",
            file_path="",
            statement_coverage=None,
            function_coverage=None,
            branch_coverage=None,
            line_coverage=None,
            uncovered_lines=None,
            uncovered_functions=None,
            uncovered_branches=None,
        )
        expected_url = "https://github.com///blob//"
        assert expected_url in result

        # Test with very small coverage values
        result = get_issue_body(
            owner="owner",
            repo="repo",
            branch="main",
            file_path="test.py",
            statement_coverage=0.01,
            function_coverage=None,
            branch_coverage=None,
            line_coverage=None,
            uncovered_lines=None,
            uncovered_functions=None,
            uncovered_branches=None,
        )
        assert "- Statement Coverage: 0%" in result

    def test_get_issue_body_return_type(self, mock_constants):
        """Test that the function returns a string."""
        result = get_issue_body(
            owner="owner",
            repo="repo",
            branch="main",
            file_path="test.py",
            statement_coverage=50.0,
            function_coverage=None,
            branch_coverage=None,
            line_coverage=None,
            uncovered_lines=None,
            uncovered_functions=None,
            uncovered_branches=None,
        )
        assert isinstance(result, str)

        result = get_issue_body(
            owner="owner",
            repo="repo",
            branch="main",
            file_path="test.py",
            statement_coverage=None,
            function_coverage=None,
            branch_coverage=None,
            line_coverage=None,
            uncovered_lines=None,
            uncovered_functions=None,
            uncovered_branches=None,
        )
        assert isinstance(result, str)

    def test_get_issue_body_integration_without_mocking(self):
        """Test the function with actual imported constants."""
        result = get_issue_body(
            owner="testowner",
            repo="testrepo",
            branch="main",
            file_path="src/example.py",
            statement_coverage=60.0,
            function_coverage=None,
            branch_coverage=None,
            line_coverage=None,
            uncovered_lines=None,
            uncovered_functions=None,
            uncovered_branches=None,
        )

        # Verify the structure without mocking constants
        assert "Add unit tests for [src/example.py]" in result
        assert "https://github.com/testowner/testrepo/blob/main/src/example.py" in result
        assert "- Statement Coverage: 60%" in result
        # The actual SETTINGS_LINKS should be present
        assert "You can [turn off triggers]" in result
        assert "update coding rules" in result
        assert "exclude files" in result

    def test_get_issue_body_mixed_coverage_combinations(self, mock_constants):
        """Test various combinations of coverage types."""
        # Test line + statement coverage only
        result = get_issue_body(
            owner="owner",
            repo="repo",
            branch="main",
            file_path="test.py",
            statement_coverage=75.0,
            function_coverage=None,
            branch_coverage=None,
            line_coverage=80.0,
            uncovered_lines="1,2,3",
            uncovered_functions=None,
            uncovered_branches=None,
        )
        assert "- Line Coverage: 80% (Uncovered Lines: 1,2,3)" in result
        assert "- Statement Coverage: 75%" in result
        assert "Function Coverage:" not in result
        assert "Branch Coverage:" not in result

        # Test function + branch coverage only
        result = get_issue_body(
            owner="owner",
            repo="repo",
            branch="main",
            file_path="test.py",
            statement_coverage=None,
            function_coverage=85.0,
            branch_coverage=65.0,
            line_coverage=None,
            uncovered_lines=None,
            uncovered_functions="func1,func2",
            uncovered_branches="branch1,branch2",
        )
        assert "- Function Coverage: 85% (Uncovered Functions: func1,func2)" in result
        assert "- Branch Coverage: 65% (Uncovered Branches: branch1,branch2)" in result
        assert "Line Coverage:" not in result
        assert "Statement Coverage:" not in result

    def test_get_issue_body_whitespace_uncovered_strings(self, mock_constants):
        """Test with whitespace-only uncovered strings."""
        result = get_issue_body(
            owner="owner",
            repo="repo",
            branch="main",
            file_path="test.py",
            statement_coverage=None,
            function_coverage=80.0,
            branch_coverage=None,
            line_coverage=90.0,
            uncovered_lines="   ",  # Whitespace only
            uncovered_functions="   ",  # Whitespace only
            uncovered_branches=None,
        )

        # Whitespace-only strings should be treated as truthy, so uncovered text should appear
        assert "- Line Coverage: 90% (Uncovered Lines:    )" in result
        assert "- Function Coverage: 80% (Uncovered Functions:    )" in result
