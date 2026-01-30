from utils.error.handle_exceptions import handle_exceptions

SETUP_PR_TITLE = "GitAuto setup"

SETUP_PR_BODY_TEMPLATE = """## Summary

This PR configures the repository for GitAuto.

## Changes

"""


@handle_exceptions(default_return_value="", raise_on_error=False)
def build_setup_pr_body(changes: list[str]):
    body = SETUP_PR_BODY_TEMPLATE
    for change in changes:
        body += f"- {change}\n"
    return body
