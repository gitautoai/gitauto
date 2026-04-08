# Standard imports
import json

# Local imports
from constants.claude import MAX_OUTPUT_TOKENS
from services.claude.client import claude
from services.model_selection import get_model
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger
from utils.prompts.quality_check import QUALITY_CHECK_SYSTEM_PROMPT


@handle_exceptions(default_return_value=None, raise_on_error=False)
def evaluate_quality_checks(
    source_content: str,
    source_path: str,
    test_files: list[tuple[str, str]],
):
    """test_files: list of (path, content) tuples for all test files covering this source."""
    if not source_content:
        logger.info("Empty source content for %s", source_path)
        return None

    user_message = f"## Source file: {source_path}\n\n```\n{source_content}\n```"
    if test_files:
        for path, content in test_files:
            user_message += f"\n\n## Test file: {path}\n\n```\n{content}\n```"
    else:
        user_message += "\n\n## Test file: No test file exists for this source file."

    # Attempted structured output (output_format JSON schema) but got 400:
    # "The compiled grammar is too large" (8 categories x 41 checks x {status, reason}).
    # Fallback: prompt-guided JSON with regular messages.create.
    model = get_model()
    response = claude.messages.create(
        model=model,
        max_tokens=MAX_OUTPUT_TOKENS[model],
        temperature=0,
        system=QUALITY_CHECK_SYSTEM_PROMPT
        + "\n\nRespond with ONLY the JSON object, no other text.",
        messages=[{"role": "user", "content": user_message}],
    )

    text_attr = getattr(response.content[0], "text", "")
    if not isinstance(text_attr, str):
        logger.error("Expected str but got %s: %s", type(text_attr), text_attr)
        return None

    # Strip markdown code fences if present
    text = text_attr.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3].strip()

    result: dict[str, dict[str, dict[str, str]]] = json.loads(text)
    logger.info(
        "Quality checks for %s: %s categories evaluated", source_path, len(result)
    )
    return result
