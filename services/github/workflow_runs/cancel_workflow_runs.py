from services.github.workflow_runs.cancel_workflow_run import cancel_workflow_run
from services.github.workflow_runs.get_workflow_runs import get_workflow_runs
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def cancel_workflow_runs(
    owner: str,
    repo: str,
    token: str,
    commit_sha: str | None = None,
    branch: str | None = None,
):
    """https://docs.github.com/en/rest/actions/workflow-runs#list-workflow-runs-for-a-repository"""
    workflow_runs = get_workflow_runs(
        owner=owner, repo=repo, token=token, commit_sha=commit_sha, branch=branch
    )
    statuses_to_cancel = ["queued", "in_progress", "pending", "waiting", "requested"]

    for run in workflow_runs:
        run_id = run["id"]
        run_status = run["status"]

        if run_status in statuses_to_cancel:
            cancel_workflow_run(owner=owner, repo=repo, run_id=run_id, token=token)
