import re

from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value="", raise_on_error=False)
def upsert_pr_body_section(current_body: str, marker: str, content: str):
    open_tag = f"<!-- {marker} -->"
    close_tag = f"<!-- /{marker} -->"
    section_block = f"{open_tag}\n{content}\n{close_tag}"

    # Try replacing existing section
    pattern = re.compile(re.escape(open_tag) + r".*?" + re.escape(close_tag), re.DOTALL)
    if pattern.search(current_body):
        logger.info("Replacing existing %s section in PR body", marker)
        return pattern.sub(section_block, current_body)

    # Append new section — add --- separator if no GA sections exist yet
    has_ga_section = "<!-- GITAUTO_" in current_body
    separator = "" if has_ga_section else "\n\n---\n\n"
    logger.info("Appending new %s section to PR body", marker)
    return current_body + separator + section_block + "\n"
