from typing import Literal, Optional, TypedDict, Union


from services.github.types.check_run import CheckRun
from services.github.types.installation import Installation
from services.github.types.installation_details import InstallationDetails
from services.github.types.issue import Issue
from services.github.types.label import Label
from services.github.types.organization import Organization
from services.github.types.repository import Repository
from services.github.types.sender import Sender
from services.github.types.user import User


class BaseArgs(TypedDict):
    input_from: Literal["github", "jira"]
    owner_type: Literal["user", "organization"]
    owner_id: int
    owner: str
    repo_id: int
    repo: str
    clone_url: str
    is_fork: bool
    issue_number: int
    issue_title: str
    issue_body: str
    issue_comments: list[str]
    latest_commit_sha: str
    comment_url: str | None
    issuer_name: str
    base_branch: str
    new_branch: str
    installation_id: int
    token: str
    sender_id: int
    sender_name: str
    sender_email: str
    is_automation: bool
    reviewers: list[str]
    github_urls: list[str]
    other_urls: list[str]
    pr_body: str


class CheckRunCompletedPayload(TypedDict):
    action: str
    check_run: CheckRun
    repository: Repository
    sender: Sender
    installation: Installation


class GitHubInstallationPayload(TypedDict):
    action: str
    installation: InstallationDetails
    repositories: list[Repository]
    repository_selection: str
    repositories_added: list[Repository]
    repositories_removed: list[Repository]
    requester: Optional[User]
    sender: User


class GitHubLabeledPayload(TypedDict):
    action: str
    issue: Issue
    label: Label
    repository: Repository
    organization: Organization
    sender: User
    installation: Installation


class GitHubContentInfo(TypedDict):
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


class GitHubPullRequestInfo(TypedDict):
    url: str
    id: int
    node_id: str
    html_url: str
    diff_url: str
    patch_url: str
    issue_url: str
    number: int
    state: str
    locked: bool
    title: str
    user: User
    body: str
    created_at: str
    updated_at: str
    closed_at: Optional[str]
    merged_at: Optional[str]
    merge_commit_sha: Optional[str]
    assignee: Optional[User]
    assignees: list[User]
    requested_reviewers: list[User]
    requested_teams: list[dict]
    labels: list[Label]
    milestone: Optional[dict]
    draft: bool
    commits_url: str
    review_comments_url: str
    review_comment_url: str
    comments_url: str
    statuses_url: str
    head: dict
    base: dict
    _links: dict
    author_association: str
    auto_merge: Optional[dict]
    active_lock_reason: Optional[str]
    merged: bool
    mergeable: Optional[bool]
    rebaseable: Optional[bool]
    mergeable_state: str
    merged_by: Optional[User]
    comments: int
    review_comments: int
    maintainer_can_modify: bool
    commits: int
    additions: int
    deletions: int
    changed_files: int


class GitHubPullRequestClosedPayload(TypedDict):
    action: str
    number: int
    pull_request: GitHubPullRequestInfo
    repository: Repository
    organization: Organization
    sender: User
    installation: Installation


GitHubEventPayload = Union[
    GitHubInstallationPayload, GitHubLabeledPayload, GitHubPullRequestClosedPayload
]
