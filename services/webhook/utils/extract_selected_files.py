import re


def extract_selected_files(comment_body: str) -> list[str]:
    selected_files = []

    pattern = r"- \[x\] `([^`]+)`"
    matches = re.findall(pattern, comment_body)

    for match in matches:
        if "Generate Tests" not in match:
            selected_files.append(match)

    return selected_files
