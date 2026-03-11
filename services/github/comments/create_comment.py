import requests
from anthropic.types import ToolUnionParam

from config import GITHUB_API_URL, TIMEOUT
from services.github.utils.create_headers import create_headers
from services.types.base_args import BaseArgs
from utils.error.handle_exceptions import handle_exceptions

# See https://docs.anthropic.com/en/docs/build-with-claude/tool-use#defining-tools
CREATE_COMMENT: ToolUnionParam = {
    "name": "create_comment",
    "description": "Creates a note/notification on the GitHub pull request. The user is not there - they will see it later. After commenting, continue working on what you CAN do. WHEN TO USE: To inform the user about something they need to know (e.g., you are restricted to test files but the fix requires source file changes, or secrets need to be added via GitHub UI). WHEN NOT TO USE: Status updates, progress reports, or asking questions. WHAT TO SAY: State the fact briefly - what you found and what the user needs to do later. Do not ask questions.",
    "input_schema": {
        "type": "object",
        "properties": {
            "body": {
                "type": "string",
                "description": "The comment text to post.",
            },
        },
        "required": ["body"],
        "additionalProperties": False,
    },
    "strict": True,
}


@handle_exceptions(default_return_value=None, raise_on_error=False)
def create_comment(body: str, base_args: BaseArgs, **_kwargs):
    # https://docs.github.com/en/rest/issues/comments?apiVersion=2022-11-28#create-an-issue-comment
    # PRs are issues in GitHub's data model, so this works for both issues and PRs.
    owner = base_args["owner"]
    repo = base_args["repo"]
    token = base_args["token"]
    number = base_args["pr_number"]

    response = requests.post(
        url=f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues/{number}/comments",
        headers=create_headers(token=token),
        json={"body": body},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    url: str = response.json()["url"]
    return url
