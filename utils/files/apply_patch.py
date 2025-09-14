# pylint: disable=broad-exception-caught

# Standard imports
import os
import subprocess
import tempfile


# Local imports
from config import UTF8
from utils.files.get_file_content import get_file_content
from utils.new_lines.detect_new_line import detect_line_break
from utils.text.strip_trailing_spaces import strip_trailing_spaces


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

    # Detect the line break in the original text
    line_break: str = detect_line_break(text=original_text)

    # Create temporary files as subprocess.run() accepts only file paths
    with tempfile.NamedTemporaryFile(
        mode="w+", encoding=UTF8, newline="\n", delete=False
    ) as org_file:
        org_fname: str = org_file.name
        if original_text:
            s = original_text.replace("\r\n", "\n").replace("\r", "\n")
            if not s.endswith("\n"):
                s += "\n"
            org_file.write(s)

    with tempfile.NamedTemporaryFile(
        mode="w+", encoding=UTF8, newline="\n", delete=False
    ) as diff_file:
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
            with open(
                file=org_fname, mode="w", encoding=UTF8, newline="\n"
            ) as new_file:
                new_file.write(new_content)

        # Modified or deleted file
        else:
            with open(file=diff_fname, mode="r", encoding=UTF8, newline="\n") as diff:
                # Run patch command
                subprocess.run(
                    # See https://www.man7.org/linux/man-pages/man1/patch.1.html
                    args=["patch", "-u", "--fuzz=3", "--forward", org_fname],
                    input=diff.read(),
                    text=True,  # If True, input and output are strings
                    encoding=UTF8,
                    # capture_output=True,  # Redundant so commented out
                    check=True,  # If True, raise a CalledProcessError if the return code is non-zero
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )

        # Handle file deletion case
        if not os.path.exists(org_fname):
            return "", ""

        modified_text = get_file_content(file_path=org_fname)
        modified_text = strip_trailing_spaces(modified_text)
        modified_text = modified_text.replace("\n", line_break)

    except subprocess.CalledProcessError as e:
        stdout: str = e.stdout
        stderr: str = e.stderr

        # Check if the error message indicates that the patch was already applied
        msg = f"Failed to apply patch because the diff is already applied. But it's OK, move on to the next fix!\n\ndiff_text:\n{diff_text}\n\nstderr:\n{stderr}\n"
        if "already exists!" in stdout:
            return "", msg
        if "Ignoring previously applied (or reversed) patch." in stdout:
            return "", msg

        # Get the original, diff, and reject file contents for debugging
        modified_text = get_file_content(file_path=org_fname)
        modified_text = strip_trailing_spaces(modified_text)
        modified_text = modified_text.replace("\n", line_break)
        diff_text = (
            get_file_content(file_path=diff_fname)
            .replace(" ", "·")
            .replace("\t", "→")
            .replace("\\t", "→")
        )
        rej_f_name: str = f"{org_fname}.rej"
        rej_text = ""
        if os.path.exists(path=rej_f_name):
            rej_text = (
                get_file_content(file_path=rej_f_name)
                .replace(" ", "·")
                .replace("\t", "→")
            )

        # Log the error and return an empty string not to break the flow
        msg = f"Failed to apply patch partially or entirelly because something is wrong in diff. Analyze the reason from stderr and rej_text, modify the diff, and try again.\n\ndiff_text:\n{diff_text}\n\nstderr:\n{stderr}\n\nrej_text:\n{rej_text}\n"
        return modified_text, msg

    except FileNotFoundError as e:
        return "", f"Error: {e}"

    except Exception as e:  # pylint: disable=broad-except
        return "", f"Error: {e}"
    finally:
        # Remove temporary files
        try:
            os.remove(path=org_fname)
        except Exception as e:
            print(f"Failed to remove org file: {e}")

        try:
            os.remove(path=diff_fname)
        except Exception as e:
            print(f"Failed to remove diff file: {e}")

        # Remove any Oops.rej* files in the root directory
        root_dir = os.getcwd()
        for filename in os.listdir(root_dir):
            if filename.startswith("Oops.rej"):
                os.remove(os.path.join(root_dir, filename))

    return modified_text, ""
