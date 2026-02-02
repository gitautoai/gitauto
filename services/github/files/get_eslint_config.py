import json

from services.github.types.github_types import BaseArgs
from services.node.read_file_content import read_file_content
from utils.error.handle_exceptions import handle_exceptions

# Flat configs first (ESLint 9+ default), then legacy configs
CONFIG_FILES = [
    "eslint.config.mjs",
    "eslint.config.js",
    "eslint.config.cjs",
    ".eslintrc.js",
    ".eslintrc.cjs",
    ".eslintrc.json",
    ".eslintrc.yml",
    ".eslintrc.yaml",
    ".eslintrc",
]


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_eslint_config(base_args: BaseArgs):
    clone_dir = base_args["clone_dir"]
    owner = base_args["owner"]
    repo = base_args["repo"]
    token = base_args["token"]
    branch = base_args["base_branch"]

    for config_file in CONFIG_FILES:
        content = read_file_content(
            config_file,
            local_dir=clone_dir,
            owner=owner,
            repo=repo,
            branch=branch,
            token=token,
        )
        if content:
            return {"filename": config_file, "content": content}

    # ESLint config can also be defined in package.json under the "eslintConfig" key
    package_content = read_file_content(
        "package.json",
        local_dir=clone_dir,
        owner=owner,
        repo=repo,
        branch=branch,
        token=token,
    )
    if package_content:
        package_json = json.loads(package_content)
        if "eslintConfig" in package_json:
            return {
                "filename": "package.json",
                "content": json.dumps(package_json["eslintConfig"], indent=2),
            }

    return None
