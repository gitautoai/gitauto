# pylint: disable=redefined-outer-name
from unittest.mock import patch, MagicMock
import pytest
from gql.transport.exceptions import TransportError

from services.github.issues.get_issue_body import get_issue_body


class TestGetIssueBody:
    """Test cases for get_issue_body function."""

    @pytest.fixture
    def mock_graphql_client(self):
        """Fixture to provide a mocked GraphQL client."""
        with patch("services.github.issues.get_issue_body.get_graphql_client") as mock:
            mock_client = MagicMock()
            mock.return_value = mock_client
            yield mock_client

    @pytest.fixture
    def sample_params(self):
        """Fixture to provide sample parameters for testing."""
        return {
            "owner": "testowner",
            "repo": "testrepo",
            "issue_number": 123,
            "token": "test_token_123",
        }

    def test_get_issue_body_successful_response(
        self, mock_graphql_client, sample_params
    ):
        """Test successful retrieval of issue body."""
        expected_body = "This is the issue body content"
        mock_graphql_client.execute.return_value = {
            "repository": {"issue": {"body": expected_body}}
        }

        result = get_issue_body(**sample_params)

        assert result == expected_body
        mock_graphql_client.execute.assert_called_once()

    def test_get_issue_body_null_body(self, mock_graphql_client, sample_params):
        """Test when issue body is null."""
        mock_graphql_client.execute.return_value = {
            "repository": {"issue": {"body": None}}
        }

        result = get_issue_body(**sample_params)

        assert result is None
        mock_graphql_client.execute.assert_called_once()

    def test_get_issue_body_empty_string_body(self, mock_graphql_client, sample_params):
        """Test when issue body is an empty string."""
        mock_graphql_client.execute.return_value = {
            "repository": {"issue": {"body": ""}}
        }

        result = get_issue_body(**sample_params)

        assert result == ""
        mock_graphql_client.execute.assert_called_once()

    def test_get_issue_body_missing_repository(
        self, mock_graphql_client, sample_params
    ):
        """Test when repository is missing from response."""
        mock_graphql_client.execute.return_value = {}

        result = get_issue_body(**sample_params)

        assert result is None
        mock_graphql_client.execute.assert_called_once()

    def test_get_issue_body_missing_issue(self, mock_graphql_client, sample_params):
        """Test when issue is missing from repository response."""
        mock_graphql_client.execute.return_value = {"repository": {}}

        result = get_issue_body(**sample_params)

        assert result is None
        mock_graphql_client.execute.assert_called_once()

    def test_get_issue_body_missing_body_field(
        self, mock_graphql_client, sample_params
    ):
        """Test when body field is missing from issue response."""
        mock_graphql_client.execute.return_value = {"repository": {"issue": {}}}

        result = get_issue_body(**sample_params)

        assert result is None
        mock_graphql_client.execute.assert_called_once()

    def test_get_issue_body_graphql_query_structure(
        self, mock_graphql_client, sample_params
    ):
        """Test that the GraphQL query is constructed correctly."""
        mock_graphql_client.execute.return_value = {
            "repository": {"issue": {"body": "test"}}
        }

        get_issue_body(**sample_params)

        # Verify execute was called with correct parameters
        call_args = mock_graphql_client.execute.call_args
        assert call_args is not None

        # Check that document parameter is a gql query
        document = call_args.kwargs.get("document") or call_args[1]["document"]
        assert document is not None

        # Check variable_values parameter
        variable_values = (
            call_args.kwargs.get("variable_values") or call_args[1]["variable_values"]
        )
        expected_variables = {
            "owner": sample_params["owner"],
            "repo": sample_params["repo"],
            "number": sample_params["issue_number"],
        }
        assert variable_values == expected_variables

    def test_get_issue_body_with_different_parameters(self, mock_graphql_client):
        """Test function with various parameter combinations."""
        test_cases = [
            {"owner": "github", "repo": "docs", "issue_number": 1, "token": "token1"},
            {
                "owner": "microsoft",
                "repo": "vscode",
                "issue_number": 999999,
                "token": "very_long_token_string_123456789",
            },
            {"owner": "a", "repo": "b", "issue_number": 0, "token": ""},
        ]

        for params in test_cases:
            mock_graphql_client.reset_mock()
            mock_graphql_client.execute.return_value = {
                "repository": {"issue": {"body": f"body for {params['issue_number']}"}}
            }

            result = get_issue_body(**params)

            assert result == f"body for {params['issue_number']}"
            mock_graphql_client.execute.assert_called_once()

    def test_get_issue_body_multiline_content(self, mock_graphql_client, sample_params):
        """Test with multiline issue body content."""
        multiline_body = """This is a multiline issue body.

It contains:
- Multiple lines
- Special characters: !@#$%^&*()
- Unicode: 🚀 ✨ 🎉

And some code:
```python
def hello():
    print("Hello, World!")
```

End of issue body."""

        mock_graphql_client.execute.return_value = {
            "repository": {"issue": {"body": multiline_body}}
        }

        result = get_issue_body(**sample_params)

        assert result == multiline_body
        mock_graphql_client.execute.assert_called_once()

    def test_get_issue_body_special_characters(
        self, mock_graphql_client, sample_params
    ):
        """Test with issue body containing special characters."""
        special_body = "Issue with special chars: <>&\"'`~!@#$%^&*()_+-=[]{}|;:,.<>?"

        mock_graphql_client.execute.return_value = {
            "repository": {"issue": {"body": special_body}}
        }

        result = get_issue_body(**sample_params)

        assert result == special_body
        mock_graphql_client.execute.assert_called_once()

    def test_get_issue_body_unicode_content(self, mock_graphql_client, sample_params):
        """Test with issue body containing Unicode characters."""
        unicode_body = "Unicode test: 🚀 ✨ 🎉 中文 العربية русский язык"

        mock_graphql_client.execute.return_value = {
            "repository": {"issue": {"body": unicode_body}}
        }

        result = get_issue_body(**sample_params)

        assert result == unicode_body
        mock_graphql_client.execute.assert_called_once()

    def test_get_issue_body_very_long_content(self, mock_graphql_client, sample_params):
        """Test with very long issue body content."""
        long_body = "A" * 10000  # 10KB of content

        mock_graphql_client.execute.return_value = {
            "repository": {"issue": {"body": long_body}}
        }

        result = get_issue_body(**sample_params)

        assert result is not None
        assert result == long_body
        assert len(result) == 10000
        mock_graphql_client.execute.assert_called_once()

    @patch("services.github.issues.get_issue_body.get_graphql_client")
    def test_get_issue_body_client_creation(self, mock_get_client, sample_params):
        """Test that GraphQL client is created with correct token."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.execute.return_value = {"repository": {"issue": {"body": "test"}}}

        get_issue_body(**sample_params)

        mock_get_client.assert_called_once_with(sample_params["token"])

    def test_get_issue_body_exception_handling_returns_none(
        self, mock_graphql_client, sample_params
    ):
        """Test that exceptions are handled and None is returned due to @handle_exceptions decorator."""
        # Simulate a GraphQL transport error
        mock_graphql_client.execute.side_effect = TransportError("Network error")

        result = get_issue_body(**sample_params)

        # Due to @handle_exceptions decorator with default_return_value=None
        assert result is None

    def test_get_issue_body_key_error_handling(
        self, mock_graphql_client, sample_params
    ):
        """Test handling of KeyError when accessing nested response data."""
        # This should not raise KeyError due to safe .get() usage
        mock_graphql_client.execute.return_value = {
            "repository": {"issue": {"different_field": "value"}}
        }

        result = get_issue_body(**sample_params)

        assert result is None
        mock_graphql_client.execute.assert_called_once()

    def test_get_issue_body_malformed_response(
        self, mock_graphql_client, sample_params
    ):
        """Test handling of malformed response structure."""
        malformed_responses = [
            None,
            "string_instead_of_dict",
            123,
            [],
            {"repository": None},
            {"repository": "string"},
            {"repository": {"issue": None}},
            {"repository": {"issue": "string"}},
        ]

        for malformed_response in malformed_responses:
            mock_graphql_client.reset_mock()
            mock_graphql_client.execute.return_value = malformed_response

            result = get_issue_body(**sample_params)

            assert result is None
            mock_graphql_client.execute.assert_called_once()

    def test_get_issue_body_return_type_consistency(
        self, mock_graphql_client, sample_params
    ):
        """Test that return type is consistent (str or None)."""
        test_bodies = ["normal string", "", None, "123", "true", "false"]

        for body in test_bodies:
            mock_graphql_client.reset_mock()
            mock_graphql_client.execute.return_value = {
                "repository": {"issue": {"body": body}}
            }

            result = get_issue_body(**sample_params)

            assert result == body
            assert isinstance(result, (str, type(None)))

    def test_get_issue_body_parameter_types(self, mock_graphql_client):
        mock_graphql_client.execute.return_value = {
            "repository": {"issue": {"body": "test"}}
        }

        result = get_issue_body("owner", "repo", -1, "token")
        assert result == "test"

    def test_get_issue_body_edge_case_parameters(self, mock_graphql_client):
        """Test function with edge case parameters."""
        mock_graphql_client.execute.return_value = {
            "repository": {"issue": {"body": "test"}}
        }

        # Test with empty strings
        result = get_issue_body("", "", 1, "")
        assert result == "test"

        # Test with very long strings
        long_string = "a" * 1000
        result = get_issue_body(long_string, long_string, 1, long_string)
        assert result == "test"

    def test_get_issue_body_graphql_variables_mapping(
        self, mock_graphql_client, sample_params
    ):
        """Test that function parameters are correctly mapped to GraphQL variables."""
        mock_graphql_client.execute.return_value = {
            "repository": {"issue": {"body": "test"}}
        }

        get_issue_body(**sample_params)

        call_args = mock_graphql_client.execute.call_args
        variable_values = (
            call_args.kwargs.get("variable_values") or call_args[1]["variable_values"]
        )

        # Verify the mapping: issue_number -> number
        assert variable_values["owner"] == sample_params["owner"]
        assert variable_values["repo"] == sample_params["repo"]
        assert variable_values["number"] == sample_params["issue_number"]
        assert "token" not in variable_values  # token is not passed to GraphQL
        assert "issue_number" not in variable_values  # should be mapped to "number"

    def test_get_issue_body_integration_with_real_gql_query(
        self, mock_graphql_client, sample_params
    ):
        """Test that the function works with the actual GraphQL query structure."""
        mock_graphql_client.execute.return_value = {
            "repository": {"issue": {"body": "integration test"}}
        }

        result = get_issue_body(**sample_params)

        # Verify the query structure by checking the call
        call_args = mock_graphql_client.execute.call_args
        document = call_args.kwargs.get("document") or call_args[1]["document"]

        # The document should be a gql object with the expected query structure
        assert document is not None
        assert result == "integration test"

    def test_get_issue_body_with_nested_response_variations(
        self, mock_graphql_client, sample_params
    ):
        """Test various nested response structures that might be returned."""
        test_responses = [
            # Normal response
            {"repository": {"issue": {"body": "normal"}}},
            # Repository exists but issue is None
            {"repository": {"issue": None}},
            # Repository exists but no issue key
            {"repository": {}},
            # No repository key
            {},
            # Repository is None
            {"repository": None},
        ]

        expected_results = ["normal", None, None, None, None]

        for response, expected in zip(test_responses, expected_results):
            mock_graphql_client.reset_mock()
            mock_graphql_client.execute.return_value = response

            result = get_issue_body(**sample_params)
            assert result == expected

    def test_get_issue_body_function_docstring_exists(self):
        """Test that the function has proper documentation."""
        assert get_issue_body.__doc__ is not None
        assert "Get issue body using GraphQL API" in get_issue_body.__doc__

    def test_get_issue_body_decorator_applied(self):
        """Test that the @handle_exceptions decorator is properly applied."""
        assert hasattr(get_issue_body, "__wrapped__")
