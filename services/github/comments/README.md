# GitHub Comments Service

This directory contains functionality for interacting with GitHub comments API.

## Files

- `create_comment.py`: Creates a comment on a GitHub issue or pull request
- `get_comments.py`: Retrieves comments from a GitHub issue or pull request
- `update_comment.py`: Updates an existing comment on a GitHub issue or pull request

## Test Coverage

The test files ensure comprehensive coverage of the comment functionality:

- `test_create_comment.py`: Unit tests for the create_comment function
  - Tests successful comment creation
  - Tests behavior with different input sources (github, jira)
  - Tests default input_from parameter behavior
  - Tests error handling with request failures

- `test_create_comment_integration.py`: Integration tests using the responses library
  - Tests successful API interactions
  - Tests server error handling

- `test_create_comment_new.py`: Additional tests for specific error conditions
  - Tests connection errors
  - Tests timeout errors