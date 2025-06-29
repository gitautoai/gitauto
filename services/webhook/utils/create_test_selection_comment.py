from typing import TypedDict
from constants.urls import (
    SETTINGS_TRIGGERS_URL,
    SETTINGS_RULES_URL,
    DASHBOARD_COVERAGE_URL,
)
from services.github.pull_requests.get_pull_request_files import Status


class FileChecklistItem(TypedDict):
    path: str
    checked: bool
    coverage_info: str
    status: Status


def create_test_selection_comment(checklist: list[FileChecklistItem]) -> str:
    comment_lines = [
        "## 🧪 Manage Tests?",
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
            "- [ ] Manage Tests",
            "",
            f"⚙️ [Turn off triggers]({SETTINGS_TRIGGERS_URL}) | 📋 [Coding rules]({SETTINGS_RULES_URL}) | 🎯 [Exclude files]({DASHBOARD_COVERAGE_URL})",
        ]
    )

    return "\n".join(comment_lines)
