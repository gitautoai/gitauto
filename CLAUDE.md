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

# Run specific test files
pytest test_config.py
pytest tests/test_main.py
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
source .env && psql "postgresql://postgres.dkrxtcbaqzrodvsagwwn:$SUPABASE_DB_PASSWORD@aws-0-us-west-1.pooler.supabase.com:6543/postgres"

# Connect to Supabase PostgreSQL database (Production)
source .env && psql "postgresql://postgres.awegqusxzsmlgxaxyyrq:$SUPABASE_DB_PASSWORD@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
```

### AWS CLI

AWS CLI is available and configured for us-west-1 region.

#### Searching CloudWatch Logs

```bash
# Search production Lambda logs
# Log group: /aws/lambda/pr-agent-prod

# IMPORTANT: First check today's date with 'date' command to ensure correct timestamp calculation
# Convert date to epoch milliseconds for AWS logs
python3 -c "import datetime; print(int(datetime.datetime(2025, 8, 19, 19, 0, 0).timestamp() * 1000))"

# Search for errors
aws logs filter-log-events --log-group-name "/aws/lambda/pr-agent-prod" --filter-pattern "ERROR" --start-time START_EPOCH --end-time END_EPOCH --max-items 100

# Get recent logs without filter
aws logs filter-log-events --log-group-name "/aws/lambda/pr-agent-prod" --start-time START_EPOCH --end-time END_EPOCH --max-items 50

# List available log groups
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda" --max-items 20
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

- NO DOCSTRINGS: Do not add docstrings to functions or classes. Keep code clean and minimal.
- NO TYPE HINTS USING ->: Do not add return type hints using -> because this is assertion
- NO TYPE: IGNORE: Do not use # type: ignore comments to suppress type errors. Fix the underlying type issues instead.
- NO CAST: Do not use typing.cast() to suppress type errors. Fix the underlying type issues instead.
- NO ANY: Do not use Any type. Fix the specific type issues instead.

## LGTM Workflow

When the user says "LGTM" (Looks Good To Me), automatically execute this workflow:

1. Run black formatting: `black .`
2. Run ruff linting: `ruff check . --fix`
3. Run pylint: `pylint . --fail-under=10.0`
4. Run pyright type checking: `pyright`
5. Run pytest: `python -m pytest -r fE -x`
6. Check current branch is not main: `git branch --show-current`
7. Merge latest main: `git fetch origin main && git merge origin/main`
8. Add changes: `git add .`
9. Commit with descriptive message: `git commit -m "descriptive message"` (NO Claude credits in commit message)
10. Push to remote: `git push`

IMPORTANT: Must fix every error/failure in each step before proceeding to the next step.
