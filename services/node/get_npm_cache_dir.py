from constants.general import IS_PRD


def set_npm_cache_env(env: dict):
    # Without npm_config_cache, npm defaults to /home/sbx_user1051 (Lambda sandbox user) which doesn't exist → ENOENT
    # /tmp/.npm on Lambda (shared across PRs so downloaded packages can be reused), default (~/.npm) locally
    if IS_PRD:
        env["npm_config_cache"] = "/tmp/.npm"
