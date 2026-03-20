from services.coverages.create_empty_stats import create_empty_stats


def test_create_empty_stats_returns_dict():
    """Test that create_empty_stats returns a dictionary"""
    result = create_empty_stats()
    assert isinstance(result, dict)


def test_create_empty_stats_has_all_required_keys():
    """Test that create_empty_stats returns all required keys"""
    result = create_empty_stats()
    expected_keys = {
        "lines_total",
        "lines_covered",
        "functions_total",
        "functions_covered",
        "branches_total",
        "branches_covered",
        "uncovered_lines",
        "uncovered_functions",
        "uncovered_branches",
    }
    assert set(result.keys()) == expected_keys


def test_create_empty_stats_numeric_values():
    """Test that numeric fields are initialized to None (not yet seen in LCOV)"""
    result = create_empty_stats()
    assert result["lines_total"] is None
    assert result["lines_covered"] is None
    assert result["functions_total"] is None
    assert result["functions_covered"] is None
    assert result["branches_total"] is None
    assert result["branches_covered"] is None


def test_create_empty_stats_set_values():
    """Test that set fields are initialized as empty sets"""
    result = create_empty_stats()
    assert result["uncovered_lines"] == set()
    assert result["uncovered_functions"] == set()
    assert result["uncovered_branches"] == set()
    assert isinstance(result["uncovered_lines"], set)
    assert isinstance(result["uncovered_functions"], set)
    assert isinstance(result["uncovered_branches"], set)


def test_create_empty_stats_immutability():
    """Test that multiple calls return independent dictionaries"""
    result1 = create_empty_stats()
    result2 = create_empty_stats()

    # Verify they are separate objects
    assert result1 is not result2

    # Modify one and verify the other is unchanged
    result1["lines_total"] = 100
    result1["uncovered_lines"].add(5)

    assert result2["lines_total"] is None
    assert result2["uncovered_lines"] == set()


def test_create_empty_stats_complete_structure():
    """Test the complete structure matches expected format"""
    result = create_empty_stats()
    expected = {
        "lines_total": None,
        "lines_covered": None,
        "functions_total": None,
        "functions_covered": None,
        "branches_total": None,
        "branches_covered": None,
        "uncovered_lines": set(),
        "uncovered_functions": set(),
        "uncovered_branches": set(),
    }
    assert result == expected


def test_create_empty_stats_no_parameters():
    """Test that function accepts no parameters"""
    # This should not raise any exception
    result = create_empty_stats()
    assert result is not None


def test_create_empty_stats_return_type_consistency():
    """Test that return types are consistent across calls"""
    result = create_empty_stats()

    # Test None types (not yet seen in LCOV)
    assert result["lines_total"] is None
    assert result["lines_covered"] is None
    assert result["functions_total"] is None
    assert result["functions_covered"] is None
    assert result["branches_total"] is None
    assert result["branches_covered"] is None

    # Test set types
    assert isinstance(result["uncovered_lines"], set)
    assert isinstance(result["uncovered_functions"], set)
    assert isinstance(result["uncovered_branches"], set)
