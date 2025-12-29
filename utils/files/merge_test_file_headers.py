import re
from typing import TypedDict
from utils.error.handle_exceptions import handle_exceptions
from utils.files.is_test_file import is_test_file


class LanguageConfig(TypedDict):
    extensions: list[str]
    rules: list[str]
    pattern: str
    format: str


TEST_FILE_HEADERS: dict[str, LanguageConfig] = {
    "typescript": {
        "extensions": [".ts", ".tsx"],
        "rules": [
            "@typescript-eslint/no-unused-vars",
            "@typescript-eslint/no-var-requires",
        ],
        "pattern": r"/\*\s*eslint-disable\s+([^*]+)\s*\*/",
        "format": "/* eslint-disable {rules} */",
    },
    "javascript": {
        "extensions": [".js", ".jsx"],
        "rules": ["no-unused-vars"],
        "pattern": r"/\*\s*eslint-disable\s+([^*]+)\s*\*/",
        "format": "/* eslint-disable {rules} */",
    },
    "python": {
        "extensions": [".py"],
        "rules": ["redefined-outer-name", "unused-argument"],
        "pattern": r"#\s*pylint:\s*disable=([^\n]+)",
        "format": "# pylint: disable={rules}",
    },
    "php": {
        "extensions": [".php"],
        "rules": ["unused-variable"],
        "pattern": r"//\s*phpcs:disable\s+([^\n]+)",
        "format": "// phpcs:disable {rules}",
    },
}


@handle_exceptions(default_return_value="", raise_on_error=False)
def merge_test_file_headers(
    file_content: str | None, file_path: str | None
) -> str | None:
    if not isinstance(file_content, str) or not isinstance(file_path, str):
        return file_content

    if not is_test_file(file_path):
        return file_content

    file_path_lower = file_path.lower()

    config: LanguageConfig | None = None
    for cfg in TEST_FILE_HEADERS.values():
        for ext in cfg["extensions"]:
            if file_path_lower.endswith(ext):
                config = cfg
                break
        if config:
            break

    if not config:
        return file_content

    needed_rules = set(config["rules"])
    existing_rules = set()

    pattern = config["pattern"]
    matches = list(re.finditer(pattern, file_content))

    for match in matches:
        rules_text = match.group(1).strip()
        if "," in rules_text:
            rules = [r.strip() for r in rules_text.split(",")]
        else:
            rules = [rules_text.strip()]

        for rule in rules:
            if rule:
                existing_rules.add(rule)

    missing_rules = needed_rules - existing_rules

    if not missing_rules:
        return file_content

    all_rules = sorted(existing_rules | needed_rules)
    rules_str = ", ".join(all_rules)
    new_header = config["format"].format(rules=rules_str)

    if matches:
        content_without_comments = file_content
        for match in reversed(matches):
            end_pos = match.end()
            if (
                end_pos < len(content_without_comments)
                and content_without_comments[end_pos] == "\n"
            ):
                end_pos += 1
            content_without_comments = (
                content_without_comments[: match.start()]
                + content_without_comments[end_pos:]
            )
        content_without_comments = content_without_comments.lstrip()
        return new_header + "\n" + content_without_comments
    return new_header + "\n" + file_content
