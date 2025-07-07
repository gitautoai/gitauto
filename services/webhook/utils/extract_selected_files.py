import re


def extract_selected_files(comment_body: str) -> list[str]:
    selected_files = []

    # Pattern allows for indentation before dash, requires space after dash and before backtick
    pattern = r"\s*-\s+\[x\]\s+`([^`]+)`"
    matches = re.findall(pattern, comment_body)

    for match in matches:
        if "Generate Tests" not in match:
            selected_files.append(match)

    return selected_files