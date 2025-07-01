from typing import TypedDict
from config import PRODUCT_NAME
from constants.messages import SETTINGS_LINKS
from services.github.pulls.get_pull_request_files import Status
from utils.text.comment_identifiers import TEST_SELECTION_COMMENT_IDENTIFIER
from utils.text.reset_command import create_reset_command_message


class FileChecklistItem(TypedDict):
    path: str
    checked: bool
    coverage_info: str
    status: Status


def create_test_selection_comment(checklist: list[FileChecklistItem], branch_name: str):
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
            "- [ ] Yes, manage tests",
            "",
            f"Click the checkbox and {PRODUCT_NAME} will add/update/remove tests for the selected files to this PR.",
        ]
    )

    # Add reset command
    comment_lines.append(create_reset_command_message(branch_name))
    comment_lines.append("")

    # Add settings links
    comment_lines.append(SETTINGS_LINKS)

    return "\n".join(comment_lines)
