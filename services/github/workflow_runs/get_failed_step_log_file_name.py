# Third-party libraries
from requests import get

# Internal libraries
from config import GITHUB_API_URL, TIMEOUT
from services.github.utils.create_headers import create_headers


def get_failed_step_log_file_name(owner: str, repo: str, run_id: int, token: str):
    """No official API documents"""
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/actions/runs/{run_id}/jobs"
    headers = create_headers(token=token)
    response = get(url=url, headers=headers, timeout=TIMEOUT)
    if response.status_code == 404 and "Not Found" in response.text:
        return response.status_code
    response.raise_for_status()
    data = response.json()

    # Get the first failed step name
    for job in data.get("jobs", []):
        job_name = job.get("name", "unknown_job")
        for step in job.get("steps", []):
            if step.get("conclusion") == "failure":
                step_number = step.get("number")
                step_name = step.get("name")
                return f"{job_name}/{step_number}_{step_name}.txt"

    # Return None if no failed step is found
    return None
