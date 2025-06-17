from services.coverages.create_empty_stats import create_empty_stats


def test_create_empty_stats_returns_dict():
    result = create_empty_stats()
    assert isinstance(result, dict)


def test_create_empty_stats_has_all_required_keys():
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
        "current_function"
    }
    assert set(result.keys()) == expected_keys


def test_create_empty_stats_numeric_values_are_zero():
    result = create_empty_stats()
    assert result["lines_total"] == 0
    assert result["lines_covered"] == 0
    assert result["functions_total"] == 0
    assert result["functions_covered"] == 0
    assert result["branches_total"] == 0
    assert result["branches_covered"] == 0


def test_create_empty_stats_sets_are_empty():
    result = create_empty_stats()
    assert result["uncovered_lines"] == set()
    assert result["uncovered_functions"] == set()
    assert result["uncovered_branches"] == set()
    assert isinstance(result["uncovered_lines"], set)
    assert isinstance(result["uncovered_functions"], set)
    assert isinstance(result["uncovered_branches"], set)


def test_create_empty_stats_none_values():
    result = create_empty_stats()
    assert result["test_name"] is None
    assert result["current_function"] is None
