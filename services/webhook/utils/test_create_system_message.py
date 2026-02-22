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
        "blank_lines": 10,
        "comment_lines": 20,
        "code_lines": 70,
        "target_branch": "main",
        "trigger_on_review_comment": True,
        "trigger_on_test_failure": True,
        "trigger_on_commit": False,
        "trigger_on_merged": False,
        "trigger_on_schedule": False,
        "schedule_frequency": None,
        "schedule_minute": None,
        "schedule_time": None,
        "schedule_day_of_week": None,
        "schedule_include_weekends": False,
        "structured_rules": structured_rules,
        "trigger_on_pr_change": True,
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


def test_minimal_call_no_repo_settings(mock_read_xml_file, mock_get_trigger_prompt):
    mock_read_xml_file.return_value = "<rules>Rules</rules>"
    mock_get_trigger_prompt.return_value = (
        "<trigger_instruction>Issue trigger</trigger_instruction>"
    )

    result = create_system_message("dashboard")

    assert "<trigger_instruction>Issue trigger</trigger_instruction>" in result
    mock_get_trigger_prompt.assert_called_once_with("dashboard")
    # read_xml_file is called for coding_standards.xml
    assert mock_read_xml_file.call_count == 1


def test_all_trigger_types(mock_read_xml_file, mock_get_trigger_prompt):
    mock_read_xml_file.return_value = "<rules>Rules</rules>"
    mock_get_trigger_prompt.return_value = "<trigger>Content</trigger>"

    triggers: list[Trigger] = [
        "dashboard",
        "review_comment",
        "test_failure",
        "schedule",
    ]

    for trigger in triggers:
        result = create_system_message(trigger)
        assert result
        mock_get_trigger_prompt.assert_called_with(trigger)


def test_with_structured_rules_only(mock_read_xml_file, mock_get_trigger_prompt):
    mock_read_xml_file.return_value = "<rules>Rules</rules>"
    mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"

    structured_rules = {
        "codePatternStrategy": "Best practices first",
        "preferredApiApproach": "GraphQL first",
        "enforceOneFunctionPerFile": True,
        "preferConciseCodeTechniques": True,
    }
    repo_settings = create_repositories_data(structured_rules=structured_rules)

    result = create_system_message("dashboard", repo_settings)

    assert "<structured_repository_rules>" in result
    assert "codePatternStrategy: Best practices first" in result
    assert "preferredApiApproach: GraphQL first" in result
    assert "enforceOneFunctionPerFile: True" in result
    assert "preferConciseCodeTechniques: True" in result
    assert "</structured_repository_rules>" in result
    assert "<freeform_repository_rules>" not in result


def test_with_repo_rules_only(mock_read_xml_file, mock_get_trigger_prompt):
    mock_read_xml_file.return_value = "<rules>Rules</rules>"
    mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"

    repo_rules = "Always use TypeScript\nPrefer functional components\nUse ESLint"
    repo_settings = create_repositories_data(repo_rules=repo_rules)

    result = create_system_message("dashboard", repo_settings)

    assert "<freeform_repository_rules>" in result
    assert "Always use TypeScript" in result
    assert "Prefer functional components" in result
    assert "Use ESLint" in result
    assert "</freeform_repository_rules>" in result
    assert "<structured_repository_rules>" not in result


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

    assert "<structured_repository_rules>" in result
    assert "testFramework: Jest" in result
    assert "enableMocking: True" in result
    assert "</structured_repository_rules>" in result
    assert "<freeform_repository_rules>" in result
    assert "Use strict mode" in result
    assert "Document all functions" in result
    assert "</freeform_repository_rules>" in result


def test_with_empty_structured_rules(mock_read_xml_file, mock_get_trigger_prompt):
    mock_read_xml_file.return_value = "<rules>Rules</rules>"
    mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"

    repo_settings = create_repositories_data(structured_rules={})

    result = create_system_message("dashboard", repo_settings)

    assert "<structured_repository_rules>" not in result
    assert "<freeform_repository_rules>" not in result


def test_with_empty_repo_rules(mock_read_xml_file, mock_get_trigger_prompt):
    mock_read_xml_file.return_value = "<rules>Rules</rules>"
    mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"

    repo_settings = create_repositories_data(repo_rules="")

    result = create_system_message("dashboard", repo_settings)

    assert "<freeform_repository_rules>" not in result


def test_with_whitespace_only_repo_rules(mock_read_xml_file, mock_get_trigger_prompt):
    mock_read_xml_file.return_value = "<rules>Rules</rules>"
    mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"

    repo_settings = create_repositories_data(repo_rules="   \n\t  ")

    result = create_system_message("dashboard", repo_settings)

    assert "<freeform_repository_rules>" not in result


def test_with_none_structured_rules(mock_read_xml_file, mock_get_trigger_prompt):
    mock_read_xml_file.return_value = "<rules>Rules</rules>"
    mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"

    repo_settings = create_repositories_data(structured_rules=None)

    result = create_system_message("dashboard", repo_settings)

    assert "<structured_repository_rules>" not in result


def test_with_none_repo_rules(mock_read_xml_file, mock_get_trigger_prompt):
    mock_read_xml_file.return_value = "<rules>Rules</rules>"
    mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"

    repo_settings = create_repositories_data(repo_rules=None)

    result = create_system_message("dashboard", repo_settings)

    assert "<freeform_repository_rules>" not in result


def test_trigger_prompt_returns_none(mock_read_xml_file, mock_get_trigger_prompt):
    mock_read_xml_file.return_value = "<rules>Rules</rules>"
    mock_get_trigger_prompt.return_value = None

    result = create_system_message("dashboard")

    assert result
    assert "<rules>Rules</rules>" in result


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

    assert "stringValue: test string" in result
    assert "intValue: 42" in result
    assert "floatValue: 3.14" in result
    assert "boolValue: True" in result
    assert "listValue: ['item1', 'item2']" in result
    assert "dictValue: {'nested': 'value'}" in result
    assert "noneValue: None" in result


def test_repo_rules_with_leading_trailing_whitespace(
    mock_read_xml_file, mock_get_trigger_prompt
):
    mock_read_xml_file.return_value = "<rules>Rules</rules>"
    mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"

    repo_rules = "  \n  Use clean code principles  \n  "
    repo_settings = create_repositories_data(repo_rules=repo_rules)

    result = create_system_message("dashboard", repo_settings)

    assert "<freeform_repository_rules>" in result
    assert "Use clean code principles" in result
    assert "</freeform_repository_rules>" in result
    assert "  \n  Use clean code principles  \n  " not in result


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
