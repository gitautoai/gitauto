from gql import gql
from services.github.graphql_client import get_graphql_client
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_parent_issue(owner: str, repo: str, issue_number: int, token: str):
    """Get parent issue information (number, title, body) using GraphQL API

    https://docs.github.com/en/graphql/reference/objects#issue
    """
    client = get_graphql_client(token)
    query = gql(
        """
        query GetParentIssue($owner: String!, $repo: String!, $number: Int!) {
          repository(owner: $owner, name: $repo) {
            issue(number: $number) {
              parent {
                number
                title
                body
              }
            }
          }
        }
    """
    )

    variables = {"owner": owner, "repo": repo, "number": issue_number}
    result = client.execute(document=query, variable_values=variables)

    parent = result.get("repository", {}).get("issue", {}).get("parent", {})
    if not parent:
        return None
    output = {
        "number": parent.get("number"),
        "title": parent.get("title"),
        "body": parent.get("body"),
    }
    return output
