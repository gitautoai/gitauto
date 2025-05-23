from typing import TypedDict


class Contents(TypedDict):
    """GitHub repository contents type
    
    See: https://docs.github.com/en/rest/repos/contents?apiVersion=2022-11-28
    
    Example values:
    - type: "file"
    - encoding: "base64"
    - size: 5362
    - name: "README.md"
    - path: "README.md"
    - content: "encoded content here"
    - sha: "3d21ec53a331a6f037a91c368710b99387d012c1"
    - url: "https://api.github.com/repos/octokit/octokit.rb/contents/README.md"
    - git_url: "https://api.github.com/repos/octokit/octokit.rb/git/blobs/3d21ec53a331a6f037a91c368710b99387d012c1"
    - html_url: "https://github.com/octokit/octokit.rb/blob/master/README.md"
    - download_url: "https://raw.githubusercontent.com/octokit/octokit.rb/master/README.md"
    """
    type: str
    encoding: str
    size: int
    name: str
    path: str
    content: str
    sha: str
    url: str
    git_url: str
    html_url: str
    download_url: str
    _links: dict[str, str]