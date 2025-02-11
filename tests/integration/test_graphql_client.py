import pytest
from gql import Client
from services.github.graphql_client import get_graphql_client
from tests.constants import TOKEN


def test_get_graphql_client_integration():
    """
    Integration test for get_graphql_client
    
    This test creates a GraphQL client for the GitHub API using the token from
    tests/constants.py. It verifies that the client is an instance of gql.Client.

    For more details, refer to the GitHub GraphQL API docs: https://docs.github.com/en/graphql
    """
    client = get_graphql_client(TOKEN)
    assert isinstance(client, Client)
