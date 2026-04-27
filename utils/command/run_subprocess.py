import subprocess

from utils.env.passthrough_env_for_subprocess import passthrough_env_for_subprocess
from utils.logging.logging_config import logger


def run_subprocess(args: list[str], cwd: str):
    if not args:
        logger.error("run_subprocess called with empty args")
        raise ValueError("Command cannot be empty")

    logger.info("Running: %s in %s", " ".join(args), cwd)

    # Sentry AGENT-3KJ/3KK/3KM/3KH/3KF/3KG: customer Node apps with @sentry/node imported auto-init the SDK against any SENTRY_DSN they find in env, so the parent's DSN must not propagate. Same exposure exists for every other key in SSM `/gitauto/*` (OpenAI, Anthropic, Stripe, GH App private key, Supabase service role, ...). passthrough_env_for_subprocess strips those names from the env handed to children; vars set at runtime via the `set_env` agent tool (NPM_TOKEN, MONGOMS_DISTRO, etc.) and operational CFN-inline vars (GIT_CONFIG_GLOBAL) are not in SSM and pass through.
    try:
        result = subprocess.run(
            args=args,
            capture_output=True,  # Capture stdout and stderr instead of printing to terminal
            check=False,  # Don't raise CalledProcessError; we check returncode manually below
            cwd=cwd,
            text=True,  # Return stdout/stderr as str instead of bytes
            shell=False,  # Args are passed directly to the process, so callers don't need shlex.quote() which is a bug breeding ground when forgotten
            env=passthrough_env_for_subprocess(),
        )
    except (FileNotFoundError, OSError) as e:
        raise ValueError(f"Command failed: {e}") from e

    if result.returncode != 0:
        logger.warning("run_subprocess: non-zero exit %d", result.returncode)
        raise ValueError(f"Command failed: {result.stderr}")

    return result
