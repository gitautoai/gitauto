# pyright: reportUnusedVariable=false
from typing import Any, cast
from unittest.mock import MagicMock, patch

import pytest

from schemas.supabase.types import Repositories
from constants.triggers import Trigger
from services.webhook.utils.create_system_message import create_system_message


def create_repositories_data(
    structured_rules: dict[str, Any] | None = None,
    repo_rules: str | None = None,
    preferred_language: str | None = None,
    **overrides,
) -> Repositories:
    base_data = {
        "id": 1,
        "owner_id": 123,
        "repo_id": 456,
        "repo_name": "test-repo",
        "created_at": "2023-01-01T00:00:00Z",
        "created_by": "testuser",
        "updated_at": "2023-01-01T00:00:00Z",
        "updated_by": "testuser",
        "use_screenshots": False,
        "production_url": None,
        "local_port": None,
        "startup_commands": None,
        "web_urls": None,
        "file_paths": None,
        "repo_rules": repo_rules,
        "file_count": 100,
        "code_lines": 70,
        "target_branch": "main",
        "trigger_on_review_comment": True,
        "trigger_on_test_failure": True,
        "trigger_on_schedule": False,
        "schedule_frequency": None,
        "schedule_minute": None,
        "schedule_time": None,
        "schedule_day_of_week": None,
        "schedule_include_weekends": False,
        "structured_rules": structured_rules,
        "preferred_language": preferred_language,
        "schedule_execution_count": 0,
        "schedule_interval_minutes": 60,
    }
    base_data.update(overrides)
    return cast(Repositories, base_data)


@pytest.fixture
def mock_read_xml_file():
    with patch("services.webhook.utils.create_system_message.read_xml_file") as mock:
        yield mock


@pytest.fixture
def mock_get_trigger_prompt():
    with patch(
        "services.webhook.utils.create_system_message.get_trigger_prompt"
    ) as mock:
        yield mock


_CHECKLIST_BLOCK = (
    "<quality_checklist>\n"
    "When writing tests, ensure coverage of these quality categories where applicable to the file:\n"
    "{\n"
    '  "case_coverage": [\n'
    '    "dimension_enumeration",\n'
    '    "combinatorial_matrix",\n'
    '    "explicit_expected_per_cell"\n'
    "  ],\n"
    '  "integration": [\n'
    '    "db_operations_use_real_test_db",\n'
    '    "api_calls_tested_end_to_end",\n'
    '    "env_var_guards_for_secrets"\n'
    "  ],\n"
    '  "business_logic": [\n'
    '    "domain_rules",\n'
    '    "state_transitions",\n'
    '    "calculation_accuracy",\n'
    '    "data_integrity",\n'
    '    "workflow_correctness"\n'
    "  ],\n"
    '  "adversarial": [\n'
    '    "null_undefined_inputs",\n'
    '    "empty_strings_arrays",\n'
    '    "boundary_values",\n'
    '    "type_coercion",\n'
    '    "large_inputs",\n'
    '    "race_conditions",\n'
    '    "unicode_special_chars"\n'
    "  ],\n"
    '  "security": [\n'
    '    "xss",\n'
    '    "sql_injection",\n'
    '    "command_injection",\n'
    '    "code_injection",\n'
    '    "csrf",\n'
    '    "auth_bypass",\n'
    '    "sensitive_data_exposure",\n'
    '    "untrusted_input_sanitization",\n'
    '    "open_redirects",\n'
    '    "path_traversal"\n'
    "  ],\n"
    '  "performance": [\n'
    '    "quadratic_algorithms",\n'
    '    "heavy_sync_operations",\n'
    '    "n_plus_1_queries",\n'
    '    "large_imports",\n'
    '    "redundant_computation"\n'
    "  ],\n"
    '  "memory": [\n'
    '    "event_listener_cleanup",\n'
    '    "subscription_timer_cleanup",\n'
    '    "circular_references",\n'
    '    "closure_retention"\n'
    "  ],\n"
    '  "error_handling": [\n'
    '    "graceful_degradation",\n'
    '    "user_error_messages"\n'
    "  ],\n"
    '  "accessibility": [\n'
    '    "aria_attributes",\n'
    '    "keyboard_navigation",\n'
    '    "screen_reader",\n'
    '    "focus_management"\n'
    "  ],\n"
    '  "seo": [\n'
    '    "meta_tags",\n'
    '    "semantic_html",\n'
    '    "heading_hierarchy",\n'
    '    "alt_text"\n'
    "  ]\n"
    "}\n"
    "</quality_checklist>"
)


def _build_expected(
    *,
    language_block: str | None = None,
    trigger_block: str | None = None,
    coding_standards: str = "<rules>Rules</rules>",
    structured_block: str | None = None,
    freeform_block: str | None = None,
    gitauto_md_block: str | None = None,
) -> str:
    parts: list[str] = []
    if language_block is not None:
        parts.append(language_block)
    if trigger_block is not None:
        parts.append(trigger_block)
    parts.append(coding_standards)
    parts.append(_CHECKLIST_BLOCK)
    if structured_block is not None:
        parts.append(structured_block)
    if freeform_block is not None:
        parts.append(freeform_block)
    if gitauto_md_block is not None:
        parts.append(gitauto_md_block)
    return "\n\n".join(parts)


def test_minimal_call_no_repo_settings(mock_read_xml_file, mock_get_trigger_prompt):
    mock_read_xml_file.return_value = "<rules>Rules</rules>"
    mock_get_trigger_prompt.return_value = (
        "<trigger_instruction>Issue trigger</trigger_instruction>"
    )

    result = create_system_message("dashboard")

    assert result == _build_expected(
        trigger_block="<trigger_instruction>Issue trigger</trigger_instruction>"
    )
    mock_get_trigger_prompt.assert_called_once_with("dashboard")
    # read_xml_file is called for coding_standards.xml
    assert mock_read_xml_file.call_count == 1


def test_all_trigger_types(mock_read_xml_file, mock_get_trigger_prompt):
    mock_read_xml_file.return_value = "<rules>Rules</rules>"
    mock_get_trigger_prompt.return_value = "<trigger>Content</trigger>"

    triggers: list[Trigger] = [
        "dashboard",
        "pr_file_review",
        "test_failure",
        "schedule",
    ]

    expected = _build_expected(trigger_block="<trigger>Content</trigger>")
    for trigger in triggers:
        result = create_system_message(trigger)
        assert result == expected
        mock_get_trigger_prompt.assert_called_with(trigger)


def test_with_structured_rules_only(mock_read_xml_file, mock_get_trigger_prompt):
    mock_read_xml_file.return_value = "<rules>Rules</rules>"
    mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"

    structured_rules = {
        "codePatternStrategy": "Best practices first",
        "enableCommentsInGeneratedTestCode": False,
        "enforceComponentIsolationInTests": True,
    }
    repo_settings = create_repositories_data(structured_rules=structured_rules)

    result = create_system_message("dashboard", repo_settings)

    assert result == _build_expected(
        trigger_block="<trigger>Trigger</trigger>",
        structured_block=(
            "<structured_repository_rules>\n"
            "codePatternStrategy: Best practices first\n"
            "enableCommentsInGeneratedTestCode: False\n"
            "enforceComponentIsolationInTests: True\n"
            "</structured_repository_rules>"
        ),
    )


def test_with_repo_rules_only(mock_read_xml_file, mock_get_trigger_prompt):
    mock_read_xml_file.return_value = "<rules>Rules</rules>"
    mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"

    repo_rules = "Always use TypeScript\nPrefer functional components\nUse ESLint"
    repo_settings = create_repositories_data(repo_rules=repo_rules)

    result = create_system_message("dashboard", repo_settings)

    assert result == _build_expected(
        trigger_block="<trigger>Trigger</trigger>",
        freeform_block=(
            "<freeform_repository_rules>\n"
            "Always use TypeScript\nPrefer functional components\nUse ESLint\n"
            "</freeform_repository_rules>"
        ),
    )


def test_with_both_structured_and_repo_rules(
    mock_read_xml_file, mock_get_trigger_prompt
):
    mock_read_xml_file.return_value = "<rules>Rules</rules>"
    mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"

    structured_rules = {
        "testFramework": "Jest",
        "enableMocking": True,
    }
    repo_rules = "Use strict mode\nDocument all functions"
    repo_settings = create_repositories_data(
        structured_rules=structured_rules, repo_rules=repo_rules
    )

    result = create_system_message("dashboard", repo_settings)

    assert result == _build_expected(
        trigger_block="<trigger>Trigger</trigger>",
        structured_block=(
            "<structured_repository_rules>\n"
            "testFramework: Jest\n"
            "enableMocking: True\n"
            "</structured_repository_rules>"
        ),
        freeform_block=(
            "<freeform_repository_rules>\n"
            "Use strict mode\nDocument all functions\n"
            "</freeform_repository_rules>"
        ),
    )


def test_with_empty_structured_rules(mock_read_xml_file, mock_get_trigger_prompt):
    mock_read_xml_file.return_value = "<rules>Rules</rules>"
    mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"

    repo_settings = create_repositories_data(structured_rules={})

    result = create_system_message("dashboard", repo_settings)

    assert result == _build_expected(trigger_block="<trigger>Trigger</trigger>")


def test_with_empty_repo_rules(mock_read_xml_file, mock_get_trigger_prompt):
    mock_read_xml_file.return_value = "<rules>Rules</rules>"
    mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"

    repo_settings = create_repositories_data(repo_rules="")

    result = create_system_message("dashboard", repo_settings)

    assert result == _build_expected(trigger_block="<trigger>Trigger</trigger>")


def test_with_whitespace_only_repo_rules(mock_read_xml_file, mock_get_trigger_prompt):
    mock_read_xml_file.return_value = "<rules>Rules</rules>"
    mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"

    repo_settings = create_repositories_data(repo_rules="   \n\t  ")

    result = create_system_message("dashboard", repo_settings)

    assert result == _build_expected(trigger_block="<trigger>Trigger</trigger>")


def test_with_none_structured_rules(mock_read_xml_file, mock_get_trigger_prompt):
    mock_read_xml_file.return_value = "<rules>Rules</rules>"
    mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"

    repo_settings = create_repositories_data(structured_rules=None)

    result = create_system_message("dashboard", repo_settings)

    assert result == _build_expected(trigger_block="<trigger>Trigger</trigger>")


def test_with_none_repo_rules(mock_read_xml_file, mock_get_trigger_prompt):
    mock_read_xml_file.return_value = "<rules>Rules</rules>"
    mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"

    repo_settings = create_repositories_data(repo_rules=None)

    result = create_system_message("dashboard", repo_settings)

    assert result == _build_expected(trigger_block="<trigger>Trigger</trigger>")


def test_trigger_prompt_returns_none(mock_read_xml_file, mock_get_trigger_prompt):
    mock_read_xml_file.return_value = "<rules>Rules</rules>"
    mock_get_trigger_prompt.return_value = None

    result = create_system_message("dashboard")

    # No trigger block is emitted when get_trigger_prompt returns None.
    assert result == _build_expected()


def test_structured_rules_with_various_data_types(
    mock_read_xml_file, mock_get_trigger_prompt
):
    mock_read_xml_file.return_value = "<rules>Rules</rules>"
    mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"

    structured_rules = {
        "stringValue": "test string",
        "intValue": 42,
        "floatValue": 3.14,
        "boolValue": True,
        "listValue": ["item1", "item2"],
        "dictValue": {"nested": "value"},
        "noneValue": None,
    }
    repo_settings = create_repositories_data(structured_rules=structured_rules)

    result = create_system_message("dashboard", repo_settings)

    assert result == _build_expected(
        trigger_block="<trigger>Trigger</trigger>",
        structured_block=(
            "<structured_repository_rules>\n"
            "stringValue: test string\n"
            "intValue: 42\n"
            "floatValue: 3.14\n"
            "boolValue: True\n"
            "listValue: ['item1', 'item2']\n"
            "dictValue: {'nested': 'value'}\n"
            "noneValue: None\n"
            "</structured_repository_rules>"
        ),
    )


def test_repo_rules_with_leading_trailing_whitespace(
    mock_read_xml_file, mock_get_trigger_prompt
):
    mock_read_xml_file.return_value = "<rules>Rules</rules>"
    mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"

    repo_rules = "  \n  Use clean code principles  \n  "
    repo_settings = create_repositories_data(repo_rules=repo_rules)

    result = create_system_message("dashboard", repo_settings)

    # Whitespace trims on both ends; content stays.
    assert result == _build_expected(
        trigger_block="<trigger>Trigger</trigger>",
        freeform_block=(
            "<freeform_repository_rules>\n"
            "Use clean code principles\n"
            "</freeform_repository_rules>"
        ),
    )


def test_integration_without_mocks():
    structured_rules = {"testRule": "testValue"}
    repo_rules = "Test repo rule"
    repo_settings = create_repositories_data(
        structured_rules=structured_rules, repo_rules=repo_rules
    )

    result = create_system_message("dashboard", repo_settings)

    assert isinstance(result, str)


def test_exception_handling_returns_default_value(
    mock_read_xml_file, mock_get_trigger_prompt
):
    mock_read_xml_file.side_effect = Exception("File read error")
    mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"

    result = create_system_message("dashboard")

    assert result == ""


def test_file_not_found_error_handling(mock_read_xml_file, mock_get_trigger_prompt):
    mock_read_xml_file.side_effect = FileNotFoundError("XML file not found")
    mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"

    result = create_system_message("dashboard")

    assert result == ""


def test_type_error_in_structured_rules_handling(
    mock_read_xml_file, mock_get_trigger_prompt
):
    mock_read_xml_file.return_value = "<rules>Rules</rules>"
    mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"

    mock_repo_settings = MagicMock()
    mock_repo_settings.get.side_effect = TypeError("Type error in get method")

    result = create_system_message("dashboard", mock_repo_settings)

    assert result == ""


def test_attribute_error_handling(mock_read_xml_file, mock_get_trigger_prompt):
    mock_read_xml_file.return_value = "<rules>Rules</rules>"
    mock_get_trigger_prompt.side_effect = AttributeError("Attribute error")

    result = create_system_message("dashboard")

    assert result == ""


@patch("services.webhook.utils.create_system_message.read_local_file")
def test_with_gitauto_md_content(
    mock_read_local, mock_read_xml_file, mock_get_trigger_prompt
):
    mock_read_xml_file.return_value = "<rules>Rules</rules>"
    mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"
    mock_read_local.return_value = "## Testing\n- Use factories instead of mocks"

    result = create_system_message("dashboard", clone_dir="/tmp/repo")

    assert result == _build_expected(
        trigger_block="<trigger>Trigger</trigger>",
        gitauto_md_block=(
            "<gitauto_md_rules>\n"
            "## Testing\n- Use factories instead of mocks\n"
            "</gitauto_md_rules>"
        ),
    )
    mock_read_local.assert_called_once_with(
        file_path="GITAUTO.md", base_dir="/tmp/repo"
    )


def test_gitauto_md_no_clone_dir(mock_read_xml_file, mock_get_trigger_prompt):
    mock_read_xml_file.return_value = "<rules>Rules</rules>"
    mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"

    result = create_system_message("dashboard", clone_dir=None)

    assert result == _build_expected(trigger_block="<trigger>Trigger</trigger>")


@patch("services.webhook.utils.create_system_message.read_local_file")
def test_gitauto_md_file_not_found(
    mock_read_local, mock_read_xml_file, mock_get_trigger_prompt
):
    mock_read_xml_file.return_value = "<rules>Rules</rules>"
    mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"
    mock_read_local.return_value = None

    result = create_system_message("dashboard", clone_dir="/tmp/repo")

    assert result == _build_expected(trigger_block="<trigger>Trigger</trigger>")


@patch("services.webhook.utils.create_system_message.read_local_file")
def test_gitauto_md_content_empty(
    mock_read_local, mock_read_xml_file, mock_get_trigger_prompt
):
    mock_read_xml_file.return_value = "<rules>Rules</rules>"
    mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"
    mock_read_local.return_value = "   \n\t  "

    result = create_system_message("dashboard", clone_dir="/tmp/repo")

    assert result == _build_expected(trigger_block="<trigger>Trigger</trigger>")


@patch("services.webhook.utils.create_system_message.read_local_file")
def test_gitauto_md_comes_after_repo_rules(
    mock_read_local, mock_read_xml_file, mock_get_trigger_prompt
):
    mock_read_xml_file.return_value = "<rules>Rules</rules>"
    mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"
    mock_read_local.return_value = "## Testing\n- Use factories"

    repo_settings = create_repositories_data(repo_rules="Use TypeScript")
    result = create_system_message("dashboard", repo_settings, clone_dir="/tmp/repo")

    # _build_expected emits freeform before gitauto_md, encoding the ordering contract.
    assert result == _build_expected(
        trigger_block="<trigger>Trigger</trigger>",
        freeform_block=(
            "<freeform_repository_rules>\n"
            "Use TypeScript\n"
            "</freeform_repository_rules>"
        ),
        gitauto_md_block=(
            "<gitauto_md_rules>\n" "## Testing\n- Use factories\n" "</gitauto_md_rules>"
        ),
    )


def test_with_preferred_language_japanese(mock_read_xml_file, mock_get_trigger_prompt):
    mock_read_xml_file.return_value = "<rules>Rules</rules>"
    mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"

    repo_settings = create_repositories_data(preferred_language="ja")
    result = create_system_message("dashboard", repo_settings)

    assert result == _build_expected(
        language_block=(
            "<user_language_preference>\n"
            "Write all GitHub comments and code comments in ja (ISO 639 language code).\n"
            "</user_language_preference>"
        ),
        trigger_block="<trigger>Trigger</trigger>",
    )


def test_with_no_preferred_language(mock_read_xml_file, mock_get_trigger_prompt):
    mock_read_xml_file.return_value = "<rules>Rules</rules>"
    mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"

    repo_settings = create_repositories_data(preferred_language=None)
    result = create_system_message("dashboard", repo_settings)

    assert result == _build_expected(trigger_block="<trigger>Trigger</trigger>")


def test_with_preferred_language_english(mock_read_xml_file, mock_get_trigger_prompt):
    mock_read_xml_file.return_value = "<rules>Rules</rules>"
    mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"

    repo_settings = create_repositories_data(preferred_language="en")
    result = create_system_message("dashboard", repo_settings)

    assert result == _build_expected(trigger_block="<trigger>Trigger</trigger>")


def test_preferred_language_appears_first(mock_read_xml_file, mock_get_trigger_prompt):
    mock_read_xml_file.return_value = "<rules>Rules</rules>"
    mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"

    repo_settings = create_repositories_data(preferred_language="fr")
    result = create_system_message("dashboard", repo_settings)

    lang_pos = result.index("<user_language_preference>")
    trigger_pos = result.index("<trigger>")
    assert lang_pos < trigger_pos
