from typing import TypedDict


class Contents(TypedDict):
    """https://docs.github.com/en/rest/repos/contents?apiVersion=2022-11-28"""

    type: str
    encoding: str
    size: int
    name: str
    path: str
    content: str
    sha: str  # ex) "3d21ec53a331a6f037a91c368710b99387d012c1"
    url: str  # ex) "https://api.github.com/repos/octokit/octokit.rb/contents/README.md"
    git_url: str  # ex) "https://api.github.com/repos/octokit/octokit.rb/git/blobs/3d21ec53a331a6f037a91c368710b99387d012c1" # noqa: E501
    html_url: str  # ex) "https://github.com/octokit/octokit.rb/blob/master/README.md"
    download_url: str  # ex) "https://raw.githubusercontent.com/octokit/octokit.rb/master/README.md"
    _links: dict[str, str]
