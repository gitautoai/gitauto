# GitHub Utils Test Coverage

This document describes the comprehensive test coverage for `services/github/github_utils.py`.

## Test Files

### 1. `test_github_utils.py` - Unit Tests
Comprehensive unit tests with mocked dependencies.

### 2. `test_github_utils_integration.py` - Integration Tests
Integration tests that use real dependencies where possible.

## Functions Tested

### `create_permission_url()`

**Test Coverage:**
- ✅ Organization owner type
- ✅ User owner type
- ✅ Different installation IDs
- ✅ Edge cases (empty names, special characters, zero IDs)

**Test Cases:**
- `test_create_permission_url_organization`
- `test_create_permission_url_user`
- `test_create_permission_url_different_installation_ids`
- `test_create_permission_url_edge_cases`

### `deconstruct_github_payload()`

**Test Coverage:**
- ✅ Successful payload deconstruction with all fields
- ✅ Target branch handling (exists/doesn't exist/not set)
- ✅ Repository settings integration
- ✅ URL extraction from issue body
- ✅ Parent issue handling
- ✅ Automation detection (GitHub App user)
- ✅ Reviewer filtering (bots excluded, duplicates removed)
- ✅ Fork repository handling
- ✅ Empty/null issue body handling
- ✅ Different owner types (Organization/User)
- ✅ Error handling (missing token)
- ✅ Edge cases and boundary conditions

**Test Cases:**
- `test_deconstruct_github_payload_success`
- `test_deconstruct_github_payload_no_target_branch`
- `test_deconstruct_github_payload_target_branch_not_exists`
- `test_deconstruct_github_payload_no_token`
- `test_deconstruct_github_payload_automation_sender`
- `test_deconstruct_github_payload_bot_reviewers_filtered`
- `test_deconstruct_github_payload_forked_repo`
- `test_deconstruct_github_payload_empty_issue_body`
- `test_deconstruct_github_payload_user_owner_type`
- `test_deconstruct_github_payload_duplicate_reviewers`
- `test_deconstruct_github_payload_repo_settings_with_additional_fields`
- `test_deconstruct_github_payload_missing_fork_field`

## Dependencies Mocked

- `get_installation_access_token` - GitHub installation token retrieval
- `get_repository_settings` - Supabase repository settings
- `check_branch_exists` - GitHub branch existence check
- `extract_urls` - URL extraction from text
- `get_user_public_email` - GitHub user email retrieval
- `get_parent_issue` - GitHub parent issue information
- `datetime` - Date/time generation for branch naming
- `choices` - Random string generation for branch naming

## Key Test Scenarios

### Branch Name Generation
Tests verify that branch names follow the expected format:
`{PRODUCT_ID}{ISSUE_NUMBER_FORMAT}{issue_number}-{date}-{time}-{random_str}`

### Reviewer Logic
Tests ensure that:
- Bot users (containing "[bot]") are filtered out
- Duplicate reviewers are removed
- Both sender and issue creator are included (if not bots)

### Error Handling
Tests verify proper error handling for:
- Missing installation tokens
- Invalid repository configurations
- Missing or malformed payload data

## Running the Tests

```bash
# Run unit tests
python -m pytest services/github/test_github_utils.py -v

# Run integration tests
python -m pytest services/github/test_github_utils_integration.py -v

# Run all tests
python -m pytest services/github/test_github_utils*.py -v

# Run with coverage
python -m pytest services/github/test_github_utils*.py --cov=services.github.github_utils --cov-report=html
```

## Coverage Goals

These tests aim to achieve:
- **Line Coverage**: >90%
- **Function Coverage**: 100%
- **Branch Coverage**: >85%

The comprehensive test suite covers all major code paths, edge cases, and error conditions to ensure the reliability and maintainability of the `github_utils.py` module.
