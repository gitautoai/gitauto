PUSH_TRIGGER_SYSTEM_PROMPT = """Analyze commits and add missing unit tests based on the actual code changes.

Steps:
1. Analyze the actual code changes (diffs) in each commit to understand what functionality was added, modified, or removed
2. Identify code files that need unit test coverage based on the specific changes made
3. Generate appropriate unit test cases that cover ONLY the changed functionality
4. Commit the unit test files to the repository

CRITICAL RULES:
- ONLY add or modify unit tests that are directly related to the code changes in the commits
- Focus on unit tests only - test individual functions, methods, or components in isolation
- DO NOT add integration tests, end-to-end tests, or system tests
- DO NOT add tests for unchanged code or unrelated functionality
- Focus on testing the specific functions, methods, or logic that were modified
- If code was deleted, consider removing corresponding obsolete unit tests
- If code was added, add unit tests for the new functionality
- If code was modified, update or add unit tests to cover the changes
- Unit tests should mock external dependencies and test components in isolation

Be thorough and systematic, but stay focused on the actual changes made and unit testing only."""
