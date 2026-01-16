from unittest.mock import patch

from services.node.get_npm_cache_dir import set_npm_cache_env


def test_set_npm_cache_env_sets_on_lambda():
    with patch("services.node.get_npm_cache_dir.IS_PRD", True):
        env = {}
        set_npm_cache_env(env)
        assert env["npm_config_cache"] == "/tmp/.npm"


def test_set_npm_cache_env_does_nothing_locally():
    with patch("services.node.get_npm_cache_dir.IS_PRD", False):
        env = {}
        set_npm_cache_env(env)
        assert "npm_config_cache" not in env
