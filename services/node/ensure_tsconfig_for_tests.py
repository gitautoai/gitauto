import json
import re

import jsonc

from services.github.commits.replace_remote_file import replace_remote_file_content
from services.github.files.get_raw_content import get_raw_content
from services.github.trees.get_file_tree import get_file_tree
from services.github.types.github_types import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

TSCONFIG_TEST_PATH = "tsconfig.test.json"
TSCONFIG_VARIANT_PATTERN = re.compile(r"^tsconfig\..+\.json$")

REQUIRED_OPTIONS = {"noUnusedLocals": False, "noUnusedParameters": False}


@handle_exceptions(default_return_value=None, raise_on_error=False)
def ensure_tsconfig_for_tests(base_args: BaseArgs, commit_message: str):
    """
    Ensure a tsconfig variant exists with relaxed settings for test files.
    Checks all tsconfig.*.json files first. Only creates tsconfig.test.json if none have correct settings.
    """
    owner = base_args["owner"]
    repo = base_args["repo"]
    token = base_args["token"]
    new_branch = base_args["new_branch"]

    tree_items = get_file_tree(
        owner=owner, repo=repo, ref=new_branch, token=token, root_only=True
    )
    root_files = [item["path"] for item in tree_items if item["type"] == "blob"]

    if "tsconfig.json" not in root_files:
        logger.debug("Not a TypeScript repo, skipping")
        return None

    variant_files = [f for f in root_files if TSCONFIG_VARIANT_PATTERN.match(f)]

    if not variant_files:
        logger.info("No tsconfig.*.json files found, creating %s", TSCONFIG_TEST_PATH)
        default_config = {
            "extends": "./tsconfig.json",
            "compilerOptions": REQUIRED_OPTIONS,
        }
        content = json.dumps(default_config, indent=2)
        result = replace_remote_file_content(
            file_content=content,
            file_path=TSCONFIG_TEST_PATH,
            base_args=base_args,
            commit_message=commit_message,
        )
        if result:
            logger.info("Created %s", TSCONFIG_TEST_PATH)
            return f"Created {TSCONFIG_TEST_PATH}"
        return None

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
                return None

            logger.info("%s missing relaxed settings, updating", variant_path)
            config.setdefault("compilerOptions", {})
            for key, value in REQUIRED_OPTIONS.items():
                config["compilerOptions"][key] = value

            updated_content = json.dumps(config, indent=2)
            result = replace_remote_file_content(
                file_content=updated_content,
                file_path=variant_path,
                base_args=base_args,
                commit_message=commit_message,
            )
            if result:
                logger.info("Updated %s", variant_path)
                return f"Updated {variant_path}"

            return None

        except json.JSONDecodeError as e:
            logger.warning("Invalid JSON in %s: %s, skipping", variant_path, e)
            continue

    return None
