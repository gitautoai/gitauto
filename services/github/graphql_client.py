from gql import Client
from gql.transport.requests import RequestsHTTPTransport
from config import GITHUB_API_URL


def get_graphql_client(token: str) -> Client:
    """Create and return a GraphQL client for GitHub API"""
    transport = RequestsHTTPTransport(
        url=f"{GITHUB_API_URL}/graphql",
        headers={"Authorization": f"Bearer {token}"},
        verify=True,
        retries=3,
    )

    client = Client(transport=transport, fetch_schema_from_transport=True)
    original_execute = client.execute
    def new_execute(query, *args, **kwargs):
        from gql import gql
        if isinstance(query, str):
            query = gql(query)
        return original_execute(query, *args, **kwargs)
    client.execute = new_execute
