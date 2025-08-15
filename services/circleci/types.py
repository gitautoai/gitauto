"""Type definitions for CircleCI API responses."""

from typing import Optional, Any
from typing_extensions import TypedDict


class CircleCIWorkflowJob(TypedDict):
    """A job within a CircleCI workflow."""

    job_number: int
    stopped_at: Optional[str]
    started_at: Optional[str]
    name: str
    project_slug: str
    type: str
    requires: dict[str, Any]
    status: str  # "failed", "success", etc.
    id: str
    dependencies: list[Any]


class CircleCIWorkflowJobsData(TypedDict):
    """Response data from CircleCI workflow jobs API."""

    next_page_token: Optional[str]
    items: list[CircleCIWorkflowJob]


class CircleCIBuildAction(TypedDict):
    """CircleCI build action from v1.1 API."""

    index: int
    step: int
    allocation_id: str
    name: str
    type: str
    start_time: Optional[str]
    end_time: Optional[str]
    exit_code: Optional[int]
    run_time_millis: int
    output_url: Optional[str]
    status: str
    failed: Optional[bool]
    infrastructure_fail: Optional[bool]
    timedout: Optional[bool]
    canceled: Optional[bool]
    bash_command: Optional[str]
    background: bool
    parallel: bool
    has_output: bool
    truncated: bool


class CircleCIBuildStep(TypedDict):
    """CircleCI build step from v1.1 API."""

    name: str
    actions: list[CircleCIBuildAction]


class CircleCIBuildData(TypedDict):
    """CircleCI build data from v1.1 API."""

    build_num: int
    build_url: str
    status: str
    failed: bool
    infrastructure_fail: bool
    timedout: bool
    canceled: bool
    branch: str
    author_name: str
    author_email: str
    subject: str
    body: str
    start_time: Optional[str]
    stop_time: Optional[str]
    build_time_millis: int
    steps: list[CircleCIBuildStep]
    vcs_revision: str
    vcs_url: str
    reponame: str


class CircleCILogEntry(TypedDict):
    """CircleCI log entry from output URL."""

    message: str
    time: str
    type: str
    truncated: bool
