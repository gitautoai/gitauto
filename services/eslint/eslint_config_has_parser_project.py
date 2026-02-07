import json

from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=False, raise_on_error=False)
def eslint_config_has_parser_project(eslint_config: dict[str, str]):
    content = eslint_config.get("content", "")
    if not content:
        logger.info("ESLint config has no content, skipping parser project check")
        return False

    # Try JSON parsing first (ESLint JSON configs are always top-level objects)
    try:
        parsed = json.loads(content)
        if not isinstance(parsed, dict):
            logger.info("ESLint config parsed to non-dict type, skipping")
            return False

        parser_options = parsed.get("parserOptions", {})
        if isinstance(parser_options, dict) and parser_options.get("project"):
            logger.info(
                "ESLint config has parserOptions.project: %s",
                parser_options.get("project"),
            )
            return True

        for override in parsed.get("overrides", []):
            if not isinstance(override, dict):
                continue

            override_parser_options = override.get("parserOptions", {})
            if isinstance(
                override_parser_options, dict
            ) and override_parser_options.get("project"):
                logger.info(
                    "ESLint config override has parserOptions.project: %s",
                    override_parser_options.get("project"),
                )
                return True

        return False

    except (json.JSONDecodeError, ValueError):
        logger.info("ESLint config is not valid JSON, falling back to heuristic")

    # Heuristic for non-JSON configs (JS, YAML, etc.)
    has_project = "parserOptions" in content and "project" in content
    logger.info(
        "ESLint config heuristic check for parserOptions.project: %s", has_project
    )
    return has_project
