# Standard imports
from typing import Literal, Optional, TypedDict, Union
from typing_extensions import NotRequired

# Local imports
from services.github.types.check_run import CheckRun
from services.github.types.check_suite import CheckSuite
from services.github.types.installation import Installation
from services.github.types.installation_details import InstallationDetails
from services.github.types.issue import Issue
from services.github.types.label import Label
from services.github.types.organization import Organization
from services.github.types.owner import OwnerType
from services.github.types.pull_request import PullRequest
from services.github.types.repository import Repository
from services.github.types.sender import Sender
from services.github.types.user import User


class BaseArgs(TypedDict):
    # Required fields - set by both deconstruct functions
    input_from: Literal["github", "jira"]
    owner_type: OwnerType
    owner_id: int
    owner: str
    repo_id: int
    repo: str
    clone_url: str
    is_fork: bool
    issue_number: int
    issue_title: str
    issue_body: str
    issue_comments: NotRequired[list[str]]
    latest_commit_sha: NotRequired[str]
    issuer_name: str
    base_branch: str
    new_branch: str
    installation_id: int
    token: str
    sender_id: int
    sender_name: str
    sender_email: str | None
    is_automation: bool
    reviewers: list[str]
    github_urls: list[str]
    other_urls: list[str]

    # Optional fields
    check_run_name: NotRequired[str]
    comment_url: NotRequired[str | None]
    issuer_email: NotRequired[str]
    pull_number: NotRequired[int]
    workflow_id: NotRequired[str | int]
    parent_issue_body: NotRequired[str | None]
    parent_issue_number: NotRequired[int | None]
    parent_issue_title: NotRequired[str | None]
    pr_body: NotRequired[str]
    pr_number: NotRequired[int]
    review_id: NotRequired[int]
    skip_ci: NotRequired[bool]


class ReviewBaseArgs(BaseArgs):
    pull_title: str
    pull_body: str
    pull_url: str
    pull_file_url: str
    review_path: str
    review_subject_type: str
    review_line: int
    review_side: str
    review_body: str
    review_comment: str


class CheckRunCompletedPayload(TypedDict):
    action: str
    check_run: CheckRun
    repository: Repository
    sender: Sender
    installation: Installation


class CheckSuiteCompletedPayload(TypedDict):
    action: str
    check_suite: CheckSuite
    repository: Repository
    sender: Sender
    installation: Installation


class GitHubInstallationPayload(TypedDict):
    action: str
    installation: InstallationDetails
    repositories: list[Repository]
    requester: Optional[User]
    sender: User


class GitHubInstallationRepositoriesPayload(TypedDict):
    action: str
    installation: InstallationDetails
    repository_selection: str
    repositories_added: list[Repository]
    repositories_removed: list[Repository]
    requester: Optional[User]
    sender: User


class GitHubLabeledPayload(TypedDict, total=True):
    action: str
    issue: Issue
    label: Label
    repository: Repository
    organization: Organization
    sender: User
    installation: Installation


class GitHubPullRequestClosedPayload(TypedDict, total=True):
    action: str
    number: int
    pull_request: PullRequest
    repository: Repository
    organization: Organization
    sender: User
    installation: Installation


GitHubEventPayload = Union[
    GitHubInstallationPayload, GitHubLabeledPayload, GitHubPullRequestClosedPayload
]
