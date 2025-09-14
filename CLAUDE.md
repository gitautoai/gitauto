# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup

```bash
# Start development environment (recommended)
./start.sh

# Manual setup if needed
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Testing

```bash
# Run all tests
pytest

# Run tests with coverage (matches CI)
python -m pytest -r fE -x --cov-branch --cov=./ --cov-report=lcov:coverage/lcov.info

# Run only last failed tests (faster iteration)
python -m pytest --lf -x

# Run specific test files
pytest test_config.py
pytest tests/test_main.py

# Run only modified test files
MODIFIED_TEST_FILES=$({ git diff --name-only; git diff --name-only --staged; git ls-files --others --exclude-standard; } | sort -u | grep "test_" | grep "\.py$"); [ -n "$MODIFIED_TEST_FILES" ] && echo "$MODIFIED_TEST_FILES" | xargs python -m pytest -v
```

### Code Quality

```bash
# Pre-commit hooks (auto-runs pip freeze)
pre-commit run --all-files

# When adding new dependencies, use pip freeze
pip install package_name
pip freeze > requirements.txt
```

### Development Server

```bash
# FastAPI server (included in start.sh)
uvicorn main:app --reload --port 8000 --log-level warning
```

### Database Access

```bash
# Connect to Supabase PostgreSQL database (Development)
source .env && psql "postgresql://postgres.dkrxtcbaqzrodvsagwwn:$SUPABASE_DB_PASSWORD_DEV@aws-0-us-west-1.pooler.supabase.com:6543/postgres"

# Connect to Supabase PostgreSQL database (Production)
# READ-ONLY access
source .env && psql "postgresql://postgres.awegqusxzsmlgxaxyyrq:$SUPABASE_DB_PASSWORD_PRD@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
```

### Sentry CLI

Sentry CLI is available for accessing error logs and issues.

#### Installation

```bash
# Install Sentry CLI if not already installed
brew install getsentry/tools/sentry-cli
```

#### Accessing Sentry Issues

Sentry issues are identified by IDs like `AGENT-129`. Use these commands to investigate specific issues:

```bash
# List recent issues (requires SENTRY_PERSONAL_TOKEN in .env)
source .env && sentry-cli issues list --auth-token "$SENTRY_PERSONAL_TOKEN" --org "$SENTRY_ORG_SLUG" --project "$SENTRY_PROJECT_ID" --max-rows 10

# List issues with specific status
source .env && sentry-cli issues list --auth-token "$SENTRY_PERSONAL_TOKEN" --org "$SENTRY_ORG_SLUG" --project "$SENTRY_PROJECT_ID" --status unresolved --max-rows 20

# Get details for a specific issue by ID (replace AGENT-129 with actual issue ID)
source .env && sentry-cli issues list --auth-token "$SENTRY_PERSONAL_TOKEN" --org "$SENTRY_ORG_SLUG" --project "$SENTRY_PROJECT_ID" --id AGENT-129

# Search issues with query
source .env && sentry-cli issues list --auth-token "$SENTRY_PERSONAL_TOKEN" --org "$SENTRY_ORG_SLUG" --project "$SENTRY_PROJECT_ID" --query "is:unresolved level:error" --max-rows 10

# Get full event details for a specific issue (replace AGENT-129 with actual issue ID)
source .env && curl -sS -H "Authorization: Bearer $SENTRY_PERSONAL_TOKEN" \
  "https://sentry.io/api/0/organizations/$SENTRY_ORG_SLUG/issues/AGENT-129/events/latest/" | python -m json.tool
```

#### Issue ID Format

- Issues are identified with IDs like `AGENT-129`
- Use the exact issue ID in commands (e.g., `--id AGENT-129` or in API URLs)
- Issue IDs can be found in Sentry dashboard or error notifications

#### Finding Exact Error Location

When analyzing Sentry issues, use grep to find the specific error location instead of reading truncated output:

```bash
# INCORRECT - Shows truncated middleware frames only
source .env && curl -sS -H "Authorization: Bearer $SENTRY_PERSONAL_TOKEN" "https://sentry.io/api/0/organizations/$SENTRY_ORG_SLUG/issues/ISSUE_ID/events/latest/" | python -m json.tool

# CORRECT - Shows actual application code where error occurs
source .env && curl -sS -H "Authorization: Bearer $SENTRY_PERSONAL_TOKEN" "https://sentry.io/api/0/organizations/$SENTRY_ORG_SLUG/issues/ISSUE_ID/events/latest/" | python -m json.tool | grep -A 10 -B 5 "error_keyword"
```

#### Investigating Token/Context Limit Errors (e.g., AGENT-146) 

When a Sentry issue shows a token limit error (e.g., "167,154 token context limit"), find the actual input that caused it:

```bash
# 1. Get the CloudWatch URL from Sentry error
source .env && curl -sS -H "Authorization: Bearer $SENTRY_PERSONAL_TOKEN" \
  "https://sentry.io/api/0/organizations/$SENTRY_ORG_SLUG/issues/AGENT-146/events/latest/" | \
  python -m json.tool | grep -A 5 "cloudwatch"

# Example output shows log stream and request ID:
# "cloudwatch logs": {
#     "log_stream": "2025/09/04/pr-agent-prod[$LATEST]841315c5054c49ca80316cf2861696a3"
# }
# "aws_request_id": "17921070-5cb6-43ee-8d2e-b5161ae89729"

# 2. Use the exact stream from Sentry (get stream timestamps)
STREAM="2025/09/04/pr-agent-prod[\$LATEST]841315c5054c49ca80316cf2861696a3"
aws logs describe-log-streams \
  --log-group-name "/aws/lambda/pr-agent-prod" \
  --log-stream-name-prefix "2025/09/04/pr-agent-prod" | \
  grep -A 3 "841315c5054c49ca80316cf2861696a3"

# 3. Get ALL events from the exact stream and find the largest message
# IMPORTANT: AWS get-log-events may return empty results even when logs exist!
# You MUST use --start-from-head or implement pagination with nextToken
aws logs get-log-events \
  --log-group-name "/aws/lambda/pr-agent-prod" \
  --log-stream-name "$STREAM" \
  --start-from-head \
  --start-time 1756990862750 \
  --end-time 1756992771853 | \
  python3 -c "
import sys, json
data = json.load(sys.stdin)
max_size = 0
large_msg = None
for event in data.get('events', []):
    size = len(event['message'])
    if size > max_size:
        max_size = size
        large_msg = event['message']

if max_size > 100000:
    print(f'Found input: {max_size} chars')
    if 'error_log' in large_msg:
        print('SUCCESS: This is the token limit input')
"

# Verified: AGENT-146 input was 262,118 chars causing token limit error
```

#### Required Environment Variables

The following variables must be set in .env file:

- `SENTRY_PERSONAL_TOKEN`: Personal auth token with project:read permissions (get from <https://gitauto-ai.sentry.io/settings/auth-tokens/>)
- `SENTRY_ORG_SLUG`: Organization slug (gitauto-ai)
- `SENTRY_PROJECT_ID`: Project ID (4506865231200256)

### AWS CLI

AWS CLI is available and configured for us-west-1 region.

#### IMPORTANT: CloudWatch Log Retrieval Issues

**Known Issue:** The AWS CLI `get-log-events` command **will** return empty results even when logs exist in the CloudWatch console under these conditions:
1. When called without `--start-from-head` (starts from end of stream by default)
2. When at a page boundary with no events in that specific page
3. When not using pagination with nextToken to retrieve subsequent pages

This is documented AWS API behavior, not a bug.

**Solutions:**

1. **Always use `--start-from-head` parameter:**
```bash
aws logs get-log-events \
  --log-group-name "/aws/lambda/pr-agent-prod" \
  --log-stream-name "STREAM_NAME" \
  --start-from-head
```

2. **Implement pagination with nextToken:**
```python
import boto3

log_client = boto3.client("logs", region_name="us-west-1")
params = {
    "logGroupName": "/aws/lambda/pr-agent-prod",
    "logStreamName": "your-stream-name",
    "startFromHead": True,
}

all_events = []
while True:
    response = log_client.get_log_events(**params)
    events = response.get("events", [])
    all_events.extend(events)
    
    next_token = response.get("nextForwardToken")
    # Stop when token repeats (no more events)
    if next_token == params.get("nextToken"):
        break
    params['nextToken'] = next_token
```

3. **Alternative: Use `filter-log-events` instead:**
```bash
aws logs filter-log-events \
  --log-group-name "/aws/lambda/pr-agent-prod" \
  --log-stream-names "STREAM_NAME"
```

#### Searching CloudWatch Logs

```bash
# Search production Lambda logs
# Main log group: /aws/lambda/pr-agent-prod (configured for the Lambda function)

# IMPORTANT: Sentry provides a direct CloudWatch logs URL in the error context!
# Look for "cloudwatch logs" section in Sentry error details, it contains a URL like:
# https://console.aws.amazon.com/cloudwatch/home?region=us-west-1#logEventViewer:group=/aws/lambda/pr-agent-prod;stream=2025/08/29/pr-agent-prod[$LATEST]65d5c604f2fc4f44b1a2105a77aaf7cd;start=2025-08-29T13:08:32Z;end=2025-08-29T13:08:51Z
#
# Extract the stream name and timestamps from this URL:
# - Stream: 2025/08/29/pr-agent-prod[$LATEST]65d5c604f2fc4f44b1a2105a77aaf7cd
# - Start: 2025-08-29T13:08:32Z
# - End: 2025-08-29T13:08:51Z
#
# Convert the timestamps to epoch milliseconds:
python3 -c "import datetime; start = datetime.datetime(2025, 8, 29, 13, 8, 32); end = datetime.datetime(2025, 8, 29, 13, 8, 51); print(f'Start: {int(start.timestamp() * 1000)}, End: {int(end.timestamp() * 1000)}')"
#
# For relative time ranges (usually more practical):
python3 -c "import datetime; now = datetime.datetime.now(); print(f'Last 2 hours - Start: {int((now - datetime.timedelta(hours=2)).timestamp() * 1000)}, End: {int(now.timestamp() * 1000)}')"

# Search for errors in main log group
aws logs filter-log-events --log-group-name "/aws/lambda/pr-agent-prod" --filter-pattern "ERROR" --start-time START_EPOCH --end-time END_EPOCH --max-items 100

# Get recent logs without filter
aws logs filter-log-events --log-group-name "/aws/lambda/pr-agent-prod" --start-time START_EPOCH --end-time END_EPOCH --max-items 50

# List available log groups
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda" --max-items 20

# List log streams in a specific log group (recent streams first)
aws logs describe-log-streams --log-group-name "/aws/lambda/pr-agent-prod" --order-by LastEventTime --descending --max-items 10

# List log streams from a specific date (cannot use --order-by with prefix)
aws logs describe-log-streams --log-group-name "/aws/lambda/pr-agent-prod" --log-stream-name-prefix "2025/08/29/" --max-items 20

# Get logs from a specific stream (use [\$LATEST] with escape for $)
aws logs get-log-events --log-group-name "/aws/lambda/pr-agent-prod" --log-stream-name "2025/08/29/pr-agent-prod[\$LATEST]65d5c604f2fc4f44b1a2105a77aaf7cd" --start-time START_EPOCH --end-time END_EPOCH --limit 100

# Search by keyword across all streams in a time range
aws logs filter-log-events --log-group-name "/aws/lambda/pr-agent-prod" --filter-pattern "Foxquilt" --start-time START_EPOCH --end-time END_EPOCH --max-items 10

# Find specific error by request ID or issue ID
aws logs filter-log-events --log-group-name "/aws/lambda/pr-agent-prod" --filter-pattern "AGENT-12N OR req_011CSc46UReJXaoSqKaUX2Lz" --start-time START_EPOCH --end-time END_EPOCH --max-items 10

# Save logs to file for detailed analysis
aws logs get-log-events --log-group-name "/aws/lambda/pr-agent-prod" --log-stream-name "STREAM_NAME" --start-time START_EPOCH --end-time END_EPOCH --limit 200 > /tmp/cloudwatch_logs.txt

# Parse saved logs with Python
cat /tmp/cloudwatch_logs.txt | python3 -c "import sys, json; data = json.load(sys.stdin); [print(e['message']) for e in data['events'] if 'ERROR' in e['message']]"

# Update Lambda function log group configuration
aws lambda update-function-configuration --function-name pr-agent-prod --logging-config LogFormat=Text,LogGroup=/aws/lambda/pr-agent-prod
```

## Architecture Overview

### Core Application Structure

- FastAPI Application: `main.py` - Entry point with webhook endpoints
- AWS Lambda Handler: `handler()` function supports both HTTP requests and EventBridge scheduled events
- Configuration: `config.py` - Centralized environment variable management
- Webhook Processing: `services/webhook/` - GitHub event handlers

### Key Service Layers

#### GitHub Integration (`services/github/`)

- API Management: `github_manager.py` - Core GitHub API client
- Authentication: `token/` - JWT and installation token handling
- Repository Operations: `repositories/`, `branches/`, `commits/`
- Issue/PR Management: `issues/`, `pulls/`, `comments/`
- Webhook Processing: Handles GitHub events (issues, PRs, check runs)

#### AI Model Integration

- Anthropic: `services/anthropic/` - Claude API integration with function calling
- OpenAI: `services/openai/` - GPT model integration (legacy support)
- Model Selection: `services/model_selection.py` - Dynamic model routing

#### Database Layer (`services/supabase/`)

- Installation Management: Track GitHub app installations
- Usage Tracking: Monitor API usage and billing
- Repository Data: Store repo metadata and coverage stats
- Issue/PR Tracking: Link GitHub entities to internal records

#### External Integrations

- Stripe: `services/stripe/` - Payment and subscription management
- Slack: `services/slack/` - Internal notifications
- Jira: `services/jira/` - Alternative issue source

### Event-Driven Architecture

#### Webhook Event Flow

1. GitHub Webhook → `main.py:/webhook` → `services/webhook/webhook_handler.py`
2. Event Routing: Based on `X-GitHub-Event` header
3. Specialized Handlers: `issue_handler.py`, `merge_handler.py`, etc.
4. AI Processing: Generate code changes via Anthropic/OpenAI
5. GitHub Actions: Create PRs, comments, commits

#### Scheduled Events

- EventBridge Triggers: `schedule_handler.py` - Proactive issue processing
- Repository Analysis: Coverage-based file selection
- Batch Processing: Handle multiple issues per repository

### Key Patterns

#### Error Handling

- Centralized: `utils/error/handle_exceptions.py`
- Sentry Integration: Production error tracking
- Graceful Degradation: Continue processing on non-critical failures

#### Testing Strategy

- Co-located Tests: Test files alongside source code
- Integration Tests: Full GitHub API interactions
- Coverage Tracking: LCOV format for tooling integration
- Test Patterns: `test_*.py`, `*_test.py` naming

#### Configuration Management

- Environment Variables: All secrets and config via `.env`
- Type Safety: Validated environment variable loading
- Multi-Environment: Support for `prod`, `stage`, local development

#### File Processing

- Code Detection: `utils/files/is_code_file.py` - Language-aware filtering
- Coverage Analysis: `services/coverages/` - Test coverage integration
- Diff Generation: `services/github/commits/apply_diff_to_file.py`

### Development Workflow

#### Local Development

1. GitHub App Setup: Create personal development app
2. Ngrok Tunneling: Webhook forwarding to localhost
3. Environment Configuration: Copy and customize `.env`
4. Database Access: Supabase connection for full functionality

#### Branch Management

- Main Branch: Primary development target
- Developer Branches: Personal feature branches (e.g., `wes`)
- PR Workflow: Standard GitHub flow with GitAuto integration

#### Deployment

- AWS Lambda: Serverless function deployment
- CloudFormation: Infrastructure as code
- Environment Promotion: `stage` → `prod` pipeline

## Important Notes

### Authentication Requirements

- GitHub App credentials required for full functionality
- Anthropic/OpenAI API keys for AI features
- Supabase credentials for database operations
- Stripe keys for billing features

### Testing Considerations

- Integration tests require external API access
- Mock objects available in `test_*.py` files
- Coverage reports generated in LCOV format
- Pre-commit hooks maintain code quality

### Security Practices

- All secrets managed via environment variables
- Webhook signature verification
- JWT-based GitHub authentication
- Database row-level security via Supabase

### Performance Characteristics

- AWS Lambda cold start considerations
- GitHub API rate limiting
- Anthropic/OpenAI token limits
- Async processing for webhook handlers

## Coding Standards

- NO DOCSTRINGS: Do not add docstrings to functions or classes. Keep code clean and minimal. Always add API documentation URLs as comments for external API calls.
- API URLS: Always verify API documentation URLs using WebFetch before using them. Never guess API endpoints.
- NO COMMENTS: Do not add any comments in code when making changes. Never explain what was removed or why in the code itself. Explanations belong in terminal responses, not in code.
- NO TYPE HINTS USING ->: Do not add return type hints using -> because it asserts type and ignores what the implementation actually returns. Return type hints are PROHIBITED.
- NO TYPE: IGNORE: Do not use # type: ignore comments to suppress type errors. Fix the underlying type issues instead.
- NO CAST: Do not use typing.cast() to suppress type errors. Fix the underlying type issues instead.
- NO ANY: Do not use Any type. Fix the specific type issues instead.

## Proactive Code Cleanup

When refactoring or replacing old systems, always be PROACTIVE and think comprehensively. Don't wait for the user to point out every piece of old code that needs cleanup.

### Examples of Proactive Cleanup

1. **Function Replacement**: When replacing `is_request_limit_reached()` with new billing system:
   - AUTOMATICALLY search for ALL usages: imports, function calls, test files
   - Remove the old function file entirely
   - Remove ALL related test files and test functions
   - Search for related functions like `request_limit_reached()`, `get_billing_type()`
   - Remove ALL old/unused functions from the same refactoring session

2. **When Changing Function Signatures**: When changing `update_repository()` to accept `**kwargs`:
   - AUTOMATICALLY search ALL files that call this function
   - Update ALL call sites systematically using grep/search
   - Don't make the user repeatedly tell you about missed files

3. **Comprehensive Search Patterns**: Use multiple search approaches:

   ```bash
   # Search for function imports
   grep -r "from.*function_name" .
   # Search for function calls  
   grep -r "function_name(" .
   # Search for test files
   find . -name "*test*" -exec grep -l "function_name" {} \;
   # Search for related functions with similar names
   ```

4. **When Removing Old Code**: Always check for:
   - Original function files
   - Test files (`test_*.py`, `*_test.py`)
   - Import statements
   - Related helper functions
   - Similar naming patterns

5. **System-Wide Impact**: When making architecture changes:

   - Think about ALL handlers that might use the old pattern
   - Search for ALL files in related directories
   - Look for similar patterns that should be updated consistently

### Bad Examples (Reactive)

- User: "You missed schedule_handler.py" → You fix only that file
- User: "What about the test files?" → You then look for tests
- User: "Remove get_billing_type too" → You remove only that

### Good Examples (Proactive)

- User: "Replace is_request_limit_reached" → You automatically:
  1. Find ALL files using it (handlers, tests, utilities)
  2. Replace ALL usages with new billing system
  3. Remove the old function file
  4. Remove ALL related test files
  5. Search for related functions (request_limit_reached, get_billing_type, etc.)
  6. Remove ALL old functions from that refactoring session
  7. Verify no remaining references exist

**ALWAYS THINK: "What other files/functions/tests are related to this change?" and handle them ALL at once.**

## LGTM Workflow

When the user says "LGTM" (Looks Good To Me), automatically execute this workflow:

1. Activate virtual environment: `source venv/bin/activate`
2. Run black formatting: `black .`
3. Run ruff linting: `ruff check . --fix` (fix ALL ruff errors, not just modified files - if any errors remain unfixed, STOP and fix them before continuing)
4. Get list of modified files: `{ git diff --name-only; git diff --name-only --staged; git ls-files --others --exclude-standard; } | sort -u`
5. Run pylint on modified Python files only: `PYFILES=$({ git diff --name-only; git diff --name-only --staged; git ls-files --others --exclude-standard; } | sort -u | grep "\.py$" | while read f; do [ -f "$f" ] && echo "$f"; done); [ -n "$PYFILES" ] && echo "$PYFILES" | xargs pylint --fail-under=10.0 || echo "No Python files to check"` - **IF ANY PYLINT ERRORS/WARNINGS ARE FOUND, FIX THEM ALL BEFORE CONTINUING**
6. Run pyright on modified Python files only: `PYFILES=$({ git diff --name-only; git diff --name-only --staged; git ls-files --others --exclude-standard; } | sort -u | grep "\.py$" | while read f; do [ -f "$f" ] && echo "$f"; done); [ -n "$PYFILES" ] && echo "$PYFILES" | xargs pyright || echo "No Python files to check"` - **IF ANY PYRIGHT ERRORS/WARNINGS ARE FOUND, FIX THEM ALL BEFORE CONTINUING**
7. Run pytest: `MODIFIED_TEST_FILES=$({ git diff --name-only; git diff --name-only --staged; git ls-files --others --exclude-standard; } | sort -u | grep "test_" | grep "\.py$"); [ -n "$MODIFIED_TEST_FILES" ] && echo "$MODIFIED_TEST_FILES" | xargs python -m pytest -v` - **IF ANY TESTS FAIL, FIX THEM ALL BEFORE CONTINUING**
8. Check current branch is not main: `git branch --show-current`
9. Merge latest main: `git fetch origin main && git merge origin/main`
10. **CRITICAL**: Add ONLY the specific files that were modified: `git add file1.py file2.py file3.py` (**NEVER use `git add .`**)
11. Commit with descriptive message: `git commit -m "descriptive message"` (NO Claude credits in commit message)
12. Push to remote: `git push`

**CRITICAL GIT RULES:**

- **NEVER EVER use `git add .`** - this adds ALL files including unrelated changes
- **ALWAYS specify exact files**: Use `git diff --name-only HEAD` to see what's changed, then add only those specific files
- **Example**: `git add $(git diff --name-only HEAD)` or list files manually

IMPORTANT: When pylint and pyright show many alerts/errors, focus on fixing issues related to your code changes unless explicitly told to fix all issues. Don't ignore everything, but prioritize errors in files you modified.

**CRITICAL VERIFICATION REQUIREMENT:**

- NEVER claim completion without running ALL checks on ALL modified files
- Must achieve EXACTLY 10.0/10 pylint score and 0 pyright errors
- Must verify ALL tests pass by actually running them
- NEVER say "close to 10.00" or "good progress" - either it's PERFECT or it's NOT DONE
- LAZY CHECKING IS UNACCEPTABLE and will result in punishment
