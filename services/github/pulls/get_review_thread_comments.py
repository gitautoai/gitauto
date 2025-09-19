from gql import gql
from services.github.graphql_client import get_graphql_client
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=[], raise_on_error=False)
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
    repository = result.get("repository")
    if not isinstance(repository, dict):
        return []
    pull_request = repository.get("pullRequest")
    if not isinstance(pull_request, dict):
        return []
    review_threads = pull_request.get("reviewThreads")
    if not isinstance(review_threads, dict):
        return []
    threads = review_threads.get("nodes", [])
    if not isinstance(threads, list):
        return []

    # Find the thread containing our comment
    for thread in threads:
        if not isinstance(thread, dict):
            continue
        thread_comments = thread.get("comments")
        if not isinstance(thread_comments, dict):
            continue
        comments = thread_comments.get("nodes", [])
        if not isinstance(comments, list):
            continue
        for comment in comments:
            if isinstance(comment, dict) and comment.get("id") == comment_node_id:
                # print(f"get_review_thread_comments: {dumps(obj=comments, indent=2)}")
                # Filter out non-dict comments and return only valid comment dictionaries
                return [c for c in comments if isinstance(c, dict)]

    return []
