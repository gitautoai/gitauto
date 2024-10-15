import os
import requests
from dotenv import load_dotenv

load_dotenv()

PRODUCT_ID_STRING = "PRODUCT_ID"
GH_TEST_REPO_URL_STRING = "GH_TEST_REPO_URL"
GH_PERSONAL_ACCESS_TOKEN_STRING = "GH_PERSONAL_ACCESS_TOKEN"

def create_github_issue(title, body, labels=None):
    # GitHub API endpoint for creating an issue
    if (test_repo_base_url := os.environ.get(GH_TEST_REPO_URL_STRING)) is None:
        raise ValueError(f"{GH_TEST_REPO_URL_STRING} environment variable not set.")
    url = f"{test_repo_base_url}/issues"

    # Your GitHub personal access token

    if (token := os.environ.get(GH_PERSONAL_ACCESS_TOKEN_STRING)) is None:
        raise ValueError(f"{GH_PERSONAL_ACCESS_TOKEN_STRING} environment variable not set.")

    # Headers for authentication and specifying API version
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Data for the new issue
    data = {
        "title": title,
        "body": body,
        "labels": labels or []
    }

    # Send POST request to create the issue
    response = requests.post(url, json=data, headers=headers)

    # Check if the request was successful
    if response.status_code == 201:
        print("Issue created successfully!")
        return response.json()
    else:
        print(f"Failed to create issue. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return None

# Example usage
if __name__ == "__main__":
    issue_title = "Test Issue"
    issue_body = "This is a test issue created programmatically."
    PRODUCT_ID = os.environ.get(PRODUCT_ID_STRING)
    if not PRODUCT_ID:
        raise ValueError(f"{PRODUCT_ID_STRING} environment variable not set.")
    issue_labels = ["bug", "enhancement", PRODUCT_ID]

    created_issue = create_github_issue(issue_title, issue_body, issue_labels)
    if created_issue:
        print(f"Issue URL: {created_issue['html_url']}")
