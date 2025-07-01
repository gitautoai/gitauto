import json
from typing import Any, cast, Literal

# Third party imports
from schemas.supabase.fastapi.schema_public_latest import Repositories

# Local imports
from services.supabase.usage.insert_usage import Trigger
from utils.error.handle_exceptions import handle_exceptions

# Local imports (Mode Prompts)
from utils.prompts.modes.commit_changes import COMMIT_CHANGES_MODE
from utils.prompts.modes.explore_repo import EXPLORE_REPO_MODE
from utils.prompts.modes.search_google import SEARCH_GOOGLE_MODE
from utils.prompts.modes.update_comment import UPDATE_COMMENT_MODE

# Local imports (Trigger Prompts)
from utils.prompts.triggers.check_run import CHECK_RUN_TRIGGER
from utils.prompts.triggers.issue import ISSUE_TRIGGER
from utils.prompts.triggers.pr_checkbox import PR_CHECKBOX_TRIGGER
from utils.prompts.triggers.pr_merge import PR_MERGE_TRIGGER
from utils.prompts.triggers.review import REVIEW_TRIGGER

# Local imports (Utils)
from utils.text.xml_wrapper import wrap_xml


@handle_exceptions(default_return_value="", raise_on_error=False)
def create_system_message(
    trigger: Trigger,
    mode: Literal["comment", "commit", "explore", "get", "search"],
    repo_settings: Repositories | None = None,
):
    content_parts = []

    # Trigger mapping
    trigger_map = {
        "issue_comment": ISSUE_TRIGGER,
        "issue_label": ISSUE_TRIGGER,
        "test_failure": CHECK_RUN_TRIGGER,
        "review_comment": REVIEW_TRIGGER,
        "pr_checkbox": PR_CHECKBOX_TRIGGER,
        "pr_merge": PR_MERGE_TRIGGER,
    }

    # Mode mapping
    mode_map = {
        "comment": UPDATE_COMMENT_MODE,
        "commit": COMMIT_CHANGES_MODE,
        "explore": EXPLORE_REPO_MODE,
        "get": EXPLORE_REPO_MODE,
        "search": SEARCH_GOOGLE_MODE,
    }

    # Add trigger instruction
    if trigger in trigger_map:
        content_parts.append(wrap_xml("trigger_instruction", trigger_map[trigger]))

    # Add mode instruction
    if mode in mode_map:
        content_parts.append(wrap_xml("mode_instruction", mode_map[mode]))

    # Add repository rules if available
    if repo_settings:
        # Add structured rules
        structured_rules = cast(dict[str, Any], repo_settings.get("structured_rules"))
        if structured_rules:
            structured_content = "\n".join(
                f"{k}: {v}" for k, v in structured_rules.items()
            )
            content_parts.append(
                wrap_xml("structured_repository_rules", structured_content)
            )

        # Add free-format repository rules
        free_rules = cast(str | None, repo_settings.get("repo_rules"))
        if free_rules and free_rules.strip():
            content_parts.append(
                wrap_xml("freeform_repository_rules", free_rules.strip())
            )

    combined_content = "\n\n".join(content_parts) if content_parts else ""

    print(f"\nSystem content:\n{json.dumps(combined_content, indent=2)}")
    return combined_content
