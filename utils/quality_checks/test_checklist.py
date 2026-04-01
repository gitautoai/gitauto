from utils.quality_checks.checklist import QUALITY_CHECKLIST
from utils.quality_checks.get_checklist_hash import get_checklist_hash


def test_checklist_has_all_categories():
    expected_categories = {
        "adversarial",
        "security",
        "performance",
        "memory",
        "error_handling",
        "accessibility",
        "business_logic",
        "seo",
    }
    assert set(QUALITY_CHECKLIST.keys()) == expected_categories


def test_each_category_has_checks():
    for category, checks in QUALITY_CHECKLIST.items():
        assert len(checks) > 0, f"Category '{category}' has no checks"
        for check in checks:
            assert isinstance(
                check, str
            ), f"Check '{check}' in '{category}' is not a string"
            assert len(check) > 0, f"Empty check name in '{category}'"


def test_no_duplicate_checks_within_categories():
    for category, checks in QUALITY_CHECKLIST.items():
        assert len(checks) == len(set(checks)), f"Duplicate checks in '{category}'"


def test_get_checklist_hash_returns_hex_string():
    result = get_checklist_hash()
    assert isinstance(result, str)
    assert len(result) == 64  # SHA256 hex digest is 64 chars
    int(result, 16)  # Should be valid hex


def test_get_checklist_hash_is_stable():
    hash1 = get_checklist_hash()
    hash2 = get_checklist_hash()
    assert hash1 == hash2
