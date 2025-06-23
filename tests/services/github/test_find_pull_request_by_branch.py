from services.github.pull_requests.find_pull_request_by_branch import find_pull_request_by_branch


class DummyGraphqlClient:
    def execute(self, query, variable_values):
        # If headRefName is 'exists', return a pull request; otherwise return empty
        if variable_values.get("headRefName") == "exists":
            return {
                "repository": {
                    "pullRequests": {
                        "nodes": [{
                            "number": 1,
                            "title": "Test PR",
                            "url": "http://example.com/pr/1",
                            "htmlUrl": "http://example.com/pr/1/html",
                            "headRef": {"name": "exists"},
                            "baseRef": {"name": "main"}
                        }]
                    }
                }
            }
        else:
            return {"repository": {"pullRequests": {"nodes": []}}}


def test_find_pull_request_found(monkeypatch):
    # Monkey-patch get_graphql_client to return our dummy client
    monkeypatch.setattr(
        "services.github.pull_requests.find_pull_request_by_branch.get_graphql_client",
        lambda token: DummyGraphqlClient()
    )
    result = find_pull_request_by_branch("dummy_owner", "dummy_repo", "exists", "dummy_token")
    assert result is not None
    assert result["number"] == 1
    assert result["title"] == "Test PR"


def test_find_pull_request_not_found(monkeypatch):
    monkeypatch.setattr(
        "services.github.pull_requests.find_pull_request_by_branch.get_graphql_client",
        lambda token: DummyGraphqlClient()
    )
    result = find_pull_request_by_branch("dummy_owner", "dummy_repo", "nonexistent", "dummy_token")
    assert result is None
