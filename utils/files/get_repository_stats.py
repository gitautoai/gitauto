# Local imports
from utils.files.count_repo_total_files import count_repo_total_files
from utils.files.count_repo_total_lines import count_repo_total_lines


DEFAULT_REPO_STATS = {
    "file_count": 0,
    "code_lines": 0,
}


def get_repository_stats(local_path: str):
    file_count = count_repo_total_files(local_path=local_path)
    code_lines = count_repo_total_lines(local_path=local_path)
    return {
        "file_count": file_count,
        "code_lines": code_lines,
    }
