from typing import TypedDict


class WorkflowRun(TypedDict):
    id: int
    name: str
    node_id: str
    head_branch: str
    head_sha: str
    path: str
    display_title: str
    run_number: int
    event: str
    status: str
    conclusion: str | None
    workflow_id: int
    check_suite_id: int
    check_suite_node_id: str
    url: str
    html_url: str
    created_at: str
    updated_at: str
    actor: dict
    run_attempt: int
    referenced_workflows: list
    run_started_at: str
    triggering_actor: dict
    jobs_url: str
    logs_url: str
    check_suite_url: str
    artifacts_url: str
    cancel_url: str
    rerun_url: str
    previous_attempt_url: str | None
    workflow_url: str
    head_commit: dict
    repository: dict
    head_repository: dict
