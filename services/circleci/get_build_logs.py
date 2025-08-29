# Third-party libraries
from requests import get

# Internal libraries
from config import TIMEOUT
from services.circleci.circleci_types import CircleCIBuildData, CircleCILogEntry
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(raise_on_error=True)
def get_circleci_build_logs(project_slug: str, build_number: int, circle_token: str):
    """https://circleci.com/docs/api/v1/index.html#single-build"""
    # Use v1.1 API because v2 doesn't provide step outputs
    base_url = "https://circleci.com/api/v1.1"

    # Build the URL for v1.1 API
    # Format: /project/:vcs-type/:username/:project/:build_num
    url = f"{base_url}/project/{project_slug}/{build_number}"
    headers = {"Circle-Token": circle_token}

    # Get build details using v1.1 API
    response = get(url=url, headers=headers, timeout=TIMEOUT)
    if response.status_code == 404:
        return 404
    if response.status_code == 401:
        return "CircleCI authentication failed. Please check your token."
    response.raise_for_status()

    build_data: CircleCIBuildData = response.json()

    # Check if build failed
    if build_data.get("status") not in ["failed", "infrastructure_fail", "timedout"]:
        return None  # Build didn't fail, no error logs to retrieve

    # Extract failed steps and their logs
    logs_content = []
    steps = build_data.get("steps", [])

    for step in steps:
        step_name = step.get("name", "Unknown Step")
        actions = step.get("actions", [])

        for action in actions:
            # Check if this action failed
            if action.get("status") not in [
                "failed",
                "infrastructure_fail",
                "timedout",
            ]:
                continue

            # Get the output URL for this action
            output_url = action.get("output_url")
            if not output_url:
                continue

            # Fetch the actual log output
            log_response = get(url=output_url, headers=headers, timeout=TIMEOUT)
            if log_response.status_code != 200:
                continue

            # Parse the log data - CircleCI returns a list of log entries
            log_data: list[CircleCILogEntry] = log_response.json()

            # Format the log content similar to GitHub Actions
            formatted_log = f"```CircleCI Build Log: {step_name}\n"

            # CircleCI log data is a list of dictionaries with message, time, type fields
            if isinstance(log_data, list):
                for entry in log_data:
                    if isinstance(entry, dict):
                        message = entry.get("message", "")
                        # Remove carriage returns and clean up the message
                        clean_message = message.replace("\r\n", "\n").replace(
                            "\r", "\n"
                        )
                        formatted_log += clean_message
                    else:
                        formatted_log += str(entry) + "\n"
            else:
                formatted_log += str(log_data)

            formatted_log += "\n```"
            logs_content.append(formatted_log)

            # Only get the first failed action per step
            break

    return (
        "\n\n".join(logs_content)
        if logs_content
        else "No error logs found in CircleCI build."
    )
