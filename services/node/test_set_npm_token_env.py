import os
from unittest.mock import patch

from services.node.set_npm_token_env import set_npm_token_env


def test_set_npm_token_env_sets_token():
    with patch("services.node.set_npm_token_env.get_npm_token") as mock_get:
        mock_get.return_value = "test-token-123"
        set_npm_token_env(12345)
        assert os.environ.get("NPM_TOKEN") == "test-token-123"
        mock_get.assert_called_once_with(12345)
    # Clean up
    if "NPM_TOKEN" in os.environ:
        del os.environ["NPM_TOKEN"]


def test_set_npm_token_env_no_token():
    with patch("services.node.set_npm_token_env.get_npm_token") as mock_get:
        mock_get.return_value = None
        original = os.environ.get("NPM_TOKEN")
        set_npm_token_env(12345)
        # Should not set NPM_TOKEN if None returned
        if original is None:
            assert os.environ.get("NPM_TOKEN") is None
        mock_get.assert_called_once_with(12345)
