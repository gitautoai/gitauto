import requests

from config import TIMEOUT
from services.codecov.codecov_types import CodecovCommitResponse, CodecovFileResult
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_codecov_commit_coverage(
    owner: str, repo: str, commit_sha: str, codecov_token: str, service: str = "github"
):
    # https://docs.codecov.com/reference/repos_report_retrieve
    url = f"https://api.codecov.io/api/v2/{service}/{owner}/repos/{repo}/commits/{commit_sha}/"
    headers = {"Authorization": f"Bearer {codecov_token}", "Accept": "application/json"}

    response = requests.get(url, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
    data: CodecovCommitResponse = response.json()

    # Extract and format file-level coverage with uncovered lines
    files = data["files"]
    processed_files: list[CodecovFileResult] = []
    for file in files:
        file_name = file["name"]
        totals = file["totals"]
        coverage = totals["coverage"]

        # Extract uncovered and partially covered lines (hit=0/miss=1/partial=2)
        line_coverage = file["line_coverage"]
        uncovered_lines = [
            i + 1 for i, status in enumerate(line_coverage) if status == 1
        ]
        partially_covered_lines = [
            i + 1 for i, status in enumerate(line_coverage) if status == 2
        ]

        processed_files.append(
            {
                "name": file_name,
                "coverage": coverage,
                "uncovered_lines": uncovered_lines,
                "partially_covered_lines": partially_covered_lines,
            }
        )

    return processed_files
