from __future__ import annotations

import datetime

from pydantic import UUID4, BaseModel, Field, Json

# CUSTOM CLASSES
# Note: These are custom model classes for defining common features among
# Pydantic Base Schema.


class CustomModel(BaseModel):
    """Base model class with common features."""

    pass


class CustomModelInsert(CustomModel):
    """Base model for insert operations with common features."""

    pass


class CustomModelUpdate(CustomModel):
    """Base model for update operations with common features."""

    pass


# BASE CLASSES
# Note: These are the base Row models that include all fields.


class CircleciTokensBaseSchema(CustomModel):
    """CircleciTokens Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    created_at: datetime.datetime
    created_by: str
    owner_id: int
    token: str
    updated_at: datetime.datetime
    updated_by: str


class ContactsBaseSchema(CustomModel):
    """Contacts Base Schema."""

    # Primary Keys
    id: int

    # Columns
    additional_info: str | None = Field(default=None)
    company_url: str
    created_at: datetime.datetime | None = Field(default=None)
    current_coverage: str
    current_coverage_other: str | None = Field(default=None)
    email: str
    first_name: str
    job_description: str
    job_title: str
    last_name: str
    minimum_coverage: str
    minimum_coverage_other: str | None = Field(default=None)
    target_coverage: str
    target_coverage_other: str | None = Field(default=None)
    team_size: str
    team_size_other: str | None = Field(default=None)
    testing_challenges: str | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    user_id: int | None = Field(default=None)
    user_name: str | None = Field(default=None)


class CoveragesBaseSchema(CustomModel):
    """Coverages Base Schema."""

    # Primary Keys
    id: int

    # Columns
    branch_coverage: float | None = Field(default=None)
    branch_name: str
    created_at: datetime.datetime
    created_by: str
    file_size: int | None = Field(default=None)
    full_path: str
    function_coverage: float | None = Field(default=None)
    github_issue_url: str | None = Field(default=None)
    is_excluded_from_testing: bool | None = Field(default=None)
    level: str
    line_coverage: float | None = Field(default=None)
    owner_id: int
    package_name: str | None = Field(default=None)
    path_coverage: float | None = Field(default=None)
    primary_language: str | None = Field(default=None)
    repo_id: int
    statement_coverage: float | None = Field(default=None)
    uncovered_branches: str | None = Field(default=None)
    uncovered_functions: str | None = Field(default=None)
    uncovered_lines: str | None = Field(default=None)
    updated_at: datetime.datetime
    updated_by: str


class CreditsBaseSchema(CustomModel):
    """Credits Base Schema."""

    # Primary Keys
    id: int

    # Columns
    amount_usd: int
    created_at: datetime.datetime
    expires_at: datetime.datetime | None = Field(default=None)
    owner_id: int
    stripe_payment_intent_id: str | None = Field(default=None)
    transaction_type: str
    usage_id: int | None = Field(default=None)


class InstallationsBaseSchema(CustomModel):
    """Installations Base Schema."""

    # Primary Keys
    installation_id: int

    # Columns
    created_at: datetime.datetime
    created_by: str | None = Field(default=None)
    owner_id: int
    owner_name: str
    owner_type: str
    uninstalled_at: datetime.datetime | None = Field(default=None)
    uninstalled_by: str | None = Field(default=None)


class IssuesBaseSchema(CustomModel):
    """Issues Base Schema."""

    # Primary Keys
    id: int

    # Columns
    created_at: datetime.datetime
    created_by: str | None = Field(default=None)
    installation_id: int
    issue_number: int
    merged: bool
    owner_id: int
    owner_name: str
    owner_type: str
    repo_id: int
    repo_name: str
    run_id: int | None = Field(default=None)


class JiraGithubLinksBaseSchema(CustomModel):
    """JiraGithubLinks Base Schema."""

    # Primary Keys
    id: int

    # Columns
    created_at: datetime.datetime | None = Field(default=None)
    created_by: int
    github_owner_id: int
    github_owner_name: str
    github_repo_id: int
    github_repo_name: str
    jira_project_id: int
    jira_project_name: str
    jira_site_id: str
    jira_site_name: str
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: int | None = Field(default=None)


class OauthTokensBaseSchema(CustomModel):
    """OauthTokens Base Schema."""

    # Primary Keys
    id: int

    # Columns
    access_token: str
    created_at: datetime.datetime
    created_by: int
    expires_at: datetime.datetime
    refresh_token: str | None = Field(default=None)
    scope: str
    service_name: str
    updated_at: datetime.datetime
    updated_by: int | None = Field(default=None)
    user_id: int


class OwnersBaseSchema(CustomModel):
    """Owners Base Schema."""

    # Primary Keys
    owner_id: int

    # Columns
    auto_reload_enabled: bool
    auto_reload_target_usd: int
    auto_reload_threshold_usd: int
    created_at: datetime.datetime
    created_by: str | None = Field(default=None)
    credit_balance_usd: int
    max_spending_limit_usd: int | None = Field(default=None)
    org_rules: str
    owner_name: str
    owner_type: str
    stripe_customer_id: str
    updated_at: datetime.datetime
    updated_by: str | None = Field(default=None)


class RepoCoverageBaseSchema(CustomModel):
    """RepoCoverage Base Schema."""

    # Primary Keys
    id: int

    # Columns
    branch_coverage: float
    branch_name: str
    created_at: datetime.datetime
    created_by: str
    function_coverage: float
    line_coverage: float
    owner_id: int
    owner_name: str
    primary_language: str | None = Field(default=None)
    repo_id: int
    repo_name: str
    statement_coverage: float


class RepositoriesBaseSchema(CustomModel):
    """Repositories Base Schema."""

    # Primary Keys
    id: int

    # Columns
    blank_lines: int
    code_lines: int
    comment_lines: int
    created_at: datetime.datetime
    created_by: str
    file_count: int
    file_paths: list | None = Field(default=None)
    local_port: int | None = Field(default=None)
    owner_id: int
    production_url: str | None = Field(default=None)
    repo_id: int
    repo_name: str
    repo_rules: str | None = Field(default=None)
    schedule_day_of_week: str | None = Field(default=None)
    schedule_execution_count: int
    schedule_frequency: str | None = Field(default=None)
    schedule_include_weekends: bool
    schedule_interval_minutes: int
    schedule_minute: int | None = Field(default=None)
    schedule_time: datetime.time | None = Field(default=None)
    startup_commands: list | None = Field(default=None)
    structured_rules: dict | Json | None = Field(default=None)
    target_branch: str
    trigger_on_commit: bool
    trigger_on_merged: bool
    trigger_on_pr_change: bool
    trigger_on_review_comment: bool
    trigger_on_schedule: bool
    trigger_on_test_failure: bool
    updated_at: datetime.datetime
    updated_by: str
    use_screenshots: bool | None = Field(default=None)
    web_urls: list | None = Field(default=None)


class UsageBaseSchema(CustomModel):
    """Usage Base Schema."""

    # Primary Keys
    id: int

    # Columns
    created_at: datetime.datetime
    created_by: str | None = Field(default=None)
    installation_id: int
    is_completed: bool
    is_merged: bool
    is_test_passed: bool
    issue_number: int
    owner_id: int
    owner_name: str
    owner_type: str
    pr_number: int | None = Field(default=None)
    repo_id: int
    repo_name: str
    retry_workflow_id_hash_pairs: list | None = Field(default=None)
    source: str
    token_input: int | None = Field(default=None)
    token_output: int | None = Field(default=None)
    total_seconds: int | None = Field(default=None)
    trigger: str
    user_id: int


class UsageWithIssuesBaseSchema(CustomModel):
    """UsageWithIssues Base Schema."""

    # Columns
    created_at: datetime.datetime | None = Field(default=None)
    created_by: str | None = Field(default=None)
    id: int | None = Field(default=None)
    installation_id: int | None = Field(default=None)
    is_completed: bool | None = Field(default=None)
    issue_number: int | None = Field(default=None)
    merged: bool | None = Field(default=None)
    owner_id: int | None = Field(default=None)
    owner_name: str | None = Field(default=None)
    owner_type: str | None = Field(default=None)
    repo_id: int | None = Field(default=None)
    repo_name: str | None = Field(default=None)
    source: str | None = Field(default=None)
    token_input: int | None = Field(default=None)
    token_output: int | None = Field(default=None)
    total_seconds: int | None = Field(default=None)
    user_id: int | None = Field(default=None)


class UsersBaseSchema(CustomModel):
    """Users Base Schema."""

    # Primary Keys
    id: int

    # Columns
    created_at: datetime.datetime
    created_by: str | None = Field(default=None)
    email: str | None = Field(default=None)
    user_id: int
    user_name: str
    user_rules: str


# INSERT CLASSES
# Note: These models are used for insert operations. Auto-generated fields
# (like IDs and timestamps) are optional.


class CircleciTokensInsert(CustomModelInsert):
    """CircleciTokens Insert Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)  # has default value

    # Field properties:
    # created_at: has default value
    # updated_at: has default value

    # Required fields
    created_by: str
    owner_id: int
    token: str
    updated_by: str

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)


class ContactsInsert(CustomModelInsert):
    """Contacts Insert Schema."""

    # Primary Keys
    id: int | None = Field(default=None)  # has default value, auto-generated

    # Field properties:
    # additional_info: nullable
    # created_at: nullable, has default value
    # current_coverage_other: nullable
    # minimum_coverage_other: nullable
    # target_coverage_other: nullable
    # team_size_other: nullable
    # testing_challenges: nullable
    # updated_at: nullable, has default value
    # user_id: nullable
    # user_name: nullable

    # Required fields
    company_url: str
    current_coverage: str
    email: str
    first_name: str
    job_description: str
    job_title: str
    last_name: str
    minimum_coverage: str
    target_coverage: str
    team_size: str

    # Optional fields
    additional_info: str | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    current_coverage_other: str | None = Field(default=None)
    minimum_coverage_other: str | None = Field(default=None)
    target_coverage_other: str | None = Field(default=None)
    team_size_other: str | None = Field(default=None)
    testing_challenges: str | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    user_id: int | None = Field(default=None)
    user_name: str | None = Field(default=None)


class CoveragesInsert(CustomModelInsert):
    """Coverages Insert Schema."""

    # Primary Keys

    # Field properties:
    # branch_coverage: nullable, has default value
    # branch_name: has default value
    # created_at: has default value
    # file_size: nullable, has default value
    # function_coverage: nullable, has default value
    # github_issue_url: nullable
    # is_excluded_from_testing: nullable, has default value
    # line_coverage: nullable, has default value
    # package_name: nullable
    # path_coverage: nullable, has default value
    # primary_language: nullable
    # statement_coverage: nullable, has default value
    # uncovered_branches: nullable
    # uncovered_functions: nullable
    # uncovered_lines: nullable
    # updated_at: has default value

    # Required fields
    created_by: str
    full_path: str
    level: str
    owner_id: int
    repo_id: int
    updated_by: str

    # Optional fields
    branch_coverage: float | None = Field(default=None)
    branch_name: str | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    file_size: int | None = Field(default=None)
    function_coverage: float | None = Field(default=None)
    github_issue_url: str | None = Field(default=None)
    is_excluded_from_testing: bool | None = Field(default=None)
    line_coverage: float | None = Field(default=None)
    package_name: str | None = Field(default=None)
    path_coverage: float | None = Field(default=None)
    primary_language: str | None = Field(default=None)
    statement_coverage: float | None = Field(default=None)
    uncovered_branches: str | None = Field(default=None)
    uncovered_functions: str | None = Field(default=None)
    uncovered_lines: str | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)


class CreditsInsert(CustomModelInsert):
    """Credits Insert Schema."""

    # Primary Keys
    id: int | None = Field(default=None)  # has default value, auto-generated

    # Field properties:
    # created_at: has default value
    # expires_at: nullable
    # stripe_payment_intent_id: nullable
    # usage_id: nullable

    # Required fields
    amount_usd: int
    owner_id: int
    transaction_type: str

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    expires_at: datetime.datetime | None = Field(default=None)
    stripe_payment_intent_id: str | None = Field(default=None)
    usage_id: int | None = Field(default=None)


class InstallationsInsert(CustomModelInsert):
    """Installations Insert Schema."""

    # Primary Keys
    installation_id: int

    # Field properties:
    # created_at: has default value
    # created_by: nullable
    # owner_id: has default value
    # owner_type: has default value
    # uninstalled_at: nullable
    # uninstalled_by: nullable

    # Required fields
    owner_name: str

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    created_by: str | None = Field(default=None)
    owner_id: int | None = Field(default=None)
    owner_type: str | None = Field(default=None)
    uninstalled_at: datetime.datetime | None = Field(default=None)
    uninstalled_by: str | None = Field(default=None)


class IssuesInsert(CustomModelInsert):
    """Issues Insert Schema."""

    # Primary Keys

    # Field properties:
    # created_at: has default value
    # created_by: nullable
    # issue_number: has default value
    # merged: has default value
    # owner_id: has default value
    # owner_name: has default value
    # owner_type: has default value
    # repo_id: has default value
    # repo_name: has default value
    # run_id: nullable

    # Required fields
    installation_id: int

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    created_by: str | None = Field(default=None)
    issue_number: int | None = Field(default=None)
    merged: bool | None = Field(default=None)
    owner_id: int | None = Field(default=None)
    owner_name: str | None = Field(default=None)
    owner_type: str | None = Field(default=None)
    repo_id: int | None = Field(default=None)
    repo_name: str | None = Field(default=None)
    run_id: int | None = Field(default=None)


class JiraGithubLinksInsert(CustomModelInsert):
    """JiraGithubLinks Insert Schema."""

    # Primary Keys
    id: int | None = Field(default=None)  # has default value, auto-generated

    # Field properties:
    # created_at: nullable, has default value
    # updated_at: nullable, has default value
    # updated_by: nullable

    # Required fields
    created_by: int
    github_owner_id: int
    github_owner_name: str
    github_repo_id: int
    github_repo_name: str
    jira_project_id: int
    jira_project_name: str
    jira_site_id: str
    jira_site_name: str

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: int | None = Field(default=None)


class OauthTokensInsert(CustomModelInsert):
    """OauthTokens Insert Schema."""

    # Primary Keys
    id: int | None = Field(default=None)  # has default value, auto-generated

    # Field properties:
    # created_at: has default value
    # refresh_token: nullable
    # updated_at: has default value
    # updated_by: nullable

    # Required fields
    access_token: str
    created_by: int
    expires_at: datetime.datetime
    scope: str
    service_name: str
    user_id: int

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    refresh_token: str | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: int | None = Field(default=None)


class OwnersInsert(CustomModelInsert):
    """Owners Insert Schema."""

    # Primary Keys
    owner_id: int

    # Field properties:
    # auto_reload_enabled: has default value
    # auto_reload_target_usd: has default value
    # auto_reload_threshold_usd: has default value
    # created_at: has default value
    # created_by: nullable
    # credit_balance_usd: has default value
    # max_spending_limit_usd: nullable
    # org_rules: has default value
    # owner_name: has default value
    # owner_type: has default value
    # updated_at: has default value
    # updated_by: nullable

    # Required fields
    stripe_customer_id: str

    # Optional fields
    auto_reload_enabled: bool | None = Field(default=None)
    auto_reload_target_usd: int | None = Field(default=None)
    auto_reload_threshold_usd: int | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    created_by: str | None = Field(default=None)
    credit_balance_usd: int | None = Field(default=None)
    max_spending_limit_usd: int | None = Field(default=None)
    org_rules: str | None = Field(default=None)
    owner_name: str | None = Field(default=None)
    owner_type: str | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: str | None = Field(default=None)


class RepoCoverageInsert(CustomModelInsert):
    """RepoCoverage Insert Schema."""

    # Primary Keys
    id: int | None = Field(default=None)  # has default value, auto-generated

    # Field properties:
    # branch_coverage: has default value
    # created_at: has default value
    # function_coverage: has default value
    # line_coverage: has default value
    # primary_language: nullable
    # statement_coverage: has default value

    # Required fields
    branch_name: str
    created_by: str
    owner_id: int
    owner_name: str
    repo_id: int
    repo_name: str

    # Optional fields
    branch_coverage: float | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    function_coverage: float | None = Field(default=None)
    line_coverage: float | None = Field(default=None)
    primary_language: str | None = Field(default=None)
    statement_coverage: float | None = Field(default=None)


class RepositoriesInsert(CustomModelInsert):
    """Repositories Insert Schema."""

    # Primary Keys

    # Field properties:
    # blank_lines: has default value
    # code_lines: has default value
    # comment_lines: has default value
    # created_at: has default value
    # file_count: has default value
    # file_paths: nullable, has default value
    # local_port: nullable, has default value
    # production_url: nullable, has default value
    # repo_rules: nullable, has default value
    # schedule_day_of_week: nullable
    # schedule_execution_count: has default value
    # schedule_frequency: nullable
    # schedule_include_weekends: has default value
    # schedule_interval_minutes: has default value
    # schedule_minute: nullable
    # schedule_time: nullable
    # startup_commands: nullable, has default value
    # structured_rules: nullable
    # target_branch: has default value
    # trigger_on_commit: has default value
    # trigger_on_merged: has default value
    # trigger_on_pr_change: has default value
    # trigger_on_review_comment: has default value
    # trigger_on_schedule: has default value
    # trigger_on_test_failure: has default value
    # updated_at: has default value
    # use_screenshots: nullable, has default value
    # web_urls: nullable, has default value

    # Required fields
    created_by: str
    owner_id: int
    repo_id: int
    repo_name: str
    updated_by: str

    # Optional fields
    blank_lines: int | None = Field(default=None)
    code_lines: int | None = Field(default=None)
    comment_lines: int | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    file_count: int | None = Field(default=None)
    file_paths: list | None = Field(default=None)
    local_port: int | None = Field(default=None)
    production_url: str | None = Field(default=None)
    repo_rules: str | None = Field(default=None)
    schedule_day_of_week: str | None = Field(default=None)
    schedule_execution_count: int | None = Field(default=None)
    schedule_frequency: str | None = Field(default=None)
    schedule_include_weekends: bool | None = Field(default=None)
    schedule_interval_minutes: int | None = Field(default=None)
    schedule_minute: int | None = Field(default=None)
    schedule_time: datetime.time | None = Field(default=None)
    startup_commands: list | None = Field(default=None)
    structured_rules: dict | Json | None = Field(default=None)
    target_branch: str | None = Field(default=None)
    trigger_on_commit: bool | None = Field(default=None)
    trigger_on_merged: bool | None = Field(default=None)
    trigger_on_pr_change: bool | None = Field(default=None)
    trigger_on_review_comment: bool | None = Field(default=None)
    trigger_on_schedule: bool | None = Field(default=None)
    trigger_on_test_failure: bool | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    use_screenshots: bool | None = Field(default=None)
    web_urls: list | None = Field(default=None)


class UsageInsert(CustomModelInsert):
    """Usage Insert Schema."""

    # Primary Keys
    id: int | None = Field(default=None)  # has default value, auto-generated

    # Field properties:
    # created_at: has default value
    # created_by: nullable
    # is_completed: has default value
    # is_merged: has default value
    # is_test_passed: has default value
    # issue_number: has default value
    # owner_id: has default value
    # owner_name: has default value
    # owner_type: has default value
    # pr_number: nullable
    # repo_id: has default value
    # repo_name: has default value
    # retry_workflow_id_hash_pairs: nullable
    # source: has default value
    # token_input: nullable
    # token_output: nullable
    # total_seconds: nullable
    # trigger: has default value

    # Required fields
    installation_id: int
    user_id: int

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    created_by: str | None = Field(default=None)
    is_completed: bool | None = Field(default=None)
    is_merged: bool | None = Field(default=None)
    is_test_passed: bool | None = Field(default=None)
    issue_number: int | None = Field(default=None)
    owner_id: int | None = Field(default=None)
    owner_name: str | None = Field(default=None)
    owner_type: str | None = Field(default=None)
    pr_number: int | None = Field(default=None)
    repo_id: int | None = Field(default=None)
    repo_name: str | None = Field(default=None)
    retry_workflow_id_hash_pairs: list | None = Field(default=None)
    source: str | None = Field(default=None)
    token_input: int | None = Field(default=None)
    token_output: int | None = Field(default=None)
    total_seconds: int | None = Field(default=None)
    trigger: str | None = Field(default=None)


class UsageWithIssuesInsert(CustomModelInsert):
    """UsageWithIssues Insert Schema."""

    # Field properties:
    # created_at: nullable
    # created_by: nullable
    # id: nullable
    # installation_id: nullable
    # is_completed: nullable
    # issue_number: nullable
    # merged: nullable
    # owner_id: nullable
    # owner_name: nullable
    # owner_type: nullable
    # repo_id: nullable
    # repo_name: nullable
    # source: nullable
    # token_input: nullable
    # token_output: nullable
    # total_seconds: nullable
    # user_id: nullable

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    created_by: str | None = Field(default=None)
    id: int | None = Field(default=None)
    installation_id: int | None = Field(default=None)
    is_completed: bool | None = Field(default=None)
    issue_number: int | None = Field(default=None)
    merged: bool | None = Field(default=None)
    owner_id: int | None = Field(default=None)
    owner_name: str | None = Field(default=None)
    owner_type: str | None = Field(default=None)
    repo_id: int | None = Field(default=None)
    repo_name: str | None = Field(default=None)
    source: str | None = Field(default=None)
    token_input: int | None = Field(default=None)
    token_output: int | None = Field(default=None)
    total_seconds: int | None = Field(default=None)
    user_id: int | None = Field(default=None)


class UsersInsert(CustomModelInsert):
    """Users Insert Schema."""

    # Primary Keys
    id: int | None = Field(default=None)  # has default value, auto-generated

    # Field properties:
    # created_at: has default value
    # created_by: nullable
    # email: nullable
    # user_rules: has default value

    # Required fields
    user_id: int
    user_name: str

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    created_by: str | None = Field(default=None)
    email: str | None = Field(default=None)
    user_rules: str | None = Field(default=None)


# UPDATE CLASSES
# Note: These models are used for update operations. All fields are optional.


class CircleciTokensUpdate(CustomModelUpdate):
    """CircleciTokens Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # created_at: has default value
    # updated_at: has default value

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    created_by: str | None = Field(default=None)
    owner_id: int | None = Field(default=None)
    token: str | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: str | None = Field(default=None)


class ContactsUpdate(CustomModelUpdate):
    """Contacts Update Schema."""

    # Primary Keys
    id: int | None = Field(default=None)

    # Field properties:
    # additional_info: nullable
    # created_at: nullable, has default value
    # current_coverage_other: nullable
    # minimum_coverage_other: nullable
    # target_coverage_other: nullable
    # team_size_other: nullable
    # testing_challenges: nullable
    # updated_at: nullable, has default value
    # user_id: nullable
    # user_name: nullable

    # Optional fields
    additional_info: str | None = Field(default=None)
    company_url: str | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    current_coverage: str | None = Field(default=None)
    current_coverage_other: str | None = Field(default=None)
    email: str | None = Field(default=None)
    first_name: str | None = Field(default=None)
    job_description: str | None = Field(default=None)
    job_title: str | None = Field(default=None)
    last_name: str | None = Field(default=None)
    minimum_coverage: str | None = Field(default=None)
    minimum_coverage_other: str | None = Field(default=None)
    target_coverage: str | None = Field(default=None)
    target_coverage_other: str | None = Field(default=None)
    team_size: str | None = Field(default=None)
    team_size_other: str | None = Field(default=None)
    testing_challenges: str | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    user_id: int | None = Field(default=None)
    user_name: str | None = Field(default=None)


class CoveragesUpdate(CustomModelUpdate):
    """Coverages Update Schema."""

    # Primary Keys

    # Field properties:
    # branch_coverage: nullable, has default value
    # branch_name: has default value
    # created_at: has default value
    # file_size: nullable, has default value
    # function_coverage: nullable, has default value
    # github_issue_url: nullable
    # is_excluded_from_testing: nullable, has default value
    # line_coverage: nullable, has default value
    # package_name: nullable
    # path_coverage: nullable, has default value
    # primary_language: nullable
    # statement_coverage: nullable, has default value
    # uncovered_branches: nullable
    # uncovered_functions: nullable
    # uncovered_lines: nullable
    # updated_at: has default value

    # Optional fields
    branch_coverage: float | None = Field(default=None)
    branch_name: str | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    created_by: str | None = Field(default=None)
    file_size: int | None = Field(default=None)
    full_path: str | None = Field(default=None)
    function_coverage: float | None = Field(default=None)
    github_issue_url: str | None = Field(default=None)
    is_excluded_from_testing: bool | None = Field(default=None)
    level: str | None = Field(default=None)
    line_coverage: float | None = Field(default=None)
    owner_id: int | None = Field(default=None)
    package_name: str | None = Field(default=None)
    path_coverage: float | None = Field(default=None)
    primary_language: str | None = Field(default=None)
    repo_id: int | None = Field(default=None)
    statement_coverage: float | None = Field(default=None)
    uncovered_branches: str | None = Field(default=None)
    uncovered_functions: str | None = Field(default=None)
    uncovered_lines: str | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: str | None = Field(default=None)


class CreditsUpdate(CustomModelUpdate):
    """Credits Update Schema."""

    # Primary Keys
    id: int | None = Field(default=None)

    # Field properties:
    # created_at: has default value
    # expires_at: nullable
    # stripe_payment_intent_id: nullable
    # usage_id: nullable

    # Optional fields
    amount_usd: int | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    expires_at: datetime.datetime | None = Field(default=None)
    owner_id: int | None = Field(default=None)
    stripe_payment_intent_id: str | None = Field(default=None)
    transaction_type: str | None = Field(default=None)
    usage_id: int | None = Field(default=None)


class InstallationsUpdate(CustomModelUpdate):
    """Installations Update Schema."""

    # Primary Keys
    installation_id: int | None = Field(default=None)

    # Field properties:
    # created_at: has default value
    # created_by: nullable
    # owner_id: has default value
    # owner_type: has default value
    # uninstalled_at: nullable
    # uninstalled_by: nullable

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    created_by: str | None = Field(default=None)
    owner_id: int | None = Field(default=None)
    owner_name: str | None = Field(default=None)
    owner_type: str | None = Field(default=None)
    uninstalled_at: datetime.datetime | None = Field(default=None)
    uninstalled_by: str | None = Field(default=None)


class IssuesUpdate(CustomModelUpdate):
    """Issues Update Schema."""

    # Primary Keys

    # Field properties:
    # created_at: has default value
    # created_by: nullable
    # issue_number: has default value
    # merged: has default value
    # owner_id: has default value
    # owner_name: has default value
    # owner_type: has default value
    # repo_id: has default value
    # repo_name: has default value
    # run_id: nullable

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    created_by: str | None = Field(default=None)
    installation_id: int | None = Field(default=None)
    issue_number: int | None = Field(default=None)
    merged: bool | None = Field(default=None)
    owner_id: int | None = Field(default=None)
    owner_name: str | None = Field(default=None)
    owner_type: str | None = Field(default=None)
    repo_id: int | None = Field(default=None)
    repo_name: str | None = Field(default=None)
    run_id: int | None = Field(default=None)


class JiraGithubLinksUpdate(CustomModelUpdate):
    """JiraGithubLinks Update Schema."""

    # Primary Keys
    id: int | None = Field(default=None)

    # Field properties:
    # created_at: nullable, has default value
    # updated_at: nullable, has default value
    # updated_by: nullable

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    created_by: int | None = Field(default=None)
    github_owner_id: int | None = Field(default=None)
    github_owner_name: str | None = Field(default=None)
    github_repo_id: int | None = Field(default=None)
    github_repo_name: str | None = Field(default=None)
    jira_project_id: int | None = Field(default=None)
    jira_project_name: str | None = Field(default=None)
    jira_site_id: str | None = Field(default=None)
    jira_site_name: str | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: int | None = Field(default=None)


class OauthTokensUpdate(CustomModelUpdate):
    """OauthTokens Update Schema."""

    # Primary Keys
    id: int | None = Field(default=None)

    # Field properties:
    # created_at: has default value
    # refresh_token: nullable
    # updated_at: has default value
    # updated_by: nullable

    # Optional fields
    access_token: str | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    created_by: int | None = Field(default=None)
    expires_at: datetime.datetime | None = Field(default=None)
    refresh_token: str | None = Field(default=None)
    scope: str | None = Field(default=None)
    service_name: str | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: int | None = Field(default=None)
    user_id: int | None = Field(default=None)


class OwnersUpdate(CustomModelUpdate):
    """Owners Update Schema."""

    # Primary Keys
    owner_id: int | None = Field(default=None)

    # Field properties:
    # auto_reload_enabled: has default value
    # auto_reload_target_usd: has default value
    # auto_reload_threshold_usd: has default value
    # created_at: has default value
    # created_by: nullable
    # credit_balance_usd: has default value
    # max_spending_limit_usd: nullable
    # org_rules: has default value
    # owner_name: has default value
    # owner_type: has default value
    # updated_at: has default value
    # updated_by: nullable

    # Optional fields
    auto_reload_enabled: bool | None = Field(default=None)
    auto_reload_target_usd: int | None = Field(default=None)
    auto_reload_threshold_usd: int | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    created_by: str | None = Field(default=None)
    credit_balance_usd: int | None = Field(default=None)
    max_spending_limit_usd: int | None = Field(default=None)
    org_rules: str | None = Field(default=None)
    owner_name: str | None = Field(default=None)
    owner_type: str | None = Field(default=None)
    stripe_customer_id: str | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: str | None = Field(default=None)


class RepoCoverageUpdate(CustomModelUpdate):
    """RepoCoverage Update Schema."""

    # Primary Keys
    id: int | None = Field(default=None)

    # Field properties:
    # branch_coverage: has default value
    # created_at: has default value
    # function_coverage: has default value
    # line_coverage: has default value
    # primary_language: nullable
    # statement_coverage: has default value

    # Optional fields
    branch_coverage: float | None = Field(default=None)
    branch_name: str | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    created_by: str | None = Field(default=None)
    function_coverage: float | None = Field(default=None)
    line_coverage: float | None = Field(default=None)
    owner_id: int | None = Field(default=None)
    owner_name: str | None = Field(default=None)
    primary_language: str | None = Field(default=None)
    repo_id: int | None = Field(default=None)
    repo_name: str | None = Field(default=None)
    statement_coverage: float | None = Field(default=None)


class RepositoriesUpdate(CustomModelUpdate):
    """Repositories Update Schema."""

    # Primary Keys

    # Field properties:
    # blank_lines: has default value
    # code_lines: has default value
    # comment_lines: has default value
    # created_at: has default value
    # file_count: has default value
    # file_paths: nullable, has default value
    # local_port: nullable, has default value
    # production_url: nullable, has default value
    # repo_rules: nullable, has default value
    # schedule_day_of_week: nullable
    # schedule_execution_count: has default value
    # schedule_frequency: nullable
    # schedule_include_weekends: has default value
    # schedule_interval_minutes: has default value
    # schedule_minute: nullable
    # schedule_time: nullable
    # startup_commands: nullable, has default value
    # structured_rules: nullable
    # target_branch: has default value
    # trigger_on_commit: has default value
    # trigger_on_merged: has default value
    # trigger_on_pr_change: has default value
    # trigger_on_review_comment: has default value
    # trigger_on_schedule: has default value
    # trigger_on_test_failure: has default value
    # updated_at: has default value
    # use_screenshots: nullable, has default value
    # web_urls: nullable, has default value

    # Optional fields
    blank_lines: int | None = Field(default=None)
    code_lines: int | None = Field(default=None)
    comment_lines: int | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    created_by: str | None = Field(default=None)
    file_count: int | None = Field(default=None)
    file_paths: list | None = Field(default=None)
    local_port: int | None = Field(default=None)
    owner_id: int | None = Field(default=None)
    production_url: str | None = Field(default=None)
    repo_id: int | None = Field(default=None)
    repo_name: str | None = Field(default=None)
    repo_rules: str | None = Field(default=None)
    schedule_day_of_week: str | None = Field(default=None)
    schedule_execution_count: int | None = Field(default=None)
    schedule_frequency: str | None = Field(default=None)
    schedule_include_weekends: bool | None = Field(default=None)
    schedule_interval_minutes: int | None = Field(default=None)
    schedule_minute: int | None = Field(default=None)
    schedule_time: datetime.time | None = Field(default=None)
    startup_commands: list | None = Field(default=None)
    structured_rules: dict | Json | None = Field(default=None)
    target_branch: str | None = Field(default=None)
    trigger_on_commit: bool | None = Field(default=None)
    trigger_on_merged: bool | None = Field(default=None)
    trigger_on_pr_change: bool | None = Field(default=None)
    trigger_on_review_comment: bool | None = Field(default=None)
    trigger_on_schedule: bool | None = Field(default=None)
    trigger_on_test_failure: bool | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: str | None = Field(default=None)
    use_screenshots: bool | None = Field(default=None)
    web_urls: list | None = Field(default=None)


class UsageUpdate(CustomModelUpdate):
    """Usage Update Schema."""

    # Primary Keys
    id: int | None = Field(default=None)

    # Field properties:
    # created_at: has default value
    # created_by: nullable
    # is_completed: has default value
    # is_merged: has default value
    # is_test_passed: has default value
    # issue_number: has default value
    # owner_id: has default value
    # owner_name: has default value
    # owner_type: has default value
    # pr_number: nullable
    # repo_id: has default value
    # repo_name: has default value
    # retry_workflow_id_hash_pairs: nullable
    # source: has default value
    # token_input: nullable
    # token_output: nullable
    # total_seconds: nullable
    # trigger: has default value

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    created_by: str | None = Field(default=None)
    installation_id: int | None = Field(default=None)
    is_completed: bool | None = Field(default=None)
    is_merged: bool | None = Field(default=None)
    is_test_passed: bool | None = Field(default=None)
    issue_number: int | None = Field(default=None)
    owner_id: int | None = Field(default=None)
    owner_name: str | None = Field(default=None)
    owner_type: str | None = Field(default=None)
    pr_number: int | None = Field(default=None)
    repo_id: int | None = Field(default=None)
    repo_name: str | None = Field(default=None)
    retry_workflow_id_hash_pairs: list | None = Field(default=None)
    source: str | None = Field(default=None)
    token_input: int | None = Field(default=None)
    token_output: int | None = Field(default=None)
    total_seconds: int | None = Field(default=None)
    trigger: str | None = Field(default=None)
    user_id: int | None = Field(default=None)


class UsageWithIssuesUpdate(CustomModelUpdate):
    """UsageWithIssues Update Schema."""

    # Field properties:
    # created_at: nullable
    # created_by: nullable
    # id: nullable
    # installation_id: nullable
    # is_completed: nullable
    # issue_number: nullable
    # merged: nullable
    # owner_id: nullable
    # owner_name: nullable
    # owner_type: nullable
    # repo_id: nullable
    # repo_name: nullable
    # source: nullable
    # token_input: nullable
    # token_output: nullable
    # total_seconds: nullable
    # user_id: nullable

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    created_by: str | None = Field(default=None)
    id: int | None = Field(default=None)
    installation_id: int | None = Field(default=None)
    is_completed: bool | None = Field(default=None)
    issue_number: int | None = Field(default=None)
    merged: bool | None = Field(default=None)
    owner_id: int | None = Field(default=None)
    owner_name: str | None = Field(default=None)
    owner_type: str | None = Field(default=None)
    repo_id: int | None = Field(default=None)
    repo_name: str | None = Field(default=None)
    source: str | None = Field(default=None)
    token_input: int | None = Field(default=None)
    token_output: int | None = Field(default=None)
    total_seconds: int | None = Field(default=None)
    user_id: int | None = Field(default=None)


class UsersUpdate(CustomModelUpdate):
    """Users Update Schema."""

    # Primary Keys
    id: int | None = Field(default=None)

    # Field properties:
    # created_at: has default value
    # created_by: nullable
    # email: nullable
    # user_rules: has default value

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    created_by: str | None = Field(default=None)
    email: str | None = Field(default=None)
    user_id: int | None = Field(default=None)
    user_name: str | None = Field(default=None)
    user_rules: str | None = Field(default=None)


# OPERATIONAL CLASSES


class CircleciTokens(CircleciTokensBaseSchema):
    """CircleciTokens Schema for Pydantic.

    Inherits from CircleciTokensBaseSchema. Add any customization here.
    """

    pass


class Contacts(ContactsBaseSchema):
    """Contacts Schema for Pydantic.

    Inherits from ContactsBaseSchema. Add any customization here.
    """

    pass


class Coverages(CoveragesBaseSchema):
    """Coverages Schema for Pydantic.

    Inherits from CoveragesBaseSchema. Add any customization here.
    """

    # Foreign Keys
    owners: Owners | None = Field(default=None)


class Credits(CreditsBaseSchema):
    """Credits Schema for Pydantic.

    Inherits from CreditsBaseSchema. Add any customization here.
    """

    # Foreign Keys
    owners: Owners | None = Field(default=None)
    usage: Usage | None = Field(default=None)


class Installations(InstallationsBaseSchema):
    """Installations Schema for Pydantic.

    Inherits from InstallationsBaseSchema. Add any customization here.
    """

    # Foreign Keys
    owners: Owners | None = Field(default=None)
    issues: Issues | None = Field(default=None)


class Issues(IssuesBaseSchema):
    """Issues Schema for Pydantic.

    Inherits from IssuesBaseSchema. Add any customization here.
    """

    # Foreign Keys
    installations: Installations | None = Field(default=None)


class JiraGithubLinks(JiraGithubLinksBaseSchema):
    """JiraGithubLinks Schema for Pydantic.

    Inherits from JiraGithubLinksBaseSchema. Add any customization here.
    """

    pass


class OauthTokens(OauthTokensBaseSchema):
    """OauthTokens Schema for Pydantic.

    Inherits from OauthTokensBaseSchema. Add any customization here.
    """

    pass


class Owners(OwnersBaseSchema):
    """Owners Schema for Pydantic.

    Inherits from OwnersBaseSchema. Add any customization here.
    """

    # Foreign Keys
    coverages: Coverages | None = Field(default=None)
    credits: Credits | None = Field(default=None)
    installations: Installations | None = Field(default=None)
    repositories: Repositories | None = Field(default=None)


class RepoCoverage(RepoCoverageBaseSchema):
    """RepoCoverage Schema for Pydantic.

    Inherits from RepoCoverageBaseSchema. Add any customization here.
    """

    pass


class Repositories(RepositoriesBaseSchema):
    """Repositories Schema for Pydantic.

    Inherits from RepositoriesBaseSchema. Add any customization here.
    """

    # Foreign Keys
    owners: Owners | None = Field(default=None)


class Usage(UsageBaseSchema):
    """Usage Schema for Pydantic.

    Inherits from UsageBaseSchema. Add any customization here.
    """

    # Foreign Keys
    credits: list[Credits] | None = Field(default=None)


class UsageWithIssues(UsageWithIssuesBaseSchema):
    """UsageWithIssues Schema for Pydantic.

    Inherits from UsageWithIssuesBaseSchema. Add any customization here.
    """

    pass


class Users(UsersBaseSchema):
    """Users Schema for Pydantic.

    Inherits from UsersBaseSchema. Add any customization here.
    """

    pass
