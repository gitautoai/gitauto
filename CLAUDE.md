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
# Linting and formatting
black .
ruff check .
pylint services/

# Pre-commit hooks (auto-runs pip freeze)
pre-commit run --all-files
```

### Development Server

```bash
# FastAPI server (included in start.sh)
uvicorn main:app --reload --port 8000 --log-level warning
```

## Architecture Overview

### Core Application Structure

- **FastAPI Application**: `main.py` - Entry point with webhook endpoints
- **AWS Lambda Handler**: `handler()` function supports both HTTP requests and EventBridge scheduled events
- **Configuration**: `config.py` - Centralized environment variable management
- **Webhook Processing**: `services/webhook/` - GitHub event handlers

### Key Service Layers

#### GitHub Integration (`services/github/`)

- **API Management**: `github_manager.py` - Core GitHub API client
- **Authentication**: `token/` - JWT and installation token handling
- **Repository Operations**: `repositories/`, `branches/`, `commits/`
- **Issue/PR Management**: `issues/`, `pulls/`, `comments/`
- **Webhook Processing**: Handles GitHub events (issues, PRs, check runs)

#### AI Model Integration

- **Anthropic**: `services/anthropic/` - Claude API integration with function calling
- **OpenAI**: `services/openai/` - GPT model integration (legacy support)
- **Model Selection**: `services/model_selection.py` - Dynamic model routing

#### Database Layer (`services/supabase/`)

- **Installation Management**: Track GitHub app installations
- **Usage Tracking**: Monitor API usage and billing
- **Repository Data**: Store repo metadata and coverage stats
- **Issue/PR Tracking**: Link GitHub entities to internal records

#### External Integrations

- **Stripe**: `services/stripe/` - Payment and subscription management
- **Slack**: `services/slack/` - Internal notifications
- **Jira**: `services/jira/` - Alternative issue source

### Event-Driven Architecture

#### Webhook Event Flow

1. **GitHub Webhook** → `main.py:/webhook` → `services/webhook/webhook_handler.py`
2. **Event Routing**: Based on `X-GitHub-Event` header
3. **Specialized Handlers**: `issue_handler.py`, `merge_handler.py`, etc.
4. **AI Processing**: Generate code changes via Anthropic/OpenAI
5. **GitHub Actions**: Create PRs, comments, commits

#### Scheduled Events

- **EventBridge Triggers**: `schedule_handler.py` - Proactive issue processing
- **Repository Analysis**: Coverage-based file selection
- **Batch Processing**: Handle multiple issues per repository

### Key Patterns

#### Error Handling

- **Centralized**: `utils/error/handle_exceptions.py`
- **Sentry Integration**: Production error tracking
- **Graceful Degradation**: Continue processing on non-critical failures

#### Testing Strategy

- **Co-located Tests**: Test files alongside source code
- **Integration Tests**: Full GitHub API interactions
- **Coverage Tracking**: LCOV format for tooling integration
- **Test Patterns**: `test_*.py`, `*_test.py` naming

#### Configuration Management

- **Environment Variables**: All secrets and config via `.env`
- **Type Safety**: Validated environment variable loading
- **Multi-Environment**: Support for `prod`, `stage`, local development

#### File Processing

- **Code Detection**: `utils/files/is_code_file.py` - Language-aware filtering
- **Coverage Analysis**: `services/coverages/` - Test coverage integration
- **Diff Generation**: `services/github/commits/apply_diff_to_file.py`

### Development Workflow

#### Local Development

1. **GitHub App Setup**: Create personal development app
2. **Ngrok Tunneling**: Webhook forwarding to localhost
3. **Environment Configuration**: Copy and customize `.env`
4. **Database Access**: Supabase connection for full functionality

#### Branch Management

- **Main Branch**: Primary development target
- **Developer Branches**: Personal feature branches (e.g., `wes`)
- **PR Workflow**: Standard GitHub flow with GitAuto integration

#### Deployment

- **AWS Lambda**: Serverless function deployment
- **CloudFormation**: Infrastructure as code
- **Environment Promotion**: `stage` → `prod` pipeline

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

## LGTM Workflow

When the user says "LGTM" (Looks Good To Me), automatically execute this workflow:

1. Run black formatting: `black .`
2. Run ruff linting: `ruff check . --fix`
3. Run pylint: `pylint .`
4. Run pytest: `python -m pytest -r fE -x --cov-branch --cov=./ --cov-report=lcov:coverage/lcov.info`
5. Check current branch is not main: `git branch --show-current`
6. Add changes: `git add .`
7. Commit with descriptive message: `git commit -m "descriptive message"`
8. Push to remote: `git push`

IMPORTANT: Must fix every error/failure in each step before proceeding to the next step.
