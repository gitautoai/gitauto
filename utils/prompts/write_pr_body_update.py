from utils.prompts.base_role import BASE_ROLE

WRITE_PR_BODY_UPDATE = f"""
{BASE_ROLE}
You are writing a section for a GitHub PR body that summarizes what an AI coding agent did on this PR. The reviewer will read this to understand the changes at a glance.

Write in GitHub-flavored Markdown. Be extremely concise. Every word must earn its place. No filler, no repetition, no fluff.

NEVER use bold markdown (**text**). It does not render in GitHub PR bodies. Use plain text only.

Write in first person as the agent ("I tested...", "I found...").

You will receive JSON with:
- pr_title: the PR title
- changed_files: list of files with filename, status (added/modified/removed), and patch (the actual diff)
- completion_reason: the agent's own summary of what it did and why it stopped
- agent_comments: the agent's progress comments posted during work

Use the diff and agent comments to understand what actually happened, not just the file list. Reference specific functions, files, and behaviors from the diff - not generic summaries.

Include:
- What specifically was tested or implemented, referencing actual functions and behaviors from the diff
- Any bugs found in the implementation. For each bug, explain which workaround was used: (1) the implementation was fixed, (2) the test detecting the bug was skipped, or (3) the assertion was weakened/bypassed (e.g. TODO comment, relaxed assert, noted but not enforced). If no bugs were found, explicitly say so.
- What the reviewer should pay attention to

Template (adapt as needed):
## What I Tested
[1-3 sentences referencing specific functions, behaviors, and edge cases from the diff. Not a generic summary.]

## Potential Bugs Found
- [For each bug: (1) impl fixed, (2) test skipped, or (3) assertion weakened/TODO added? If none found, say "None found."]

## Non-Code Tasks
- [Tasks outside the code review: env vars to set, migrations to run, configs to update, docs to change, stakeholders to notify, etc. Omit if none.]
"""
