# get_comments.py Specification

## Overview

The `get_comments.py` module provides functionality to retrieve comments from GitHub issues. It fetches comments via the GitHub REST API and includes filtering capabilities to exclude comments made by the GitAuto application itself.

## Module Location

```
services/github/comments/get_comments.py
```

## Dependencies

### Standard Library
- `typing.Any` - Type annotations for generic objects

### Third Party
- `requests` - HTTP library for making API calls to GitHub

### Local Imports
- `config.GITHUB_API_URL` - Base URL for GitHub API
- `config.GITHUB_APP_IDS` - List of GitHub App IDs to filter out
- `config.TIMEOUT` - Request timeout configuration
- `services.github.create_headers.create_headers` - Creates authentication headers
- `services.github.github_types.BaseArgs` - Type definition for base arguments
- `utils.error.handle_exceptions.handle_exceptions` - Error handling decorator

## Functions

### get_comments

Retrieves comments from a GitHub issue with optional filtering to exclude GitAuto app comments.

#### Signature

```python
@handle_exceptions(default_return_value=[], raise_on_error=False)
def get_comments(
    issue_number: int, 
    base_args: BaseArgs, 
    includes_me: bool = False
) -> list[str]:
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `issue_number` | `int` | Yes | - | The GitHub issue number to retrieve comments from |
| `base_args` | `BaseArgs` | Yes | - | Dictionary containing repository and authentication information |
| `includes_me` | `bool` | No | `False` | Whether to include comments made by GitAuto app |

#### BaseArgs Structure

The `base_args` parameter must contain the following keys:

| Key | Type | Description |
|-----|------|-------------|
| `owner` | `str` | Repository owner (username or organization) |
| `repo` | `str` | Repository name |
| `token` | `str` | GitHub authentication token |

#### Return Value

- **Type**: `list[str]`
- **Description**: List of comment body texts
- **Default on Error**: `[]` (empty list)

#### Behavior

1. **API Call**: Makes a GET request to GitHub's issue comments endpoint
2. **Authentication**: Uses the provided token to authenticate the request
3. **Filtering**: 
   - If `includes_me=False` (default): Filters out comments made by GitAuto apps
   - If `includes_me=True`: Returns all comments without filtering
4. **Response Processing**: Extracts the `body` field from each comment
5. **Error Handling**: Returns empty list on any errors (network, authentication, etc.)

#### GitHub API Reference

This function implements the GitHub REST API endpoint:
- **Endpoint**: `GET /repos/{owner}/{repo}/issues/{issue_number}/comments`
- **Documentation**: https://docs.github.com/en/rest/issues/comments#list-issue-comments

#### Filtering Logic

Comments are filtered based on the `performed_via_github_app` field:

```python
# Comment is excluded if:
# 1. It has performed_via_github_app field AND
# 2. The app ID is in GITHUB_APP_IDS list

if comment.get("performed_via_github_app") is None:
    # Include: Regular user comment
elif comment["performed_via_github_app"].get("id") not in GITHUB_APP_IDS:
    # Include: Comment from other apps
else:
    # Exclude: Comment from GitAuto app
```

#### Error Handling

The function is decorated with `@handle_exceptions` which:
- Returns `[]` (empty list) on any exception
- Does not raise errors (`raise_on_error=False`)
- Handles common scenarios:
  - Network timeouts
  - Authentication failures (401, 403)
  - Issue not found (404)
  - Rate limiting (429)
  - Server errors (5xx)

## Usage Examples

### Basic Usage

```python
from services.github.comments.get_comments import get_comments

base_args = {
    "owner": "gitautoai",
    "repo": "gitauto", 
    "token": "ghp_xxxxxxxxxxxx"
}

# Get comments excluding GitAuto app comments
comments = get_comments(issue_number=123, base_args=base_args)
print(f"Found {len(comments)} user comments")
```

### Include All Comments

```python
# Get all comments including GitAuto app comments
all_comments = get_comments(
    issue_number=123, 
    base_args=base_args, 
    includes_me=True
)
print(f"Found {len(all_comments)} total comments")
```

## Configuration

The function relies on these configuration constants:

- `GITHUB_API_URL`: Base GitHub API URL (`https://api.github.com`)
- `GITHUB_APP_IDS`: List of GitAuto app IDs to filter out
- `TIMEOUT`: Request timeout in seconds (120)

## Testing

The module includes comprehensive tests in `test_get_comments.py`:

- ✅ Successful comment retrieval
- ✅ Filtering GitAuto app comments
- ✅ Including all comments when requested
- ✅ Error handling and fallback behavior

## Related Files

- `services/github/comments/create_comment.py` - Create new comments
- `services/github/comments/update_comment.py` - Update existing comments
- `services/github/create_headers.py` - Authentication header creation
- `services/github/github_types.py` - Type definitions