<!-- markdownlint-disable MD029 MD032 MD036 -->
# CLAUDE.md

## CRITICAL: Never Guess - Always Verify

**NEVER use "likely", "probably", "might be", "seems like", "most likely", "somehow".** Verify through: (1) CloudWatch logs, (2) reading actual code, (3) scripts/APIs, (4) database queries. Only state verified facts.

## CRITICAL: Red PRs Are Still Your Problem

If a PR is failing, do not classify failures as "related" or "unrelated" and move on. A red PR stays your problem until you do one of these with evidence:

1. Fix the failing cause in the current PR.
2. Trace the failing cause to a specific previous GitAuto PR, verify it in code/logs, and fix that cause instead of hand-waving it away.
3. Prove the blocker is external and unfixable from the PR branch, with concrete logs/code and an explanation of what was attempted.

Do not use "unrelated failures" as a stopping point. Investigate every blocking failure that keeps the PR red until you have a verified root cause and an action.

## Development Commands

### Shell Environment

The Claude Code shell already has the project `.venv` activated and `.env` loaded — run commands directly without prepending `source .env && source .venv/bin/activate &&`. For pytest specifically, use `python -m pytest ...` (not `pytest ...` or `uv run pytest ...`) so cwd is added to `sys.path` and top-level imports like `from constants.models ...` resolve without setting `PYTHONPATH`.

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
scripts/supabase/tables.sh --dev                              # List all tables (dev)
scripts/supabase/describe.sh --dev users                      # Show columns for a table (dev)
scripts/supabase/query.sh --dev "SELECT * FROM users LIMIT 1" # Run a query (dev, tabular)
scripts/supabase/query.sh --dev -x "SELECT * FROM users LIMIT 1" # Vertical display
scripts/supabase/query.sh --prd "SELECT ..."                  # Run against production
```

### Sentry CLI

```bash
sentry-cli issues list --org gitauto-ai --project agent --query "search terms"
python3 scripts/sentry/get_issue.py AGENT-20N
```

Don't pass `--max-rows`. The CLI defaults already return the full list; capping it means you miss issues that should be resolved but sit below the cap.

Then **just `Read` `/tmp/sentry_agent-20n.json`** — it's small. Don't pipe through `python -m json.tool`, `jq`, or inline `python3 -c`; those fail on quoting and waste retries.

Don't pipe `resolve_issue.py` output through `tail` — each issue prints one line and any failure gets hidden if the truncation window is wrong.

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
- **COMMENTS**: Don't delete unless outdated. Preserve URLs. One line when possible. **Don't hard-wrap sentences mid-thought** — if a comment is two sentences, two lines is fine; but don't break one sentence across multiple lines because it makes the comment unreadable when scanned. Let the editor wrap it visually. Decorative divider bars (e.g. `# =====`, `# -----`) are fine next to prose — they're visual separators, not wrapped sentences.
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
- **Never blindly copy expected values from running the function**: Running the impl to get output is OK, but you MUST manually trace through the logic to verify the result is correct. Understand WHY the output is what it is — don't just paste it. If you can't explain each value, the test is worthless.
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
- **Never stop at "target tests pass"**: If the PR is still red, keep investigating the actual blockers. Passing target tests only means one layer is verified; it does not mean the PR is done.

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
6. Check recent posts to vary openers: scan `.pr-bodies/` (e.g. `ls -t .pr-bodies/ | head -5` then read the most recent files).
7. Write the body to `.pr-bodies/<pr#>.md` (gitignored), then `gh pr edit <number> --body-file .pr-bodies/<pr#>.md`. Re-read the local file when iterating instead of `gh pr view`/fetching from GitHub — the local copy is the source of truth and avoids round-tripping through the API for every edit.
    - Technical, descriptive title. **No `## Summary` and no `## Test plan`** — the commit message and diff already explain what changed; don't restate it. Body is just the social-post sections below.
    - **Six sections** (customer-facing only) — four author × platform cells plus HN title and body. See `## Social Media Rules` below for the voice, length, and style rules for each. Headers (parsed by `extract-social-posts.js`):
      - `## Social Media Post (GitAuto on X)`
      - `## Social Media Post (GitAuto on LinkedIn)`
      - `## Social Media Post (Wes on X)`
      - `## Social Media Post (Wes on LinkedIn)`
      - `## Social Media Post (HN Title)`
      - `## Social Media Post (HN Body)`
    - **Each section is independent.** If a section exists, that post fires; if it's missing, only that post is skipped. No all-or-nothing coupling. HN is the one exception: both `HN Title` and `HN Body` must be present for the HN job to fire.
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

## Social Media Rules

Six sections per PR — four cells of {GitAuto, Wes} × {X, LinkedIn}, plus HN title and body. Don't copy text across platforms — each reader and format is different. Before writing, scan recent files in `.pr-bodies/` to see what openers and angles have been used and vary yours.

**Shared rules (apply to all sections):**

- No em dashes (—). No marketing keywords. No negative framing.
- **No internal identifiers**: don't expose internal tool names, function names, variable names, file paths, or class names. Reword in plain language (e.g., "the tool that reads files" not "get_local_file_content"; "the agent loop" not "chat_with_agent"). Public API terms from documented specs (e.g., Anthropic's `tool_use` / `tool_result` block types) are fine.
- **Banned words**: "harness" (sounds like marketing). Use "agent loop", "agent runner", or "the code around the model" instead.
- No small absolute numbers — use relative language ("30% faster", not "2s faster").
- Honest, technical tone. Specify model names (e.g., "Claude Opus 4.6").
- Customer-facing only — skip test/internal changes.
- **Banned openers** (do not start any post with these or close variants):
  - "Spent the morning [verb-ing]…" and close variants ("Spent the day…", "Spent the weekend…", "Spent N hours…").
  Open with the concrete finding, the before/after, or the user-facing outcome. Never chronological autobiography.
- **No "we broke X and fixed it" framing.** Every PR is a fix of something, so postmortem-style posts on every PR turn the feed into a wall of failures and debrand the product — even when each story is individually true. Frame posts as **capability, outcome, or design decision**, not as confession:
  - Capability: "GitAuto now X" / "X now handles Y case".
  - Outcome: "30% faster PR review" / "200 PRs auto-merged last week".
  - Design decision: "Why we chose X over Y" / "How X works under the hood".
  Confession framing ("we broke X", "we had a bug where…", "we used to do X wrong") is reserved for rare cases where the lesson is genuinely novel and the bug affected customers visibly — and even then, lead with the principle, not the embarrassment. If the only angle is "we fixed our own bug," skip the post.
- **Every post needs business meaning, not just mechanism.** Technical detail without a "so what" reads as inside-baseball and loses non-engineers. Each post must tie the change to one of these outcomes for the reader's business:
  - **Time**: dev hours saved, review latency cut, onboarding faster.
  - **Money**: infra cost down, headcount load lighter, fewer paid incidents.
  - **Risk**: fewer regressions in prod, fewer security holes, fewer compliance gaps.
  - **Throughput**: more PRs shipped, more features out, faster release cadence.
  - **Quality**: higher test coverage, cleaner diffs, fewer review cycles.
  Don't stop at "we refactored the quality gate" — say what an engineering team gets from it (e.g., "your PRs now pass review in one round instead of three"). The mechanism is the evidence; the business outcome is the point.
- **URLs are optional.** Most posts should be pure text. Include a URL only when the post genuinely points somewhere (blog post, docs page, demo). When included, put it inline in the text — X and LinkedIn both auto-expand naked URLs into preview cards from the destination's OG tags.

### GitAuto on X

- **Reader**: devs scrolling fast. First line decides everything.
- **Voice**: product changelog. Terse, factual.
- **Length**: **hard limit 280 chars** (free tier, truncated at 277 + `...` if over).
- **Format**: one-liner headline + tight feature bullets. Each feature on one line. Include items from the PR title.
- **Avoid**: hashtag stuffing, 🧵 threads, self-promotion beyond the changelog fact.

### GitAuto on LinkedIn

- **Reader**: engineering managers, founders, buyers. They care about team throughput, dev time, cost, risk — not about our internal mechanisms. Slower scroll, will click "see more".
- **Voice**: business outcome for the customer. "Your team gets X" / "Engineering leaders can now Y". Not a technical write-up.
- **Length**: **400-800 chars**. Line breaks between sentences for scannability.
- **Format**: lead with the outcome for their team (hours saved, PRs shipped, regressions avoided, cost cut). Keep any mechanism to a single clause, only if it's the evidence that the outcome is real. Skip code, skip internal terminology, skip model names unless the reader would recognize them.
- **Avoid**: technical deep-dives, mechanism-first framing, hashtag spam, emoji walls, tweet-style copy without line breaks, thought-leadership platitudes, postmortems of our own bugs.

### Wes on X

- **Reader**: devs following a build-in-public founder. Looking for signal, humor, and real stories.
- **Voice**: personal. First person. Don't emphasize "GitAuto" — the post is about what you built, not the product.
- **Length**: Wes has **X Premium** so long-form is allowed (up to 25k chars). Use **first 280 chars as a hook** (this is what shows above "Show more"). Expand below the fold with the full story if the lesson deserves it.
- **Format**: counterintuitive findings, specific before/after snippets, design-decision takes. Frame as "here's a thing I figured out" rather than "here's a bug I had".
- **Avoid**: corporate voice, LinkedIn-style "I learned that…" openers, generic advice, starting with the same opener as recent posts, confession-style "I broke X" framing.

### Wes on LinkedIn

- **Reader**: professional network. Engineering leaders, founders, and operators. They want perspective on how to run a product, a team, or a technical business — not a code walkthrough.
- **Voice**: personal, narrative, founder-operator. Don't emphasize "GitAuto". Don't emphasize code.
- **Length**: **600-1200 chars**. Line breaks between thoughts.
- **Format**: observation → implication for how you run engineering/product/business. A decision, a tradeoff, or a principle framed at the team/org/company level, not at the code level.
- **Avoid**: technical deep-dives, code snippets, mechanism-first framing, hashtags, selling, tweet-style copy, overly polished "lesson learned" framing, confession-style "I broke X" framing.

### Hacker News

- **Reader**: senior engineers, skeptical, allergic to marketing. Title is ~90% of the click, but a thin body gets flagged as an ad.
- **Format**: submitted with title + URL + body text. `post-hackernews.js` hardcodes the URL to `https://gitauto.ai?utm_source=hackernews&utm_medium=referral`, so the author only writes title and body. Both sections must be present or the HN job skips.
- **`## Social Media Post (HN Title)`**:
  - **Length**: **≤80 chars**, hard cap (truncated in `post-hackernews.js`).
  - **Voice**: technical and specific. Design-decision framing ("Why X uses Y instead of Z"), mechanism framing ("How X handles Y"), or "Show HN:" for tools. Never changelog-style, never promotional. Postmortem framing about our own bugs is reserved for when the bug was externally visible and the lesson is genuinely novel — don't default to it.
  - **Avoid**: product names as the subject, marketing adjectives ("revolutionary", "powerful", "simple"), vague claims.
- **`## Social Media Post (HN Body)`**:
  - **Length**: **600-2000 chars**. Appears as the top comment on the submission (HN's behavior when both URL and text are provided), so it should stand on its own as a short engineering write-up.
  - **Voice**: engineering write-up. Lead with the concrete problem space, explain the tradeoff or mechanism, show the approach. First person singular or plural is fine.
  - **Format**: prose with short paragraphs. Inline code fences are OK for short snippets. No lists of bullet points dressed up as a post.
  - **Avoid**: restating the title, cross-posting X/LinkedIn copy, extra links back to `gitauto.ai` (URL is already set), emoji, hashtags, confession-framing about our own bugs.
- **Why separate from GitAuto X**: changelog voice (280 char) trims poorly to 80, and HN's audience wants a design/mechanism write-up rather than a product announcement.

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
