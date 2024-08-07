import re


def extract_urls(text) -> tuple[list[str], list[str]]:
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
        r"https://github\.com/[A-Za-z0-9_-]+/[A-Za-z0-9_-]+/blob/"
        r"([A-Za-z0-9_-]+|[a-f0-9]+)/(?:[^\s#]+)(?:#L\d+(?:-L\d+)?)?"
    )
    all_url_pattern = r"https?://[^\s]+"

    all_urls = re.findall(all_url_pattern, text)
    github_urls = [url for url in all_urls if re.match(github_pattern, url)]
    other_urls = [url for url in all_urls if url not in github_urls]

    return github_urls, other_urls
