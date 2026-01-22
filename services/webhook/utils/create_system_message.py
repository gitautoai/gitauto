from typing import Any, cast

# Third party imports
from schemas.supabase.types import Repositories

# Local imports
from services.supabase.usage.insert_usage import Trigger
from utils.error.handle_exceptions import handle_exceptions
from utils.files.read_xml_file import read_xml_file
from utils.logging.logging_config import logger
from utils.prompts.get_trigger_prompt import get_trigger_prompt


@handle_exceptions(default_return_value="", raise_on_error=False)
def create_system_message(
    trigger: Trigger,
    repo_settings: Repositories | None = None,
):
    content_parts = []

    # Add trigger instruction
    trigger_content = get_trigger_prompt(trigger)
    if trigger_content:
        content_parts.append(trigger_content)
        logger.info("Trigger prompt: %s", trigger_content)

    # Add coding standards
    content_parts.append(read_xml_file("utils/prompts/coding_standards.xml"))

    # Repository rules
    if repo_settings:
        structured_rules = cast(dict[str, Any], repo_settings.get("structured_rules"))
        if structured_rules:
            structured_content = "\n".join(
                f"{k}: {v}" for k, v in structured_rules.items()
            )
            content_parts.append(
                f"<structured_repository_rules>\n{structured_content}\n</structured_repository_rules>"
            )
            logger.info("Structured rules: %s", structured_content)

        free_rules = cast(str | None, repo_settings.get("repo_rules"))
        if free_rules and free_rules.strip():
            content_parts.append(
                f"<freeform_repository_rules>\n{free_rules.strip()}\n</freeform_repository_rules>"
            )
            logger.info("Freeform rules: %s", free_rules.strip())

    combined_content = "\n\n".join(content_parts) if content_parts else ""
    return combined_content
