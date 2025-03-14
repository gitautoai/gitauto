import pytest
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
from tests.constants import TOKEN, OWNER, REPO
from services.github.graphql_client import get_graphql_client


def test_get_graphql_client_returns_client():
    client = get_graphql_client(token=TOKEN)
    assert isinstance(client, Client)
    assert isinstance(client.transport, RequestsHTTPTransport)


def test_graphql_client_can_execute_query():
    client = get_graphql_client(token=TOKEN)
    query = gql(
        """
        query GetRepository($owner: String!, $name: String!) {
          repository(owner: $owner, name: $name) {
            name
            owner {
              login
            }
          }
        }
        """
    )
    result = client.execute(query, variable_values={"owner": OWNER, "name": REPO})
    assert result["repository"]["name"] == REPO
    assert result["repository"]["owner"]["login"] == OWNER


def test_graphql_client_with_invalid_token():
    client = get_graphql_client(token="invalid_token")
    with pytest.raises(Exception):
        client.execute(gql("query { viewer { login } }"))