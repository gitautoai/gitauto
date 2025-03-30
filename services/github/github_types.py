from dataclasses import dataclass
from typing import Literal, TypedDict, Dict, List, Optional, Union
import datetime


class BaseArgs(TypedDict):
    input_from: Literal["github", "jira"]
    owner_type: Literal["user", "organization"]
    owner_id: int
    owner: str
    repo: str
    clone_url: str
    is_fork: bool
    issue_number: int
    issue_title: str
    issue_body: str
    issue_comments: List[str]
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
    reviewers: List[str]
    github_urls: List[str]
    other_urls: List[str]
    pr_body: str


@dataclass
class Owner:
    login: str
    id: int
    node_id: str
    avatar_url: str
    gravatar_id: str
    url: str
    html_url: str
    followers_url: str
    following_url: str
    gists_url: str
    starred_url: str
    subscriptions_url: str
    organizations_url: str
    repos_url: str
    events_url: str
    received_events_url: str
    type: str
    user_view_type: str
    site_admin: bool


@dataclass
class App:
    id: int
    client_id: str
    slug: str
    node_id: str
    owner: Owner
    name: str
    description: str
    external_url: str
    html_url: str
    created_at: datetime
    updated_at: datetime
    permissions: dict
    events: List[str]


@dataclass
class PullRequest:
    url: str
    id: int
    number: int
    head: dict
    base: dict


@dataclass
class CheckSuite:
    id: int
    node_id: str
    head_branch: str
    head_sha: str
    status: str
    conclusion: Optional[str]
    url: str
    before: str
    after: str
    pull_requests: List[PullRequest]
    app: App
    created_at: datetime
    updated_at: datetime


@dataclass
class Output:
    title: Optional[str]
    summary: Optional[str]
    text: Optional[str]
    annotations_count: int
    annotations_url: str


@dataclass
class CheckRun:
    id: int
    name: str
    node_id: str
    head_sha: str
    external_id: str
    url: str
    html_url: str
    details_url: str
    status: str
    conclusion: str
    started_at: datetime
    completed_at: datetime
    output: Output
    check_suite: CheckSuite
    app: App
    pull_requests: List[PullRequest]


@dataclass
class Repository:
    id: int
    node_id: str
    name: str
    full_name: str
    private: bool
    owner: Owner
    html_url: str
    description: str
    fork: bool
    url: str
    created_at: datetime
    updated_at: datetime
    pushed_at: datetime
    git_url: str
    ssh_url: str
    clone_url: str
    svn_url: str
    homepage: str
    size: int
    stargazers_count: int
    watchers_count: int
    language: Optional[str]
    has_issues: bool
    has_projects: bool
    has_downloads: bool
    has_wiki: bool
    has_pages: bool
    has_discussions: bool
    forks_count: int
    mirror_url: Optional[str]
    archived: bool
    disabled: bool
    open_issues_count: int
    license: dict
    allow_forking: bool
    is_template: bool
    web_commit_signoff_required: bool
    topics: List[str]
    visibility: str
    forks: int
    open_issues: int
    watchers: int
    default_branch: str


@dataclass
class Sender:
    login: str
    id: int
    node_id: str
    avatar_url: str
    gravatar_id: str
    url: str
    html_url: str
    followers_url: str
    following_url: str
    gists_url: str
    starred_url: str
    subscriptions_url: str
    organizations_url: str
    repos_url: str
    events_url: str
    received_events_url: str
    type: str
    user_view_type: str
    site_admin: bool


@dataclass
class Installation:
    id: int
    node_id: str


@dataclass
class CheckRunCompletedPayload:
    action: str
    check_run: CheckRun
    repository: Repository
    sender: Sender
    installation: Installation


class LabelInfo(TypedDict):
    id: int
    node_id: str
    url: str
    name: str
    color: str
    default: bool
    description: Optional[str]


class UserInfo(TypedDict):
    login: str
    id: int
    node_id: str
    avatar_url: str
    gravatar_id: str
    url: str
    html_url: str
    followers_url: str
    following_url: str
    gists_url: str
    starred_url: str
    subscriptions_url: str
    organizations_url: str
    repos_url: str
    events_url: str
    received_events_url: str
    type: str
    site_admin: bool


class IssueInfo(TypedDict):
    url: str
    repository_url: str
    labels_url: str
    comments_url: str
    events_url: str
    html_url: str
    id: int
    node_id: str
    number: int
    title: str
    user: UserInfo
    labels: List[LabelInfo]
    state: str
    locked: bool
    assignee: Optional[UserInfo]
    assignees: List[UserInfo]
    milestone: Optional[str]
    comments: int
    created_at: str
    updated_at: str
    closed_at: Optional[str]
    author_association: str
    active_lock_reason: Optional[str]
    body: Optional[str]
    reactions: Dict[str, int]
    timeline_url: str
    performed_via_github_app: Optional[str]
    state_reason: Optional[str]


class OrganizationInfo(TypedDict):
    login: str
    id: int
    node_id: str
    url: str
    repos_url: str
    events_url: str
    hooks_url: str
    issues_url: str
    members_url: str
    public_members_url: str
    avatar_url: str
    description: Optional[str]


class RepositoryInfo(TypedDict):
    id: int
    node_id: str
    name: str
    full_name: str
    private: bool
    owner: UserInfo
    html_url: str
    description: Optional[str]
    fork: bool
    url: str
    forks_url: str
    keys_url: str
    collaborators_url: str
    teams_url: str
    hooks_url: str
    issue_events_url: str
    events_url: str
    assignees_url: str
    branches_url: str
    tags_url: str
    blobs_url: str
    git_tags_url: str
    git_refs_url: str
    trees_url: str
    statuses_url: str
    languages_url: str
    stargazers_url: str
    contributors_url: str
    subscribers_url: str
    subscription_url: str
    commits_url: str
    git_commits_url: str
    comments_url: str
    issue_comment_url: str
    contents_url: str
    compare_url: str
    merges_url: str
    archive_url: str
    downloads_url: str
    issues_url: str
    pulls_url: str
    milestones_url: str
    notifications_url: str
    labels_url: str
    releases_url: str
    deployments_url: str
    created_at: str
    updated_at: str
    pushed_at: str
    git_url: str
    ssh_url: str
    clone_url: str
    svn_url: str
    homepage: Optional[str]
    size: int
    stargazers_count: int
    watchers_count: int
    language: Optional[str]
    has_issues: bool
    has_projects: bool
    has_downloads: bool
    has_wiki: bool
    has_pages: bool
    forks_count: int
    mirror_url: Optional[str]
    archived: bool
    disabled: bool
    open_issues_count: int
    license: Optional[str]
    allow_forking: bool
    is_template: bool
    web_commit_signoff_required: bool
    topics: List[str]
    visibility: str
    forks: int
    open_issues: int
    watchers: int
    default_branch: str
    custom_properties: Dict[str, str]


class PermissionsInfo(TypedDict):
    actions: str
    contents: str
    metadata: str
    workflows: str
    repository_hooks: str


class InstallationMiniInfo(TypedDict):
    id: int
    node_id: str


class InstallationInfo(TypedDict):
    id: int
    account: UserInfo
    repository_selection: str
    access_tokens_url: str
    repositories_url: str
    html_url: str
    app_id: int
    app_slug: str
    target_id: int
    target_type: str
    permissions: PermissionsInfo
    events: List[str]
    created_at: str
    updated_at: str
    single_file_name: Optional[str]
    has_multiple_single_files: bool
    single_file_paths: List[str]
    suspended_by: Optional[str]
    suspended_at: Optional[str]


class GitHubInstallationPayload(TypedDict):
    action: str
    installation: InstallationInfo
    repositories: List[RepositoryInfo]
    repository_selection: str
    repositories_added: List[RepositoryInfo]
    repositories_removed: List[RepositoryInfo]
    requester: Optional[UserInfo]
    sender: UserInfo


class GitHubLabeledPayload(TypedDict):
    action: str
    issue: IssueInfo
    label: LabelInfo
    repository: RepositoryInfo
    organization: OrganizationInfo
    sender: UserInfo
    installation: InstallationMiniInfo


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
    _links: Dict[str, str]


GitHubEventPayload = Union[GitHubInstallationPayload, GitHubLabeledPayload]


class Artifact(TypedDict):
    id: int  # ex) 2846035038
    node_id: str  # ex) "MDg6QXJ0aWZhY3QyODQ2MDM1MDM4"
    name: str  # ex) "coverage-report"
    size_in_bytes: int  # ex) 7446
    url: str  # ex) "https://api.github.com/repos/gitautoai/sample-flutter-getwidget/actions/artifacts/2846035038"
    archive_download_url: str  # ex) "https://api.github.com/repos/gitautoai/sample-flutter-getwidget/actions/artifacts/2846035038/zip"
    expired: bool  # ex) False
    created_at: str  # ex) "2025-03-29T00:00:00Z"
    updated_at: str  # ex) "2025-03-29T00:00:00Z"
    expires_at: str  # ex) "2025-04-28T00:00:00Z"
