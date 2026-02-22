from typing import Literal, Union

ReviewTrigger = Literal["review_comment"]

Trigger = Union[
    Literal[
        "check_suite_completed",
        "cleanup_stale_repos",
        "clone_and_install",
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
