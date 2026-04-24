import json

# Third party imports
from schemas.supabase.types import Repositories

# Local imports
from constants.triggers import Trigger
from utils.error.handle_exceptions import handle_exceptions
from utils.files.read_local_file import read_local_file
from utils.files.read_xml_file import read_xml_file
from utils.logging.logging_config import logger
from utils.prompts.get_trigger_prompt import get_trigger_prompt
from utils.quality_checks.checklist import QUALITY_CHECKLIST


@handle_exceptions(default_return_value="", raise_on_error=False)
def create_system_message(
    trigger: Trigger,
    repo_settings: Repositories | None = None,
    clone_dir: str | None = None,
):
    content_parts = []

    # Add repo's preferred language (first, so it's a high-priority instruction)
    if repo_settings:
        logger.info("Repo settings provided, evaluating language preference")
        preferred_language = repo_settings.get("preferred_language")
        if preferred_language and preferred_language != "en":
            logger.info("Language preference: %s", preferred_language)
            content_parts.append(
                f"<user_language_preference>\nWrite all GitHub comments and code comments in {preferred_language} (ISO 639 language code).\n</user_language_preference>"
            )

    # Add trigger instruction
    trigger_content = get_trigger_prompt(trigger)
    if trigger_content:
        logger.info("Trigger prompt: %s", trigger_content)
        content_parts.append(trigger_content)

    # Add coding standards
    content_parts.append(read_xml_file("utils/prompts/coding_standards.xml"))

    # Add quality checklist so generated tests cover all quality categories
    checklist_json = json.dumps(QUALITY_CHECKLIST, indent=2)
    content_parts.append(
        f"<quality_checklist>\nWhen writing tests, ensure coverage of these quality categories where applicable to the file:\n{checklist_json}\n</quality_checklist>"
    )
    logger.info("Quality checklist injected (%d categories)", len(QUALITY_CHECKLIST))

    # Repository rules
    if repo_settings:
        logger.info("Evaluating repository rules from repo_settings")
        structured_rules = repo_settings.get("structured_rules")
        if structured_rules:
            logger.info("Structured rules present, formatting")
            structured_content = "\n".join(
                f"{k}: {v}" for k, v in structured_rules.items()
            )
            logger.info("Structured rules: %s", structured_content)
            content_parts.append(
                f"<structured_repository_rules>\n{structured_content}\n</structured_repository_rules>"
            )

        free_rules = repo_settings.get("repo_rules")
        if free_rules and free_rules.strip():
            logger.info("Freeform rules: %s", free_rules.strip())
            content_parts.append(
                f"<freeform_repository_rules>\n{free_rules.strip()}\n</freeform_repository_rules>"
            )

    # GITAUTO.md rules (highest priority - repo-specific learnings from feedback)
    if clone_dir:
        logger.info("Clone dir provided, loading GITAUTO.md if present")
        gitauto_md_content = read_local_file(file_path="GITAUTO.md", base_dir=clone_dir)
        if gitauto_md_content and gitauto_md_content.strip():
            logger.info(
                "GITAUTO.md rules loaded (%d chars)", len(gitauto_md_content.strip())
            )
            content_parts.append(
                f"<gitauto_md_rules>\n{gitauto_md_content.strip()}\n</gitauto_md_rules>"
            )

    combined_content = "\n\n".join(content_parts) if content_parts else ""
    logger.info("create_system_message returning %d chars", len(combined_content))
    return combined_content
