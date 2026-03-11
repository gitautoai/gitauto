# Standard imports
import os
import subprocess
import tempfile
from dataclasses import dataclass

# Local imports
from config import UTF8
from utils.files.ensure_diff_ab_prefixes import ensure_diff_ab_prefixes
from utils.files.fix_diff_hunk_counts import fix_diff_hunk_counts
from utils.files.read_local_file import read_local_file
from utils.files.write_local_file import write_local_file
from utils.logging.logging_config import logger
from utils.new_lines.detect_new_line import detect_line_break
from utils.text.ensure_final_newline import ensure_final_newline
from utils.text.sort_imports import sort_imports
from utils.text.strip_trailing_spaces import strip_trailing_spaces


@dataclass
class PatchResult:
    """Result of applying a patch."""

    content: str
    error: str


def apply_patch(original_text: str, diff_text: str, clone_dir: str, file_path: str):
    """Apply a unified diff using git apply in the clone directory."""

    line_break = detect_line_break(text=original_text)
    target_path = os.path.join(clone_dir, file_path)

    diff_fname = ""
    try:
        # Write original content so git apply can diff against it
        # Normalize to LF so diff context lines match during git apply
        if original_text:
            normalized = original_text.replace("\r\n", "\n").replace("\r", "\n")
            if not normalized.endswith("\n"):
                normalized += "\n"
            write_local_file(file_path, clone_dir, normalized)

        diff_text = ensure_diff_ab_prefixes(diff_text)
        diff_text = fix_diff_hunk_counts(diff_text)

        # Write diff to a temp file
        diff_content = diff_text if diff_text.endswith("\n") else diff_text + "\n"
        with tempfile.NamedTemporaryFile(
            mode="w", encoding=UTF8, newline="\n", delete=False, suffix=".diff"
        ) as diff_file:
            diff_fname = diff_file.name
            diff_file.write(diff_content)

        # Log file state before git apply for debugging patch failures
        content_before = read_local_file(file_path, clone_dir)
        if content_before is not None:
            logger.info("File before git apply:\n%s", content_before)
        else:
            logger.info("File does not exist before git apply: %s", target_path)

        # See https://git-scm.com/docs/git-apply
        subprocess.run(
            args=["git", "apply", "--verbose", diff_fname],
            cwd=clone_dir,
            text=True,
            encoding=UTF8,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Handle file deletion case
        if not os.path.exists(target_path):
            return PatchResult(content="", error="")

        modified_text = read_local_file(file_path, clone_dir) or ""
        modified_text = sort_imports(modified_text, target_path)
        modified_text = strip_trailing_spaces(modified_text)
        modified_text = ensure_final_newline(modified_text)
        modified_text = modified_text.replace("\n", line_break)
        write_local_file(file_path, clone_dir, modified_text)
        return PatchResult(content=modified_text, error="")

    except subprocess.CalledProcessError as e:
        stderr: str = e.stderr or ""
        diff_display = (
            diff_text.replace(" ", "·").replace("\t", "→").replace("\\t", "→")
        )
        msg = f"Failed to apply diff. Fix the diff and try again.\n\ndiff_text:\n{diff_display}\n\nstderr:\n{stderr}\n"
        return PatchResult(content="", error=msg)

    except FileNotFoundError as e:
        return PatchResult(content="", error=f"Error: {e}")

    except OSError as e:
        return PatchResult(content="", error=f"Error: {e}")

    finally:
        if diff_fname:
            try:
                os.remove(diff_fname)
            except OSError as e:
                logger.error("Failed to remove diff file: %s", e)
