from dataclasses import dataclass, field

from gql import gql

from services.github.graphql_client import get_graphql_client
from utils.error.handle_exceptions import handle_exceptions


@dataclass
class ReviewThreadResult:
    comments: list[dict] = field(default_factory=list)
    is_resolved: bool = False


@handle_exceptions(default_return_value=ReviewThreadResult(), raise_on_error=False)
def get_review_thread_comments(
    owner: str, repo: str, pr_number: int, comment_node_id: str, token: str
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
                  isResolved
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
        "pull_number": pr_number,
    }

    result = client.execute(document=query, variable_values=variables)
    if not isinstance(result, dict):
        return ReviewThreadResult()
    repository = result.get("repository")
    if not isinstance(repository, dict):
        return ReviewThreadResult()
    pull_request = repository.get("pullRequest")
    if not isinstance(pull_request, dict):
        return ReviewThreadResult()
    review_threads = pull_request.get("reviewThreads")
    if not isinstance(review_threads, dict):
        return ReviewThreadResult()
    threads = review_threads.get("nodes", [])
    if not isinstance(threads, list):
        return ReviewThreadResult()

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
                valid_comments = [c for c in comments if isinstance(c, dict)]
                is_resolved = thread.get("isResolved", False)
                return ReviewThreadResult(
                    comments=valid_comments, is_resolved=bool(is_resolved)
                )

    return ReviewThreadResult()
