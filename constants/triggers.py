from typing import Literal, Union

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
        "setup",
        "test_failure",
        "workflow_run_completed",
    ],
    NewPrTrigger,
    ReviewTrigger,
]
