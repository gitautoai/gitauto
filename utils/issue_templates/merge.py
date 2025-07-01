def get_issue_title_for_pr_merged(pr_number: int):
    return f"Add unit tests for files changed in PR #{pr_number}"


def get_issue_body_for_pr_merged(pr_number: int, file_list: list[str]):
    files = "\n".join(f"- {file}" for file in file_list)
    return f"Add unit tests for files changed in PR #{pr_number}:\n{files}"
