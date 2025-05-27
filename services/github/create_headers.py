from config import GITHUB_APP_NAME


def create_headers(additional_headers=None):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "GitAuto-Agent",
    }
    if additional_headers:
        headers.update(additional_headers)
    return headers
