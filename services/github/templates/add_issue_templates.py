# Standard imports
from uuid import uuid4

# Third-party imports
from github import Auth, Github
from github.ContentFile import ContentFile
from github.PullRequest import PullRequest
from github.Repository import Repository

# Local imports
from config import (
    GITHUB_ISSUE_DIR,
    GITHUB_ISSUE_TEMPLATES,
    PRODUCT_NAME,
    PRODUCT_ID,
)

# Local imports (GitHub)
from services.github.commits.get_latest_remote_commit_sha import (
    get_latest_remote_commit_sha,
)

# Local imports (Utils)
from utils.error.handle_exceptions import handle_exceptions
from utils.files.get_file_content import get_file_content


@handle_exceptions(default_return_value=None, raise_on_error=False)
def add_issue_templates(full_name: str, installer_name: str, token: str) -> None:
    print(f"Adding issue templates to the repo: '{full_name}' by '{installer_name}'.\n")
    auth = Auth.Token(token)
    gh = Github(auth=auth)
    repo: Repository = gh.get_repo(full_name_or_id=full_name)
    owner, repo_name = full_name.split("/")
    default_branch_name = repo.default_branch

    # Get latest commit SHA directly
    base_args = {
        "owner": owner,
        "repo": repo_name,
        "base_branch": default_branch_name,
        "token": token,
    }
    clone_url = repo.clone_url
    latest_sha = get_latest_remote_commit_sha(clone_url=clone_url, base_args=base_args)  # type: ignore

    # Create a new branch using the SHA
    new_branch_name: str = f"{PRODUCT_ID}/add-issue-templates-{str(object=uuid4())}"
    ref = f"refs/heads/{new_branch_name}"
    repo.create_git_ref(ref=ref, sha=latest_sha)

    # Add issue templates to the new branch
    added_templates: list[str] = []
    for template_file in GITHUB_ISSUE_TEMPLATES:
        # Get an issue template content from GitAuto repository
        template_path: str = GITHUB_ISSUE_DIR + "/" + template_file
        content = get_file_content(file_path=template_path)

        # Get the list of existing files in the user's remote repository at the GITHUB_ISSUE_DIR. We need to use try except as repo.get_contents() raises a 404 error if the directory doesn't exist. Also directory path MUST end without a slash.
        try:
            remote_files_result = repo.get_contents(path=GITHUB_ISSUE_DIR)
            remote_files: list[ContentFile] = remote_files_result if isinstance(remote_files_result, list) else [remote_files_result]
            remote_file_names: list[str] = [file.name for file in remote_files]
        except Exception:  # pylint: disable=broad-except
            remote_file_names = []

        # Skip if the template already exists
        if template_file in remote_file_names:
            continue

        # Add file to the new branch
        msg = f"Add a template: {template_file}"
        repo.create_file(
            path=template_path, message=msg, content=content, branch=new_branch_name
        )
        added_templates.append(template_file)

    # Return early if no templates were added
    if not added_templates:
        return

    # If there are added templates, create a PR
    pr: PullRequest = repo.create_pull(
        base=default_branch_name,
        head=new_branch_name,
        # Add X issue templates: bug_report.yml, feature_request.yml
        title=f"Add {len(added_templates)} issue templates",
        body=f"## Overview\n\nThis PR adds issue templates to the repository so that you can create issues more easily for {PRODUCT_NAME} and your project. Please review the changes and merge the PR if you agree.\n\n## Added templates:\n\n- "
        + "\n- ".join(added_templates),
        maintainer_can_modify=True,
        draft=False,
    )

    # Add reviewers to the PR. When I tried to add reviewers, I got a 422 error. So, "reviewers" parameter must be an array of strings, not a string.
    pr.create_review_request(reviewers=[installer_name])
