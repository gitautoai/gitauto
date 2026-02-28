import datetime
from typing import Any, Literal
from typing_extensions import TypedDict, NotRequired


class CheckSuites(TypedDict):
    check_suite_id: int
    created_at: datetime.datetime | None


class CheckSuitesInsert(TypedDict):
    check_suite_id: int


class CircleciTokens(TypedDict):
    id: str
    owner_id: int
    token: str
    created_by: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    updated_by: str


class CircleciTokensInsert(TypedDict):
    owner_id: int
    token: str
    created_by: str
    updated_by: str


class CodecovTokens(TypedDict):
    id: str
    owner_id: int
    token: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    created_by: str
    updated_by: str


class CodecovTokensInsert(TypedDict):
    owner_id: int
    token: str
    created_by: str
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


class ContactsInsert(TypedDict):
    user_id: NotRequired[int | None]
    user_name: NotRequired[str | None]
    first_name: str
    last_name: str
    email: str
    company_url: str
    job_title: str
    team_size: str
    team_size_other: NotRequired[str | None]
    job_description: str
    current_coverage: str
    current_coverage_other: NotRequired[str | None]
    minimum_coverage: str
    minimum_coverage_other: NotRequired[str | None]
    target_coverage: str
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
    exclusion_reason: str | None


class CoveragesInsert(TypedDict):
    owner_id: int
    repo_id: int
    language: NotRequired[str | None]
    package_name: NotRequired[str | None]
    level: str
    full_path: str
    statement_coverage: NotRequired[float | None]
    function_coverage: NotRequired[float | None]
    branch_coverage: NotRequired[float | None]
    line_coverage: NotRequired[float | None]
    uncovered_lines: NotRequired[str | None]
    created_by: str
    updated_by: str
    github_issue_url: NotRequired[str | None]
    uncovered_functions: NotRequired[str | None]
    uncovered_branches: NotRequired[str | None]
    branch_name: str
    file_size: NotRequired[int | None]
    is_excluded_from_testing: NotRequired[bool | None]
    exclusion_reason: NotRequired[str | None]


class Credits(TypedDict):
    id: int
    owner_id: int
    amount_usd: int
    transaction_type: Literal["purchase", "usage", "expiration", "refund", "auto_reload", "trial", "grant", "salvage"]
    stripe_payment_intent_id: str | None
    usage_id: int | None
    expires_at: datetime.datetime | None
    created_at: datetime.datetime


class CreditsInsert(TypedDict):
    owner_id: int
    amount_usd: int
    transaction_type: Literal["purchase", "usage", "expiration", "refund", "auto_reload", "trial", "grant", "salvage"]
    stripe_payment_intent_id: NotRequired[str | None]
    usage_id: NotRequired[int | None]
    expires_at: NotRequired[datetime.datetime | None]


class EmailSends(TypedDict):
    id: int
    owner_id: int
    owner_name: str
    email_type: str
    resend_email_id: str | None
    created_at: datetime.datetime


class EmailSendsInsert(TypedDict):
    owner_id: int
    owner_name: str
    email_type: str
    resend_email_id: NotRequired[str | None]


class Installations(TypedDict):
    created_at: datetime.datetime
    installation_id: int
    owner_name: str
    uninstalled_at: datetime.datetime | None
    owner_type: Literal["User", "Organization"]
    owner_id: int
    created_by: str | None
    uninstalled_by: str | None


class InstallationsInsert(TypedDict):
    installation_id: int
    owner_name: str
    uninstalled_at: NotRequired[datetime.datetime | None]
    owner_type: Literal["User", "Organization"]
    owner_id: int
    created_by: NotRequired[str | None]
    uninstalled_by: NotRequired[str | None]


class LlmRequests(TypedDict):
    id: int
    usage_id: int | None
    provider: str
    model_id: str
    input_content: str
    input_length: int
    input_tokens: int
    input_cost_usd: float
    output_content: str
    output_length: int
    output_tokens: int
    output_cost_usd: float
    total_cost_usd: float
    response_time_ms: int | None
    error_message: str | None
    created_at: datetime.datetime
    created_by: str | None
    updated_at: datetime.datetime
    updated_by: str | None


class LlmRequestsInsert(TypedDict):
    usage_id: NotRequired[int | None]
    provider: str
    model_id: str
    input_content: str
    input_length: int
    input_tokens: int
    input_cost_usd: float
    output_content: str
    output_length: int
    output_tokens: int
    output_cost_usd: float
    total_cost_usd: float
    response_time_ms: NotRequired[int | None]
    error_message: NotRequired[str | None]
    created_by: NotRequired[str | None]
    updated_by: NotRequired[str | None]


class MarketingCoverage(TypedDict):
    id: int
    owner_id: int
    owner_name: str
    repo_id: int
    repo_name: str
    source: str
    line_coverage: float | None
    lines: int | None
    created_at: datetime.datetime
    updated_at: datetime.datetime


class MarketingCoverageInsert(TypedDict):
    owner_id: int
    owner_name: str
    repo_id: int
    repo_name: str
    source: str
    line_coverage: NotRequired[float | None]
    lines: NotRequired[int | None]


class MarketingSearchHistory(TypedDict):
    id: int
    owner_id: int
    owner_name: str
    created_at: datetime.datetime


class MarketingSearchHistoryInsert(TypedDict):
    owner_id: int
    owner_name: str


class MarketingUsers(TypedDict):
    id: int
    owner_id: int
    owner_name: str
    repo_id: int
    repo_name: str
    user_id: int
    username: str
    first_name: str | None
    last_name: str | None
    email: str
    email_source: str
    created_at: datetime.datetime
    updated_at: datetime.datetime


class MarketingUsersInsert(TypedDict):
    owner_id: int
    owner_name: str
    repo_id: int
    repo_name: str
    user_id: int
    username: str
    first_name: NotRequired[str | None]
    last_name: NotRequired[str | None]
    email: str
    email_source: str


class NpmTokens(TypedDict):
    id: str
    owner_id: int
    token: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    created_by: str
    updated_by: str


class NpmTokensInsert(TypedDict):
    owner_id: int
    token: str
    created_by: str
    updated_by: str


class Owners(TypedDict):
    created_at: datetime.datetime
    owner_id: int
    stripe_customer_id: str
    created_by: str | None
    owner_name: str
    org_rules: str
    owner_type: Literal["User", "Organization"]
    updated_by: str | None
    updated_at: datetime.datetime
    credit_balance_usd: int
    auto_reload_enabled: bool
    auto_reload_threshold_usd: int
    auto_reload_target_usd: int
    max_spending_limit_usd: int | None


class OwnersInsert(TypedDict):
    owner_id: int
    stripe_customer_id: str
    created_by: NotRequired[str | None]
    owner_name: str
    org_rules: str
    owner_type: Literal["User", "Organization"]
    updated_by: NotRequired[str | None]
    credit_balance_usd: int
    auto_reload_enabled: bool
    auto_reload_threshold_usd: int
    auto_reload_target_usd: int
    max_spending_limit_usd: NotRequired[int | None]


class RepoCoverage(TypedDict):
    id: int
    owner_id: int
    owner_name: str
    repo_id: int
    repo_name: str
    branch_name: str
    line_coverage: float | None
    statement_coverage: float | None
    function_coverage: float | None
    branch_coverage: float | None
    created_at: datetime.datetime
    created_by: str
    language: str
    lines_covered: int
    lines_total: int
    functions_total: int
    functions_covered: int
    branches_total: int
    branches_covered: int


class RepoCoverageInsert(TypedDict):
    owner_id: int
    owner_name: str
    repo_id: int
    repo_name: str
    branch_name: str
    line_coverage: NotRequired[float | None]
    statement_coverage: NotRequired[float | None]
    function_coverage: NotRequired[float | None]
    branch_coverage: NotRequired[float | None]
    created_by: str
    language: str
    lines_covered: int
    lines_total: int
    functions_total: int
    functions_covered: int
    branches_total: int
    branches_covered: int


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
    startup_commands: list[str] | None
    web_urls: list[str] | None
    file_paths: list[str] | None
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
    test_dir_prefixes: list[str]


class RepositoriesInsert(TypedDict):
    owner_id: int
    repo_id: int
    repo_name: str
    created_by: str
    updated_by: str
    use_screenshots: NotRequired[bool | None]
    production_url: NotRequired[str | None]
    local_port: NotRequired[int | None]
    startup_commands: NotRequired[list[str] | None]
    web_urls: NotRequired[list[str] | None]
    file_paths: NotRequired[list[str] | None]
    repo_rules: NotRequired[str | None]
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
    schedule_frequency: NotRequired[str | None]
    schedule_minute: NotRequired[int | None]
    schedule_time: NotRequired[Any | None]
    schedule_day_of_week: NotRequired[str | None]
    schedule_include_weekends: bool
    structured_rules: NotRequired[dict[str, Any] | None]
    trigger_on_pr_change: bool
    schedule_execution_count: int
    schedule_interval_minutes: int
    test_dir_prefixes: list[str]


class RepositoryFeatures(TypedDict):
    id: int
    owner_id: int
    owner_name: str
    repo_id: int
    repo_name: str
    auto_merge: bool
    auto_merge_only_test_files: bool
    merge_method: str
    created_at: datetime.datetime
    created_by: str
    updated_at: datetime.datetime
    updated_by: str
    allow_edit_any_file: bool
    restrict_edit_to_target_test_file_only: bool


class RepositoryFeaturesInsert(TypedDict):
    owner_id: int
    owner_name: str
    repo_id: int
    repo_name: str
    auto_merge: bool
    auto_merge_only_test_files: bool
    merge_method: str
    created_by: str
    updated_by: str
    allow_edit_any_file: bool
    restrict_edit_to_target_test_file_only: bool


class SchedulePauses(TypedDict):
    id: str
    owner_id: int
    repo_id: int
    pause_start: datetime.datetime
    pause_end: datetime.datetime
    reason: str | None
    created_by: str
    created_at: datetime.datetime
    updated_by: str
    updated_at: datetime.datetime


class SchedulePausesInsert(TypedDict):
    owner_id: int
    repo_id: int
    pause_start: datetime.datetime
    pause_end: datetime.datetime
    reason: NotRequired[str | None]
    created_by: str
    updated_by: str


class TotalRepoCoverage(TypedDict):
    owner_id: int | None
    coverage_date: Any | None
    lines_covered: int | None
    lines_total: int | None
    functions_covered: int | None
    functions_total: int | None
    branches_covered: int | None
    branches_total: int | None
    statement_coverage: float | None
    function_coverage: float | None
    branch_coverage: float | None


class TotalRepoCoverageInsert(TypedDict):
    owner_id: NotRequired[int | None]
    coverage_date: NotRequired[Any | None]
    lines_covered: NotRequired[int | None]
    lines_total: NotRequired[int | None]
    functions_covered: NotRequired[int | None]
    functions_total: NotRequired[int | None]
    branches_covered: NotRequired[int | None]
    branches_total: NotRequired[int | None]
    statement_coverage: NotRequired[float | None]
    function_coverage: NotRequired[float | None]
    branch_coverage: NotRequired[float | None]


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
    owner_type: Literal["User", "Organization"]
    owner_name: str
    repo_id: int
    repo_name: str
    issue_number: int
    source: str
    pr_number: int | None
    is_test_passed: bool
    retry_workflow_id_hash_pairs: list[str] | None
    is_merged: bool
    trigger: str
    original_error_log: str | None
    minimized_error_log: str | None
    lambda_log_group: str | None
    lambda_log_stream: str | None
    lambda_request_id: str | None


class UsageInsert(TypedDict):
    is_completed: bool
    token_input: NotRequired[int | None]
    token_output: NotRequired[int | None]
    user_id: int
    installation_id: int
    created_by: NotRequired[str | None]
    total_seconds: NotRequired[int | None]
    owner_id: int
    owner_type: Literal["User", "Organization"]
    owner_name: str
    repo_id: int
    repo_name: str
    issue_number: int
    source: str
    pr_number: NotRequired[int | None]
    is_test_passed: bool
    retry_workflow_id_hash_pairs: NotRequired[list[str] | None]
    is_merged: bool
    trigger: str
    original_error_log: NotRequired[str | None]
    minimized_error_log: NotRequired[str | None]
    lambda_log_group: NotRequired[str | None]
    lambda_log_stream: NotRequired[str | None]
    lambda_request_id: NotRequired[str | None]


class Users(TypedDict):
    id: int
    user_name: str
    user_id: int
    email: str | None
    created_at: datetime.datetime
    created_by: str | None
    user_rules: str
    display_name: str
    deleted_at: datetime.datetime | None
    display_name_override: str | None
    skip_drip_emails: bool


class UsersInsert(TypedDict):
    user_name: str
    user_id: int
    email: NotRequired[str | None]
    created_by: NotRequired[str | None]
    user_rules: str
    display_name: str
    deleted_at: NotRequired[datetime.datetime | None]
    display_name_override: NotRequired[str | None]
    skip_drip_emails: bool


class WebhookDeliveries(TypedDict):
    id: int
    delivery_id: str
    event_name: str
    created_at: datetime.datetime | None


class WebhookDeliveriesInsert(TypedDict):
    delivery_id: str
    event_name: str
