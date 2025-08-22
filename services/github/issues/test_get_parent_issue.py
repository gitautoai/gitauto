# pylint: disable=redefined-outer-name
from unittest.mock import patch, MagicMock
import pytest
from gql.transport.exceptions import TransportError

from services.github.issues.get_parent_issue import get_parent_issue


class TestGetParentIssue:
    """Test cases for get_parent_issue function."""

    @pytest.fixture
    def mock_graphql_client(self):
        """Fixture to provide a mocked GraphQL client."""
        with patch("services.github.issues.get_parent_issue.get_graphql_client") as mock:
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

    def test_get_parent_issue_successful_response(
        self, mock_graphql_client, sample_params
    ):
        """Test successful retrieval of parent issue information."""
        expected_parent = {
            "number": 456,
            "title": "Parent Issue Title",
            "body": "This is the parent issue body content",
        }
        mock_graphql_client.execute.return_value = {
            "repository": {
                "issue": {
                    "parent": {
                        "number": 456,
                        "title": "Parent Issue Title",
                        "body": "This is the parent issue body content",
                    }
                }
            }
        }

        result = get_parent_issue(**sample_params)

        assert result == expected_parent
        mock_graphql_client.execute.assert_called_once()

    def test_get_parent_issue_no_parent(self, mock_graphql_client, sample_params):
        """Test when issue has no parent."""
        mock_graphql_client.execute.return_value = {
            "repository": {"issue": {"parent": None}}
        }

        result = get_parent_issue(**sample_params)

        assert result is None
        mock_graphql_client.execute.assert_called_once()

    def test_get_parent_issue_empty_parent(self, mock_graphql_client, sample_params):
        """Test when parent is an empty dictionary."""
        mock_graphql_client.execute.return_value = {
            "repository": {"issue": {"parent": {}}}
        }

        result = get_parent_issue(**sample_params)

        assert result is None
        mock_graphql_client.execute.assert_called_once()

    def test_get_parent_issue_partial_parent_data(
        self, mock_graphql_client, sample_params
    ):
        """Test when parent has only some fields."""
        mock_graphql_client.execute.return_value = {
            "repository": {
                "issue": {
                    "parent": {
                        "number": 789,
                        "title": "Partial Parent",
                        # body is missing
                    }
                }
            }
        }

        result = get_parent_issue(**sample_params)

        expected = {
            "number": 789,
            "title": "Partial Parent",
            "body": None,
        }
        assert result == expected
        mock_graphql_client.execute.assert_called_once()

    def test_get_parent_issue_null_parent_fields(
        self, mock_graphql_client, sample_params
    ):
        """Test when parent fields are null."""
        mock_graphql_client.execute.return_value = {
            "repository": {
                "issue": {
                    "parent": {
                        "number": None,
                        "title": None,
                        "body": None,
                    }
                }
            }
        }

        result = get_parent_issue(**sample_params)

        expected = {
            "number": None,
            "title": None,
            "body": None,
        }
        assert result == expected
        mock_graphql_client.execute.assert_called_once()

    def test_get_parent_issue_missing_repository(
        self, mock_graphql_client, sample_params
    ):
        """Test when repository is missing from response."""
        mock_graphql_client.execute.return_value = {}

        result = get_parent_issue(**sample_params)

        assert result is None
        mock_graphql_client.execute.assert_called_once()

    def test_get_parent_issue_missing_issue(self, mock_graphql_client, sample_params):
        """Test when issue is missing from repository response."""
        mock_graphql_client.execute.return_value = {"repository": {}}

        result = get_parent_issue(**sample_params)

        assert result is None
        mock_graphql_client.execute.assert_called_once()

    def test_get_parent_issue_missing_parent_field(
        self, mock_graphql_client, sample_params
    ):
        """Test when parent field is missing from issue response."""
        mock_graphql_client.execute.return_value = {"repository": {"issue": {}}}

        result = get_parent_issue(**sample_params)

        assert result is None
        mock_graphql_client.execute.assert_called_once()

    def test_get_parent_issue_graphql_query_structure(
        self, mock_graphql_client, sample_params
    ):
        """Test that the GraphQL query is constructed correctly."""
        mock_graphql_client.execute.return_value = {
            "repository": {
                "issue": {
                    "parent": {
                        "number": 123,
                        "title": "Test",
                        "body": "Test body",
                    }
                }
            }
        }

        get_parent_issue(**sample_params)

        # Verify execute was called with correct parameters
        call_args = mock_graphql_client.execute.call_args
        assert call_args is not None

        # Check that document parameter is a gql query
        document = call_args.kwargs.get("document") or call_args[0][0]
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

    def test_get_parent_issue_with_different_parameters(self, mock_graphql_client):
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
                "repository": {
                    "issue": {
                        "parent": {
                            "number": params["issue_number"] + 1000,
                            "title": f"Parent for {params['issue_number']}",
                            "body": f"Body for parent of {params['issue_number']}",
                        }
                    }
                }
            }

            result = get_parent_issue(**params)

            expected = {
                "number": params["issue_number"] + 1000,
                "title": f"Parent for {params['issue_number']}",
                "body": f"Body for parent of {params['issue_number']}",
            }
            assert result == expected
            mock_graphql_client.execute.assert_called_once()

    def test_get_parent_issue_multiline_content(self, mock_graphql_client, sample_params):
        """Test with multiline parent issue content."""
        multiline_title = "Multi-line\nTitle"
        multiline_body = """This is a multiline parent issue body.

It contains:
- Multiple lines
- Special characters: !@#$%^&*()
- Unicode: 🚀 ✨ 🎉

And some code:
```python
def hello():
    print("Hello, World!")
```

End of parent issue body."""

        mock_graphql_client.execute.return_value = {
            "repository": {
                "issue": {
                    "parent": {
                        "number": 999,
                        "title": multiline_title,
                        "body": multiline_body,
                    }
                }
            }
        }

        result = get_parent_issue(**sample_params)

        expected = {
            "number": 999,
            "title": multiline_title,
            "body": multiline_body,
        }
        assert result == expected
        mock_graphql_client.execute.assert_called_once()

    def test_get_parent_issue_special_characters(
        self, mock_graphql_client, sample_params
    ):
        """Test with parent issue containing special characters."""
        special_title = "Issue with special chars: <>&\"'`~!@#$%^&*()"
        special_body = "Body with special chars: _+-=[]{}|;:,.<>?"

        mock_graphql_client.execute.return_value = {
            "repository": {
                "issue": {
                    "parent": {
                        "number": 777,
                        "title": special_title,
                        "body": special_body,
                    }
                }
            }
        }

        result = get_parent_issue(**sample_params)

        expected = {
            "number": 777,
            "title": special_title,
            "body": special_body,
        }
        assert result == expected
        mock_graphql_client.execute.assert_called_once()

    def test_get_parent_issue_unicode_content(self, mock_graphql_client, sample_params):
        """Test with parent issue containing Unicode characters."""
        unicode_title = "Unicode test: 🚀 ✨ 🎉"
        unicode_body = "Unicode body: 中文 العربية русский язык"

        mock_graphql_client.execute.return_value = {
            "repository": {
                "issue": {
                    "parent": {
                        "number": 888,
                        "title": unicode_title,
                        "body": unicode_body,
                    }
                }
            }
        }

        result = get_parent_issue(**sample_params)

        expected = {
            "number": 888,
            "title": unicode_title,
            "body": unicode_body,
        }
        assert result == expected
        mock_graphql_client.execute.assert_called_once()

    @patch("services.github.issues.get_parent_issue.get_graphql_client")
    def test_get_parent_issue_client_creation(self, mock_get_client, sample_params):
        """Test that GraphQL client is created with correct token."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.execute.return_value = {
            "repository": {
                "issue": {
                    "parent": {
                        "number": 123,
                        "title": "test",
                        "body": "test body",
                    }
                }
            }
        }

        get_parent_issue(**sample_params)

        mock_get_client.assert_called_once_with(sample_params["token"])

    def test_get_parent_issue_exception_handling_returns_none(
        self, mock_graphql_client, sample_params
    ):
        """Test that exceptions are handled and None is returned due to @handle_exceptions decorator."""
        # Simulate a GraphQL transport error
        mock_graphql_client.execute.side_effect = TransportError("Network error")

        result = get_parent_issue(**sample_params)

        # Due to @handle_exceptions decorator with default_return_value=None
        assert result is None

    def test_get_parent_issue_malformed_response(
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
            {"repository": {"issue": {"parent": "string"}}},
        ]

        for malformed_response in malformed_responses:
            mock_graphql_client.reset_mock()
            mock_graphql_client.execute.return_value = malformed_response

            result = get_parent_issue(**sample_params)

            assert result is None
            mock_graphql_client.execute.assert_called_once()

    def test_get_parent_issue_return_type_consistency(
        self, mock_graphql_client, sample_params
    ):
        """Test that return type is consistent (dict or None)."""
        # Test with valid parent data
        mock_graphql_client.execute.return_value = {
            "repository": {
                "issue": {
                    "parent": {
                        "number": 123,
                        "title": "Test Title",
                        "body": "Test Body",
                    }
                }
            }
        }

        result = get_parent_issue(**sample_params)
        assert isinstance(result, dict)
        assert "number" in result
        assert "title" in result
        assert "body" in result

        # Test with no parent
        mock_graphql_client.reset_mock()
        mock_graphql_client.execute.return_value = {
            "repository": {"issue": {"parent": None}}
        }

        result = get_parent_issue(**sample_params)
        assert result is None

    def test_get_parent_issue_function_docstring_exists(self):
        """Test that the function has proper documentation."""
        assert get_parent_issue.__doc__ is not None
        assert "Get parent issue information" in get_parent_issue.__doc__
        assert "GraphQL API" in get_parent_issue.__doc__

    def test_get_parent_issue_decorator_applied(self):
        """Test that the @handle_exceptions decorator is properly applied."""
        assert hasattr(get_parent_issue, "__wrapped__")
