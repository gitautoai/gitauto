# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from unittest.mock import patch

import pytest

from constants.shell import ALLOWED_PREFIXES
from services.shell.run_command import run_command


class TestRunCommand:
    @patch("services.shell.run_command.slack_notify")
    def test_npm_view_returns_version(self, _mock_slack, create_test_base_args):
        base_args = create_test_base_args()
        result = run_command(base_args, "npm view express version")
        assert result is not None
        # express always has a version like "4.x.x" or "5.x.x"
        assert result.strip()[0].isdigit()

    @patch("services.shell.run_command.slack_notify")
    def test_blocked_command(self, _mock_slack, create_test_base_args):
        base_args = create_test_base_args()
        result = run_command(base_args, "rm -rf /")
        assert result is not None
        assert "not allowed" in result.lower()

    @patch("services.shell.run_command.slack_notify")
    def test_ls_runs(self, _mock_slack, create_test_base_args):
        base_args = create_test_base_args()
        result = run_command(base_args, "ls /tmp")
        assert result is not None

    @patch("services.shell.run_command.slack_notify")
    def test_npm_view_nonexistent_package(self, _mock_slack, create_test_base_args):
        base_args = create_test_base_args()
        result = run_command(
            base_args, "npm view this-package-does-not-exist-xyz123 version"
        )
        assert result is not None
        assert "404" in result

    @patch("services.shell.run_command.slack_notify")
    def test_yarn_info(self, _mock_slack, create_test_base_args):
        base_args = create_test_base_args()
        result = run_command(base_args, "yarn info express version")
        assert result is not None

    @patch("services.shell.run_command.slack_notify")
    def test_large_output_saved_to_file(self, _mock_slack, create_test_base_args):
        base_args = create_test_base_args()
        # npm view express (no field) returns lots of metadata
        result = run_command(base_args, "npm view express")
        assert result is not None
        if "Saved to:" in result:
            assert "/tmp/cmd_" in result
            assert "get_local_file_content" in result

    @patch("services.shell.run_command.slack_notify")
    def test_cat_blocked_outside_tmp(self, _mock_slack, create_test_base_args):
        base_args = create_test_base_args()
        result = run_command(base_args, "cat /etc/passwd")
        assert result is not None
        assert "not allowed" in result.lower()

    @patch("services.shell.run_command.slack_notify")
    def test_cat_blocked_proc_environ(self, _mock_slack, create_test_base_args):
        base_args = create_test_base_args()
        result = run_command(base_args, "cat /proc/self/environ")
        assert result is not None
        assert "not allowed" in result.lower()

    @patch("services.shell.run_command.slack_notify")
    def test_cat_blocked_traversal(self, _mock_slack, create_test_base_args):
        base_args = create_test_base_args()
        result = run_command(base_args, "cat /tmp/../../etc/passwd")
        assert result is not None
        assert "not allowed" in result.lower()

    @patch("services.shell.run_command.slack_notify")
    def test_ls_blocked_outside_tmp(self, _mock_slack, create_test_base_args):
        base_args = create_test_base_args()
        result = run_command(base_args, "ls /etc")
        assert result is not None
        assert "not allowed" in result.lower()

    @pytest.mark.parametrize("prefix", ALLOWED_PREFIXES)
    def test_all_allowed_prefixes_are_read_only(self, prefix):
        # Verify no write commands snuck into the whitelist
        dangerous = ("rm", "install", "uninstall", "add", "remove", "publish", "exec")
        assert not any(d in prefix for d in dangerous)
