<!-- markdownlint-disable MD029 -->
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## CRITICAL: Always Read Before Using

**AFTER EVERY CONVERSATION COMPACTION/SUMMARY**: You MUST read the relevant script/function file BEFORE using it. You will forget how to use functions after compaction.

**Example mistakes you keep making:**

- Trying to use `scripts/github/update_file.py` without reading it first
- Forgetting it needs to be called as a Python function from within a Python script, not as a standalone CLI command
- Forgetting the correct parameter order and types

**Correct workflow:**

1. Read `scripts/README.md` to understand which script to use
2. Read the actual script file (e.g., `scripts/github/update_file.py`) to see the function signature
3. Write Python code that imports and calls the function correctly

## CRITICAL: Never Guess - Always Verify

**NEVER use words like "likely", "probably", "might be", "seems like", "most likely", "somehow" when diagnosing bugs or explaining root causes.**

These words mean you are GUESSING, not providing facts.

**What to do instead:**

1. Check AWS CloudWatch logs to see the ACTUAL events and code execution
2. Read the actual code to see what ACTUALLY happens
3. Use scripts to get ACTUAL data from GitHub API, database, etc.
4. Only state facts that you have verified through logs, code, or data

**Example of WRONG approach:**

- "The bug is likely caused by..."
- "This probably triggers when..."
- "It seems like the issue is..."

**Example of CORRECT approach:**

- "The CloudWatch logs show that at 17:57:33, webhook event X was received and handler Y was called"
- "Reading the code at line 123 shows that function Z calls check_availability"
- "The GitHub API returns issue #1445 for this query"

## CRITICAL: Never Use `cd` Command

**The `cd` command is NOT ALLOWED and DOES NOT WORK in bash commands.**

- The working directory is automatically reset after EVERY bash command execution
- Even if you use `cd`, you will be redirected back to the original working directory
- Using `cd` is completely nonsense and a waste of time

**What to do instead:**

- Use absolute paths in commands: `python3 /path/to/script.py` instead of `cd /path && python3 script.py`
- For Python scripts that need to import local modules, use `sys.path.insert(0, '/absolute/path')` inside the script
- Never chain commands with `cd` - always use full paths

**Example of WRONG approach:**

```bash
cd /tmp/repo && python3 script.py
```

**Example of CORRECT approach:**

```bash
python3 /tmp/repo/script.py
```

Or if imports are needed:

```python
import sys
sys.path.insert(0, '/Users/rwest/Repositories/gitauto')
from scripts.github.update_file import update_file
```

## CRITICAL: Never Bypass Workflow Scripts

**NEVER use git commands directly to bypass workflow scripts like commit_file.py or push_repo.py.**

When workflow scripts fail, fix the ROOT CAUSE instead of working around them:

**Example of WRONG approach:**

```bash
# Script fails because eslint is missing, so bypass it with git directly
git -C /path/to/repo add file.ts && git -C /path/to/repo commit -m "message"

# Or modify the script to skip validation
# Or add exceptions to skip certain file types
```

**Example of CORRECT approach:**

```bash
# Script fails because eslint is missing
# Install the missing dependencies
npm install --prefix /path/to/repo
# or
yarn --cwd /path/to/repo install

# Then use the proper workflow:
python3 << 'EOF'
from scripts.git.commit_file import commit_file
from scripts.github.get_installation_token import get_installation_token

token = get_installation_token('owner')
commit_file(owner='owner', repo='repo', file_path='file.ts', pr_number=123, commit_message='message', token=token)
EOF
```

**Why:** Workflow scripts exist for a reason (linting, validation, safety checks). Bypassing them leads to:

- Code quality issues
- Broken CI/CD pipelines
- Inconsistent commit history
- Missing safety checks

**Always fix the fundamental issue (install missing tools) instead of working around it (skip validation).**

## CRITICAL: Web Search Best Practices

**NEVER include years in search queries unless specifically searching for historical information.**

Years in search queries are almost always unnecessary and can limit results:

**Example of WRONG approach:**

- "GitHub repository ID unique globally 2025"
- "PostgreSQL JSONB best practices 2024"

**Example of CORRECT approach:**

- "GitHub repository ID unique globally"
- "PostgreSQL JSONB best practices"

**Why:** Search engines automatically prioritize recent, relevant results. Adding years artificially limits results and may exclude the most current information.

## Testing Workflow

When modifying a file, follow this test-driven approach:

1. Run the test file first - it should fail if your change affects behavior
2. If tests don't fail, the test coverage is insufficient - add new test cases
3. Update the implementation to fix the failing tests
4. Run tests again to confirm they pass

### CRITICAL: Never Celebrate Partial Success

**NEVER celebrate or claim success when ANY check/test fails. Work is NOT done until ALL checks pass.**

This applies to:

- PR status checks (`get_pr_status.py` returns FAIL)
- Test runs (some tests pass but others fail)
- CI/CD checks (CircleCI passes but codecov fails)
- Build steps (tests pass but lint fails)
- ANY situation where work is incomplete

**WRONG responses (celebrating partial success):**

- "Great! CircleCI Checks: success!" (when codecov/project: failure)
- "Tests are passing, only codecov is failing"
- "DatePicker is passing now!" (when overall PR status is FAIL)
- "14 tests passing!" (when 2 tests are still failing)
- "CircleCI is green, just a coverage issue"
- "Build succeeded, just some lint warnings"

**CORRECT responses:**

- "PR status: FAIL. codecov/project failing. Investigating..."
- "14 tests pass, 2 tests fail. Fixing failures..."
- "Overall status: FAIL. Must fix all failures."

**Why:** If work is incomplete, celebrating partial progress wastes time and frustrates users. The job is either DONE (all checks pass) or NOT DONE (any check fails). There is no middle ground.

### Common Jest Testing Patterns

toBeInstanceOf Fails After jest.resetModules()

When tests use `jest.resetModules()` in `beforeEach`, `.toBeInstanceOf()` assertions fail:

```typescript
expect(received).toBeInstanceOf(expected)
Expected constructor: ApolloClient
Received constructor: ApolloClient
```

**Root Cause:** After `jest.resetModules()`, class constructors are reloaded. The constructor from the import is different from the instantiated object's constructor.

**Fix:** Use `.constructor.name` instead:

```typescript
// BEFORE (fails)
expect(APOLLO_CLIENT).toBeInstanceOf(ApolloClient);

// AFTER (works)
expect(APOLLO_CLIENT.constructor.name).toBe('ApolloClient');
```

**Batch fix with sed:**

```bash
sed -i '' 's/expect(\(.*\))\.toBeInstanceOf(ApolloClient)/expect(\1.constructor.name).toBe('\''ApolloClient'\'')/g' test.ts

# ALWAYS verify changes before uploading
grep "toBeInstanceOf" test.ts  # Should return nothing
grep "constructor.name" test.ts | head -5  # Verify correct format
```

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

**IMPORTANT: You are PROHIBITED from running ANY database schema changes (ALTER TABLE, CREATE TABLE, DROP TABLE, etc.) without explicit user consent. You may only run SELECT queries for reading data.**

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

## GitHub API Access for Production Customer Repository Investigation

### Getting Installation Access Token for Production

When investigating customer repository issues in production, you can access their repositories via the GitHub API:

```python
import time
import jwt
import requests

# 1. Create JWT token for GitHub App authentication
# Use production private key: /Users/rwest/Downloads/gitauto-ai.2024-12-11.private-key.pem
with open('/Users/rwest/Downloads/gitauto-ai.2024-12-11.private-key.pem', 'r') as f:
    private_key = f.read()

app_id = '844909'  # GitAuto production app ID
now = int(time.time())
payload = {
    'iat': now,
    'exp': now + 600,  # JWT expires in 10 minutes
    'iss': app_id
}
jwt_token = jwt.encode(payload=payload, key=private_key, algorithm='RS256')

# 2. Find the customer's installation ID
headers = {
    'Authorization': f'Bearer {jwt_token}',
    'Accept': 'application/vnd.github.v3+json'
}
response = requests.get('https://api.github.com/app/installations', headers=headers)
installations = response.json()

# Search for customer (e.g., 'Foxquilt')
for install in installations:
    if 'fox' in install['account']['login'].lower():
        installation_id = install['id']
        print(f"Found: {install['account']['login']} - ID: {installation_id}")

# 3. Get installation access token for the customer
response = requests.post(
    f'https://api.github.com/app/installations/{installation_id}/access_tokens',
    headers=headers
)
access_token = response.json()['token']

# 4. Now use the access token to access customer repositories
headers = {'Authorization': f'token {access_token}', 'Accept': 'application/vnd.github.v3+json'}

# List repositories GitAuto has access to
response = requests.get('https://api.github.com/installation/repositories', headers=headers)
repos = response.json()
for repo in repos['repositories']:
    print(f"  - {repo['full_name']}")

# Get repository settings
response = requests.get('https://api.github.com/repos/OWNER/REPO', headers=headers)
repo_settings = response.json()
```

### Common Investigation Tasks

1. **Check Repository Settings**:
   - Default branch, merge settings, delete branch on merge
   - Permissions GitAuto has for the repository

2. **List Accessible Repositories**:
   - Shows which repositories GitAuto can access in the customer's organization
   - Useful for verifying if GitAuto is installed on specific repos

3. **Check GitAuto Permissions**:

   ```python
   response = requests.get(f'https://api.github.com/app/installations/{installation_id}', headers=jwt_headers)
   permissions = response.json().get('permissions', {})
   ```

### Security Notes

- GitAuto may not have access to all repositories in an organization
- Branch protection rules and webhook settings require admin permissions (usually not available)
- The installation access token expires after 1 hour
- Always use production app ID (844909) and production private key for customer investigations

## Architecture Overview

### Lambda Runtime Environment

**CRITICAL**: GitAuto runs entirely on AWS Lambda using Docker containers, not in client environments.

#### Container Configuration

- **Base Image**: `public.ecr.aws/lambda/python:3.12` (Amazon Linux 2023)
- **Node.js Runtime**: LTS version (20.x) installed via nodesource repository  
- **Package Manager**: npm/npx available for JavaScript/TypeScript tooling
- **Memory**: 512MB allocated, timeout: 900 seconds (15 minutes)
- **Storage**: `/tmp` directory (2GB) for temporary file operations

#### JavaScript/TypeScript Support

- **ESLint**: Available via `npx --yes eslint@latest` (downloads on-demand)
- **Import Sorting**: Full support for JS/TS via ESLint sort-imports rule
- **Cold Start**: First ESLint download adds ~5-10 seconds per container instance
- **Caching**: Downloaded npm packages persist per Lambda container

#### Tool Installation
All code analysis, generation, and file processing happens on our Lambda instances. We can install tools via:

- Python packages in requirements.txt (e.g., isort, black, ruff)
- System packages via Dockerfile's dnf (e.g., patch, git)
- Node packages via Dockerfile's npm (e.g., prettier, eslint)
- For Python tools, prefer direct imports over subprocess for better performance
- Client repository configurations (.isort.cfg, .prettierrc, etc.) are not directly accessible
- We should use neutral/default settings when formatting client code (no opinionated profiles)

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
- NO TYPE HINTS USING ->: Do not add return type hints using -> because it overwrites the inferred return type without actually validating that the implementation returns that type. It's a lie to the type checker that cannot be verified at runtime. Return type hints are PROHIBITED.
- NO TYPE: IGNORE: Do not use # type: ignore comments to suppress type errors. This silences the type checker without fixing the actual type mismatch. Fix the underlying type issues instead.
- NO CAST: Do not use typing.cast() to suppress type errors. Cast doesn't validate or guarantee the type is correct - it just tells the type checker to trust you without verification. Fix the underlying type issues instead.
- NO PYRIGHT SUPPRESSION: Do not use # pyright: reportArgumentType=false or any other pyright suppression comments. Fix the underlying type issues instead.
- NO ANY: Do not use Any type. Fix the specific type issues instead.
- ALLOWED: Variable type annotations ARE allowed (e.g., `data: RepositoryFeatures = result.data[0]`) because they document intent and help type inference, though they don't enforce runtime validation. Use them to clarify types when the inferred type is too broad.
- CRITICAL: When using `as any` in TypeScript/JavaScript, ALWAYS add a comment above explaining why it's needed. Example:
  
  ```typescript
  // NOTE: Context type from require() is unknown, cast to any to access login_hint property
  const context = React.useContext(require('./authContext').AuthContext) as any;
  ```

## Testing Anti-Patterns to Avoid

### CRITICAL: Do NOT prioritize passing tests over meaningful tests

**BAD HABIT**: Creating tests that pass but don't verify actual functionality:

- Tests that only check if functions can be imported
- Tests that mock everything and never exercise real logic
- Tests that verify string presence in source code instead of behavior
- Tests designed to pass rather than catch bugs

**CORRECT APPROACH**: Create meaningful tests that verify actual behavior:

- Integration tests that exercise real code paths with minimal mocking
- Tests that verify the actual business logic works correctly
- Tests that would fail if the implementation is broken
- Tests that provide confidence the feature actually works

**Example of BAD test**:

```python
def test_function_has_variables():
    source = inspect.getsource(function)
    assert "variable_name" in source  # Meaningless - just checks text
```

**Example of GOOD test**:

```python
def test_function_accumulates_tokens():
    result = function(input_with_tokens)
    assert result.total_tokens == expected_sum  # Verifies actual behavior
```

**Remember**: Tests should provide confidence that the code works, not just that it compiles.

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

1. Run black formatting: `black .`
2. Run ruff linting: `ruff check . --fix` (fix ALL ruff errors, not just modified files - if any errors remain unfixed, STOP and fix them before continuing)
3. **CRITICAL**: Check `git status` FIRST to see ALL changes including deleted/renamed files
4. Get list of modified, created, AND deleted files ONCE: `{ git diff --name-only; git diff --name-only --staged; git ls-files --others --exclude-standard; } | sort -u`
   - This command captures: modified files, staged files, and newly created untracked files
   - NOTE: Deleted files that are already staged won't appear in this list but MUST be included in the commit
   - Store this list and use it for all subsequent steps
   - Extract Python files from this list: filter for `.py` files
   - Extract test files from this list: filter for `test_*.py` files
   - **CRITICAL**: For pylint, pyright, flake8, and pytest, filter out deleted files that no longer exist
5. Run flake8 on the Python files identified in step 4 (excluding deleted files): `flake8 file1.py file2.py file3.py` - **IF ANY FLAKE8 ERRORS/WARNINGS ARE FOUND, FIX THEM ALL BEFORE CONTINUING**
6. Run pylint on the Python files identified in step 4 (excluding deleted files): `pylint file1.py file2.py file3.py` - **IF ANY PYLINT ERRORS/WARNINGS ARE FOUND, FIX THEM ALL BEFORE CONTINUING**
7. Run pyright on the Python files identified in step 4 (excluding deleted files): `pyright file1.py file2.py file3.py` - **IF ANY PYRIGHT ERRORS/WARNINGS ARE FOUND, FIX THEM ALL BEFORE CONTINUING**
8. Run pytest on the test files identified in step 4 (excluding deleted files): `python -m pytest test_file1.py test_file2.py` - **IF ANY TESTS FAIL, FIX THEM ALL BEFORE CONTINUING**
9. Check current branch is not main: `git branch --show-current`
10. Merge latest main: `git fetch origin main && git merge origin/main`
11. **CRITICAL**: Review `git status` again to ensure ALL changes are staged:
    - Add all modified/new files identified in step 4
    - Ensure deleted files are staged (they should already be if renamed with `mv`)
    - Use specific file names: `git add file1.py file2.py file3.py` (**NEVER use `git add .`**)
    - For deleted files already staged, they'll be included automatically in the commit
12. Commit with descriptive message: `git commit -m "descriptive message"` (NO Claude credits in commit message)
13. Push to remote: `git push`

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
