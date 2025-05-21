import pytest
from config import GITHUB_API_URL
import importlib.util

# Check if responses is installed
responses_spec = importlib.util.find_spec("responses")
if responses_spec is None:
    pytest.skip("responses package is required for this test", allow_module_level=True)
import responses

from services.github.comments.create_comment import create_comment
from services.github.create_headers import create_headers
from tests.constants import OWNER, REPO, TOKEN


@responses.activate
def test_create_comment_integration_success():
    # Arrange
    issue_number = 123
    comment_body = "Test integration comment"
    expected_url = f"{GITHUB_API_URL}/repos/{OWNER}/{REPO}/issues/{issue_number}/comments"
    response_data = {
        "url": f"{GITHUB_API_URL}/repos/{OWNER}/{REPO}/issues/comments/456"
    }
    
    responses.add(
        responses.POST,
        expected_url,
        json=response_data,
        status=201
    )
    
    base_args = {
        "owner": OWNER,
        "repo": REPO,
        "token": TOKEN,
        "issue_number": issue_number,
        "input_from": "github"
    }
    
    # Act
    result = create_comment(comment_body, base_args)
    
    # Assert
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == expected_url
    assert responses.calls[0].request.headers["Authorization"] == f"Bearer {TOKEN}"
    assert result == response_data["url"]
