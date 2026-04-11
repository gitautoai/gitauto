<!-- markdownlint-disable MD029 MD032 MD036 -->
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## CRITICAL: Never Guess - Always Verify

**NEVER use words like "likely", "probably", "might be", "seems like", "most likely", "somehow" when diagnosing bugs or explaining root causes.**

Always verify through: (1) AWS CloudWatch logs, (2) reading actual code, (3) scripts/APIs for actual data, (4) database queries. Only state verified facts.

## Development Commands

### Running Locally

```bash
./start.sh
```

### Code Quality

```bash
pre-commit run --all-files

# When adding new dependencies
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
# - Always use SELECT * ... LIMIT 1 with -x first to see schema before narrowing columns
# - Use -c "SELECT ..." for single queries
# - Use -x for vertical display when rows have many columns or wide values
```

**CRITICAL: Do NOT use pipes with psql commands** - pipe causes env vars to not expand. Use SQL LIMIT/LEFT() instead.

### Sentry CLI

```bash
# List issues
source .env && sentry-cli issues list --org gitauto-ai --project agent --query "search terms"

# Get detailed issue info (saves to /tmp/sentry_<issue_id>.json)
python3 scripts/sentry/get_issue.py AGENT-20N

# Search saved JSON for keywords
cat /tmp/sentry_agent-20n.json | python -m json.tool | grep -A 10 -B 5 "error_keyword"
```

### AWS CLI

AWS CLI is configured for us-west-1. **Always use `--start-from-head`** with `get-log-events` or results may be empty.

```bash
# Searching CloudWatch Logs (preferred method)
python3 scripts/aws/filter_log_events_across_streams.py --owner Foxquilt --repo foxcom-forms --pr 1089
python3 scripts/aws/filter_log_events_across_streams.py --hours 24 --owner Foxquilt --repo foxcom-forms

# SSH to NAT Instance
ssh -i infrastructure/nat-instance-ssh-private-key.pem ec2-user@54.176.165.89
```

## Architecture Overview

**CRITICAL**: GitAuto runs on AWS Lambda, not in client environments. Infrastructure is managed via CloudFormation:

- `Dockerfile` - Lambda container image
- `infrastructure/setup-infra.yml` - VPC, NAT, S3, CodeBuild project and IAM role
- `infrastructure/deploy-lambda.yml` - Lambda function and IAM role

### Testing Strategy

- Co-located tests alongside source code, pattern: `test_*.py`
- MUST have both solitary tests (mocked dependencies) AND sociable tests (real dependencies). Solitary tests verify individual function logic; sociable tests verify the chain of calls actually works end-to-end. Without sociable tests, we don't know if functions compose correctly in practice. Example: git clone → fetch → checkout must produce a working repo; mocking each individually doesn't prove the chain works.
- Git sociable tests: Use `local_repo` fixture from `services/git/conftest.py`, mark with `@pytest.mark.integration`.

## Platform Agnostic

We aim to be platform-agnostic. Avoid relying on GitHub API as much as possible. Use local git operations (via /tmp clones) instead. Only use GitHub API when there's no alternative, e.g. `get_github_file_tree` exists because a user can install GitAuto and immediately visit the file coverage page before the local clone completes.

## Coding Standards

- **No DOCSTRINGS**: Don't add unless explicitly told to. Don't delete existing unless outdated.
- **COMMENTS**: Don't delete existing unless outdated. Preserve URL references. Keep on one line when possible.
- **LOGGERS**: Every `continue`, `break`, and `return` inside a function MUST be preceded by a `logger.info(...)` (or warning/error) call. Silent exits make debugging impossible.
- **API URLS**: Always verify API documentation URLs using WebFetch before using them.
- **NO TYPE HINTS USING ->**: Return type hints are PROHIBITED - they can't be validated at runtime.
- **NO TYPE: IGNORE / NO SUPPRESSION**: Fix underlying type issues instead of suppressing.
- **NO CAST**: Exception: use cast when external libraries return `Any` or in test fixtures for TypedDict.
- **NO ANY**: Always use specific types. `response.json()` must be assigned to a fully typed variable. Break `.get()` chains into separate variables to avoid `Any` propagation.
- **NO `.get()` DEFAULTS**: Use `.get("key")` and handle `None` explicitly. No `.get("key", {})` or `.get("key", "")`.
- **No annotations**: Don't use `var: type = value`. Fix root cause of type issues.
- **SINGLE RESPONSIBILITY**: One file, one function. No `_`-prefixed private functions — either inline the logic or give it its own file. Move to own file if reused.
- **KEEP `main.py` THIN**: Entrypoint for routing only. Logic lives in its own file.
- **ALWAYS USE `@handle_exceptions` DECORATOR**: From `utils.error.handle_exceptions`. Use `@handle_exceptions(default_return_value=..., raise_on_error=False)`.
- **NO `__init__.py`**: Python 3.13 implicit namespace packages.

## Testing Standards

### Write tests automatically

When you create new functions/modules OR fix a bug, ALWAYS write tests without being asked. Bug fix tests should fail without the fix and pass with it.

### Use real captured output, not synthetic data

When testing code that parses external tool output (Jest, ESLint, git, CI logs, etc.), capture real output from the actual tool. Synthetic data can mask bugs (e.g., we assumed Jest writes PASS/FAIL to stdout, but it actually uses stderr).

Process: Run the real tool, capture stdout/stderr separately, verify which stream has what, use as fixture constants with documentation of source.

**Save raw data as-is — stripping or extracting parts is PROHIBITED.** If the raw data from the database/API has a prefix, wrapper, or extra fields, save the whole thing. Partial extraction is not "real data" — it's synthetic data with extra steps. If the function under test only operates on a subset, the test should slice the raw fixture the same way the production code does.

### Never generate expected output from the function under test

Using the function to generate its own expected output is circular and proves nothing. If the function has a bug, the expected output will have the same bug, and the test will pass. Expected fixtures must be created independently — by manual editing, external tools, or verified hand calculations.

### Use real cloned repos for integration-style tests

Customer repos are cloned at `../owner/repo` (e.g., `../Foxquilt/foxcom-forms`, `../SPIDERPLUS/SPIDERPLUS-web`). When testing functions that operate on file trees (find_test_files, prioritize_test_files, etc.), run them against real repos to get real data, then use that data in tests. Never make up file paths — verify they exist first.

### ZERO toy tests

**Toy tests are POINTLESS and PROHIBITED.** A test with a curated 4-item list proves nothing — any broken logic still passes because there's no real noise to filter through. Think mutation testing: if an "evil coder" could change a key value and your tests still pass, your tests are worthless.

**ALWAYS use real full-scale data:**
1. Run `git ls-files` (no filtering, no `head`) on real cloned repos
2. Save the FULL output as fixture files (e.g., `utils/files/fixtures/foxcom-forms.txt`)
3. Load fixtures in tests and run the function against the full file list (389, 1659, 13608 files — not 4)
4. Assert specific real impl→test mappings that you verified manually

**Never curate a minimal `all_files` list.** The whole point is that the function must filter through hundreds/thousands of real files to find the right match. That's what catches real bugs.

### Write meaningful tests

Tests must verify actual behavior, not just that code compiles. No tests that only check imports, mock everything, or verify string presence in source code.

### Assert what the result IS, never what it ISN'T

**NEVER write `assert X not in result` or `assert result != Y`.** These are lazy assertions that don't verify correct behavior - they only verify one wrong answer is absent while accepting infinite other wrong answers.

**ALWAYS assert the exact expected return value with `==`**, regardless of data size. If the input fixture is 600K, save the expected output as a 600K fixture file and assert `result == expected`. Never skip exact matching because the data is "too big" — that's exactly when partial assertions miss bugs.

```python
# WRONG - proves nothing, passes even if function returns garbage
assert "foo.integration.test.ts" not in result

# WRONG - checks individual fields but misses unexpected mutations elsewhere
assert result[0]["content"][0]["input"]["old_string"] == "[Outdated search text removed]"

# RIGHT - verifies the function returns exactly what we expect
assert find_test_files("foo.ts", all_files, None) == ["foo.test.ts"]

# RIGHT - exact match against full expected fixture, catches any unintended change
with open("fixtures/expected_output.json") as f:
    expected = json.loads(f.read())
assert result == expected
```

**Before writing an assertion**, look at the real data (repo fixtures, actual files) to determine what the correct answer is. Then assert that exact answer. Never run the function first and use its output as the expected value - that's circular and just tests that the function returns what it returns.

### NEVER dismiss test failures when fixing PRs

**NEVER say "this test is not part of this PR" or "this is a pre-existing issue".** CI failed. The PR is blocked. ALL failing tests are your problem. Focus on WHAT failed and HOW you fixed it.

## Thinking Principles

These principles apply to ALL architectural decisions, debugging, and feature work:

1. **Ask "why" 5 times**: Don't accept existing code at face value. Question every assumption - yours and the codebase's. "Why is this sync?" → "Why do we need it here?" → "When is the result actually used?" → etc.

2. **Think multiple angles simultaneously**: When something is slow/broken, always ask BOTH "can we skip/avoid it entirely?" AND "can we make it faster?" in parallel.

3. **Think long-term**: Before inlining a helper with 1 caller, ask what similar features will need it. Design for the roadmap, not just the current state.

4. **Be proactive, not reactive**: When refactoring, AUTOMATICALLY search for ALL usages (imports, calls, tests, related functions). Don't wait for the user to point out missed files. Always think: "What other files/functions/tests are related to this change?"

5. **Think about production edge cases**: Authentication/credentials needed? Which tool version runs? Customer-specific requirements (private packages, monorepos, yarn vs npm)?

## LGTM Workflow

**CRITICAL: NEVER Start LGTM Without Explicit User Request**

**CRITICAL: PR Must Be Clean** - Don't ignore unrelated failures. Ask the user how to proceed with mixed issues.

When the user explicitly says "LGTM", execute this workflow:

1. Check `git status` to see ALL changes including deleted/renamed files
2. Get changed files: `scripts/git/list_changed_files.sh` - store for staging reference
3. Check current branch is not main: `git branch --show-current`
4. Merge latest main: `git fetch origin main && git merge origin/main`
5. Stage only files related to YOUR task (**NEVER `git add .`**). Multiple Claude sessions may be working on this repo simultaneously, so `git status` may show changes from other sessions. Only stage files you created or modified for this specific task. If unsure whether a file is yours, check its content to determine if it's related to your task.
6. Commit: `git commit -m "descriptive message"`
   - Git pre-commit hook runs automatically (see `scripts/git/pre_commit_hook.sh`):
     - Sequential: pip-freeze, generate-types, black, ruff --fix, print check, builtin logging check
     - Then concurrent: pylint + pyright + pytest (via `scripts/lint/pre_commit_parallel_checks.sh`)
   - Install hook once: `ln -sf ../../scripts/git/pre_commit_hook.sh .git/hooks/pre-commit`
   - **If hooks fail**: fix issues, re-stage affected files, commit again. Repeat until all pass. If a test failure is caused by another session's unstaged changes, fix the test but do NOT stage the other session's files. Only stage your fix to the test file.
   - **Use `--no-verify`** for trivial amendments that don't change code logic (e.g., removing a file, fixing a typo in a comment, re-staging after a hook-only change). Don't re-run the full test suite for non-code changes.
   - For test files with unused mock parameters, add `# pyright: reportUnusedVariable=false` at top
   - NO Claude Code credits, co-author lines, or `[skip ci]`
7. Check for existing open PR: `gh pr list --head $(git branch --show-current) --state open`
   - If exists, **STOP and ask user**
8. Push: `git push`
9. If PR includes Social Media Posts, check recent posts to avoid repeating patterns:

    ```bash
    scripts/git/recent_social_posts.sh gitauto
    scripts/git/recent_social_posts.sh wes
    ```

10. Create PR: `gh pr create --title "PR title" --body "PR description" --assignee @me`
    - PR title: technical and descriptive
    - **No `## Test plan` section**
    - **Social Media Post sections must be last** and only for customer-facing changes
    - Always write TWO posts:
      - **GitAuto post**: Product voice. What changed and why it matters for users.
      - **Wes post**: Personal voice. Either short/punchy (1 line) or long/educational (like Karpathy). Don't emphasize "GitAuto". No "traced X, found Y, fixed Z" pattern.
    - Shared guidelines:
      - **No em dashes (—)** - use regular dashes or rewrite
      - Under 280 chars ideal. Write for devs, not marketers.
      - No marketing keywords ("game-changer", "seamless", "doubling down", etc.)
      - No negative framing ("unused", "nobody used", "removing unused")
      - No internal names (function names, variable names, component names like "schedule handler", "new_pr_handler", etc.) - describe behavior in plain language
      - When there's a real failure, tell the honest story
      - Sound human. Vary openers every time - check `scripts/git/recent_social_posts.sh wes` first.
      - **No small numbers** - Don't expose specific dollar amounts or metrics that look trivial to readers (e.g. "$76/mo savings"). Use relative language instead ("biggest line item", "most of our costs"). Only include numbers that would impress the audience.
11. If fixing a Sentry issue, resolve related issues:
    - `python3 scripts/sentry/get_issue.py AGENT-XXX` to check related
    - `python3 scripts/sentry/resolve_issue.py AGENT-XXX AGENT-YYY ...` to resolve
12. **Write a blog post** in `../website/app/blog/posts/`:
    - **Filename**: `YYYY-MM-DD-kebab-case-title.mdx`
    - **Content**: Must be useful for developers in general, not just GitAuto internals. Extract the universal engineering lesson (e.g., mutation testing, log deduplication, content-based diffs) and make that the focus. Use the GitAuto story as the vehicle, not the destination. Exception: highly technical and advanced internal content is acceptable when it showcases deep engineering capability that developers would find interesting (e.g., novel algorithms, unsolved problems, trade-off analysis across approaches).
    - **Skip if lesson is thin**: Before writing, genuinely think about what a developer would learn from reading this. If the fix was a trivial config change, the debugging was straightforward, and there's no surprising or counterintuitive insight, argue back that a blog post isn't worth writing. Not every PR deserves a blog post. Only write when there's a real lesson developers would find valuable.
    - **Title length**: The blog layout appends `- GitAuto Blog` (16 chars) to the title, and the meta title must be 50-60 chars total. So `metadata.title` must be **34-44 characters**. Always count before committing.
    - **Title MUST vary**: (1) check `ls ../website/app/blog/posts/ | tail -10`, (2) verify no duplicate: `ls ../website/app/blog/posts/ | grep "your-slug-without-date"`
    - **No customer names**: Customer repo names, org names, and identifiable details are private. Use generic descriptions ("a React app", "~400 files") instead of specific names ("foxcom-forms", "SPIDERPLUS-web"). Approximate numbers instead of exact counts that could identify repos.
    - **Tone**: Honest, transparent, technical. Written for developers.
    - **Be specific about model names**: When referring to "the agent" or "the model", always specify the exact model (e.g., "Claude Opus 4.6") at least on first mention. Don't just say "an LLM" or "the agent" - readers want to know which model exhibited the behavior.
    - **MDX header format**:

      ```javascript
      export const metadata = {
        title: "34-44 chars (layout appends ' - GitAuto Blog' to reach 50-60)",
        description: "110-160 chars. SEO description of the failure and fix.",
        slug: "kebab-case-matching-filename-without-date",
        alternates: { canonical: "/blog/kebab-case-slug" },
        openGraph: { url: "/blog/kebab-case-slug" },
        author: "Wes Nishio",
        authorUrl: "https://www.linkedin.com/in/hiroshi-nishio/",
        tags: ["vary-tags-based-on-the-specific-failure-and-fix"],
        createdAt: "YYYY-MM-DDTHH:MM:SS-07:00",
        updatedAt: "YYYY-MM-DDTHH:MM:SS-07:00",
      };
      ```

    - **Body**: `# Title` heading, then: what happened, root cause, the fix, prevention. 300-600 words, use code blocks and bullet points.
    - **Explain why the model couldn't solve it**: When the post involves a failure by Claude Opus or another model, include a section explaining WHY the model failed. People believe top models can solve anything - explain the specific gap (e.g., models reason about code not environments, models trust config files without verifying which one the runner reads, training data reinforces common patterns over rare config bugs). Position GitAuto's value as the application layer that fills what the model lacks, not as a replacement for the model.
    - **Language-agnostic framing**: GitAuto is language-agnostic. When writing about a language-specific case (e.g., Jest/React), frame it as one example of a universal pattern and mention parallel examples in other languages (e.g., pytest/tox, JUnit/Maven, RSpec).
13. **Create or update a documentation page** in `../website/app/docs/`:
    - **Create NEW page** if the fix introduces a new capability not covered by existing docs
    - **Update existing page** if improving documented capability
    - **Choose the right section**: Browse `ls ../website/app/docs/` for best-fit category - don't default to `how-it-works/`
    - **New page structure**: 3 files (`page.tsx`, `layout.tsx` with `createPageMetadata()`, `jsonld.ts`). Read a nearby page to match patterns.

**CRITICAL GIT RULES:**

- **NEVER use `git add .`** - always specify exact files
- **After every `git push`, check if a PR exists**: Run `gh pr list --head $(git branch --show-current) --state open` after every push. If no PR exists, run `gh pr create` immediately. Do NOT skip this step. Do NOT assume a PR exists.

**CRITICAL VERIFICATION REQUIREMENT:**

- NEVER claim completion without running ALL checks
- Must achieve EXACTLY 10.0/10 pylint score and 0 pyright errors
- Must verify ALL tests pass by actually running them
- Either it's PERFECT or it's NOT DONE
