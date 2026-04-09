from json import dumps

from constants.triggers import TRIGGER_TO_MARKER, TRIGGER_TO_PROMPT, Trigger
from services.github.pulls.update_pull_request_body import update_pull_request_body
from services.github.pulls.upsert_pr_body_section import upsert_pr_body_section
from services.openai.chat import chat_with_ai
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def generate_and_upsert_pr_body_section(
    owner_name: str,
    repo_name: str,
    pr_number: int,
    token: str,
    current_body: str,
    trigger: Trigger,
    context: dict,
):
    marker = TRIGGER_TO_MARKER.get(trigger)
    prompt = TRIGGER_TO_PROMPT.get(trigger)
    if not marker or not prompt:
        logger.warning("No PR body config mapped for trigger '%s', skipping", trigger)
        return None

    logger.info(
        "Generating %s section content for %s/%s#%d",
        marker,
        owner_name,
        repo_name,
        pr_number,
    )
    generated_content = chat_with_ai(system_input=prompt, user_input=dumps(context))
    if not generated_content:
        logger.warning("LLM returned empty content for %s section", marker)
        return None

    new_body = upsert_pr_body_section(
        current_body=current_body, marker=marker, content=generated_content
    )
    update_pull_request_body(
        owner_name=owner_name,
        repo_name=repo_name,
        pr_number=pr_number,
        token=token,
        body=new_body,
    )
    return generated_content
