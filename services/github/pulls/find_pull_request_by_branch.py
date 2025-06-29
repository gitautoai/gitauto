from gql import gql
from services.github.graphql_client import get_graphql_client
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def find_pull_request_by_branch(
    owner: str, repo: str, branch_name: str, token: str
) -> dict | None:
    """https://docs.github.com/en/graphql/reference/objects#pullrequest"""
    client = get_graphql_client(token=token)
    query = gql(
        """
        query($owner: String!, $repo: String!, $headRefName: String!) {
            repository(owner: $owner, name: $repo) {
                pullRequests(first: 1, headRefName: $headRefName, states: OPEN) {
                    nodes {
                        number
                        title
                        url  # API URL
                        headRef { name }  # Source branch (e.g. "wes")
                        baseRef { name }  # Target branch (e.g. "main")
                    }
                }
            }
        }
    """
    )

    result = client.execute(
        query,
        variable_values={"owner": owner, "repo": repo, "headRefName": branch_name},
    )

    pulls = result.get("repository", {}).get("pullRequests", {}).get("nodes", [])
    return pulls[0] if pulls else None
