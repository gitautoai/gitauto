import datetime
from typing import Any
from typing_extensions import TypedDict


class CircleciTokens(TypedDict):
    id: str
    owner_id: int
    token: str
    created_by: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    updated_by: str


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


class Coverages(TypedDict):
    id: int
    owner_id: int
    repo_id: int
    primary_language: str | None
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


class Credits(TypedDict):
    id: int
    owner_id: int
    amount_usd: int
    transaction_type: str
    stripe_payment_intent_id: str | None
    usage_id: int | None
    expires_at: datetime.datetime | None
    created_at: datetime.datetime


class Installations(TypedDict):
    created_at: datetime.datetime
    installation_id: int
    owner_name: str
    uninstalled_at: datetime.datetime | None
    owner_type: str
    owner_id: int
    created_by: str | None
    uninstalled_by: str | None


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


class RepoCoverage(TypedDict):
    id: int
    owner_id: int
    owner_name: str
    repo_id: int
    repo_name: str
    branch_name: str
    primary_language: str | None
    line_coverage: float
    statement_coverage: float
    function_coverage: float
    branch_coverage: float
    created_at: datetime.datetime
    created_by: str


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


class Users(TypedDict):
    id: int
    user_name: str
    user_id: int
    email: str | None
    created_at: datetime.datetime
    created_by: str | None
    user_rules: str
