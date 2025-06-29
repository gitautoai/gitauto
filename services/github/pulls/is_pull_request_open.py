from gql import gql
from services.github.graphql_client import get_graphql_client
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=False, raise_on_error=False)
def is_pull_request_open(owner: str, repo: str, pull_number: int, token: str) -> bool:
    """Check if a pull request is still open using GraphQL"""
    client = get_graphql_client(token=token)
    query = gql(
        """
        query($owner: String!, $repo: String!, $pullNumber: Int!) {
            repository(owner: $owner, name: $repo) {
                pullRequest(number: $pullNumber) {
                    state
                }
            }
        }
        """
    )

    result = client.execute(
        query,
        variable_values={"owner": owner, "repo": repo, "pullNumber": pull_number},
    )

    pr_state = result.get("repository", {}).get("pullRequest", {}).get("state")
    return pr_state == "OPEN"
