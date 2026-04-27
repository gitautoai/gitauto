# pyright: reportUnusedVariable=false
# pylint: disable=unused-argument
from unittest.mock import MagicMock, patch

from services.git.deepen_until_merge_base import deepen_until_merge_base


@patch("services.git.deepen_until_merge_base.run_subprocess")
def test_skips_when_merge_base_already_exists(mock_run):
    """Happy path: an earlier operation already deepened the clone. merge-base resolves on the first try and we don't fetch any extra history."""
    mock_run.return_value = MagicMock(stdout="abc123\n")

    result = deepen_until_merge_base("/tmp/repo", "main")

    assert result is True
    mock_run.assert_called_once_with(
        ["git", "merge-base", "HEAD", "origin/main"], "/tmp/repo"
    )


@patch("services.git.deepen_until_merge_base.run_subprocess")
def test_first_deepen_finds_merge_base(mock_run):
    """Initial merge-base check fails (shallow clone), deepen by 100, retry succeeds. Asserts the schedule starts at 100."""
    call_log = []

    def mock_subprocess(args, cwd):
        call_log.append(args)
        if args[:2] == ["git", "merge-base"] and len(call_log) == 1:
            raise ValueError("Command failed: fatal: Not a valid commit")
        return MagicMock(stdout="")

    mock_run.side_effect = mock_subprocess

    result = deepen_until_merge_base("/tmp/repo", "main")

    assert result is True
    assert call_log[0] == ["git", "merge-base", "HEAD", "origin/main"]
    assert call_log[1] == ["git", "fetch", "--deepen", "100", "origin", "main"]
    assert call_log[2] == ["git", "merge-base", "HEAD", "origin/main"]
    assert len(call_log) == 3


@patch("services.git.deepen_until_merge_base.run_subprocess")
def test_exponential_climbs_through_schedule(mock_run):
    """When the first few deepens don't reach the merge-base, the schedule climbs 100 -> 500 -> 2500. At 2500 merge-base resolves. Locks the geometric step in place — if the schedule changes, this test must change."""
    deepen_attempts = {"count": 0}

    def mock_subprocess(args, cwd):
        if args[:3] == ["git", "fetch", "--deepen"]:
            deepen_attempts["count"] += 1
            return MagicMock(stdout="")
        if args[:2] == ["git", "merge-base"]:
            if deepen_attempts["count"] < 3:
                raise ValueError("Command failed: fatal: Not a valid commit")
            return MagicMock(stdout="abc123\n")
        return MagicMock(stdout="")

    mock_run.side_effect = mock_subprocess

    result = deepen_until_merge_base("/tmp/repo", "main")

    assert result is True
    deepens = [
        c[0][0]
        for c in mock_run.call_args_list
        if c[0][0][:3] == ["git", "fetch", "--deepen"]
    ]
    assert deepens == [
        ["git", "fetch", "--deepen", "100", "origin", "main"],
        ["git", "fetch", "--deepen", "500", "origin", "main"],
        ["git", "fetch", "--deepen", "2500", "origin", "main"],
    ]


@patch("services.git.deepen_until_merge_base.run_subprocess")
def test_falls_back_to_unshallow_when_schedule_exhausts(mock_run):
    """When 100 + 500 + 2500 + 12500 still doesn't surface a merge-base, fall back to --unshallow as a last resort. Slow on big repos but always correct."""
    call_log = []

    def mock_subprocess(args, cwd):
        call_log.append(args)
        if args[:2] == ["git", "merge-base"]:
            raise ValueError("Command failed: fatal: Not a valid commit")
        return MagicMock(stdout="")

    mock_run.side_effect = mock_subprocess

    result = deepen_until_merge_base("/tmp/repo", "main")

    assert result is True
    deepen_steps = [c[3] for c in call_log if c[:3] == ["git", "fetch", "--deepen"]]
    assert deepen_steps == ["100", "500", "2500", "12500"]
    assert call_log[-1] == ["git", "fetch", "--unshallow", "origin", "main"]


@patch("services.git.deepen_until_merge_base.run_subprocess")
def test_uses_caller_supplied_base_branch(mock_run):
    """Schedule must operate on whatever base_branch the caller passed (not hardcode 'main'). Repos with master/develop/release branches must work the same way."""
    mock_run.return_value = MagicMock(stdout="abc123\n")

    deepen_until_merge_base("/tmp/repo", "release/2026-q2")

    mock_run.assert_called_once_with(
        ["git", "merge-base", "HEAD", "origin/release/2026-q2"], "/tmp/repo"
    )
