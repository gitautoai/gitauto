import re
from typing import TypedDict


class GitHubURLParts(TypedDict):
    owner: str
    repo: str
    ref: str
    file_path: str
    start_line: int | None
    end_line: int | None


def parse_github_url(url) -> GitHubURLParts:
    parts: list[str] = re.split(r"/blob/|#L", url)
    owner_repo = parts[0].replace("https://github.com/", "").split("/")
    owner = owner_repo[0]
    repo = owner_repo[1]
    ref_path = parts[1].split("/")
    ref = ref_path[0]
    file_path = "/".join(ref_path[1:])
    start = None
    end = None
    if len(parts) > 2:
        lines = parts[2].split("-L")
        start = int(lines[0]) if lines[0] else None
        end = int(lines[1]) if len(lines) > 1 and lines[1] else None
    return {
        "owner": owner,
        "repo": repo,
        "ref": ref,
        "file_path": file_path,
        "start_line": start,
        "end_line": end,
    }
