from unittest.mock import patch

from utils.env.passthrough_env_for_subprocess import passthrough_env_for_subprocess

PARENT_ENV = {
    "SENTRY_DSN": "https://fake@sentry.io/1",
    "OPENAI_API_KEY": "sk-secret",
    "GH_PRIVATE_KEY": "PRIVATE",
    "PATH": "/usr/bin:/bin",
    "HOME": "/tmp",
    "NPM_TOKEN": "npm-tok-from-set-env",
    "MONGOMS_DISTRO": "ubuntu-22.04",
}


@patch.dict("os.environ", PARENT_ENV, clear=True)
@patch("utils.env.passthrough_env_for_subprocess.get_internal_env_var_names")
def test_strips_internal_names_keeps_others(mock_names):
    """Sentry AGENT-3KJ et al.: names returned by get_internal_env_var_names must be stripped from os.environ before subprocess inherits it. Operational vars (PATH, HOME) and runtime-injected vars (NPM_TOKEN, MONGOMS_DISTRO from the set_env tool) survive."""
    mock_names.return_value = {"SENTRY_DSN", "OPENAI_API_KEY", "GH_PRIVATE_KEY"}

    assert passthrough_env_for_subprocess() == {
        "PATH": "/usr/bin:/bin",
        "HOME": "/tmp",
        "NPM_TOKEN": "npm-tok-from-set-env",
        "MONGOMS_DISTRO": "ubuntu-22.04",
    }


@patch.dict(
    "os.environ",
    {"SENTRY_DSN": "https://fake@sentry.io/1", "PATH": "/usr/bin:/bin"},
    clear=True,
)
@patch("utils.env.passthrough_env_for_subprocess.get_internal_env_var_names")
def test_empty_scrub_set_returns_full_environ(mock_names):
    """When the scrub set is empty (local dev, or SSM lookup failed), every parent env var passes through unchanged."""
    mock_names.return_value = set()

    assert passthrough_env_for_subprocess() == {
        "SENTRY_DSN": "https://fake@sentry.io/1",
        "PATH": "/usr/bin:/bin",
    }


@patch("utils.env.passthrough_env_for_subprocess.get_internal_env_var_names")
def test_returns_empty_dict_on_failure(mock_names):
    """If anything raises inside the function, @handle_exceptions returns {} so subprocess fails closed (no env, breaks loudly) rather than fail open (full env, secrets leak — defeats the entire fix)."""
    mock_names.side_effect = RuntimeError("boom")

    assert passthrough_env_for_subprocess() == {}
