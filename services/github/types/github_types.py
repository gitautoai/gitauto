# Standard imports
from typing import Optional, TypedDict, Union
from typing_extensions import NotRequired

# Local imports
from services.github.types.check_run import CheckRun
from services.github.types.check_suite import CheckSuite
from services.github.types.installation import Installation
from services.github.types.installation_details import InstallationDetails
from services.github.types.label import Label
from services.github.types.organization import Organization
from services.github.types.owner import OwnerType
from services.github.types.pull_request import PullRequest
from services.github.types.repository import Repository, RepositoryAddedOrRemoved
from services.github.types.sender import Sender
from services.github.types.user import User


class BaseArgs(TypedDict):
    # Required fields
    owner_type: OwnerType
    owner_id: int
    owner: str
    repo_id: int
    repo: str
    clone_url: str
    is_fork: bool
    base_branch: str
    new_branch: str
    installation_id: int
    token: str
    sender_id: int
    sender_name: str
    sender_email: str | None
    sender_display_name: str
    reviewers: list[str]
    github_urls: list[str]
    other_urls: list[str]
    clone_dir: str
    pr_number: int
    pr_title: str
    pr_body: str
    pr_comments: list[str]
    pr_creator: str

    # Optional fields
    check_run_name: NotRequired[str]
    comment_url: NotRequired[str | None]
    latest_commit_sha: NotRequired[str]
    workflow_id: NotRequired[str | int]
    baseline_tsc_errors: NotRequired[set[str]]
    impl_file_to_collect_coverage_from: NotRequired[str]
    review_id: NotRequired[int]
    skip_ci: NotRequired[bool]


class ReviewBaseArgs(BaseArgs):
    pr_url: str
    pr_file_url: str
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


class InstallationPayload(TypedDict):
    action: str
    installation: InstallationDetails
    repositories: list[RepositoryAddedOrRemoved]
    requester: Optional[User]
    sender: User


class InstallationRepositoriesPayload(TypedDict):
    action: str
    installation: InstallationDetails
    repository_selection: str
    repositories_added: list[RepositoryAddedOrRemoved]
    repositories_removed: list[RepositoryAddedOrRemoved]
    requester: Optional[User]
    sender: User


# Payload for pull_request.labeled webhook event
class PrLabeledPayload(TypedDict, total=True):
    action: str
    number: int
    pull_request: PullRequest
    label: Label
    repository: Repository
    organization: Organization
    sender: User
    installation: Installation


class PrClosedPayload(TypedDict, total=True):
    action: str
    number: int
    pull_request: PullRequest
    repository: Repository
    organization: Organization
    sender: User
    installation: Installation


EventPayload = Union[InstallationPayload, PrLabeledPayload, PrClosedPayload]
