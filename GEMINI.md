# GEMINI Mandates

- **Command Execution:** Do not run multiple shell commands in a single `run_shell_command` call unless they are strictly dependent or logically required to be executed together. Favor individual, sequential command calls to maintain clear audit trails and error boundaries.
- **Git Operations:** When undoing an unintended commit, prioritize using `git reset --soft` to maintain the staged status of changes, unless a hard reset is explicitly required.
- **Scope Integrity:** Never touch, revert, or modify changes in files that are unrelated to the current task or that were already present in the workspace, unless explicitly instructed by the user. Do not assume any staged or modified files are "accidental" residues.

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
      - **Wes post**: Personal voice. Pick ONE of these formats:
        - **Short**: 1 line what you did. Or 1 line sarcastic/witty commentary. Keep it punchy.
        - **Long**: A real technical insight that teaches the reader something (like Andrej Karpathy's posts). Deep, opinionated, educational. Worth reading even if you don't use GitAuto.
        - Don't emphasize "GitAuto" — no "GitAuto now does X" pattern. NEVER use the "traced X, found Y, fixed Z" pattern. That's a bug report, not a post.
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
