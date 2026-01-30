# pylint: disable=unused-argument,import-outside-toplevel
from unittest.mock import patch

import pytest


@pytest.fixture
def mock_is_prd():
    with patch("services.aws.run_install_via_ssm.IS_PRD", True):
        yield


@pytest.fixture
def mock_get_nat_instance_id():
    with patch(
        "services.aws.run_install_via_ssm.get_nat_instance_id",
        return_value="i-1234567890abcdef0",
    ):
        yield


@pytest.fixture
def mock_ssm_client():
    with patch("services.aws.run_install_via_ssm.ssm_client") as mock_client:
        mock_client.send_command.return_value = {"Command": {"CommandId": "cmd-123456"}}
        yield mock_client


@pytest.fixture
def mock_npm_token():
    with patch(
        "services.aws.run_install_via_ssm.get_npm_token", return_value="npm_test123"
    ):
        yield


class TestRunInstallViaSsm:
    def test_skips_in_non_prod(self):
        with patch("services.aws.run_install_via_ssm.IS_PRD", False):
            from services.aws.run_install_via_ssm import run_install_via_ssm

            result = run_install_via_ssm("/mnt/efs/test/repo", 123)
            assert result is None

    def test_skips_without_nat_instance_id(self, mock_is_prd):
        with patch(
            "services.aws.run_install_via_ssm.get_nat_instance_id", return_value=None
        ):
            from services.aws.run_install_via_ssm import run_install_via_ssm

            result = run_install_via_ssm("/mnt/efs/test/repo", 123)
            assert result is None

    def test_sends_ssm_command_with_npm_token(
        self, mock_is_prd, mock_get_nat_instance_id, mock_ssm_client, mock_npm_token
    ):
        from services.aws.run_install_via_ssm import run_install_via_ssm

        result = run_install_via_ssm("/mnt/efs/test/repo", 123, "yarn")

        assert result == "cmd-123456"
        mock_ssm_client.send_command.assert_called_once()
        call_args = mock_ssm_client.send_command.call_args
        commands = call_args.kwargs["Parameters"]["commands"]
        assert "NPM_TOKEN=npm_test123" in commands[0]
        assert "yarn install" in commands[0]

    def test_sends_ssm_command_without_npm_token(
        self, mock_is_prd, mock_get_nat_instance_id, mock_ssm_client
    ):
        with patch(
            "services.aws.run_install_via_ssm.get_npm_token", return_value=None
        ):
            from services.aws.run_install_via_ssm import run_install_via_ssm

            result = run_install_via_ssm("/mnt/efs/test/repo", 123, "npm")

            assert result == "cmd-123456"
            call_args = mock_ssm_client.send_command.call_args
            commands = call_args.kwargs["Parameters"]["commands"]
            assert "NPM_TOKEN" not in commands[0]
            assert "npm install" in commands[0]
