from re import findall, match
from utils.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=[], raise_on_error=False)
def extract_image_urls(text: str) -> list[str]:
    """Extract URLs from img tags in the given text.

    Example 1: ['https://github.com/user-attachments/assets/123']
    """
    pattern = r'<img[^>]*src="([^"]*)"[^>]*>'
    urls: list[str] = findall(pattern, text)
    return urls


def extract_urls(text: str) -> tuple[list[str], list[str]]:
    """
    ?: Matches 0 or 1 occurrence of the preceding expression.
    +: Matches 1 or more occurrences of the preceding expression.
    ^: Matches the start of the string. In [^abc], it negates the enclosed characters.
    []: Matches any one of the enclosed characters.
    (): Groups regular expressions and remembers matched text.
    s: Matches any whitespace character.

    GitHub URL Ex1: https://github.com/{owner}/{repo}/blob/{branch}/{file_path}
    GitHub URL Ex2: https://github.com/{owner}/{repo}/blob/{sha}/{file_path}
    """
    github_pattern = (
        r"https://github\.com/"
        r"[A-Za-z0-9_-]+/"  # owner
        r"[A-Za-z0-9_-]+/"  # repo
        r"blob/"  # blob, which is a fixed string
        r"([A-Za-z0-9_-]+|[a-f0-9]+)/"  # branch name or sha (commit hash)
        r"(?:[^\s#)]+)"  # file path, any character except whitespace and #
        r"(?:#L\d+(?:-L\d+)?)?$"  # optional line number(s), e.g., #L10 or #L10-L20
    )
    all_url_pattern = r"https?://[^\s)]+"

    all_urls: list[str] = findall(all_url_pattern, text)
    github_urls: list[str] = [url for url in all_urls if match(github_pattern, url)]
    other_urls: list[str] = [url for url in all_urls if url not in github_urls]

    return github_urls, other_urls
