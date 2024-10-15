# Standard imports
import os
import subprocess
import tempfile

# Third-party imports
import chardet

# Local imports
from config import UTF8
from utils.handle_exceptions import handle_exceptions


def apply_patch(original_text: str, diff_text: str):
    """Apply a diff using the patch command via temporary files.
    Here is comparison of patch options in handling "Assume -R?" and "Apply anyway?" prompts:

    --forward:
    Assume -R? [n]: No
    Apply anyway? [n]: No

    --batch:
    Assume -R? [y]: Yes
    Apply anyway? [y]: Yes

    --force:
    Assume -R? [n]: No
    Apply anyway? [y]: Yes
    """
    # Print encodings of input texts
    print(f"Original text encoding: {chardet.detect(original_text.encode())['encoding']}")
    print(f"Diff text encoding: {chardet.detect(diff_text.encode())['encoding']}")

    # Create temporary files as subprocess.run() accepts only file paths
    with tempfile.NamedTemporaryFile(mode="w+", newline="", delete=False) as org_file:
        org_fname: str = org_file.name
        if original_text:
            s = original_text if original_text.endswith("\n") else original_text + "\n"
            org_file.write(s)

    with tempfile.NamedTemporaryFile(mode="w+", newline="", delete=False) as diff_file:
        diff_fname: str = diff_file.name
        diff_file.write(diff_text if diff_text.endswith("\n") else diff_text + "\n")

    modified_text = ""
    try:
        # New file
        if original_text == "" and "+++ " in diff_text:
            lines: list[str] = diff_text.split(sep="\n")
            new_content_lines: list[str] = [
                line[1:] if line.startswith("+") else line for line in lines[3:]
            ]
            new_content: str = "\n".join(new_content_lines)
            with open(file=org_fname, mode="w", encoding=UTF8, newline="") as new_file:
                new_file.write(new_content)

        # Modified or deleted file
        else:
            with open(file=diff_fname, mode="r", encoding=UTF8, newline="") as diff:
                subprocess.run(
                    # See https://www.man7.org/linux/man-pages/man1/patch.1.html
                    args=["patch", "-u", "--fuzz=3", "--forward", org_fname],
                    input=diff.read(),
                    text=True,  # If True, input and output are strings
                    # capture_output=True,  # Redundant so commented out
                    check=True,  # If True, raise a CalledProcessError if the return code is non-zero
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )

        # If the patch was successfully applied, get the modified text
        modified_text = get_file_content(file_path=org_fname)

    except subprocess.CalledProcessError as e:
        stdout: str = e.stdout
        stderr: str = e.stderr

        # Check if the error message indicates that the patch was already applied
        msg = f"Failed to apply patch because the diff is already applied. But it's OK, move on to the next fix!\n\ndiff_text:\n{diff_text}\n\nstderr:\n{stderr}"
        if "already exists!" in stdout:
            print(msg, end="")
            return "", msg
        if "Ignoring previously applied (or reversed) patch." in stdout:
            print(msg, end="")
            return "", msg

        # Get the original, diff, and reject file contents for debugging
        modified_text = get_file_content(file_path=org_fname)
        diff_text = get_file_content(file_path=diff_fname)
        rej_f_name: str = f"{org_fname}.rej"
        rej_text = ""
        if os.path.exists(path=rej_f_name):
            rej_text = get_file_content(file_path=rej_f_name)

        # Log the error and return an empty string not to break the flow
        msg = f"Failed to apply patch partially or entirelly because something is wrong in diff. Analyze the reason from stderr and rej_text, modify the diff, and try again.\n\ndiff_text:\n{diff_text}\n\nstderr:\n{stderr}\n\nrej_text:\n{rej_text}\n"
        print(msg, end="")
        # logging.error(msg)
        msg += f"\n{modified_text=}\n\n{original_text=}"
        return modified_text, msg

    except Exception as e:  # pylint: disable=broad-except
        print(f"Error: {e}", end="")
        # logging.error(msg=f"Error: {e}")
        return "", f"Error: {e}"
    finally:
        os.remove(path=org_fname)
        os.remove(path=diff_fname)

    return modified_text, ""


@handle_exceptions(default_return_value="", raise_on_error=False)
def get_file_content(file_path: str) -> str:
    with open(file=file_path, mode="rb") as file:  # rb stands for "read binary"
        raw_data: bytes = file.read()

    detected: chardet.ResultDict = chardet.detect(byte_str=raw_data)
    encoding: str = detected["encoding"] or UTF8
    return raw_data.decode(encoding=encoding)


def run_command(command: str, cwd: str) -> str:
    try:
        result: subprocess.CompletedProcess[str] = subprocess.run(
            args=command,
            capture_output=True,
            check=True,
            cwd=cwd,
            text=True,
            shell=True,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        # 127: Command not found so check if Git is installed
        if e.returncode == 127:
            try:
                # Check if Git is installed
                version_result = subprocess.run(
                    args="git --version",
                    capture_output=True,
                    check=True,
                    text=True,
                    shell=True,
                )
                print(f"Git version: {version_result.stdout}", end="")
                # logging.info("Git version: %s", version_result.stdout)
            except subprocess.CalledProcessError as ve:
                print(f"Failed to get Git version: {ve.stderr}", end="")
                # logging.error("Failed to get Git version: %s", ve.stderr)

        raise ValueError(f"Command failed: {e.stderr}") from e
