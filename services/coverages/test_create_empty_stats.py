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


def test_create_empty_stats_multiple_calls_return_independent_objects():
    result1 = create_empty_stats()
    result2 = create_empty_stats()
    assert result1 is not result2
    assert result1 == result2
    result1["lines_total"] = 5
    assert result2["lines_total"] == 0


def test_create_empty_stats_sets_are_independent():
    result1 = create_empty_stats()
    result2 = create_empty_stats()
    result1["uncovered_lines"].add("line1")
    assert len(result2["uncovered_lines"]) == 0
    assert result1["uncovered_lines"] is not result2["uncovered_lines"]


def test_create_empty_stats_modifiable_return_value():
    result = create_empty_stats()
    result["lines_total"] = 100
    result["test_name"] = "test_example"
    result["uncovered_lines"].add("line5")
    assert result["lines_total"] == 100
    assert result["test_name"] == "test_example"
    assert "line5" in result["uncovered_lines"]


def test_create_empty_stats_no_parameters_required():


def test_create_empty_stats_exact_structure():
    result = create_empty_stats()
    assert len(result) == 11
