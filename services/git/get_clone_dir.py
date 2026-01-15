def get_clone_dir(owner: str, repo: str, pr_number: int | None):
    """Calculate clone directory path without actually cloning."""
    if pr_number:
        return f"/tmp/{owner}/{repo}/pr-{pr_number}"
    return f"/tmp/{owner}/{repo}"
