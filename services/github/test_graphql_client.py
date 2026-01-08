from gql.transport.requests import RequestsHTTPTransport
from services.github.graphql_client import get_graphql_client


def test_get_graphql_client(monkeypatch):
    monkeypatch.setattr(
        "services.github.graphql_client.GITHUB_API_URL", "https://api.github.com"
    )
    token = "dummy_token"
    client = get_graphql_client(token)
    assert client is not None
    transport = client.transport
    assert transport is not None
    assert isinstance(transport, RequestsHTTPTransport)
    assert transport.url == "https://api.github.com/graphql"
    assert transport.headers is not None
    assert transport.headers["Authorization"] == "Bearer dummy_token"
    assert transport.verify is True
    assert transport.retries == 3
    assert client.fetch_schema_from_transport is True


def test_empty_token(monkeypatch):
    monkeypatch.setattr(
        "services.github.graphql_client.GITHUB_API_URL", "https://api.github.com"
    )
    token = ""
    client = get_graphql_client(token)
    transport = client.transport
    assert isinstance(transport, RequestsHTTPTransport)
    assert transport.headers is not None
    assert "Authorization" in transport.headers
    assert transport.headers["Authorization"] == "Bearer "
