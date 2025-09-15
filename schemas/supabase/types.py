import datetime
from typing import Any
from typing_extensions import TypedDict, NotRequired


class CircleciTokens(TypedDict):
    id: str
    owner_id: int
    token: str
    created_by: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    updated_by: str


class CircleciTokensInsert(TypedDict):
    owner_id: NotRequired[int]
    token: NotRequired[str]
    created_by: NotRequired[str]
    updated_by: NotRequired[str]


class Contacts(TypedDict):
    id: int
    user_id: int | None
    user_name: str | None
    first_name: str
    last_name: str
    email: str
    company_url: str
    job_title: str
    team_size: str
    team_size_other: str | None
    job_description: str
    current_coverage: str
    current_coverage_other: str | None
    minimum_coverage: str
    minimum_coverage_other: str | None
    target_coverage: str
    target_coverage_other: str | None
    testing_challenges: str | None
    additional_info: str | None
    created_at: datetime.datetime | None
    updated_at: datetime.datetime | None


class ContactsInsert(TypedDict):
    user_id: NotRequired[int | None]
    user_name: NotRequired[str | None]
    first_name: NotRequired[str]
    last_name: NotRequired[str]
    email: NotRequired[str]
    company_url: NotRequired[str]
    job_title: NotRequired[str]
    team_size: NotRequired[str]
    team_size_other: NotRequired[str | None]
    job_description: NotRequired[str]
    current_coverage: NotRequired[str]
    current_coverage_other: NotRequired[str | None]
    minimum_coverage: NotRequired[str]
    minimum_coverage_other: NotRequired[str | None]
    target_coverage: NotRequired[str]
    target_coverage_other: NotRequired[str | None]
    testing_challenges: NotRequired[str | None]
    additional_info: NotRequired[str | None]


class Coverages(TypedDict):
    id: int
    owner_id: int
    repo_id: int
    language: str | None
    package_name: str | None
    level: str
    full_path: str
    statement_coverage: float | None
    function_coverage: float | None
    branch_coverage: float | None
    path_coverage: float | None
    line_coverage: float | None
    uncovered_lines: str | None
    created_at: datetime.datetime
    created_by: str
    updated_at: datetime.datetime
    updated_by: str
    github_issue_url: str | None
    uncovered_functions: str | None
    uncovered_branches: str | None
    branch_name: str
    file_size: int | None
    is_excluded_from_testing: bool | None


class CoveragesInsert(TypedDict):
    owner_id: NotRequired[int]
    repo_id: NotRequired[int]
    language: NotRequired[str | None]
    package_name: NotRequired[str | None]
    level: NotRequired[str]
    full_path: NotRequired[str]
    statement_coverage: NotRequired[float | None]
    function_coverage: NotRequired[float | None]
    branch_coverage: NotRequired[float | None]
    path_coverage: NotRequired[float | None]
    line_coverage: NotRequired[float | None]
    uncovered_lines: NotRequired[str | None]
    created_by: NotRequired[str]
    updated_by: NotRequired[str]
    github_issue_url: NotRequired[str | None]
    uncovered_functions: NotRequired[str | None]
    uncovered_branches: NotRequired[str | None]
    branch_name: NotRequired[str]
    file_size: NotRequired[int | None]
    is_excluded_from_testing: NotRequired[bool | None]


class Credits(TypedDict):
    id: int
    owner_id: int
    amount_usd: int
    transaction_type: str
    stripe_payment_intent_id: str | None
    usage_id: int | None
    expires_at: datetime.datetime | None
    created_at: datetime.datetime


class CreditsInsert(TypedDict):
    owner_id: NotRequired[int]
    amount_usd: NotRequired[int]
    transaction_type: NotRequired[str]
    stripe_payment_intent_id: NotRequired[str | None]
    usage_id: NotRequired[int | None]
    expires_at: NotRequired[datetime.datetime | None]


class Installations(TypedDict):
    created_at: datetime.datetime
    installation_id: int
    owner_name: str
    uninstalled_at: datetime.datetime | None
    owner_type: str
    owner_id: int
    created_by: str | None
    uninstalled_by: str | None


class InstallationsInsert(TypedDict):
    installation_id: NotRequired[int]
    owner_name: NotRequired[str]
    uninstalled_at: NotRequired[datetime.datetime | None]
    owner_type: NotRequired[str]
    owner_id: NotRequired[int]
    created_by: NotRequired[str | None]
    uninstalled_by: NotRequired[str | None]


class Issues(TypedDict):
    id: int
    created_at: datetime.datetime
    run_id: int | None
    installation_id: int
    merged: bool
    created_by: str | None
    owner_id: int
    owner_type: str
    owner_name: str
    repo_id: int
    repo_name: str
    issue_number: int


class IssuesInsert(TypedDict):
    run_id: NotRequired[int | None]
    installation_id: NotRequired[int]
    merged: NotRequired[bool]
    created_by: NotRequired[str | None]
    owner_id: NotRequired[int]
    owner_type: NotRequired[str]
    owner_name: NotRequired[str]
    repo_id: NotRequired[int]
    repo_name: NotRequired[str]
    issue_number: NotRequired[int]


class JiraGithubLinks(TypedDict):
    id: int
    jira_site_id: str
    jira_site_name: str
    jira_project_id: int
    jira_project_name: str
    github_owner_id: int
    github_owner_name: str
    github_repo_id: int
    github_repo_name: str
    created_at: datetime.datetime | None
    updated_at: datetime.datetime | None
    created_by: int
    updated_by: int | None


class JiraGithubLinksInsert(TypedDict):
    jira_site_id: NotRequired[str]
    jira_site_name: NotRequired[str]
    jira_project_id: NotRequired[int]
    jira_project_name: NotRequired[str]
    github_owner_id: NotRequired[int]
    github_owner_name: NotRequired[str]
    github_repo_id: NotRequired[int]
    github_repo_name: NotRequired[str]
    created_by: NotRequired[int]
    updated_by: NotRequired[int | None]


class OauthTokens(TypedDict):
    id: int
    user_id: int
    service_name: str
    access_token: str
    refresh_token: str | None
    scope: str
    expires_at: datetime.datetime
    created_at: datetime.datetime
    updated_at: datetime.datetime
    created_by: int
    updated_by: int | None


class OauthTokensInsert(TypedDict):
    user_id: NotRequired[int]
    service_name: NotRequired[str]
    access_token: NotRequired[str]
    refresh_token: NotRequired[str | None]
    scope: NotRequired[str]
    expires_at: NotRequired[datetime.datetime]
    created_by: NotRequired[int]
    updated_by: NotRequired[int | None]


class Owners(TypedDict):
    created_at: datetime.datetime
    owner_id: int
    stripe_customer_id: str
    created_by: str | None
    owner_name: str
    org_rules: str
    owner_type: str
    updated_by: str | None
    updated_at: datetime.datetime
    credit_balance_usd: int
    auto_reload_enabled: bool
    auto_reload_threshold_usd: int
    auto_reload_target_usd: int
    max_spending_limit_usd: int | None


class OwnersInsert(TypedDict):
    owner_id: NotRequired[int]
    stripe_customer_id: NotRequired[str]
    created_by: NotRequired[str | None]
    owner_name: NotRequired[str]
    org_rules: NotRequired[str]
    owner_type: NotRequired[str]
    updated_by: NotRequired[str | None]
    credit_balance_usd: NotRequired[int]
    auto_reload_enabled: NotRequired[bool]
    auto_reload_threshold_usd: NotRequired[int]
    auto_reload_target_usd: NotRequired[int]
    max_spending_limit_usd: NotRequired[int | None]


class RepoCoverage(TypedDict):
    id: int
    owner_id: int
    owner_name: str
    repo_id: int
    repo_name: str
    branch_name: str
    line_coverage: float
    statement_coverage: float
    function_coverage: float
    branch_coverage: float
    created_at: datetime.datetime
    created_by: str
    language: str


class RepoCoverageInsert(TypedDict):
    owner_id: NotRequired[int]
    owner_name: NotRequired[str]
    repo_id: NotRequired[int]
    repo_name: NotRequired[str]
    branch_name: NotRequired[str]
    line_coverage: NotRequired[float]
    statement_coverage: NotRequired[float]
    function_coverage: NotRequired[float]
    branch_coverage: NotRequired[float]
    created_by: NotRequired[str]
    language: NotRequired[str]


class Repositories(TypedDict):
    id: int
    owner_id: int
    repo_id: int
    repo_name: str
    created_at: datetime.datetime
    created_by: str
    updated_at: datetime.datetime
    updated_by: str
    use_screenshots: bool | None
    production_url: str | None
    local_port: int | None
    startup_commands: Any | None
    web_urls: Any | None
    file_paths: Any | None
    repo_rules: str | None
    file_count: int
    blank_lines: int
    comment_lines: int
    code_lines: int
    target_branch: str
    trigger_on_review_comment: bool
    trigger_on_test_failure: bool
    trigger_on_commit: bool
    trigger_on_merged: bool
    trigger_on_schedule: bool
    schedule_frequency: str | None
    schedule_minute: int | None
    schedule_time: Any | None
    schedule_day_of_week: str | None
    schedule_include_weekends: bool
    structured_rules: dict[str, Any] | None
    trigger_on_pr_change: bool
    schedule_execution_count: int
    schedule_interval_minutes: int


class RepositoriesInsert(TypedDict):
    owner_id: NotRequired[int]
    repo_id: NotRequired[int]
    repo_name: NotRequired[str]
    created_by: NotRequired[str]
    updated_by: NotRequired[str]
    use_screenshots: NotRequired[bool | None]
    production_url: NotRequired[str | None]
    local_port: NotRequired[int | None]
    startup_commands: NotRequired[Any | None]
    web_urls: NotRequired[Any | None]
    file_paths: NotRequired[Any | None]
    repo_rules: NotRequired[str | None]
    file_count: NotRequired[int]
    blank_lines: NotRequired[int]
    comment_lines: NotRequired[int]
    code_lines: NotRequired[int]
    target_branch: NotRequired[str]
    trigger_on_review_comment: NotRequired[bool]
    trigger_on_test_failure: NotRequired[bool]
    trigger_on_commit: NotRequired[bool]
    trigger_on_merged: NotRequired[bool]
    trigger_on_schedule: NotRequired[bool]
    schedule_frequency: NotRequired[str | None]
    schedule_minute: NotRequired[int | None]
    schedule_time: NotRequired[Any | None]
    schedule_day_of_week: NotRequired[str | None]
    schedule_include_weekends: NotRequired[bool]
    structured_rules: NotRequired[dict[str, Any] | None]
    trigger_on_pr_change: NotRequired[bool]
    schedule_execution_count: NotRequired[int]
    schedule_interval_minutes: NotRequired[int]


class Usage(TypedDict):
    id: int
    created_at: datetime.datetime
    is_completed: bool
    token_input: int | None
    token_output: int | None
    user_id: int
    installation_id: int
    created_by: str | None
    total_seconds: int | None
    owner_id: int
    owner_type: str
    owner_name: str
    repo_id: int
    repo_name: str
    issue_number: int
    source: str
    pr_number: int | None
    is_test_passed: bool
    retry_workflow_id_hash_pairs: Any | None
    is_merged: bool
    trigger: str
    original_error_log: str | None
    minimized_error_log: str | None
    lambda_log_group: str | None
    lambda_log_stream: str | None
    lambda_request_id: str | None


class UsageInsert(TypedDict):
    is_completed: NotRequired[bool]
    token_input: NotRequired[int | None]
    token_output: NotRequired[int | None]
    user_id: NotRequired[int]
    installation_id: NotRequired[int]
    created_by: NotRequired[str | None]
    total_seconds: NotRequired[int | None]
    owner_id: NotRequired[int]
    owner_type: NotRequired[str]
    owner_name: NotRequired[str]
    repo_id: NotRequired[int]
    repo_name: NotRequired[str]
    issue_number: NotRequired[int]
    source: NotRequired[str]
    pr_number: NotRequired[int | None]
    is_test_passed: NotRequired[bool]
    retry_workflow_id_hash_pairs: NotRequired[Any | None]
    is_merged: NotRequired[bool]
    trigger: NotRequired[str]
    original_error_log: NotRequired[str | None]
    minimized_error_log: NotRequired[str | None]
    lambda_log_group: NotRequired[str | None]
    lambda_log_stream: NotRequired[str | None]
    lambda_request_id: NotRequired[str | None]


class UsageWithIssues(TypedDict):
    id: int | None
    created_at: datetime.datetime | None
    is_completed: bool | None
    token_input: int | None
    token_output: int | None
    user_id: int | None
    installation_id: int | None
    created_by: str | None
    total_seconds: int | None
    owner_id: int | None
    owner_type: str | None
    owner_name: str | None
    repo_id: int | None
    repo_name: str | None
    issue_number: int | None
    source: str | None
    merged: bool | None


class UsageWithIssuesInsert(TypedDict):
    is_completed: NotRequired[bool | None]
    token_input: NotRequired[int | None]
    token_output: NotRequired[int | None]
    user_id: NotRequired[int | None]
    installation_id: NotRequired[int | None]
    created_by: NotRequired[str | None]
    total_seconds: NotRequired[int | None]
    owner_id: NotRequired[int | None]
    owner_type: NotRequired[str | None]
    owner_name: NotRequired[str | None]
    repo_id: NotRequired[int | None]
    repo_name: NotRequired[str | None]
    issue_number: NotRequired[int | None]
    source: NotRequired[str | None]
    merged: NotRequired[bool | None]


class Users(TypedDict):
    id: int
    user_name: str
    user_id: int
    email: str | None
    created_at: datetime.datetime
    created_by: str | None
    user_rules: str


class UsersInsert(TypedDict):
    user_name: NotRequired[str]
    user_id: NotRequired[int]
    email: NotRequired[str | None]
    created_by: NotRequired[str | None]
    user_rules: NotRequired[str]
