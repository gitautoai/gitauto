import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from utils.command.run_subprocess import run_subprocess


def test_run_subprocess_success():
    with tempfile.TemporaryDirectory() as temp_dir:
        result = run_subprocess(["echo", "hello"], temp_dir)
        assert result.returncode == 0
        assert result.stdout == "hello\n"


def test_run_subprocess_failure_raises_value_error():
    with tempfile.TemporaryDirectory() as temp_dir:
        with pytest.raises(
            ValueError,
            match=r"^Command failed: \[Errno 2\] No such file or directory:",
        ):
            run_subprocess(["nonexistent_command_xyz"], temp_dir)


def test_run_subprocess_with_stderr_output():
    with tempfile.TemporaryDirectory() as temp_dir:
        with pytest.raises(ValueError, match=r"^Command failed: error\n$"):
            run_subprocess(["sh", "-c", "echo error >&2; exit 1"], temp_dir)


def test_run_subprocess_nonzero_returncode_raises():
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "some error"

    with patch("utils.command.run_subprocess.subprocess.run", return_value=mock_result):
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(ValueError, match=r"^Command failed: some error$"):
                run_subprocess(["test_command"], temp_dir)


@patch("utils.command.run_subprocess.passthrough_env_for_subprocess")
@patch("utils.command.run_subprocess.subprocess.run")
def test_run_subprocess_subprocess_parameters(mock_run, mock_passthrough):
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_run.return_value = mock_result
    mock_passthrough.return_value = {"PATH": "/usr/bin"}

    with tempfile.TemporaryDirectory() as temp_dir:
        result = run_subprocess(["git", "status"], temp_dir)

        # Assert the full kwargs dict so a regression on any field is caught.
        assert mock_run.call_args.kwargs == {
            "args": ["git", "status"],
            "capture_output": True,
            "check": False,
            "cwd": temp_dir,
            "text": True,
            "shell": False,
            "env": {"PATH": "/usr/bin"},
        }
        assert result is mock_result


def test_run_subprocess_empty_command():
    with tempfile.TemporaryDirectory() as temp_dir:
        with pytest.raises(ValueError, match=r"^Command cannot be empty$"):
            run_subprocess([], temp_dir)


@patch.dict(
    "os.environ",
    {
        "ANTHROPIC_API_KEY": "secret-ANTHROPIC_API_KEY",
        "GH_PRIVATE_KEY": "secret-GH_PRIVATE_KEY",
        "GH_WEBHOOK_SECRET": "secret-GH_WEBHOOK_SECRET",
        "OPENAI_API_KEY": "secret-OPENAI_API_KEY",
        "SENTRY_DSN": "secret-SENTRY_DSN",
        "SLACK_BOT_TOKEN": "secret-SLACK_BOT_TOKEN",
        "STRIPE_API_KEY": "secret-STRIPE_API_KEY",
        "SUPABASE_SERVICE_ROLE_KEY": "secret-SUPABASE_SERVICE_ROLE_KEY",
        "PATH": "/usr/bin:/bin",
        "HOME": "/tmp",
        "NPM_TOKEN": "npm-tok-from-set-env",
        "MONGOMS_DISTRO": "ubuntu-22.04",
    },
    clear=True,
)
@patch("utils.env.passthrough_env_for_subprocess.get_internal_env_var_names")
@patch("utils.command.run_subprocess.subprocess.run")
def test_run_subprocess_strips_internal_env_vars(mock_run, mock_get_names):
    """Sentry AGENT-3KJ/3KK/3KM/3KH/3KF/3KG: customer Node apps with the Sentry SDK loaded read SENTRY_DSN from env, initialise against OUR project, and pipe their app-level errors into our Sentry. run_subprocess must scrub every GitAuto-internal secret from the env it hands to children — Sentry DSN, Anthropic/Google/OpenAI/Stripe/Slack tokens, GitHub app private key, Supabase service role, etc."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_run.return_value = mock_result
    # Stand in for SSM /gitauto/* — the runtime would query SSM for these names, but in tests we inject the set directly.
    mock_get_names.return_value = {
        "ANTHROPIC_API_KEY",
        "GH_PRIVATE_KEY",
        "GH_WEBHOOK_SECRET",
        "OPENAI_API_KEY",
        "SENTRY_DSN",
        "SLACK_BOT_TOKEN",
        "STRIPE_API_KEY",
        "SUPABASE_SERVICE_ROLE_KEY",
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        run_subprocess(["echo", "x"], temp_dir)

    # Operational vars (PATH, HOME) and runtime-injected set_env-tool vars (NPM_TOKEN, MONGOMS_DISTRO) survive; every secret listed above is dropped.
    assert mock_run.call_args.kwargs["env"] == {
        "PATH": "/usr/bin:/bin",
        "HOME": "/tmp",
        "NPM_TOKEN": "npm-tok-from-set-env",
        "MONGOMS_DISTRO": "ubuntu-22.04",
    }


@patch("utils.env.passthrough_env_for_subprocess.get_internal_env_var_names")
def test_run_subprocess_passes_env_set_via_monkeypatch(mock_get_names, monkeypatch):
    """End-to-end check using a real subprocess: a non-internal env var set in the parent reaches the child, and SENTRY_DSN does not."""
    mock_get_names.return_value = {"SENTRY_DSN"}
    monkeypatch.setenv("MY_BENIGN_VAR", "yes")
    monkeypatch.setenv("SENTRY_DSN", "https://fake@sentry.example/1")

    with tempfile.TemporaryDirectory() as temp_dir:
        result = run_subprocess(
            [
                "sh",
                "-c",
                "echo BENIGN=${MY_BENIGN_VAR}; echo DSN=${SENTRY_DSN:-MISSING}",
            ],
            temp_dir,
        )

    assert result.stdout == "BENIGN=yes\nDSN=MISSING\n"
    # Confirm the parent still sees SENTRY_DSN — only children are scrubbed.
    assert os.environ["SENTRY_DSN"] == "https://fake@sentry.example/1"
