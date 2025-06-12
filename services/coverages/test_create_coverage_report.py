import pytest
from services.coverages.create_coverage_report import create_coverage_report


class TestCreateCoverageReport:
    """Test cases for create_coverage_report function."""

    def test_directory_level_with_empty_path(self):
        """Test that directory level with empty path sets path to '.'"""
        stats = {
            "lines_total": 10,
            "lines_covered": 8,
            "functions_total": 5,
            "functions_covered": 4,
            "branches_total": 6,
            "branches_covered": 5,
            "uncovered_lines": {1, 2},
            "uncovered_functions": [(10, "test_func")],
            "uncovered_branches": ["line 5, block 0, branch 1"]
        }
        
        result = create_coverage_report("", stats, "directory")
        
        assert result["full_path"] == "."
        assert result["level"] == "directory"

    def test_directory_level_with_non_empty_path(self):
        """Test that directory level with non-empty path keeps original path"""
        stats = {
            "lines_total": 10,
            "lines_covered": 8,
            "functions_total": 5,
            "functions_covered": 4,
            "branches_total": 6,
            "branches_covered": 5,
            "uncovered_lines": {1, 2},
            "uncovered_functions": [(10, "test_func")],
            "uncovered_branches": ["line 5, block 0, branch 1"]
        }
        
        result = create_coverage_report("src/test", stats, "directory")
        
        assert result["full_path"] == "src/test"
        assert result["level"] == "directory"

    def test_file_level_with_empty_path(self):
        """Test that file level with empty path keeps empty path"""
        stats = {
            "lines_total": 10,
            "lines_covered": 8,
            "functions_total": 5,
            "functions_covered": 4,
            "branches_total": 6,
            "branches_covered": 5,
            "uncovered_lines": {1, 2},
            "uncovered_functions": [(10, "test_func")],
            "uncovered_branches": ["line 5, block 0, branch 1"]
        }
        
        result = create_coverage_report("", stats, "file")
        
        assert result["full_path"] == ""
        assert result["level"] == "file"

    def test_line_coverage_calculation_with_total_greater_than_zero(self):
        """Test line coverage calculation when lines_total > 0"""
        stats = {
            "lines_total": 10,
            "lines_covered": 8,
            "functions_total": 0,
            "functions_covered": 0,
            "branches_total": 0,
            "branches_covered": 0,
            "uncovered_lines": set(),
            "uncovered_functions": set(),
            "uncovered_branches": set()
        }
        
        result = create_coverage_report("test.py", stats, "file")
        
        expected_coverage = round(8 / 10 * 100, 2)
        assert result["line_coverage"] == expected_coverage
        assert result["statement_coverage"] == expected_coverage

    def test_line_coverage_calculation_with_total_zero(self):
        """Test line coverage calculation when lines_total = 0"""
        stats = {
            "lines_total": 0,
            "lines_covered": 0,
            "functions_total": 0,
            "functions_covered": 0,
            "branches_total": 0,
            "branches_covered": 0,
            "uncovered_lines": set(),
            "uncovered_functions": set(),
            "uncovered_branches": set()
        }
        
        result = create_coverage_report("test.py", stats, "file")
        
        assert result["line_coverage"] == 100.0
        assert result["statement_coverage"] == 100.0

    def test_function_coverage_calculation_with_total_greater_than_zero(self):
        """Test function coverage calculation when functions_total > 0"""
        stats = {
            "lines_total": 0,
            "lines_covered": 0,
            "functions_total": 5,
            "functions_covered": 3,
            "branches_total": 0,
            "branches_covered": 0,
            "uncovered_lines": set(),
            "uncovered_functions": set(),
            "uncovered_branches": set()
        }
        
        result = create_coverage_report("test.py", stats, "file")
        
        expected_coverage = round(3 / 5 * 100, 2)
        assert result["function_coverage"] == expected_coverage

    def test_function_coverage_calculation_with_total_zero(self):
        """Test function coverage calculation when functions_total = 0"""
        stats = {
            "lines_total": 0,
            "lines_covered": 0,
            "functions_total": 0,
            "functions_covered": 0,
            "branches_total": 0,
            "branches_covered": 0,
            "uncovered_lines": set(),
            "uncovered_functions": set(),
            "uncovered_branches": set()
        }
        
        result = create_coverage_report("test.py", stats, "file")
        
        assert result["function_coverage"] == 100.0

    def test_branch_coverage_calculation_with_total_greater_than_zero(self):
        """Test branch coverage calculation when branches_total > 0"""
        stats = {
            "lines_total": 0,
            "lines_covered": 0,
            "functions_total": 0,
            "functions_covered": 0,
            "branches_total": 8,
            "branches_covered": 6,
            "uncovered_lines": set(),
            "uncovered_functions": set(),
            "uncovered_branches": set()
        }
        
        result = create_coverage_report("test.py", stats, "file")
        
        expected_coverage = round(6 / 8 * 100, 2)
        assert result["branch_coverage"] == expected_coverage

    def test_branch_coverage_calculation_with_total_zero(self):
        """Test branch coverage calculation when branches_total = 0"""
        stats = {
            "lines_total": 0,
            "lines_covered": 0,
            "functions_total": 0,
            "functions_covered": 0,
            "branches_total": 0,
            "branches_covered": 0,
            "uncovered_lines": set(),
            "uncovered_functions": set(),
            "uncovered_branches": set()
        }
        
        result = create_coverage_report("test.py", stats, "file")
        
        assert result["branch_coverage"] == 100.0

    def test_uncovered_lines_for_file_level_with_coverage_greater_than_zero(self):
        """Test uncovered_lines formatting for file level with line_coverage > 0"""
        stats = {
            "lines_total": 10,
            "lines_covered": 8,
            "functions_total": 0,
            "functions_covered": 0,
            "branches_total": 0,
            "branches_covered": 0,
            "uncovered_lines": {5, 1, 10, 3},
            "uncovered_functions": set(),
            "uncovered_branches": set()
        }
        
        result = create_coverage_report("test.py", stats, "file")
        
        assert result["uncovered_lines"] == "1, 3, 5, 10"

    def test_uncovered_lines_for_file_level_with_zero_coverage(self):
        """Test uncovered_lines formatting for file level with line_coverage = 0"""
        stats = {
            "lines_total": 10,
            "lines_covered": 0,
            "functions_total": 0,
            "functions_covered": 0,
            "branches_total": 0,
            "branches_covered": 0,
            "uncovered_lines": {5, 1, 10, 3},
            "uncovered_functions": set(),
            "uncovered_branches": set()
        }
        
        result = create_coverage_report("test.py", stats, "file")
        
        assert result["uncovered_lines"] == ""

    def test_uncovered_lines_for_directory_level(self):
        """Test uncovered_lines formatting for directory level (should be empty)"""
        stats = {
            "lines_total": 10,
            "lines_covered": 8,
            "functions_total": 0,
            "functions_covered": 0,
            "branches_total": 0,
            "branches_covered": 0,
            "uncovered_lines": {5, 1, 10, 3},
            "uncovered_functions": set(),
            "uncovered_branches": set()
        }
        
        result = create_coverage_report("src", stats, "directory")
        
        assert result["uncovered_lines"] == ""

    def test_uncovered_functions_with_two_element_tuples(self):
        """Test uncovered_functions formatting with 2-element tuples (line, name)"""
        stats = {
            "lines_total": 0,
            "lines_covered": 0,
            "functions_total": 0,
            "functions_covered": 0,
            "branches_total": 0,
            "branches_covered": 0,
            "uncovered_lines": set(),
            "uncovered_functions": {(10, "func_a"), (5, "func_b"), (15, "func_c")},
            "uncovered_branches": set()
        }
        
        result = create_coverage_report("test.py", stats, "file")
        
        assert result["uncovered_functions"] == "L5:func_b, L10:func_a, L15:func_c"

    def test_uncovered_functions_with_three_element_tuples(self):
        """Test uncovered_functions formatting with 3-element tuples (start, end, name)"""
        stats = {
            "lines_total": 0,
            "lines_covered": 0,
            "functions_total": 0,
            "functions_covered": 0,
            "branches_total": 0,
            "branches_covered": 0,
            "uncovered_lines": set(),
            "uncovered_functions": {(10, 15, "func_a"), (5, 8, "func_b"), (20, 25, "func_c")},
            "uncovered_branches": set()
        }
        
        result = create_coverage_report("test.py", stats, "file")
        
        assert result["uncovered_functions"] == "L5-8:func_b, L10-15:func_a, L20-25:func_c"

    def test_uncovered_functions_mixed_tuple_lengths(self):
        """Test uncovered_functions formatting with mixed 2 and 3-element tuples"""
        stats = {
            "lines_total": 0,
            "lines_covered": 0,
            "functions_total": 0,
            "functions_covered": 0,
            "branches_total": 0,
            "branches_covered": 0,
            "uncovered_lines": set(),
            "uncovered_functions": {(10, "func_a"), (5, 8, "func_b"), (15, "func_c")},
            "uncovered_branches": set()
        }
        
        result = create_coverage_report("test.py", stats, "file")
        
        assert result["uncovered_functions"] == "L5-8:func_b, L10:func_a, L15:func_c"

    def test_uncovered_functions_empty_set(self):
        """Test uncovered_functions formatting with empty set"""
        stats = {
            "lines_total": 0,
            "lines_covered": 0,
            "functions_total": 0,
            "functions_covered": 0,
            "branches_total": 0,
            "branches_covered": 0,
            "uncovered_lines": set(),
            "uncovered_functions": set(),
            "uncovered_branches": set()
        }
        
        result = create_coverage_report("test.py", stats, "file")
        
        assert result["uncovered_functions"] == ""

    def test_uncovered_branches_formatting(self):
        """Test uncovered_branches formatting"""
        stats = {
            "lines_total": 0,
            "lines_covered": 0,
            "functions_total": 0,
            "functions_covered": 0,
            "branches_total": 0,
            "branches_covered": 0,
            "uncovered_lines": set(),
            "uncovered_functions": set(),
            "uncovered_branches": {"line 5, block 0, branch 1", "line 3, block 0, branch 0", "line 10, block 1, branch 2"}
        }
        
        result = create_coverage_report("test.py", stats, "file")
        
        assert result["uncovered_branches"] == "line 10, block 1, branch 2, line 3, block 0, branch 0, line 5, block 0, branch 1"

    def test_uncovered_branches_empty_set(self):
        """Test uncovered_branches formatting with empty set"""
        stats = {
            "lines_total": 0,
            "lines_covered": 0,
            "functions_total": 0,
            "functions_covered": 0,
            "branches_total": 0,
            "branches_covered": 0,
            "uncovered_lines": set(),
            "uncovered_functions": set(),
            "uncovered_branches": set()
        }
        
        result = create_coverage_report("test.py", stats, "file")
        
        assert result["uncovered_branches"] == ""

    def test_complete_return_structure(self):
        """Test that the complete return structure is correct"""
        stats = {
            "lines_total": 10,
            "lines_covered": 8,
            "functions_total": 5,
            "functions_covered": 4,
            "branches_total": 6,
            "branches_covered": 5,
            "uncovered_lines": {1, 2},
            "uncovered_functions": [(10, "test_func")],
            "uncovered_branches": {"line 5, block 0, branch 1"}
        }
        
        result = create_coverage_report("test.py", stats, "file")
        
        expected_keys = {
            "package_name", "level", "full_path", "statement_coverage",
            "function_coverage", "branch_coverage", "line_coverage",
            "uncovered_lines", "uncovered_functions", "uncovered_branches"
        }
        
        assert set(result.keys()) == expected_keys
        assert result["package_name"] is None
        assert result["level"] == "file"
        assert result["full_path"] == "test.py"

    def test_repository_level(self):
        """Test repository level coverage report"""
        stats = {
            "lines_total": 100,
            "lines_covered": 85,
            "functions_total": 20,
            "functions_covered": 18,
            "branches_total": 30,
            "branches_covered": 25,
            "uncovered_lines": set(),
            "uncovered_functions": set(),
            "uncovered_branches": set()
        }
        
        result = create_coverage_report("All", stats, "repository")
        
        assert result["level"] == "repository"
        assert result["full_path"] == "All"
        assert result["line_coverage"] == 85.0
        assert result["function_coverage"] == 90.0
        assert result["branch_coverage"] == round(25/30*100, 2)

    def test_precision_rounding(self):
        """Test that coverage percentages are rounded to 2 decimal places"""
        stats = {
            "lines_total": 3,
            "lines_covered": 1,  # 33.333...%
            "functions_total": 3,
            "functions_covered": 2,  # 66.666...%
            "branches_total": 7,
            "branches_covered": 5,  # 71.428...%
            "uncovered_lines": set(),
            "uncovered_functions": set(),
            "uncovered_branches": set()
        }
        
        result = create_coverage_report("test.py", stats, "file")
        
        assert result["line_coverage"] == 33.33
        assert result["function_coverage"] == 66.67
        assert result["branch_coverage"] == 71.43
