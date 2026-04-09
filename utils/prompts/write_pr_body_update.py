from utils.prompts.base_role import BASE_ROLE

WRITE_PR_BODY_UPDATE = f"""
{BASE_ROLE}
You are writing a section for a GitHub PR body that summarizes what an AI coding agent did on this PR. The reviewer will read this to understand the changes at a glance.

Write in GitHub-flavored Markdown. Be concise but specific. Adapt to the actual context - don't use generic filler.

Include:
- What was tested/implemented and why it matters
- Any bugs or potential issues discovered during the work (edge cases, untested paths, workarounds applied). If a bug was found, explain whether it was actually fixed or worked around (e.g. skipped the detecting test). Omit this section entirely if no bugs were found.
- What the reviewer should pay attention to

Template (adapt as needed):
## What GitAuto Did
[1-3 sentence summary of what was done and why]

## Potential Bugs Found
- [Only if bugs/issues were discovered. Describe what was found, whether it was fixed or worked around, and why.]

## Trade-offs & Assumptions
- [Design decisions, why this approach was chosen over alternatives, assumptions made, and uncertainties the reviewer should verify. Omit if straightforward.]

## Reviewer Action Items
- [Non-code tasks after merging: env vars to set, migrations to run, configs to update, docs to change, stakeholders to notify, etc. Omit if none.]
"""
