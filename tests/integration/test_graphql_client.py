import os
import pytest
from services.github.graphql_client import get_graphql_client
from tests.constants import TOKEN, OWNER, REPO

# This integration test verifies that the GitHub GraphQL client can execute a simple query.
# See documentation: https://docs.github.com/en/graphql
def test_get_graphql_client_execute():
    # Get the GitHub GraphQL client
    client = get_graphql_client(TOKEN)
    assert client is not None, "GraphQL client should not be None"

    # Prepare a simple GraphQL query to fetch repository details.
    query = """query($owner: String!, $repo: String!) {
      repository(owner: $owner, name: $repo) {
        name
        owner { login }
      }
    }"""
    variables = {"owner": OWNER, "repo": REPO}

    # Execute the query using the GraphQL client.
    response = client.execute(query, variables)
    # Check that the response contains the repository details.
    assert "repository" in response, "Response must contain repository details"
    assert response.get("repository", {}).get("name") == REPO, "Repository name must match constant"
