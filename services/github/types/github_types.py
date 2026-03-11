# Standard imports
from typing import Optional, TypedDict, Union

# Local imports
from services.github.types.check_run import CheckRun
from services.github.types.check_suite import CheckSuite
from services.github.types.installation import Installation
from services.github.types.installation_details import InstallationDetails
from services.github.types.label import Label
from services.github.types.organization import Organization
from services.github.types.pull_request import PullRequest
from services.github.types.repository import Repository, RepositoryAddedOrRemoved
from services.github.types.sender import Sender
from services.github.types.user import User


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
