import json
import re

import jsonc

from services.git.write_and_commit_file import write_and_commit_file
from services.github.files.get_raw_content import get_raw_content
from services.types.base_args import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

TSCONFIG_TEST_PATH = "tsconfig.test.json"
TSCONFIG_VARIANT_PATTERN = re.compile(r"^tsconfig\..+\.json$")

REQUIRED_OPTIONS = {"noUnusedLocals": False, "noUnusedParameters": False}


@handle_exceptions(default_return_value=(None, None), raise_on_error=False)
def ensure_tsconfig_relaxed_for_tests(root_files: list[str], base_args: BaseArgs):
    """
    Ensure a tsconfig variant exists with relaxed settings for test files.
    Checks all tsconfig.*.json files first. Only creates tsconfig.test.json if none have correct settings.
    Returns (path, status) where status is 'added', 'modified', or None if no changes were made.
    """
    owner = base_args["owner"]
    repo = base_args["repo"]
    token = base_args["token"]
    new_branch = base_args["new_branch"]

    if "tsconfig.json" not in root_files:
        logger.debug("Not a TypeScript repo, skipping")
        return None, None

    logger.info("Ensuring tsconfig has relaxed settings for test files")
    variant_files = [f for f in root_files if TSCONFIG_VARIANT_PATTERN.match(f)]

    if not variant_files:
        logger.info("No tsconfig.*.json files found, adding %s", TSCONFIG_TEST_PATH)
        default_config = {
            "extends": "./tsconfig.json",
            "compilerOptions": REQUIRED_OPTIONS,
        }
        content = json.dumps(default_config, indent=2)
        result = write_and_commit_file(
            file_content=content,
            file_path=TSCONFIG_TEST_PATH,
            base_args=base_args,
            commit_message=f"Add {TSCONFIG_TEST_PATH} with relaxed settings",
        )
        if result.success:
            logger.info("Added %s", TSCONFIG_TEST_PATH)
            return TSCONFIG_TEST_PATH, "added"

        logger.warning("Failed to add %s: %s", TSCONFIG_TEST_PATH, result.message)
        return TSCONFIG_TEST_PATH, None

    logger.info("Found %d tsconfig.*.json files: %s", len(variant_files), variant_files)

    for variant_path in variant_files:
        logger.info("Checking %s for relaxed settings", variant_path)
        content = get_raw_content(
            owner=owner, repo=repo, file_path=variant_path, ref=new_branch, token=token
        )
        if not content:
            logger.warning("Could not fetch content for %s", variant_path)
            continue

        try:
            config: dict = jsonc.loads(content)
            raw_opts = config.get("compilerOptions")
            compiler_opts = raw_opts if isinstance(raw_opts, dict) else {}
            if all(compiler_opts.get(k) == v for k, v in REQUIRED_OPTIONS.items()):
                logger.info("%s has all required relaxed settings", variant_path)
                return variant_path, None

            logger.info("%s missing relaxed settings, modifying", variant_path)
            config.setdefault("compilerOptions", {})
            for key, value in REQUIRED_OPTIONS.items():
                config["compilerOptions"][key] = value

            updated_content = json.dumps(config, indent=2)
            result = write_and_commit_file(
                file_content=updated_content,
                file_path=variant_path,
                base_args=base_args,
                commit_message=f"Modify {variant_path} with relaxed settings",
            )
            if result.success:
                logger.info("Modified %s", variant_path)
                return variant_path, "modified"

            logger.warning("Failed to modify %s: %s", variant_path, result.message)
            return variant_path, None

        except json.JSONDecodeError as e:
            logger.warning("Invalid JSON in %s: %s, skipping", variant_path, e)
            continue

    return None, None
