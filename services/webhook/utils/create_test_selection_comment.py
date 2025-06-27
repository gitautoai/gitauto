from typing import TypedDict

from config import PRODUCT_ID


class FileChecklistItem(TypedDict):
    path: str
    checked: bool
    coverage_info: str


def create_test_selection_comment(checklist: list[FileChecklistItem]) -> str:
    comment_lines = [
        "## 🧪 Test Generation Available",
        "",
        "The following files were changed and may need test coverage. Select the files you want to generate tests for:",
        "",
    ]

    for item in checklist:
        checkbox = "[x]" if item["checked"] else "[ ]"
        comment_lines.append(f"- {checkbox} `{item['path']}`{item['coverage_info']}")

    comment_lines.extend(
        [
            "",
            "---",
            "",
            "**After selecting the files above, check the box below to generate tests:**",
            "",
            "- [ ] Generate Tests",
        ]
    )

    if PRODUCT_ID != "gitauto":
        comment_lines[-1] += f" - {PRODUCT_ID}"

    comment_lines.extend(
        [
            "",
            "💡 **Tip:** You can select multiple files and generate tests for all of them at once to avoid multiple Lambda executions.",
            "",
            "🔄 This comment will be updated when the PR changes to reflect the current file list.",
        ]
    )

    return "\n".join(comment_lines)
