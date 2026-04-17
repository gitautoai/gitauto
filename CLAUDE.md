<!-- markdownlint-disable MD029 MD032 MD036 -->
# CLAUDE.md

## CRITICAL: Never Guess - Always Verify

**NEVER use "likely", "probably", "might be", "seems like", "most likely", "somehow".** Verify through: (1) CloudWatch logs, (2) reading actual code, (3) scripts/APIs, (4) database queries. Only state verified facts.

## Development Commands

### Running Locally

```bash
./start.sh
```

### Code Quality

```bash
pre-commit run --all-files

# When adding new dependencies (prod)
uv add package_name
# When adding new dev dependencies (linters, test tools, type stubs)
uv add --group dev package_name
```

### Database Access

```bash
scripts/supabase/tables.sh                              # List all tables (dev)
scripts/supabase/describe.sh users                      # Show columns for a table (dev)
scripts/supabase/query.sh "SELECT * FROM users LIMIT 1" # Run a query (dev, tabular)
scripts/supabase/query.sh -x "SELECT * FROM users LIMIT 1" # Vertical display
scripts/supabase/query.sh --prod "SELECT ..."           # Run against production
```

### Sentry CLI

```bash
source .env && sentry-cli issues list --org gitauto-ai --project agent --query "search terms"
python3 scripts/sentry/get_issue.py AGENT-20N
cat /tmp/sentry_agent-20n.json | python -m json.tool | grep -A 10 -B 5 "error_keyword"
```

### AWS CLI

Configured for us-west-1. **Always `--start-from-head`** with `get-log-events`.

```bash
python3 scripts/aws/filter_log_events_across_streams.py --hours 12 --owner Foxquilt --repo foxcom-forms --pr 1089
```

## Architecture

**GitAuto runs on AWS Lambda**, not client environments. Infrastructure via CloudFormation:

- `Dockerfile` - Lambda container image
- `infrastructure/setup-infra.yml` - VPC, NAT, S3, CodeBuild
- `infrastructure/deploy-lambda.yml` - Lambda function and IAM role

**Lambda constraints**: 900s timeout, 10GB disk, 3GB RAM. Never assume numbers are reasonable without measuring on Lambda. Local experiments are meaningless.

**Platform-agnostic**: Use local git ops (via /tmp clones) over GitHub API. Exception: `get_github_file_tree` for file coverage before clone completes.

### Testing Strategy

- Co-located: `test_*.py` alongside source code
- MUST have both solitary (mocked) AND sociable (real dependencies) tests. Sociable tests prove functions compose correctly (e.g., git clone → fetch → checkout must produce a working repo).
- Git sociable tests: `local_repo` fixture from `services/git/conftest.py`, `@pytest.mark.integration`

## Coding Standards

- **No DOCSTRINGS**: Don't add unless told. Don't delete existing unless outdated.
- **COMMENTS**: Don't delete unless outdated. Preserve URLs. One line when possible.
- **LOGGERS**: Every `continue`, `break`, `return` inside a function MUST have a preceding `logger.info(...)` (or warning/error). Also log at every conditional branch to show which path was taken.
- **`set_xxx` EARLIEST**: Call `set_trigger`, `set_owner_repo`, `set_pr_number` etc. at the earliest point in each handler, right after the value is known.
- **Don't repeat structured log context**: `set_owner_repo` in `main.py` already adds `owner_repo` to every log entry. Don't repeat owner/repo in individual logger messages.
- **`target_branch` is for custom overrides only**: Empty = use default branch at runtime via `get_default_branch()`. This is correct because repos may change their default branch.
- **API URLS**: Verify via WebFetch before using.
- **NO `->` return type hints**: Can't validate at runtime.
- **NO `type: ignore`**: Fix underlying issues.
- **NO `cast`**: Exception: external libs returning `Any` or test fixtures for TypedDict.
- **NO `Any`**: Use specific types. Break `.get()` chains to avoid `Any` propagation.
- **NO `.get()` defaults**: Use `.get("key")` + handle `None`. No `.get("key", {})`.
- **No `var: type = value` annotations**: Fix root cause.
- **SINGLE RESPONSIBILITY**: One file, one function. No `_`-prefixed private functions. Inline or own file.
- **KEEP `main.py` THIN**: Routing only.
- **ALWAYS `@handle_exceptions`**: From `utils.error.handle_exceptions` with `default_return_value=...`, `raise_on_error=False`.
- **NO `__init__.py`**: Python 3.13 implicit namespace packages.

## Testing Standards

- **Auto-write tests**: When creating functions or fixing bugs, always write tests. Bug fix tests must fail without the fix.
- **Real captured output only**: BEFORE writing test data, search for existing fixtures (`**/fixtures/*.json`, `**/test_messages.json`) and real data sources (Supabase `llm_requests` table, AWS CloudWatch logs). Use full captured data AS-IS — no stripping, minimizing, or partial extraction. Never hand-craft test dicts when real data exists. If function operates on a subset, test should slice the fixture the same way production code does.
- **Never generate expected output from the function under test**: That's circular. Create expected fixtures independently.
- **Real cloned repos**: At `../owner/repo`. Run against real repos, never make up file paths.
- **ZERO toy tests**: Use full `git ls-files` output as fixtures (hundreds/thousands of files, not 4). Save as fixture files, assert specific real mappings verified manually. Never curate a minimal list.
- **Meaningful tests**: Verify actual behavior. No import-only, mock-everything, or string-presence tests.
- **Assert exact values with `==`**: NEVER `assert X not in result` or `assert result != Y`. Always assert exact expected return value, regardless of data size. Look at real data first — never use function output as expected value.

```python
# WRONG
assert "foo.integration.test.ts" not in result
# RIGHT
assert find_test_files("foo.ts", all_files, None) == ["foo.test.ts"]
```

- **Never dismiss test failures**: ALL failing tests are your problem. Fix them. No "pre-existing", no `git stash` to check, no proving "not GA's fault."

## Thinking Principles

1. **Ask "why" 5 times**: Question every assumption — yours and the codebase's.
2. **Multiple angles**: Ask BOTH "can we skip it?" AND "can we make it faster?"
3. **Think long-term**: Before inlining a 1-caller helper, consider the roadmap.
4. **Be proactive**: When refactoring, search ALL usages (imports, calls, tests) automatically.
5. **Production edge cases**: Auth/credentials? Tool versions? Customer-specific requirements?

## LGTM Workflow

**CRITICAL: NEVER start without explicit user request. PR must be clean — don't ignore failures.**

1. `git fetch origin main && git merge origin/main`
2. `git commit -m "descriptive message"` — user has already run `git add` before saying "lgtm"
   - Pre-commit hook runs automatically (see `scripts/git/pre_commit_hook.sh`): pip-freeze, generate-types, black, ruff, print/logging checks, then pylint + pyright + pytest concurrently
   - Install: `ln -sf ../../scripts/git/pre_commit_hook.sh .git/hooks/pre-commit`
   - **If hooks fail**: fix, re-stage, commit again. Don't stage other sessions' files.
   - **`--no-verify`** only for trivial non-code changes
   - Unused mock params: `# pyright: reportUnusedVariable=false` at top
   - NO co-author lines or `[skip ci]`
3. Check for existing PR: `gh pr list --head $(git branch --show-current) --state open` — if exists, **STOP and ask**
4. `git push`
5. `gh pr create --title "PR title" --body "" --assignee @me` — create PR immediately, no body
6. Check recent posts: `scripts/git/recent_social_posts.sh gitauto` and `scripts/git/recent_social_posts.sh wes`
7. `gh pr edit <number> --body "..."` — add summary and social posts after checking recent posts
    - Technical, descriptive title. **No `## Test plan`**.
    - **Two posts** (last section, customer-facing only): GitAuto (changelog) + Wes (personal voice, don't emphasize "GitAuto")
    - Format: `## Social Media Post (GitAuto)` and `## Social Media Post (Wes)` headers (parsed by `extract-social-posts.js`)
    - **GitAuto post**: Changelog format — one-liner headline + change bullets. No storytelling.
    - **Wes post**: Honest stories. Vary openers — check recent posts first.
    - Guidelines: No em dashes (—). Under 280 chars. No marketing keywords. No negative framing. No internal names. No small numbers — use relative language.
8. If Sentry issue: `python3 scripts/sentry/get_issue.py AGENT-XXX` then `python3 scripts/sentry/resolve_issue.py AGENT-XXX ...`
9. **Blog post** in `../website/app/blog/posts/`:
    - `YYYY-MM-DD-kebab-case-title.mdx`. Universal dev lesson, not GitAuto internals (exception: deep technical content).
    - **Skip if lesson is thin** — argue back if no real insight.
    - `metadata.title`: **34-44 chars** (layout appends `- GitAuto Blog` for 50-60 total). Verify no duplicate slug.
    - No customer names. Honest, technical tone. Specify model names (e.g., "Claude Opus 4.6").
    - MDX header:

      ```javascript
      export const metadata = {
        title: "34-44 chars",
        description: "110-160 chars SEO description",
        slug: "kebab-case-slug",
        alternates: { canonical: "/blog/kebab-case-slug" },
        openGraph: { url: "/blog/kebab-case-slug" },
        author: "Wes Nishio",
        authorUrl: "https://www.linkedin.com/in/hiroshi-nishio/",
        tags: ["relevant-tags"],
        createdAt: "YYYY-MM-DDTHH:MM:SS-07:00",
        updatedAt: "YYYY-MM-DDTHH:MM:SS-07:00",
      };
      ```

    - Body: `# Title`, what happened, root cause, fix, prevention. 300-600 words.
    - If model failure: explain WHY the model failed and what gap GitAuto fills.
    - Language-agnostic framing with parallel examples.
    - **Blog cover image** (REQUIRED): One image at `../website/public/og/blog/{slug}.png` (1200x630) serves three purposes: OG meta tags, Dev.to `main_image`, and in-post cover (rendered by `app/blog/[slug]/layout.tsx`). Non-blog OG images are auto-generated by `generate-og-images.yml`.
      - **Literal and obvious, not artsy**: Search for the post's core concept directly. E.g., "let your agent forget" → "eraser chalkboard" (literal), NOT "sand wind disappearing" (too abstract/pretentious). Keep it simple and immediately recognizable.
      - Unsplash API: `source .env && curl "https://api.unsplash.com/search/photos?query=QUERY&orientation=landscape&client_id=$UNSPLASH_ACCESS_KEY"`, download with `?w=1200&h=630&fit=crop&crop=entropy`
      - Convert to PNG: `sips -s format png downloaded.jpg --out ../website/public/og/blog/{slug}.png`
      - Dev.to crops to 1000x420 — keep important content centered.
10. **Docs page** in `../website/app/docs/`: Create new or update existing. Browse for best-fit category. New pages: 3 files (`page.tsx`, `layout.tsx`, `jsonld.ts`).

## CRITICAL: Fixing Foxquilt PRs

**NEVER run checkout_pr_branch_and_get_circleci_logs.py multiple times in parallel!** Each run overwrites the previous checkout. Work ONE PR at a time: get logs → fix → commit → push → next.

1. **Find root cause**: WHY did it fail? What was the actual error?
2. **Fix it**: Don't stop at "infrastructure issue" or "unrelated to PR". Don't offer options.
3. **Prevent recurrence**: Can GitAuto logic prevent this mistake?

**CRITICAL GIT RULES:**

- **NEVER `git add .`** — always specify exact files
- **NEVER `git checkout`** — can discard staged changes
- **NEVER `gh pr merge`** — merging is the user's decision
- **After every `git push`**, check for PR: `gh pr list --head $(git branch --show-current) --state open`. If none, create immediately.
- **NEVER skip blog + docs steps** in the LGTM workflow

**CRITICAL VERIFICATION:**

- NEVER claim completion without running ALL checks
- Must achieve 10.0/10 pylint, 0 pyright errors, ALL tests passing
- Either PERFECT or NOT DONE
