# Third party imports
import json
import subprocess
from typing import cast

# Local imports
from utils.error.handle_exceptions import handle_exceptions


DEFAULT_REPO_STATS = {
    "file_count": 0,
    "blank_lines": 0,
    "comment_lines": 0,
    "code_lines": 0,
}


@handle_exceptions(default_return_value=DEFAULT_REPO_STATS, raise_on_error=False)
def get_repository_stats(local_path: str):
    cloc_result = subprocess.run(
        ["cloc", local_path, "--json"], check=True, capture_output=True, text=True
    )

    # Extract only the JSON part from stdout
    json_str = cloc_result.stdout

    # Find the first '{' and last '}' to extract valid JSON since sometimes stdout includes other text after the JSON
    start = json_str.find("{")
    end = json_str.rfind("}") + 1
    if 0 <= start < end:
        json_str = json_str[start:end]

    cloc_data = json.loads(json_str)

    # Extract statistics
    file_count = cast(int, cloc_data.get("header", {}).get("n_files", 0))
    blank_lines = cast(int, cloc_data.get("SUM", {}).get("blank", 0))
    comment_lines = cast(int, cloc_data.get("SUM", {}).get("comment", 0))
    code_lines = cast(int, cloc_data.get("SUM", {}).get("code", 0))

    return {
        "file_count": file_count,
        "blank_lines": blank_lines,
        "comment_lines": comment_lines,
        "code_lines": code_lines,
    }
