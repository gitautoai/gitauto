# Standard imports
from typing import Any

# Third-party imports
from anthropic.types import ToolUnionParam

# Local imports
from services.agents.verify_task_is_complete import (
    VERIFY_TASK_IS_COMPLETE,
    verify_task_is_complete,
)
from services.claude.forget_messages import FORGET_MESSAGES, forget_messages
from services.claude.query_file import QUERY_FILE, query_file
from services.http.curl import CURL, curl
from services.http.web_fetch import WEB_FETCH, web_fetch
from services.env.set_env import SET_ENV, set_env
from services.git.apply_diff_to_file import (
    APPLY_DIFF_TO_FILE,
    apply_diff_to_file,
)
from services.git.git_diff import GIT_DIFF, git_diff
from services.git.create_directory import CREATE_DIRECTORY, create_directory
from services.git.delete_file import DELETE_FILE, delete_file
from services.git.git_revert_file import GIT_REVERT_FILE, git_revert_file
from services.git.search_and_replace import (
    SEARCH_AND_REPLACE,
    search_and_replace,
)
from services.git.move_file import MOVE_FILE, move_file
from services.git.write_and_commit_file import (
    WRITE_AND_COMMIT_FILE,
    write_and_commit_file,
)
from services.github.comments.create_comment import CREATE_COMMENT, create_comment
from services.github.comments.reply_to_comment import (
    REPLY_TO_REVIEW_COMMENT,
    reply_to_comment,
)
from services.shell.run_command import RUN_COMMAND, run_command
from services.node.switch_node_version import (
    SWITCH_NODE_VERSION,
    switch_node_version,
)
from services.git.reset_pr_branch_to_new_base import (
    RESET_PR_BRANCH_TO_NEW_BASE,
    reset_pr_branch_to_new_base,
)
from utils.files.get_local_file_content import (
    GET_LOCAL_FILE_CONTENT,
    GET_LOCAL_FILE_CONTENT_FULL_ONLY,
    get_local_file_content,
)
from utils.files.get_local_file_tree import (
    GET_LOCAL_FILE_TREE,
    get_local_file_tree,
)
from utils.files.search_local_file_contents import (
    SEARCH_LOCAL_FILE_CONTENT,
    search_local_file_contents,
)

# Tool description best practices (Anthropic):
# - What the tool does, when it should be used, parameter meanings, caveats
# https://docs.anthropic.com/en/docs/build-with-claude/tool-use
# https://www.anthropic.com/engineering/writing-tools-for-agents

_TOOLS_BASE: list[ToolUnionParam] = [
    APPLY_DIFF_TO_FILE,
    CREATE_COMMENT,
    CREATE_DIRECTORY,
    CURL,
    DELETE_FILE,
    FORGET_MESSAGES,
    GIT_DIFF,
    GIT_REVERT_FILE,
    GET_LOCAL_FILE_TREE,
    MOVE_FILE,
    QUERY_FILE,
    RUN_COMMAND,
    SEARCH_AND_REPLACE,
    SEARCH_LOCAL_FILE_CONTENT,
    # SEARCH_WEB disabled: DDG CAPTCHAs bots. Use paid API (e.g. Brave Search) if needed.
    SWITCH_NODE_VERSION,
    VERIFY_TASK_IS_COMPLETE,
    WEB_FETCH,
    WRITE_AND_COMMIT_FILE,
]

TOOLS_FOR_ISSUES: list[ToolUnionParam] = _TOOLS_BASE + [
    GET_LOCAL_FILE_CONTENT,
    SET_ENV,
]

# PR handlers need full file reads (no partial read options)
TOOLS_FOR_PRS: list[ToolUnionParam] = _TOOLS_BASE + [
    GET_LOCAL_FILE_CONTENT_FULL_ONLY,
    SET_ENV,
]

# Review comment handler adds reply capability
TOOLS_FOR_REVIEW_COMMENTS: list[ToolUnionParam] = TOOLS_FOR_PRS + [
    REPLY_TO_REVIEW_COMMENT,
    RESET_PR_BRANCH_TO_NEW_BASE,
]

# Setup handler reads project files to detect language/framework, then creates workflow files
TOOLS_FOR_SETUP: list[ToolUnionParam] = _TOOLS_BASE + [
    GET_LOCAL_FILE_CONTENT,
]

# Define tools to call
tools_to_call: dict[str, Any] = {
    "apply_diff_to_file": apply_diff_to_file,
    "create_comment": create_comment,
    "create_directory": create_directory,
    "curl": curl,
    "delete_file": delete_file,
    "forget_messages": forget_messages,
    "git_diff": git_diff,
    "git_revert_file": git_revert_file,
    "get_local_file_content": get_local_file_content,
    "get_local_file_tree": get_local_file_tree,
    "move_file": move_file,
    "query_file": query_file,
    "reply_to_review_comment": reply_to_comment,
    "run_command": run_command,
    "reset_pr_branch_to_new_base": reset_pr_branch_to_new_base,
    "search_and_replace": search_and_replace,
    "search_local_file_contents": search_local_file_contents,
    # "search_web": web_search,  # Disabled: DDG CAPTCHAs bots
    "set_env": set_env,
    "switch_node_version": switch_node_version,
    "verify_task_is_complete": verify_task_is_complete,
    "web_fetch": web_fetch,
    "write_and_commit_file": write_and_commit_file,
}
