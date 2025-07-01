from typing import TypedDict
from constants.messages import SETTINGS_LINKS
from services.github.pulls.get_pull_request_files import Status
from utils.text.comment_identifiers import TEST_SELECTION_COMMENT_IDENTIFIER


class FileChecklistItem(TypedDict):
    path: str
    checked: bool
    coverage_info: str
    status: Status


def create_test_selection_comment(checklist: list[FileChecklistItem]) -> str:
    comment_lines = [
        TEST_SELECTION_COMMENT_IDENTIFIER,
        "",
        "Select files to manage tests for (create, update, or remove):",
        "",
    ]

    for item in checklist:
        checkbox = "[x]" if item["checked"] else "[ ]"
        comment_lines.append(
            f"- {checkbox} {item['status']} `{item['path']}`{item['coverage_info']}"
        )

    comment_lines.extend(
        [
            "",
            "---",
            "",
            "- [ ] Manage Tests",
            "",
            SETTINGS_LINKS,
        ]
    )

    return "\n".join(comment_lines)
