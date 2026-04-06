from typing import Literal, Union

ReviewTrigger = Literal["pr_comment", "pr_file_review", "pr_review"]

Trigger = Union[
    Literal[
        "check_suite_completed",
        "cleanup_stale_repos",
        "dashboard",
        "installation",
        "installation_repositories",
        "pr_merged",
        "push",
        "schedule",
        "setup",
        "test_failure",
        "workflow_run_completed",
    ],
    ReviewTrigger,
]
