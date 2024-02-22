from typing import TypedDict, Dict, List, Optional


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
