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
        "test_name",
        "current_function",
    }
    assert set(result.keys()) == expected_keys


def test_create_empty_stats_numeric_values():
    """Test that numeric fields are initialized to zero"""
    result = create_empty_stats()
    assert result["lines_total"] == 0
    assert result["lines_covered"] == 0
    assert result["functions_total"] == 0
    assert result["functions_covered"] == 0
    assert result["branches_total"] == 0
    assert result["branches_covered"] == 0


def test_create_empty_stats_set_values():
    """Test that set fields are initialized as empty sets"""
    result = create_empty_stats()
    assert result["uncovered_lines"] == set()
    assert result["uncovered_functions"] == set()
    assert result["uncovered_branches"] == set()
    assert isinstance(result["uncovered_lines"], set)
    assert isinstance(result["uncovered_functions"], set)
    assert isinstance(result["uncovered_branches"], set)


def test_create_empty_stats_none_values():
    """Test that optional fields are initialized to None"""
    result = create_empty_stats()
    assert result["test_name"] is None
    assert result["current_function"] is None


def test_create_empty_stats_immutability():
    """Test that multiple calls return independent dictionaries"""
    result1 = create_empty_stats()
    result2 = create_empty_stats()

    # Verify they are separate objects
    assert result1 is not result2

    # Modify one and verify the other is unchanged
    result1["lines_total"] = 100
    result1["uncovered_lines"].add(5)

    assert result2["lines_total"] == 0
    assert result2["uncovered_lines"] == set()


def test_create_empty_stats_complete_structure():
    """Test the complete structure matches expected format"""
    result = create_empty_stats()
    expected = {
        "lines_total": 0,
        "lines_covered": 0,
        "functions_total": 0,
        "functions_covered": 0,
        "branches_total": 0,
        "branches_covered": 0,
        "uncovered_lines": set(),
        "uncovered_functions": set(),
        "uncovered_branches": set(),
        "test_name": None,
        "current_function": None,
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

    # Test integer types
    assert isinstance(result["lines_total"], int)
    assert isinstance(result["lines_covered"], int)
    assert isinstance(result["functions_total"], int)
    assert isinstance(result["functions_covered"], int)
    assert isinstance(result["branches_total"], int)
    assert isinstance(result["branches_covered"], int)

    # Test set types
    assert isinstance(result["uncovered_lines"], set)
    assert isinstance(result["uncovered_functions"], set)
    assert isinstance(result["uncovered_branches"], set)

    # Test None types
    assert result["test_name"] is None
    assert result["current_function"] is None
