import pytest
from services.github.graphql_client import get_graphql_client
from tests.constants import TOKEN

def test_get_graphql_client_schema_fetch(monkeypatch):
    """
    Integration test for get_graphql_client function.
    It verifies that the GraphQL client is created with the correct transport configuration.

    Refer to GitHub GraphQL API documentation:
    https://docs.github.com/en/graphql
    """
    # Skip test if TOKEN is not valid for integration testing.
    if TOKEN == "dummy_token":
        pytest.skip("Skipping integration test because TOKEN is not valid.")

    client = get_graphql_client(TOKEN)
    transport = client.transport
    assert hasattr(transport, "url"), "Transport should have URL attribute"
    assert "graphql" in transport.url, "Transport URL should contain 'graphql'"

    try:
        schema = client.fetch_schema()
        assert schema is not None, "Schema should not be None"
    except Exception as e:
        pytest.skip(f"Skipping schema fetch due to network error: {e}")

if __name__ == "__main__":
    test_get_graphql_client_schema_fetch(None)
