from utils.quality_checks.checklist import QUALITY_CHECKLIST
from utils.quality_checks.get_checklist_hash import get_checklist_hash


def test_checklist_categories_match_expected():
    # Lock the category set so removing/adding categories is a deliberate edit (not a typo).
    assert set(QUALITY_CHECKLIST.keys()) == {
        "case_coverage",
        "integration",
        "business_logic",
        "adversarial",
        "security",
        "performance",
        "memory",
        "error_handling",
        "accessibility",
        "seo",
    }


def test_checklist_each_item_is_id_to_description():
    # Every category is a dict mapping check_id (snake_case) to a non-empty description.
    # The id is the stable storage key; the description is shown to the LLM evaluator.
    for category, items in QUALITY_CHECKLIST.items():
        assert isinstance(items, dict), f"category {category} must map id->description"
        for check_id, description in items.items():
            assert (
                isinstance(check_id, str) and check_id
            ), f"{category}: empty/non-string id"
            assert (
                check_id == check_id.lower() and " " not in check_id
            ), f"{category}.{check_id}: ids must be lowercase snake_case (no spaces)"
            assert (
                isinstance(description, str) and len(description) >= 30
            ), f"{category}.{check_id}: description must be a meaningful sentence (>=30 chars)"


def test_checklist_id_sets_are_locked_per_category():
    # Storage records (Coverages.quality_checks) use these ids as keys;
    # renaming or removing an id silently breaks pre-existing data, so we lock the full id set.
    actual_id_sets = {}
    for cat, items in QUALITY_CHECKLIST.items():
        actual_id_sets[cat] = sorted(items.keys())
    assert actual_id_sets == {
        "case_coverage": sorted(
            [
                "dimension_enumeration",
                "combinatorial_matrix",
                "explicit_expected_per_cell",
            ]
        ),
        "integration": sorted(
            [
                "db_operations_use_real_test_db",
                "api_calls_tested_end_to_end",
                "env_var_guards_for_secrets",
            ]
        ),
        "business_logic": sorted(
            [
                "domain_rules",
                "state_transitions",
                "calculation_accuracy",
                "data_integrity",
                "workflow_correctness",
            ]
        ),
        "adversarial": sorted(
            [
                "null_undefined_inputs",
                "empty_strings_arrays",
                "boundary_values",
                "type_coercion",
                "large_inputs",
                "race_conditions",
                "unicode_special_chars",
            ]
        ),
        "security": sorted(
            [
                "xss",
                "sql_injection",
                "command_injection",
                "code_injection",
                "csrf",
                "auth_bypass",
                "sensitive_data_exposure",
                "untrusted_input_sanitization",
                "open_redirects",
                "path_traversal",
            ]
        ),
        "performance": sorted(
            [
                "quadratic_algorithms",
                "heavy_sync_operations",
                "n_plus_1_queries",
                "large_imports",
                "redundant_computation",
            ]
        ),
        "memory": sorted(
            [
                "event_listener_cleanup",
                "subscription_timer_cleanup",
                "circular_references",
                "closure_retention",
            ]
        ),
        "error_handling": sorted(
            [
                "graceful_degradation",
                "user_error_messages",
            ]
        ),
        "accessibility": sorted(
            [
                "aria_attributes",
                "keyboard_navigation",
                "screen_reader",
                "focus_management",
            ]
        ),
        "seo": sorted(
            [
                "meta_tags",
                "semantic_html",
                "heading_hierarchy",
                "alt_text",
            ]
        ),
    }


def test_get_checklist_hash_returns_hex_string():
    result = get_checklist_hash()
    assert isinstance(result, str)
    assert len(result) == 64  # SHA256 hex digest is 64 chars
    int(result, 16)  # Should be valid hex


def test_get_checklist_hash_is_stable():
    hash1 = get_checklist_hash()
    hash2 = get_checklist_hash()
    assert hash1 == hash2
