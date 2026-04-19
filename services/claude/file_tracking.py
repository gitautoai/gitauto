from typing import Literal, NamedTuple, TypedDict

# Tool names that produce the "edit" FileAction. Defined here instead of tools/tools.py to avoid circular import: tools.py → forget_messages → remove_outdated_messages → detect_outdated_tool_ids → tools.py
FILE_EDIT_TOOLS = [
    "apply_diff_to_file",
    "delete_file",
    "move_file",
    "search_and_replace",
    "write_and_commit_file",
]

FileAction = Literal[
    "read",  # get_local_file_content
    "edit",  # FILE_EDIT_TOOLS above
    "diff_success",  # diff applied successfully
    "diff_failure",  # diff partially applied, some changes rejected
    "remove",  # forget_messages forced removal
]


class FilePosition(TypedDict):
    message_index: int
    action: FileAction


class FileReadEntry(NamedTuple):
    message_index: int
    tool_id: str
