from typing import Literal
from utils.files.read_xml_file import read_xml_file


def get_mode_prompt(
    mode: Literal["comment", "commit", "explore", "get", "search"],
):
    base_path = "utils/prompts/modes"
    mode_files = {
        "comment": f"{base_path}/update_comment.xml",
        "commit": f"{base_path}/commit_changes.xml",
        "explore": f"{base_path}/explore_repo.xml",
        "get": f"{base_path}/explore_repo.xml",
        "search": f"{base_path}/search_google.xml",
    }

    if mode in mode_files:
        return read_xml_file(mode_files[mode])
    return None
