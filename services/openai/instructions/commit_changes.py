SYSTEM_INSTRUCTION_TO_COMMIT_CHANGES = """
Based on the available context, including but not limited to issue body, files, their contents, repository structure, test coverage data, and any other relevant information, you have two options to modify files:

1. For small, targeted changes:
   Use commit_changes_to_remote_branch() with unified diff format. This is preferred for minor modifications where you need to change specific lines or small portions of a file.

2. For extensive changes:
   Use replace_remote_file_content() when you need to completely rewrite a file or make extensive changes. This is more efficient than unified diff format when modifying the majority of a file's content.

Choose the appropriate method based on the scope of your changes. Use unified diff for small changes, and complete file replacement for major rewrites.

## Coding rules

- NEVER EVER place import statements in the body of the function.
"""
