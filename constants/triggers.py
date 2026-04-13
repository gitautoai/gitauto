from typing import Literal, Union

from utils.prompts.write_pr_body_update import WRITE_PR_BODY_UPDATE

NewPrTrigger = Literal["dashboard", "schedule"]

ReviewTrigger = Literal["pr_comment", "pr_file_review", "pr_review"]

Trigger = Union[
    Literal[
        "check_suite_completed",
        "cleanup_stale_repos",
        "installation",
        "installation_repositories",
        "pr_merged",
        "push",
        "retarget",
        "setup",
        "test_failure",
        "workflow_run_completed",
    ],
    NewPrTrigger,
    ReviewTrigger,
]

TRIGGER_TO_MARKER: dict[str, str] = {
    "dashboard": "GITAUTO_UPDATE",
    "schedule": "GITAUTO_UPDATE",
    "check_suite_completed": "GITAUTO_FAILURE_FIX",
    "test_failure": "GITAUTO_FAILURE_FIX",
    "pr_comment": "GITAUTO_REVIEW_FIX",
    "pr_file_review": "GITAUTO_REVIEW_FIX",
    "pr_review": "GITAUTO_REVIEW_FIX",
}

TRIGGER_TO_PROMPT: dict[str, str] = {
    "dashboard": WRITE_PR_BODY_UPDATE,
    "schedule": WRITE_PR_BODY_UPDATE,
}
