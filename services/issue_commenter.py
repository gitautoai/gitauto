import requests

def comment_on_issue(issue_url, comment_body, token):
    """Posts a comment on a GitHub issue."""
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
    }
    data = {
        'body': comment_body
    }
    response = requests.post(issue_url, headers=headers, json=data)
    if response.status_code == 201:
        print('Comment posted successfully.')
    else:
        print(f'Failed to post comment: {response.content}')
