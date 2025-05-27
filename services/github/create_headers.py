from config import GITHUB_APP_NAME


def create_headers(token: str, media_type: str = ".v3") -> dict[str, str]:
    """https://docs.github.com/en/rest/using-the-rest-api/getting-started-with-the-rest-api?apiVersion=2022-11-28#headers"""
    return {
        "Accept": f"application/vnd.github{media_type}+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": GITHUB_APP_NAME,
    }
