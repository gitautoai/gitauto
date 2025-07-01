WRITE_PR_BODY = """Based on the provided inputs (issue title, body, changed files, code changes, etc.), write a concise pull request description using GitHub-flavored Markdown. Adapt the format based on the PR type:

If this PR adds or updates test cases, include:
## Summary
[One-line summary of test additions or changes]

## Test Patterns
- [List primary test scenarios or edge cases covered]

## Notes
[Optional: additional context or instructions]

Otherwise (bug fix or feature):
## Summary
[One-line summary of the change]

## Changes
- [Key changes]

## Impact
[Backward compatibility or required actions]"""
