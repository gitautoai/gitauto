SYSTEM_INSTRUCTION_TO_COMMIT_CHANGES = """
Given a pull request body, files and their contents, generate diff format for each file you think you need to modify, and call commit_changes_to_remote_branch() to commit the diff. commit_changes_to_remote_branch() can be called multiple times as many times as necessary.
"""
