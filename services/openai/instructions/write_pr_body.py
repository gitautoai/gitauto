WRITE_PR_BODY = """Based on the provided inputs (issue title, body, changed files, code changes, and etc.), write a GitHub pull request description in GitHub markdown format. Write in the same language as the provided inputs (issue title and body) - for example, if inputs are in English, write in English; if in Japanese, write in Japanese. These code changes were made by you, and you're creating a description for them.

The output format should start with one of these H2 headings based on the type of change:

For bug fixes:
## Why did this issue occur?
[Explain the root cause of the bug]

For feature development:
## Why is this feature needed?
[Explain the necessity and background of this feature]

Then, continue with these common sections:

## What and how are we changing? Why this approach?
[Explain the specific changes and reasoning behind the chosen solution]

## What actions are required from users?
[Detail any necessary user actions or configuration changes]

## How does it work? (Technical details)
[Explain technical aspects, including relevant libraries, functions, commands, or options]

## Is it backwards compatible?
[Address backward compatibility concerns]

## Any other considerations?
[Include additional context, alternative approaches considered, or other relevant information]"""
