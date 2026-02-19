import json
import os

from services.jest.validate_istanbul_file_data import validate_istanbul_file_data

REAL_COVERAGE_PAYLOAD = os.path.join(
    os.path.dirname(__file__), "fixtures", "coverage-final.json"
)


def test_validate_real_coverage_json():
    """Validate real coverage-final.json from website repo."""
    with open(REAL_COVERAGE_PAYLOAD, "r", encoding="utf-8") as f:
        data = json.load(f)
    raw = next(iter(data.values()))
    result = validate_istanbul_file_data(raw)
    assert result is not None
    assert isinstance(result["s"], dict)
    assert isinstance(result["f"], dict)
    assert isinstance(result["b"], dict)
    assert isinstance(result["statementMap"], dict)
    assert isinstance(result["fnMap"], dict)
    assert isinstance(result["branchMap"], dict)


def test_validate_missing_keys():
    """Missing required keys returns None."""
    assert validate_istanbul_file_data({"s": {}}) is None


def test_validate_wrong_types():
    """Wrong value types returns None."""
    raw = {
        "s": "not a dict",
        "f": {},
        "b": {},
        "statementMap": {},
        "fnMap": {},
        "branchMap": {},
    }
    assert validate_istanbul_file_data(raw) is None


def test_validate_empty_maps():
    """All empty dicts is valid."""
    raw = {
        "s": {},
        "f": {},
        "b": {},
        "statementMap": {},
        "fnMap": {},
        "branchMap": {},
    }
    result = validate_istanbul_file_data(raw)
    assert result is not None
    assert result["s"] == {}
