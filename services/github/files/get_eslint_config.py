import json

from services.github.files.get_raw_content import get_raw_content
from services.github.types.github_types import BaseArgs
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_eslint_config(base_args: BaseArgs):
    owner = base_args["owner"]
    repo = base_args["repo"]
    token = base_args["token"]
    base_branch = base_args["base_branch"]

    config_files = [
        ".eslintrc.json",
        ".eslintrc.js",
        ".eslintrc.yml",
        ".eslintrc.yaml",
        ".eslintrc",
        "eslint.config.js",
        "eslint.config.mjs",
        "eslint.config.cjs",
    ]

    for config_file in config_files:
        content = get_raw_content(
            owner=owner, repo=repo, file_path=config_file, ref=base_branch, token=token
        )
        if content:
            return {"filename": config_file, "content": content}

    package_content = get_raw_content(
        owner=owner, repo=repo, file_path="package.json", ref=base_branch, token=token
    )
    if package_content:
        package_json = json.loads(package_content)
        if "eslintConfig" in package_json:
            return {
                "filename": "package.json",
                "content": json.dumps(package_json["eslintConfig"], indent=2),
            }

    return None
