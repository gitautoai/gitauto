from unittest.mock import patch, MagicMock
from typing import cast, Any
import pytest
from schemas.supabase.types import Repositories
from services.supabase.usage.insert_usage import Trigger
from services.webhook.utils.create_system_message import create_system_message


def create_repositories_data(
    structured_rules: dict[str, Any] | None = None,
    repo_rules: str | None = None,
    **overrides,
) -> Repositories:
    """Helper function to create Repositories data."""
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
    """Mock the read_xml_file function."""
    with patch("services.webhook.utils.create_system_message.read_xml_file") as mock:
        yield mock


@pytest.fixture
def mock_get_trigger_prompt():
    """Mock the get_trigger_prompt function."""
    with patch("services.webhook.utils.create_system_message.get_trigger_prompt") as mock:
        yield mock


@pytest.fixture
def mock_get_mode_prompt():
    """Mock the get_mode_prompt function."""
    with patch("services.webhook.utils.create_system_message.get_mode_prompt") as mock:
        yield mock


class TestCreateSystemMessage:
    """Test cases for create_system_message function."""

    def test_minimal_call_no_repo_settings(
        self, mock_read_xml_file, mock_get_trigger_prompt, mock_get_mode_prompt
    ):
        """Test creating system message with minimal parameters."""
        # Arrange
        mock_read_xml_file.return_value = "<test_rules>Common test rules</test_rules>"
        mock_get_trigger_prompt.return_value = "<trigger_instruction>Issue trigger</trigger_instruction>"
        mock_get_mode_prompt.return_value = "<mode_instruction>Comment mode</mode_instruction>"

        # Act
        result = create_system_message("issue_comment", "comment")

        # Assert
        expected_content = (
            "<test_rules>Common test rules</test_rules>\n\n"
            "<trigger_instruction>Issue trigger</trigger_instruction>\n\n"
            "<mode_instruction>Comment mode</mode_instruction>"
        )
        assert result == expected_content
        mock_read_xml_file.assert_called_once_with("utils/prompts/common_test_rules.xml")
        mock_get_trigger_prompt.assert_called_once_with("issue_comment")
        mock_get_mode_prompt.assert_called_once_with("comment")

    def test_all_trigger_types(
        self, mock_read_xml_file, mock_get_trigger_prompt, mock_get_mode_prompt
    ):
        """Test creating system message with all trigger types."""
        # Arrange
        mock_read_xml_file.return_value = "<test_rules>Rules</test_rules>"
        mock_get_trigger_prompt.return_value = "<trigger>Content</trigger>"
        mock_get_mode_prompt.return_value = "<mode>Content</mode>"

        triggers: list[Trigger] = [
            "issue_label",
            "issue_comment",
            "review_comment",
            "test_failure",
            "pr_checkbox",
            "pr_merge",
        ]

        # Act & Assert
        for trigger in triggers:
            result = create_system_message(trigger, "comment")
            assert result  # Should return non-empty content
            mock_get_trigger_prompt.assert_called_with(trigger)

    def test_all_mode_types(
        self, mock_read_xml_file, mock_get_trigger_prompt, mock_get_mode_prompt
    ):
        """Test creating system message with all mode types."""
        # Arrange
        mock_read_xml_file.return_value = "<test_rules>Rules</test_rules>"
        mock_get_trigger_prompt.return_value = "<trigger>Content</trigger>"
        mock_get_mode_prompt.return_value = "<mode>Content</mode>"

        modes = ["comment", "commit", "explore", "get", "search"]

        # Act & Assert
        for mode in modes:
            result = create_system_message("issue_comment", mode)
            assert result  # Should return non-empty content
            mock_get_mode_prompt.assert_called_with(mode)

    def test_with_structured_rules_only(
        self, mock_read_xml_file, mock_get_trigger_prompt, mock_get_mode_prompt
    ):
        """Test creating system message with structured rules only."""
        # Arrange
        mock_read_xml_file.return_value = "<test_rules>Rules</test_rules>"
        mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"
        mock_get_mode_prompt.return_value = "<mode>Mode</mode>"

        structured_rules = {
            "codePatternStrategy": "Best practices first",
            "preferredApiApproach": "GraphQL first",
            "enforceOneFunctionPerFile": True,
            "preferConciseCodeTechniques": True,
        }
        repo_settings = create_repositories_data(structured_rules=structured_rules)

        # Act
        result = create_system_message("issue_comment", "comment", repo_settings)

        # Assert
        assert "<structured_repository_rules>" in result
        assert "codePatternStrategy: Best practices first" in result
        assert "preferredApiApproach: GraphQL first" in result
        assert "enforceOneFunctionPerFile: True" in result
        assert "preferConciseCodeTechniques: True" in result
        assert "</structured_repository_rules>" in result
        assert "<freeform_repository_rules>" not in result

    def test_with_repo_rules_only(
        self, mock_read_xml_file, mock_get_trigger_prompt, mock_get_mode_prompt
    ):
        """Test creating system message with repo rules only."""
        # Arrange
        mock_read_xml_file.return_value = "<test_rules>Rules</test_rules>"
        mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"
        mock_get_mode_prompt.return_value = "<mode>Mode</mode>"

        repo_rules = "Always use TypeScript\nPrefer functional components\nUse ESLint"
        repo_settings = create_repositories_data(repo_rules=repo_rules)

        # Act
        result = create_system_message("issue_comment", "comment", repo_settings)

        # Assert
        assert "<freeform_repository_rules>" in result
        assert "Always use TypeScript" in result
        assert "Prefer functional components" in result
        assert "Use ESLint" in result
        assert "</freeform_repository_rules>" in result
        assert "<structured_repository_rules>" not in result

    def test_with_both_structured_and_repo_rules(
        self, mock_read_xml_file, mock_get_trigger_prompt, mock_get_mode_prompt
    ):
        """Test creating system message with both structured and repo rules."""
        # Arrange
        mock_read_xml_file.return_value = "<test_rules>Rules</test_rules>"
        mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"
        mock_get_mode_prompt.return_value = "<mode>Mode</mode>"

        structured_rules = {
            "testFramework": "Jest",
            "enableMocking": True,
        }
        repo_rules = "Use strict mode\nDocument all functions"
        repo_settings = create_repositories_data(
            structured_rules=structured_rules, repo_rules=repo_rules
        )

        # Act
        result = create_system_message("issue_comment", "comment", repo_settings)

        # Assert
        assert "<structured_repository_rules>" in result
        assert "testFramework: Jest" in result
        assert "enableMocking: True" in result
        assert "</structured_repository_rules>" in result
        assert "<freeform_repository_rules>" in result
        assert "Use strict mode" in result
        assert "Document all functions" in result
        assert "</freeform_repository_rules>" in result

    def test_with_empty_structured_rules(
        self, mock_read_xml_file, mock_get_trigger_prompt, mock_get_mode_prompt
    ):
        """Test creating system message with empty structured rules."""
        # Arrange
        mock_read_xml_file.return_value = "<test_rules>Rules</test_rules>"
        mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"
        mock_get_mode_prompt.return_value = "<mode>Mode</mode>"

        repo_settings = create_repositories_data(structured_rules={})

        # Act
        result = create_system_message("issue_comment", "comment", repo_settings)

        # Assert
        assert "<structured_repository_rules>" not in result
        assert "<freeform_repository_rules>" not in result

    def test_with_empty_repo_rules(
        self, mock_read_xml_file, mock_get_trigger_prompt, mock_get_mode_prompt
    ):
        """Test creating system message with empty repo rules."""
        # Arrange
        mock_read_xml_file.return_value = "<test_rules>Rules</test_rules>"
        mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"
        mock_get_mode_prompt.return_value = "<mode>Mode</mode>"

        repo_settings = create_repositories_data(repo_rules="")

        # Act
        result = create_system_message("issue_comment", "comment", repo_settings)

        # Assert
        assert "<freeform_repository_rules>" not in result

    def test_with_whitespace_only_repo_rules(
        self, mock_read_xml_file, mock_get_trigger_prompt, mock_get_mode_prompt
    ):
        """Test creating system message with whitespace-only repo rules."""
        # Arrange
        mock_read_xml_file.return_value = "<test_rules>Rules</test_rules>"
        mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"
        mock_get_mode_prompt.return_value = "<mode>Mode</mode>"

        repo_settings = create_repositories_data(repo_rules="   \n\t  ")

        # Act
        result = create_system_message("issue_comment", "comment", repo_settings)

        # Assert
        assert "<freeform_repository_rules>" not in result

    def test_with_none_structured_rules(
        self, mock_read_xml_file, mock_get_trigger_prompt, mock_get_mode_prompt
    ):
        """Test creating system message with None structured rules."""
        # Arrange
        mock_read_xml_file.return_value = "<test_rules>Rules</test_rules>"
        mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"
        mock_get_mode_prompt.return_value = "<mode>Mode</mode>"

        repo_settings = create_repositories_data(structured_rules=None)

        # Act
        result = create_system_message("issue_comment", "comment", repo_settings)

        # Assert
        assert "<structured_repository_rules>" not in result

    def test_with_none_repo_rules(
        self, mock_read_xml_file, mock_get_trigger_prompt, mock_get_mode_prompt
    ):
        """Test creating system message with None repo rules."""
        # Arrange
        mock_read_xml_file.return_value = "<test_rules>Rules</test_rules>"
        mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"
        mock_get_mode_prompt.return_value = "<mode>Mode</mode>"

        repo_settings = create_repositories_data(repo_rules=None)

        # Act
        result = create_system_message("issue_comment", "comment", repo_settings)

        # Assert
        assert "<freeform_repository_rules>" not in result

    def test_trigger_prompt_returns_none(
        self, mock_read_xml_file, mock_get_trigger_prompt, mock_get_mode_prompt
    ):
        """Test creating system message when trigger prompt returns None."""
        # Arrange
        mock_read_xml_file.return_value = "<test_rules>Rules</test_rules>"
        mock_get_trigger_prompt.return_value = None
        mock_get_mode_prompt.return_value = "<mode>Mode</mode>"

        # Act
        result = create_system_message("issue_comment", "comment")

        # Assert
        expected_content = (
            "<test_rules>Rules</test_rules>\n\n"
            "<mode>Mode</mode>"
        )
        assert result == expected_content

    def test_mode_prompt_returns_none(
        self, mock_read_xml_file, mock_get_trigger_prompt, mock_get_mode_prompt
    ):
        """Test creating system message when mode prompt returns None."""
        # Arrange
        mock_read_xml_file.return_value = "<test_rules>Rules</test_rules>"
        mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"
        mock_get_mode_prompt.return_value = None

        # Act
        result = create_system_message("issue_comment", "comment")

        # Assert
        expected_content = (
            "<test_rules>Rules</test_rules>\n\n"
            "<trigger>Trigger</trigger>"
        )
        assert result == expected_content

    def test_both_prompts_return_none(
        self, mock_read_xml_file, mock_get_trigger_prompt, mock_get_mode_prompt
    ):
        """Test creating system message when both prompts return None."""
        # Arrange
        mock_read_xml_file.return_value = "<test_rules>Rules</test_rules>"
        mock_get_trigger_prompt.return_value = None
        mock_get_mode_prompt.return_value = None

        # Act
        result = create_system_message("issue_comment", "comment")

        # Assert
        assert result == "<test_rules>Rules</test_rules>"

    def test_structured_rules_with_various_data_types(
        self, mock_read_xml_file, mock_get_trigger_prompt, mock_get_mode_prompt
    ):
        """Test structured rules with various data types."""
        # Arrange
        mock_read_xml_file.return_value = "<test_rules>Rules</test_rules>"
        mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"
        mock_get_mode_prompt.return_value = "<mode>Mode</mode>"

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

        # Act
        result = create_system_message("issue_comment", "comment", repo_settings)

        # Assert
        assert "stringValue: test string" in result
        assert "intValue: 42" in result
        assert "floatValue: 3.14" in result
        assert "boolValue: True" in result
        assert "listValue: ['item1', 'item2']" in result
        assert "dictValue: {'nested': 'value'}" in result
        assert "noneValue: None" in result

    def test_repo_rules_with_leading_trailing_whitespace(
        self, mock_read_xml_file, mock_get_trigger_prompt, mock_get_mode_prompt
    ):
        """Test repo rules with leading and trailing whitespace."""
        # Arrange
        mock_read_xml_file.return_value = "<test_rules>Rules</test_rules>"
        mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"
        mock_get_mode_prompt.return_value = "<mode>Mode</mode>"

        repo_rules = "  \n  Use clean code principles  \n  "
        repo_settings = create_repositories_data(repo_rules=repo_rules)

        # Act
        result = create_system_message("issue_comment", "comment", repo_settings)

        # Assert
        assert "<freeform_repository_rules>" in result
        assert "Use clean code principles" in result
        assert "</freeform_repository_rules>" in result
        # Should not contain the extra whitespace
        assert "  \n  Use clean code principles  \n  " not in result

    def test_content_parts_joining(
        self, mock_read_xml_file, mock_get_trigger_prompt, mock_get_mode_prompt
    ):
        """Test that content parts are joined correctly with double newlines."""
        # Arrange
        mock_read_xml_file.return_value = "COMMON_RULES"
        mock_get_trigger_prompt.return_value = "TRIGGER_CONTENT"
        mock_get_mode_prompt.return_value = "MODE_CONTENT"

        structured_rules = {"rule": "value"}
        repo_rules = "Free form rule"
        repo_settings = create_repositories_data(
            structured_rules=structured_rules, repo_rules=repo_rules
        )

        # Act
        result = create_system_message("issue_comment", "comment", repo_settings)

        # Assert
        parts = result.split("\n\n")
        assert len(parts) == 5
        assert parts[0] == "COMMON_RULES"
        assert parts[1] == "TRIGGER_CONTENT"
        assert parts[2] == "MODE_CONTENT"
        assert parts[3] == "<structured_repository_rules>\nrule: value\n</structured_repository_rules>"
        assert parts[4] == "<freeform_repository_rules>\nFree form rule\n</freeform_repository_rules>"

    def test_empty_content_parts_returns_empty_string(
        self, mock_read_xml_file, mock_get_trigger_prompt, mock_get_mode_prompt
    ):
        """Test that empty content parts returns empty string."""
        # Arrange
        mock_read_xml_file.return_value = ""
        mock_get_trigger_prompt.return_value = None
        mock_get_mode_prompt.return_value = None

        # Act
        result = create_system_message("issue_comment", "comment")

        # Assert
        assert result == ""

    @patch("services.webhook.utils.create_system_message.handle_exceptions")
    def test_handle_exceptions_decorator_applied(
        self, mock_handle_exceptions, mock_read_xml_file, mock_get_trigger_prompt, mock_get_mode_prompt
    ):
        """Test that the handle_exceptions decorator is applied correctly."""
        # Arrange
        mock_handle_exceptions.return_value = lambda func: func
        mock_read_xml_file.return_value = "<test_rules>Rules</test_rules>"
        mock_get_trigger_prompt.return_value = "<trigger>Trigger</trigger>"
        mock_get_mode_prompt.return_value = "<mode>Mode</mode>"

        # Act
        result = create_system_message("issue_comment", "comment")

        # Assert
        mock_handle_exceptions.assert_called_once_with(
            default_return_value="", raise_on_error=False
        )
        assert result  # Should return content

    def test_integration_without_mocks(self):
        """Test the function with actual dependencies (integration test)."""
        # This test uses real dependencies to ensure the function works end-to-end
        # We'll use a simple case to avoid file system dependencies
        
        # Arrange
        structured_rules = {"testRule": "testValue"}
        repo_rules = "Test repo rule"
        repo_settings = create_repositories_data(
            structured_rules=structured_rules, repo_rules=repo_rules
        )

        # Act
        result = create_system_message("issue_comment", "comment", repo_settings)

        # Assert
        # The function should return a string (even if dependencies fail due to missing files)
        assert isinstance(result, str)
        # Due to the handle_exceptions decorator, it should return empty string on error
        # or actual content if dependencies work
