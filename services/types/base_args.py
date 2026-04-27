from typing import Literal, TypedDict
from typing_extensions import NotRequired

from constants.models import ModelId
from constants.triggers import Trigger
from schemas.supabase.types import OwnerType
from services.github.types.webhook.review_run_payload import ReviewSubjectType


# Git platform discriminator. Adding a new platform = add to this union and create `services/<platform>/` mirroring the GitHub/ADO shape (token, pull_requests, comments, …).
Platform = Literal["github", "azure_devops"]


# Minimal subset of BaseArgs needed by comment helpers (create_comment, update_comment, delete_comments_by_identifiers). BaseArgs is a structural superset, so callers with a full BaseArgs satisfy this too.
class CommentArgs(TypedDict):
    platform: Platform
    owner: str
    repo: str
    token: str
    pr_number: int


class BaseArgs(TypedDict):
    # Required fields
    platform: Platform
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
    model_id: ModelId
    verify_consecutive_failures: int
    quality_gate_fail_count: int
    usage_id: int

    # Optional fields
    check_run_name: NotRequired[str]
    comment_url: NotRequired[str | None]
    latest_commit_sha: NotRequired[str]
    workflow_id: NotRequired[str | int]
    baseline_tsc_errors: NotRequired[set[str]]
    trigger: NotRequired[Trigger]
    impl_file_to_collect_coverage_from: NotRequired[str]
    test_file_paths: NotRequired[list[str]]
    review_id: NotRequired[int]
    skip_ci: NotRequired[bool]
    last_quality_error: NotRequired[str]
    slack_thread_ts: NotRequired[str | None]


class ReviewBaseArgs(BaseArgs):
    pr_url: str
    pr_file_url: str
    review_path: str
    review_subject_type: ReviewSubjectType
    review_line: int
    review_side: str
    review_body: str
    review_comment: str
