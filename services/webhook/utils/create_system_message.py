from typing import Any, cast

# Third party imports
from schemas.supabase.types import Repositories

# Local imports
from constants.triggers import Trigger
from utils.error.handle_exceptions import handle_exceptions
from utils.files.read_local_file import read_local_file
from utils.files.read_xml_file import read_xml_file
from utils.logging.logging_config import logger
from utils.prompts.get_trigger_prompt import get_trigger_prompt


@handle_exceptions(default_return_value="", raise_on_error=False)
def create_system_message(
    trigger: Trigger,
    repo_settings: Repositories | None = None,
    clone_dir: str | None = None,
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

    # GITAUTO.md rules (highest priority - repo-specific learnings from feedback)
    if clone_dir:
        gitauto_md_content = read_local_file(file_path="GITAUTO.md", base_dir=clone_dir)
        if gitauto_md_content and gitauto_md_content.strip():
            content_parts.append(
                f"<gitauto_md_rules>\n{gitauto_md_content.strip()}\n</gitauto_md_rules>"
            )
            logger.info(
                "GITAUTO.md rules loaded (%d chars)", len(gitauto_md_content.strip())
            )

    combined_content = "\n\n".join(content_parts) if content_parts else ""
    return combined_content
