from gql import gql
from services.github.graphql_client import get_graphql_client
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_review_thread_comments(
    owner: str, repo: str, pull_number: int, comment_node_id: str, token: str
):
    """Get all comments in a review thread using GraphQL API
    https://docs.github.com/en/graphql/reference/objects#pullrequestreviewcomment
    """
    client = get_graphql_client(token)
    query = gql(
        """
        query GetReviewThreadComments($owner: String!, $repo: String!, $pull_number: Int!) {
          repository(owner: $owner, name: $repo) {
            pullRequest(number: $pull_number) {
              reviewThreads(first: 100) {
                nodes {
                  comments(first: 100) {
                    nodes {
                      id
                      author { login }
                      body
                      createdAt
                    }
                  }
                }
              }
            }
          }
        }
    """
    )

    variables = {
        "owner": owner,
        "repo": repo,
        "pull_number": pull_number,
    }

    result = client.execute(document=query, variable_values=variables)
    if not isinstance(result, dict):
        return []
    repository = result.get("repository") or {}
    pull_request = repository.get("pullRequest") or {}
    review_threads = pull_request.get("reviewThreads") or {}
    threads = review_threads.get("nodes", [])

    # Find the thread containing our comment
    for thread in threads:
        if not isinstance(thread, dict):
            continue
        thread_comments = thread.get("comments") or {}
        comments = thread_comments.get("nodes", [])
        for comment in comments:
            if isinstance(comment, dict) and comment.get("id") == comment_node_id:
                # print(f"get_review_thread_comments: {dumps(obj=comments, indent=2)}")
                return comments

    return []