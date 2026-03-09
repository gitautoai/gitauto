import subprocess


def run_subprocess(args: list[str], cwd: str):
    if not args:
        raise ValueError("Command cannot be empty")

    try:
        result = subprocess.run(
            args=args,
            capture_output=True,  # Capture stdout and stderr instead of printing to terminal
            check=False,  # Don't raise CalledProcessError; we check returncode manually below
            cwd=cwd,
            text=True,  # Return stdout/stderr as str instead of bytes
            shell=False,  # Args are passed directly to the process, so callers don't need shlex.quote() which is a bug breeding ground when forgotten
        )
    except (FileNotFoundError, OSError) as e:
        raise ValueError(f"Command failed: {e}") from e

    if result.returncode != 0:
        raise ValueError(f"Command failed: {result.stderr}")

    return result
