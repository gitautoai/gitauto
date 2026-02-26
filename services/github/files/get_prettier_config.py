import json

from services.github.types.github_types import BaseArgs
from utils.files.read_local_file import read_local_file
from utils.error.handle_exceptions import handle_exceptions

CONFIG_FILES = [
    ".prettierrc",
    ".prettierrc.json",
    ".prettierrc.yml",
    ".prettierrc.yaml",
    ".prettierrc.json5",
    ".prettierrc.js",
    ".prettierrc.cjs",
    ".prettierrc.mjs",
    ".prettierrc.toml",
    "prettier.config.js",
    "prettier.config.cjs",
    "prettier.config.mjs",
]


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_prettier_config(base_args: BaseArgs):
    clone_dir = base_args["clone_dir"]

    for config_file in CONFIG_FILES:
        content = read_local_file(config_file, base_dir=clone_dir)
        if content:
            return {"filename": config_file, "content": content}

    # Prettier config can also be defined in package.json under the "prettier" key
    package_content = read_local_file("package.json", base_dir=clone_dir)
    if package_content:
        package_json = json.loads(package_content)
        if "prettier" in package_json:
            return {
                "filename": "package.json",
                "content": json.dumps(package_json["prettier"], indent=2),
            }
    return None
