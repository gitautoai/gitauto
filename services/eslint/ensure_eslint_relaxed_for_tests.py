import json

import jsonc

from services.git.replace_remote_file import replace_remote_file_content
from services.github.types.github_types import BaseArgs
from utils.files.read_local_file import read_local_file
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

TEST_FILE_GLOBS = ["**/*.test.*", "**/*.spec.*", "**/__tests__/**"]

RELAXED_RULES = {"@typescript-eslint/no-explicit-any": "off"}


@handle_exceptions(default_return_value=None, raise_on_error=False)
def ensure_eslint_relaxed_for_tests(eslint_config: dict[str, str], base_args: BaseArgs):
    """
    Ensure the ESLint config has relaxed rules for test files.
    Similar to ensure_tsconfig_relaxed_for_tests which relaxes TSC options.
    Adds an overrides section for test files that disables rules like no-explicit-any.
    Returns 'modified' if the config was updated, None otherwise.
    """
    filename = eslint_config["filename"]
    content = eslint_config["content"]

    # Only handle JSON-based configs (.eslintrc, .eslintrc.json, package.json)
    # JS/YAML configs are too complex to safely modify programmatically
    is_legacy_json = filename in (".eslintrc", ".eslintrc.json")
    is_package_json = filename == "package.json"
    if not is_legacy_json and not is_package_json:
        logger.info(
            "ESLint config %s is not JSON-based, skipping test relaxation", filename
        )
        return None

    try:
        parsed = jsonc.loads(content)
    except (json.JSONDecodeError, ValueError):
        logger.warning("Could not parse ESLint config %s, skipping", filename)
        return None

    if not isinstance(parsed, dict):
        logger.warning(
            "ESLint config %s parsed to non-dict: %s, skipping", filename, parsed
        )
        return None

    # Check if an override for test files already exists with the relaxed rules
    existing_overrides = parsed.get("overrides", [])
    if not isinstance(existing_overrides, list):
        existing_overrides = []

    for override in existing_overrides:
        if not isinstance(override, dict):
            continue
        files = override.get("files", [])
        rules = override.get("rules", {})
        if not isinstance(files, list) or not isinstance(rules, dict):
            continue
        # Check if any test glob is already covered with no-explicit-any off
        has_test_glob = any(f in TEST_FILE_GLOBS for f in files)
        has_relaxed_any = rules.get("@typescript-eslint/no-explicit-any") in (
            "off",
            0,
        )
        if has_test_glob and has_relaxed_any:
            logger.info("ESLint config already has relaxed rules for test files")
            return None

    # Add override for test files
    test_override = {"files": TEST_FILE_GLOBS, "rules": RELAXED_RULES}
    overrides = parsed.setdefault("overrides", [])
    if not isinstance(overrides, list):
        logger.warning(
            "ESLint config %s has non-list overrides: %s, skipping", filename, overrides
        )
        return None
    overrides.append(test_override)

    updated_content = json.dumps(parsed, indent=2)

    # For package.json, wrap back in eslintConfig key
    if is_package_json:
        full_package = read_local_file("package.json", base_dir=base_args["clone_dir"])
        if full_package:
            try:
                pkg: dict = json.loads(full_package)
                pkg["eslintConfig"] = parsed
                updated_content = json.dumps(pkg, indent=2)
            except (json.JSONDecodeError, ValueError):
                logger.warning("Could not parse package.json for ESLint update")
                return None

    result = replace_remote_file_content(
        file_content=updated_content,
        file_path=filename,
        base_args=base_args,
        commit_message=f"Relax ESLint rules for test files in {filename}",
    )
    if result.success:
        logger.info("Modified %s with relaxed ESLint rules for test files", filename)
        return "modified"

    logger.warning("Failed to modify %s: %s", filename, result.message)
    return None
