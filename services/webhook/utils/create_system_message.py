from typing import Any, cast, Literal

# Third party imports
from schemas.supabase.types import Repositories

# Local imports
from services.supabase.usage.insert_usage import Trigger
from utils.error.handle_exceptions import handle_exceptions
from utils.prompts.get_trigger_prompt import get_trigger_prompt
from utils.prompts.get_mode_prompt import get_mode_prompt
from utils.files.read_xml_file import read_xml_file


@handle_exceptions(default_return_value="", raise_on_error=False)
def create_system_message(
    trigger: Trigger,
    mode: Literal["comment", "commit", "explore", "get", "search"],
    repo_settings: Repositories | None = None,
):
    content_parts = []

    # Add trigger instruction
    trigger_content = get_trigger_prompt(trigger)
    if trigger_content:
        content_parts.append(trigger_content)

    # Add mode instruction
    mode_content = get_mode_prompt(mode)
    if mode_content:
        content_parts.append(mode_content)

    # Add quality rules only for commit mode
    if mode == "commit":
        content_parts.append(read_xml_file("utils/prompts/commit_quality_rules.xml"))

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

        free_rules = cast(str | None, repo_settings.get("repo_rules"))
        if free_rules and free_rules.strip():
            content_parts.append(
                f"<freeform_repository_rules>\n{free_rules.strip()}\n</freeform_repository_rules>"
            )

    combined_content = "\n\n".join(content_parts) if content_parts else ""
    return combined_content
