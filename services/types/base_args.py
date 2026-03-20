from typing import TypedDict
from typing_extensions import NotRequired

from schemas.supabase.types import OwnerType
from services.github.types.webhook.review_run_payload import ReviewSubjectType


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
    review_subject_type: ReviewSubjectType
    review_line: int
    review_side: str
    review_body: str
    review_comment: str
