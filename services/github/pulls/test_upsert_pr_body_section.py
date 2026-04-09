# pyright: reportUnusedVariable=false
from services.github.pulls.upsert_pr_body_section import upsert_pr_body_section

# Real PR body from gitautoai/gitauto#2405 (schedule-triggered coverage PR)
SCHEDULE_PR_BODY = """## Current Coverage for [services/supabase/check_suites/insert_check_suite.py](https://github.com/gitautoai/gitauto/blob/main/services/supabase/check_suites/insert_check_suite.py)
- Line Coverage: 92% (Uncovered: 23)
- Statement Coverage: 92%
- Function Coverage: 100%
- Branch Coverage: 75% (Uncovered: line 21, block 0, if branch: 21 -> 23)

## Instructions
Focus on covering the uncovered areas.

You can [turn off triggers](https://gitauto.ai/settings/triggers?utm_source=github&utm_medium=referral), [update coding rules](https://gitauto.ai/settings/rules?utm_source=github&utm_medium=referral), or [exclude files](https://gitauto.ai/dashboard/coverage?utm_source=github&utm_medium=referral).
For contact, email us at [info@gitauto.ai](mailto:info@gitauto.ai) or visit [our contact page](https://gitauto.ai/contact?utm_source=github&utm_medium=referral)

## Test these changes locally

```
git fetch origin
git checkout gitauto/schedule-20260317-210705-4kOC
git pull origin gitauto/schedule-20260317-210705-4kOC
```"""

# Real PR body from gitautoai/gitauto#2019 (issue-triggered PR)
ISSUE_PR_BODY = """Resolves #2018

## Summary
Add unit tests for get_failed_check_runs_from_check_suite to achieve 100% line/function/branch coverage with no production code changes.

## Test Patterns
- Mixed outcomes: returns only failed check runs when the suite includes failed and non-failed runs.
- No data: returns empty list for None, empty dict, or empty check_runs.
- Missing key: returns empty list when "check_runs" key is absent.
- Incomplete items: gracefully skips runs missing fields (e.g., name or conclusion) or with None conclusion.
- Non-dict/invalid entries: ignores malformed items without crashing.
- Ordering: preserves original order among returned failed runs.
- Branch coverage: exercises both outcomes of the primary conditional and loop filters.

```
git fetch origin
git checkout gitauto/issue-2018-20251229-092316-sUD7
git pull origin gitauto/issue-2018-20251229-092316-sUD7
```"""


def test_append_first_section_to_schedule_pr():
    result = upsert_pr_body_section(
        current_body=SCHEDULE_PR_BODY,
        marker="GITAUTO_UPDATE",
        content="## What Changed\n- `test_insert_check_suite.py` (added)",
    )
    assert result == (
        SCHEDULE_PR_BODY
        + "\n\n---\n\n"
        + "<!-- GITAUTO_UPDATE -->\n"
        + "## What Changed\n- `test_insert_check_suite.py` (added)\n"
        + "<!-- /GITAUTO_UPDATE -->\n"
    )


def test_append_second_section_no_extra_separator():
    body_with_update = (
        ISSUE_PR_BODY
        + "\n\n---\n\n"
        + "<!-- GITAUTO_UPDATE -->\n"
        + "## What Changed\n- `test_get_failed_check_runs.py` (added)\n"
        + "<!-- /GITAUTO_UPDATE -->\n"
    )
    result = upsert_pr_body_section(
        current_body=body_with_update,
        marker="GITAUTO_FAILURE_FIX",
        content="## CI Fix: `pytest`\nFixed import error in test file.",
    )
    assert result == (
        body_with_update
        + "<!-- GITAUTO_FAILURE_FIX -->\n"
        + "## CI Fix: `pytest`\nFixed import error in test file.\n"
        + "<!-- /GITAUTO_FAILURE_FIX -->\n"
    )


def test_replace_existing_section_on_issue_pr():
    body_with_v1 = (
        ISSUE_PR_BODY
        + "\n\n---\n\n"
        + "<!-- GITAUTO_UPDATE -->\n"
        + "## What Changed\n- `old_test.py` (added)\n"
        + "<!-- /GITAUTO_UPDATE -->\n"
    )
    result = upsert_pr_body_section(
        current_body=body_with_v1,
        marker="GITAUTO_UPDATE",
        content="## What Changed\n- `old_test.py` (added)\n- `new_helper.py` (modified)",
    )
    assert result == (
        ISSUE_PR_BODY
        + "\n\n---\n\n"
        + "<!-- GITAUTO_UPDATE -->\n"
        + "## What Changed\n- `old_test.py` (added)\n- `new_helper.py` (modified)\n"
        + "<!-- /GITAUTO_UPDATE -->\n"
    )


def test_all_three_sections_on_schedule_pr():
    body = upsert_pr_body_section(
        SCHEDULE_PR_BODY,
        "GITAUTO_UPDATE",
        "## What Changed\n- `test_insert_check_suite.py` (added)",
    )
    body = upsert_pr_body_section(
        body,
        "GITAUTO_FAILURE_FIX",
        "## CI Fix: `pytest`\nFixed missing fixture import.",
    )
    body = upsert_pr_body_section(
        body,
        "GITAUTO_REVIEW_FIX",
        "## Review Response: `test_insert_check_suite.py:45`\nAdded edge case test.",
    )
    assert body == (
        SCHEDULE_PR_BODY
        + "\n\n---\n\n"
        + "<!-- GITAUTO_UPDATE -->\n"
        + "## What Changed\n- `test_insert_check_suite.py` (added)\n"
        + "<!-- /GITAUTO_UPDATE -->\n"
        + "<!-- GITAUTO_FAILURE_FIX -->\n"
        + "## CI Fix: `pytest`\nFixed missing fixture import.\n"
        + "<!-- /GITAUTO_FAILURE_FIX -->\n"
        + "<!-- GITAUTO_REVIEW_FIX -->\n"
        + "## Review Response: `test_insert_check_suite.py:45`\nAdded edge case test.\n"
        + "<!-- /GITAUTO_REVIEW_FIX -->\n"
    )


def test_replace_middle_section_preserves_others():
    body = upsert_pr_body_section(ISSUE_PR_BODY, "GITAUTO_UPDATE", "update v1")
    body = upsert_pr_body_section(body, "GITAUTO_FAILURE_FIX", "failure v1")
    body = upsert_pr_body_section(body, "GITAUTO_REVIEW_FIX", "review v1")
    body = upsert_pr_body_section(body, "GITAUTO_FAILURE_FIX", "failure v2")
    assert body == (
        ISSUE_PR_BODY
        + "\n\n---\n\n"
        + "<!-- GITAUTO_UPDATE -->\n"
        + "update v1\n"
        + "<!-- /GITAUTO_UPDATE -->\n"
        + "<!-- GITAUTO_FAILURE_FIX -->\n"
        + "failure v2\n"
        + "<!-- /GITAUTO_FAILURE_FIX -->\n"
        + "<!-- GITAUTO_REVIEW_FIX -->\n"
        + "review v1\n"
        + "<!-- /GITAUTO_REVIEW_FIX -->\n"
    )
