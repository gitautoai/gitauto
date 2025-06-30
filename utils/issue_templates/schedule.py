def get_issue_title(file_path: str):
    return f"Schedule: Add unit tests to {file_path}"


def get_issue_body(file_path: str, statement_coverage: float | None = None):
    if statement_coverage is None:
        return ""

    return f"Add unit tests for {file_path} (Coverage: {statement_coverage}%)."
