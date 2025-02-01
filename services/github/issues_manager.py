from gql import gql
from services.github.graphql_client import get_graphql_client
from utils.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_issue_body(owner: str, repo: str, issue_number: int, token: str):
    """Get issue body using GraphQL API"""
    client = get_graphql_client(token)
    query = gql(
        """
        query GetIssueBody($owner: String!, $repo: String!, $number: Int!) {
          repository(owner: $owner, name: $repo) {
            issue(number: $number) {
              body
            }
          }
        }
    """
    )

    variables = {"owner": owner, "repo": repo, "number": issue_number}
    result = client.execute(document=query, variable_values=variables)

    body: str | None = result.get("repository", {}).get("issue", {}).get("body")
    return body


