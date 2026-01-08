import subprocess


def run_command(
    command: str, cwd: str, use_shell: bool = True, env: dict | None = None
):
    try:
        if not command:
            raise ValueError("Command cannot be empty")
        # Split command into list if not using shell
        command_args = command if use_shell else command.split()
        result = subprocess.run(
            args=command_args,
            capture_output=True,
            check=True,
            cwd=cwd,
            text=True,
            shell=use_shell,
            env=env,
        )
        return result
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Command failed: {e.stderr}") from e
    except (FileNotFoundError, OSError) as e:
        raise ValueError(f"Command failed: {str(e)}") from e
