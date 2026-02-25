<!-- markdownlint-disable MD029 MD032 MD036 -->
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

## Development Commands

### Running Locally

```bash
./start.sh
```

### Code Quality

```bash
# Pre-commit hooks (auto-runs pip freeze)
pre-commit run --all-files

# When adding new dependencies, use pip freeze
pip install package_name
pip freeze > requirements.txt
```

### Database Access

**IMPORTANT: You are PROHIBITED from running ANY database schema changes (ALTER TABLE, CREATE TABLE, DROP TABLE, etc.) without explicit user consent. You may only run SELECT queries for reading data.**

```bash
# Connect to Supabase PostgreSQL database (Development)
source .env && psql "postgresql://postgres.dkrxtcbaqzrodvsagwwn:$SUPABASE_DB_PASSWORD_DEV@aws-0-us-west-1.pooler.supabase.com:6543/postgres"

# Connect to Supabase PostgreSQL database (Production)
source .env && psql "postgresql://postgres.awegqusxzsmlgxaxyyrq:$SUPABASE_DB_PASSWORD_PRD@aws-0-us-west-1.pooler.supabase.com:6543/postgres"

# Query tips:
# - NEVER specify columns first when querying unfamiliar tables - always use SELECT * ... LIMIT 1 with -x first
# - Then narrow down to specific columns after seeing the schema - guessing column names wastes time
# - Use -c "SELECT ..." for single queries
# - Use -x for vertical (expanded) display when rows have many columns or wide values (e.g., JSON)
# - Example: psql ... -x -c "SELECT * FROM repositories LIMIT 1;"
```

**CRITICAL: Do NOT use pipes with psql commands**

```bash
# WRONG - pipe causes $SUPABASE_DB_PASSWORD_PRD to not expand
source .env && psql "postgresql://...:$SUPABASE_DB_PASSWORD_PRD@..." -c "SELECT ..." | head -50

# CORRECT - no pipe, use SQL LIMIT instead
source .env && psql "postgresql://...:$SUPABASE_DB_PASSWORD_PRD@..." -c "SELECT ... LIMIT 50;"

# CORRECT - if you need to truncate output, use SQL functions
source .env && psql "postgresql://..." -c "SELECT LEFT(long_column, 3000) FROM table;"
```

### Sentry CLI

Sentry CLI is available for accessing error logs and issues.

#### Listing Issues

```bash
source .env && sentry-cli issues list --org gitauto-ai --project agent --query "search terms"
```

#### Accessing Sentry Issues

Sentry issues are identified by IDs like `AGENT-129`. Use the Python script for detailed issue analysis:

```bash
# Get detailed issue information
# Automatically loads .env and saves full JSON to /tmp/sentry_<issue_id>.json
python3 scripts/sentry/get_issue.py AGENT-20N
```

#### Finding Exact Error Location

When analyzing Sentry issues, use the saved JSON file from the script:

```bash
# Get issue details (saves to /tmp/sentry_<issue_id>.json)
python3 scripts/sentry/get_issue.py AGENT-20N

# Search for specific keywords in the saved JSON
cat /tmp/sentry_agent-20n.json | python -m json.tool | grep -A 10 -B 5 "error_keyword"

# Or examine the full JSON
python -m json.tool /tmp/sentry_agent-20n.json | less
```

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

Use `scripts/aws/filter_log_events_across_streams.py`. The most common usage is filtering by PR number:

```bash
# Filter by PR number (most common)
python3 scripts/aws/filter_log_events_across_streams.py --owner Foxquilt --repo foxcom-forms --pr 1089

# Filter by time range
python3 scripts/aws/filter_log_events_across_streams.py --hours 24 --owner Foxquilt --repo foxcom-forms
```

#### SSH to NAT Instance (EFS Mounted at /mnt/efs)

```bash
ssh -i infrastructure/nat-instance-ssh-private-key.pem ec2-user@54.176.165.89
```

## GitHub API Access for Production Customer Repository Investigation

## Architecture Overview

### Lambda Runtime Environment

**CRITICAL**: GitAuto runs on AWS, not in client environments. Infrastructure is managed via CloudFormation:

- `Dockerfile` - Lambda container image
- `infrastructure/setup-vpc-nat-efs.yml` - VPC, NAT, EFS, CodeBuild project and IAM role
- `infrastructure/deploy-lambda-with-vpc-efs.yml` - Lambda function and IAM role (memory, timeout, VPC config, EFS mount, CodeBuild permissions)

### Key Patterns

#### Testing Strategy

- Co-located Tests: Test files alongside source code
- Test Patterns: `test_*.py`

## Important Notes

## Coding Standards

- No DOCSTRINGS: Do not add docstrings unless explicitly told to. Do not delete existing docstrings unless they are outdated.
- COMMENTS: Do not delete existing comments unless they are outdated. Preserve URL references and API documentation links. Never explain what was removed or why in the code itself. Explanations belong in terminal responses, not in code. Do not split comments across multiple lines unnecessarily - keep them on one line when possible to maintain readability.
- LOGGERS: Do not delete existing logger statements unless they are outdated.
- API URLS: Always verify API documentation URLs using WebFetch before using them. Never guess API endpoints.
- NO TYPE HINTS USING ->: Do not add return type hints using -> because it overwrites the inferred return type without actually validating that the implementation returns that type. It's a lie to the type checker that cannot be verified at runtime. Return type hints are PROHIBITED.
- NO TYPE: IGNORE: Do not use # type: ignore comments to suppress type errors. This silences the type checker without fixing the actual type mismatch. Fix the underlying type issues instead.
- NO CAST: Do not use typing.cast() to suppress type errors. Cast doesn't validate or guarantee the type is correct - it just tells the type checker to trust you without verification. Fix the underlying type issues instead. **EXCEPTIONS**: (1) Use cast when external libraries (e.g., Supabase) return `Any` and you need proper type inference. Example: `return cast(str, result.data["token"])` when `result.data` is typed as `Any` by the library. (2) Use cast in test files when creating test fixtures that need to satisfy TypedDict requirements.
- NO SUPPRESSION: Do not use # pyright: reportArgumentType=false or any other pyright suppression comments. Fix the underlying type issues instead.
- NO ANY: Do not use Any type. Fix the specific type issues instead. `response.json()` returns `Any` - always assign it to a fully typed variable (e.g., `commits: list[dict[str, dict[str, str]]] = response.json()`). `dict` without value types makes `.get()` return `Any` - always specify value types so downstream `.get()` calls return concrete types, not `Any`. Similarly, chaining 2+ `.get()` calls propagates `Any` - break the chain into separate variables.
- NO `.get()` DEFAULTS: Do not use `.get("key", {})` or `.get("key", "")`. Use `.get("key")` and handle `None` explicitly. Defaults hide missing data and make bugs harder to find. When you have to use `as any` in TypeScript/JavaScript, ALWAYS add a comment above explaining why it's needed. Example:
- No annotations: Don't use annotations like var: type = value. Fix the root cause of type issues instead.
- SINGLE RESPONSIBILITY: One file, one function. Don't create 2+ functions in a file. If a helper is used multiple times within the file, keep it as a private function in that file. If it's used only once, inline it. If it's needed by other files, move it to its own file.
- ALWAYS USE `@handle_exceptions` DECORATOR: Every function (sync or async) must use the `@handle_exceptions` decorator from `utils.error.handle_exceptions`. This ensures consistent error handling, Sentry reporting, and logging across the codebase. Use `@handle_exceptions(default_return_value=..., raise_on_error=False)` with an appropriate default return value.
- NO `__init__.py`: Do not create `__init__.py` files. Python 3.3+ supports implicit namespace packages, so `__init__.py` is not required. This project uses Python 3.13.

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

## CRITICAL: NEVER Dismiss Test Failures When Fixing PRs

**NEVER say "this test is not part of this PR" or "our PR's test passed fine" or "this is a pre-existing issue on the base branch".**

This is the WORST possible response. CI failed. The PR is blocked. Fix it.

- Do NOT distinguish between "our test" and "other tests" - ALL failing tests are your problem
- Do NOT blame the base branch, other developers, or previous PRs
- Do NOT report which tests "passed fine" as if that's relevant when CI is red
- When reporting root cause and fix, focus on WHAT failed and HOW you fixed it - not on whose fault it is or which PR introduced it

**BAD (will make user angry):**
- "The failing test ApplicationTest::test_getByApplicationNo is not part of this PR - it's a pre-existing test in the base branch. Our PR's test AnnotationElectricalOutletSpotModelTest passed fine."

**GOOD:**
- "ApplicationTest::test_getByApplicationNo failed because line 351 was missing `application_no` in the factory call. Fixed by adding the missing parameter."

## Proactive Code Fixes

When refactoring or replacing old systems, always be PROACTIVE and think comprehensively. Don't wait for the user to point out every piece of old code that needs to fix.

### Examples of Proactive Fixes

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

6. **Architecture Change Side Effects**: When introducing new architecture (e.g., EFS-based caching):
   - Identify code that becomes OBSOLETE due to the new architecture
   - Example: If packages are now pre-installed on EFS, version extraction code that downloads on-demand is obsolete
   - Example: If we always run from EFS dir, temp_dir fallback is unnecessary
   - Example: Tests that ran real commands may need mocking since the environment changed
   - DON'T wait for the user to ask "why do we still have X?" - proactively find and remove X

### Bad Examples (Reactive)

- User: "You missed schedule_handler.py" → You fix only that file
- User: "What about the test files?" → You then look for tests
- User: "Remove get_billing_type too" → You remove only that
- User: "Why do we still have version extraction?" → You then remove it
- User: "Why temp_dir case?" → You then realize it's obsolete

### Good Examples (Proactive)

- User: "Replace is_request_limit_reached" → You automatically:
  1. Find ALL files using it (handlers, tests, utilities)
  2. Replace ALL usages with new billing system
  3. Remove the old function file
  4. Remove ALL related test files
  5. Search for related functions (request_limit_reached, get_billing_type, etc.)
  6. Remove ALL old functions from that refactoring session
  7. Verify no remaining references exist

- User: "Move package installation to EFS" → You automatically:
  1. Implement EFS-based installation
  2. Find code that assumed on-demand download (version extraction, temp_dir fallback)
  3. Remove ALL obsolete code paths without being asked
  4. Update tests to mock the new EFS dependencies
  5. Rename functions for clarity (e.g., `wait_for_install` → `is_install_ready` for bool return)

**ALWAYS THINK: "What other files/functions/tests are related to this change?" and handle them ALL at once.**

## Long-Term Thinking vs Short-Term Thinking

**CRITICAL**: Don't be single-minded. Think about future use cases, not just current ones.

### Bad (Short-term thinking)

- "This function has only 1 caller, let's inline it" → WRONG if future callers are obvious
- "We only need ESLint check" → WRONG because prettier, tsc, pylint, pyright, flake8 will follow
- Optimizing for current state without considering roadmap

### Good (Long-term thinking)

- "ESLint check needs EFS install ready. What else will need this?" → prettier, tsc, pylint, pyright, flake8
- "This helper has 1 caller NOW, but the pattern will repeat" → Keep it separate
- "We're building Node support. Python and PHP will follow" → Design for extensibility

### Example

When asked "should we inline `is_efs_install_ready.py` since it has 1 caller?":

- SHORT-TERM: "Yes, only run_eslint_fix uses it"
- LONG-TERM: "No, run_prettier_fix, run_tsc, run_pylint, run_pyright, run_flake8 will all need it"

### Rule

ALWAYS ASK: "What similar tools/features will need this in the future?"

## Deep Architectural Thinking

**CRITICAL**: Don't just shuffle code around. Question fundamental assumptions and think about WHY things are the way they are.

### Shallow vs Deep Thinking

**Shallow (BAD)**:
- "Clone is sync, so move it later to avoid blocking" → Just moving WHEN we block, not reducing blocking
- "Make order consistent across handlers" → Consistency for its own sake, without understanding WHY
- "Install first, clone later for parallelism" → Accepting current implementation as given

**Deep (GOOD)**:
- "Clone is sync. WHY is it sync? Do we actually need to wait for it? Clone is used for tsc/tests - we don't need it until chat_with_agent. Should clone be async?"
- "For issue_handler, PR is new so EFS has no packages. But if a nearby PR folder exists, could we copy from it to reduce install time?"
- "For defensive handlers, EFS already has packages from issue_handler. Install will be quick. The real question is whether clone should be async."

### Questions to Ask Yourself

When making architectural decisions, ask "why" 5 times:

1. **Why is this sync/async?** - Is it inherently blocking, or just implemented that way?
2. **Why do we need this here?** - When is the result actually used?
3. **Why this order?** - What dependencies exist? What can run in parallel?
4. **Why can't we optimize?** - What assumptions are we accepting without questioning?
5. **Why is this different per handler?** - Should it be different, or is it just inconsistent?

### Example: Clone and Install Order

**Shallow analysis**:
- "Install is async, clone is sync. Do async first, sync later."

**Deep analysis**:
- Clone is in /tmp, happens every Lambda invocation (not cached)
- For issue_handler: New PR, EFS has no packages. Using GitHub API for install (ignoring clone_dir) is actually efficient - install runs async during clone time
- For defensive handlers: EFS already has packages from issue_handler. Install is quick.
- Real question: Why is clone sync? We only need clone for tsc/tests during chat_with_agent. Could make clone async, start earlier, let it complete in background.
- Optimization idea: For new PRs, if nearest PR folder exists, copy from it instead of fresh clone - might reduce time.

### Anti-Patterns

- **"Keep as is"** - Without deep reasoning for WHY current implementation is correct
- **"Be consistent"** - Consistency is a means, not an end. Each handler may have different requirements.
- **"Move X later"** - Moving blocking work later doesn't reduce total blocking time
- **"This is how it's done"** - Question whether current approach is optimal

### The Right Approach

1. Understand WHAT each operation does (sync vs async, blocking vs non-blocking)
2. Understand WHEN each result is needed (immediately vs later)
3. Question WHY it's implemented this way (inherent limitation vs arbitrary choice)
4. Think about OPTIMIZATIONS (parallel execution, caching, copying from nearby resources)
5. Consider EACH HANDLER's specific context (new PR vs existing PR, empty EFS vs populated EFS)

## Always Write Tests for New Code

**CRITICAL**: When you create new functions/modules, ALWAYS write tests without being asked.

- Don't wait for the user to say "where are the tests?"
- Don't wait until LGTM to realize tests are missing
- Write tests as part of the implementation, not as an afterthought

**Bad**: Create `services/efs/is_efs_install_ready.py` → wait for user to ask for tests
**Good**: Create `services/efs/is_efs_install_ready.py` → immediately create `services/efs/test_is_efs_install_ready.py`

## Critical Thinking for Production Issues

**CRITICAL**: When implementing features, think about production edge cases and real customer scenarios.

### Questions to Always Ask

1. **Authentication/Credentials**: Does this feature need tokens/credentials to work in production?
   - Example: `npm install` needs NPM_TOKEN for private packages (stored in Supabase)
   - Example: GitHub API needs installation token
   - Example: Private registries need authentication

2. **Version/Environment Ambiguity**: Which version of a tool will be used?
   - Example: If EFS has eslint installed, which version runs? (Answer: local node_modules version)
   - Example: If multiple Python versions exist, which one runs?

3. **Customer-Specific Requirements**: What do real customers need?
   - Example: Foxquilt has private npm dependencies → needs NPM_TOKEN
   - Example: Some repos use yarn instead of npm
   - Example: Some repos have monorepo structure

### Bad (Missing Production Issues)

- Implement npm install without thinking about private packages
- Assume all packages are public
- Don't consider authentication requirements

### Good (Catching Production Issues)

- "We're running npm install. What about private packages? Do we have NPM_TOKEN?"
- "Foxquilt uses private deps. Where is the token stored? How do we pass it?"
- "Which eslint version will npx use? The one in node_modules or global?"

## LGTM Workflow

**CRITICAL: NEVER Start LGTM Without Explicit User Request**

- ONLY execute LGTM workflow when the user explicitly says "LGTM" or "lgtm"
- NEVER start LGTM on your own initiative, even if the work seems complete
- NEVER assume the user wants LGTM just because tests pass or code looks ready
- Wait for the user to explicitly request it

**CRITICAL: PR Must Be Clean**

- During LGTM, do NOT ignore unrelated failures or issues found in modified files
- If you find issues unrelated to the current task, do NOT arbitrarily decide to skip them
- Always ASK the user how to proceed when there are mixed changes or unrelated issues
- The PR should be clean - either fix all issues or get explicit user approval to proceed
- When you find unrelated issues, add them to the todo list to fix later - never just skip them silently

When the user explicitly says "LGTM" (Looks Good To Me), execute this workflow:

1. Regenerate TypedDict schemas from database: `python3 schemas/supabase/generate_types.py`
2. Run black formatting: `black .`
3. Run ruff linting: `ruff check . --fix` (fix ALL ruff errors, not just modified files - if any errors remain unfixed, STOP and fix them before continuing)
4. Check for print statements and built-in logging:
   - Run `ruff check --select=T201 . --exclude schemas/,venv/,scripts/` to find print statements - **FIX ALL before continuing** (use custom logger instead)
   - Run `scripts/lint/check_builtin_logging.sh` to find built-in logging imports - **FIX ALL before continuing** (use `from utils.logging.logging_config import logger` instead)
5. **CRITICAL**: Check `git status` FIRST to see ALL changes including deleted/renamed files
6. Get list of modified, created, AND deleted files ONCE: `scripts/git/list_changed_files.sh`
   - This script captures: modified files, staged files, and newly created untracked files
   - NOTE: Deleted files that are already staged won't appear in this list but MUST be included in the commit
   - Store this list and use it for all subsequent steps
   - Extract Python files from this list: filter for `.py` files
   - Extract test files from this list: filter for `test_*.py` files
   - **CRITICAL**: For pylint, pyright, flake8, and pytest, filter out deleted files that no longer exist
7. Run flake8 on the Python files identified in step 6 (excluding deleted files): `flake8 file1.py file2.py file3.py` - **IF ANY FLAKE8 ERRORS/WARNINGS ARE FOUND, FIX THEM ALL BEFORE CONTINUING**
8. Run pylint on the Python files identified in step 6 (excluding deleted files): `pylint file1.py file2.py file3.py` - **IF ANY PYLINT ERRORS/WARNINGS ARE FOUND, FIX THEM ALL BEFORE CONTINUING**
9. Run pyright on the whole repo: `pyright` - **IF ANY PYRIGHT ERRORS/WARNINGS ARE FOUND, FIX THEM ALL BEFORE CONTINUING**
   - For test files with many mock parameters, pyright will warn about unused variables (e.g., `_mock_update_usage is not accessed`)
   - This is expected - test files often have mock parameters that are required by the decorator order but not used in the test
   - Suppress these warnings by adding `# pyright: reportUnusedVariable=false` at the top of the test file (after pylint disables)
10. Run pytest on the test files identified in step 6 (excluding deleted files): `python -m pytest test_file1.py test_file2.py` - **IF ANY TESTS FAIL, FIX THEM ALL BEFORE CONTINUING**
11. Check current branch is not main: `git branch --show-current`
12. Merge latest main: `git fetch origin main && git merge origin/main`
13. **CRITICAL**: Review `git status` again to ensure ALL changes are staged:
    - Add all modified/new files identified in step 6
    - Ensure deleted files are staged (they should already be if renamed with `mv`)
    - Use specific file names: `git add file1.py file2.py file3.py` (**NEVER use `git add .`**)
    - For deleted files already staged, they'll be included automatically in the commit
14. Commit with descriptive message: `git commit -m "descriptive message"`
    - **CRITICAL**: NEVER include Claude Code credits or co-author lines in commit messages
    - NO "🤖 Generated with [Claude Code]" footer
    - NO "Co-Authored-By: Claude <noreply@anthropic.com>" lines
    - NO `[skip ci]` in commit messages as it skips CI
    - Keep commit messages professional and focused on the actual changes
15. **CRITICAL**: Check for existing open PR before pushing: `gh pr list --head $(git branch --show-current) --state open`
    - If an open PR exists, **STOP and ask the user** how to proceed
    - Pushing to a branch with an existing PR will add commits to that PR, potentially mixing unrelated changes
    - Options: close the existing PR, create a new branch, or confirm adding to the existing PR
16. Push to remote: `git push`
17. If the PR includes a Social Media Post section, check recent posts to avoid repeating patterns:
    ```bash
    scripts/git/recent_social_posts.sh gitauto  # GitAuto posts only
    scripts/git/recent_social_posts.sh wes      # Wes posts only
    ```
    Read the output and ensure your new post uses a different sentence structure and opener.
18. Create pull request: `gh pr create --title "PR title" --body "PR description" --assignee @me`. Example:

    ```bash
    gh pr create --title "PR title" --body "$(cat <<'EOF'
    ...
    ## Social Media Post (GitAuto)
    ...
    ## Social Media Post (Wes)
    ...
    EOF
    )" --assignee @me
    ```

    - PR title should be technical and descriptive
    - **Do NOT include a `## Test plan` section** - it's unnecessary noise
    - **Social Media Post sections must always be the last sections in the PR body**
    - **Social Media Post sections**: Only include when there are explicit customer benefits or useful dev insights. Skip for internal-only changes (refactoring, logging fixes, test improvements, infrastructure updates) that don't affect customers or teach anything.
    - Always write TWO posts:
      - **GitAuto post**: Product voice. Can mention GitAuto. Explains what changed and why it matters for users.
      - **Wes post**: Personal voice. Written as Wes (the founder) sharing what he debugged/built. Don't emphasize "GitAuto" — no "GitAuto now does X" pattern. More like telling a friend what you worked on today.
    - Shared guidelines for both posts:
      - **NEVER use em dashes (—)** in social media posts. Use regular dashes (-) or rewrite the sentence instead.
      - Be concise and fit in a tweet (under 280 characters is ideal)
      - **Write for developers, not marketers** - our customers are devs who hate corporate speak
      - **NEVER use typical marketing keywords**: "all-in", "doubling down", "sunsetting", "deeper features", "polished product", "game-changer", "seamless"
      - **NEVER frame things negatively**: "unused", "nobody used", "removing unused" - this is embarrassing
      - **Be straightforward and honest** like a dev talking to other devs
      - **Users don't know GitAuto internals** - They don't know we clone repos, install dependencies, set up working environments, etc. When relevant, educate them on what GitAuto does. NEVER use internal function/variable names (e.g. `verify_task_is_complete`, `clone_dir`) in posts - describe what happened in plain language instead.
      - **Tell the story when there's a real failure** - When you find a real flaw or failure, be transparent. Tell the story: what happened, what went wrong (e.g. Claude misunderstood X, our pipeline missed Y), what the impact was, and how we improved. Developers respect honesty and the story resonates more than hiding it. Frame it as "we found a flaw → it caused X → we improved" not "we fixed a bug".
      - **Sound like a human wrote it** - AI-generated posts are obvious and get ignored. Write like a real dev sharing something they built. Be casual, imperfect, opinionated. No polished marketing tone.
      - **Vary the opening every time** - NEVER use patterns like "GitAuto now...", "We just...", or any formula that gets stale. Start with the substance — what changed, why it matters, or a hook.
      - **Wes post: don't repeat openers** - Before writing, run `scripts/git/recent_social_posts.sh wes` and make sure your opening sentence doesn't use the same structure as any recent post.

19. If fixing a Sentry issue, list similar issues and resolve them:
    - Use `python3 scripts/sentry/get_issue.py AGENT-XXX` to check related issues
    - Use `python3 scripts/sentry/resolve_issue.py AGENT-XXX AGENT-YYY ...` to resolve fixed issues

**CRITICAL GIT RULES:**

- **NEVER EVER use `git add .`** - this adds ALL files including unrelated changes
- **ALWAYS specify exact files**: Use `git diff --name-only HEAD` to see what's changed, then add only those specific files
- **Example**: `git add $(git diff --name-only HEAD)` or list files manually
- **CRITICAL: Recognize new branch push output** - When `git push` shows:

  ```bash
  remote: Create a pull request for 'branch' on GitHub by visiting:
  remote:      https://github.com/owner/repo/pull/new/branch
  * [new branch]        branch -> branch
  ```

  This message means the remote branch didn't exist at push time. Two scenarios:
  1. **If you haven't created a PR yet**: Run `gh pr create` to create the PR.
  2. **If you JUST created a PR and see this message**: The PR was already merged. Create a NEW PR for your new commits.

IMPORTANT: When pylint and pyright show many alerts/errors, focus on fixing issues related to your code changes unless explicitly told to fix all issues. Don't ignore everything, but prioritize errors in files you modified.

**CRITICAL VERIFICATION REQUIREMENT:**

- NEVER claim completion without running ALL checks on ALL modified files
- Must achieve EXACTLY 10.0/10 pylint score and 0 pyright errors
- Must verify ALL tests pass by actually running them
- NEVER say "close to 10.00" or "good progress" - either it's PERFECT or it's NOT DONE
- LAZY CHECKING IS UNACCEPTABLE and will result in punishment
