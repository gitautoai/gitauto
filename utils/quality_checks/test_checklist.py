from utils.quality_checks.checklist import QUALITY_CHECKLIST
from utils.quality_checks.get_checklist_hash import get_checklist_hash


def test_checklist_matches_expected():
    assert QUALITY_CHECKLIST == {
        "case_coverage": [
            "dimension_enumeration",
            "combinatorial_matrix",
            "explicit_expected_per_cell",
        ],
        "integration": [
            "db_operations_use_real_test_db",
            "api_calls_tested_end_to_end",
            "env_var_guards_for_secrets",
        ],
        "business_logic": [
            "domain_rules",
            "state_transitions",
            "calculation_accuracy",
            "data_integrity",
            "workflow_correctness",
        ],
        "adversarial": [
            "null_undefined_inputs",
            "empty_strings_arrays",
            "boundary_values",
            "type_coercion",
            "large_inputs",
            "race_conditions",
            "unicode_special_chars",
        ],
        "security": [
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
        ],
        "performance": [
            "quadratic_algorithms",
            "heavy_sync_operations",
            "n_plus_1_queries",
            "large_imports",
            "redundant_computation",
        ],
        "memory": [
            "event_listener_cleanup",
            "subscription_timer_cleanup",
            "circular_references",
            "closure_retention",
        ],
        "error_handling": [
            "graceful_degradation",
            "user_error_messages",
        ],
        "accessibility": [
            "aria_attributes",
            "keyboard_navigation",
            "screen_reader",
            "focus_management",
        ],
        "seo": [
            "meta_tags",
            "semantic_html",
            "heading_hierarchy",
            "alt_text",
        ],
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
