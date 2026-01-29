from constants.general import IS_PRD


def set_npm_cache_env(env: dict):
    # npm: defaults to /home/sbx_user1051 which doesn't exist on Lambda → ENOENT; use /tmp/.npm on Lambda, ~/.npm locally
    # yarn: defaults to ~/.cache/yarn which is read-only on Lambda → no caching; use /tmp/.yarn on Lambda, ~/.cache/yarn locally
    if IS_PRD:
        env["npm_config_cache"] = "/tmp/.npm"
        env["YARN_CACHE_FOLDER"] = "/tmp/.yarn"
