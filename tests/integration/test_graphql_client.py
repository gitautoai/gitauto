import pytest
from services.github.graphql_client import get_graphql_client
from tests/constants import TOKEN


def test_get_graphql_client():
    """
    Integration test for get_graphql_client function.

    This test creates a GitHub GraphQL client using a token and performs
    a basic query to retrieve viewer information.

    For more details, refer to:
    https://docs.github.com/en/graphql
    """
    client = get_graphql_client(TOKEN)

    # A basic GitHub GraphQL query to retrieve the current authenticated user's login.
    query = """
    {
      viewer {
        login
      }
    }
    """

    result = client.execute(query)
    assert "viewer" in result, "Expected 'viewer' in response"
    assert "login" in result["viewer"], "Expected 'login' field in viewer"
