from gql import gql
from tests.constants import TOKEN, OWNER, REPO
from services.github.graphql_client import get_graphql_client


def test_get_graphql_client():
    client = get_graphql_client(token=TOKEN)
    query = gql(
        """
        query GetRepository($owner: String!, $repo: String!) {
          repository(owner: $owner, name: $repo) {
            name
            description
          }
        }
    """
    )

    variables = {"owner": OWNER, "repo": REPO}
    result = client.execute(document=query, variable_values=variables)

    repository = result.get("repository", {})
    assert repository.get("name") == REPO
    assert isinstance(repository.get("description"), (str, type(None)))


def test_get_graphql_client_with_invalid_token():
    client = get_graphql_client(token="invalid_token")
    query = gql(
        """
        query GetRepository($owner: String!, $repo: String!) {
          repository(owner: $owner, name: $repo) {
            name
          }
        }
    """
    )

    variables = {"owner": OWNER, "repo": REPO}
    try:
        client.execute(document=query, variable_values=variables)
        assert False, "Should have raised an exception"
    except Exception as e:
        assert "401" in str(e) or "Unauthorized" in str(e)


def test_get_graphql_client_with_invalid_query():
    client = get_graphql_client(token=TOKEN)
    query = gql(
        """
        query GetInvalidField($owner: String!, $repo: String!) {
          repository(owner: $owner, name: $repo) {
            nonexistentField
          }
        }
    """
    )

    variables = {"owner": OWNER, "repo": REPO}
    try:
        client.execute(document=query, variable_values=variables)
        assert False, "Should have raised an exception"
    except Exception as e:
        assert "Cannot query field" in str(e)