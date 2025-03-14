from gql import gql
from tests.constants import TOKEN
from services.github.graphql_client import get_graphql_client


def test_get_graphql_client():
    client = get_graphql_client(token=TOKEN)
    query = gql(
        """
        query {
          viewer {
            login
          }
        }
        """
    )
    result = client.execute(query)
    assert result
    assert "viewer" in result
    assert "login" in result["viewer"]
    assert isinstance(result["viewer"]["login"], str)
    assert len(result["viewer"]["login"]) > 0


test_get_graphql_client()