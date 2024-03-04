import os
import re
import subprocess
import tempfile


def apply_patch(original_text: str, diff_text: str) -> str:
    """ Apply a diff using the patch command via temporary files """
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as original_file:
        original_file_name: str = original_file.name
        original_file.write(original_text)
        original_file.flush()  # Ensure the file is written to disk

    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as diff_file:
        diff_file_name: str = diff_file.name
        diff_file.write(diff_text)
        diff_file.flush()

    try:
        result = subprocess.run(
            args=['patch', '--force', original_file_name, diff_file_name], check=True
        )
        print("Patch applied successfully.")
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}\n")
        with open(file=original_file_name, mode='r', encoding='utf-8') as modified_file:
            modified_text: str = modified_file.read()

    except subprocess.CalledProcessError as e:
        print("Failed to apply patch.")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}\n")
        raise

    finally:
        os.remove(path=original_file_name)
        os.remove(path=diff_file_name)
        print("Temporary files removed.\n")

    return modified_text


def clean_specific_lines(text: str) -> str:
    lines: list[str] = text.strip().split(sep='\n')
    cleaned_lines: list[str] = [
        line for line in lines if not (
            line.startswith('```diff') or line == '```' or line.strip() == '')
    ]
    return '\n'.join(cleaned_lines).strip()


def extract_file_name(diff_text: str) -> str:
    match = re.search(pattern=r'^\+\+\+ (.+)$', string=diff_text, flags=re.MULTILINE)
    if match:
        return match.group(1)
    raise ValueError("No file name found in the diff text.")


def split_diffs(diff_text: str) -> list[str]:
    file_diffs: list[str] = re.split(pattern=r'(?=^---\s)', string=diff_text, flags=re.MULTILINE)

    # Remove the first element if it's an empty string
    if file_diffs and file_diffs[0] == "":
        file_diffs.pop(0)

    # Remove leading and trailing whitespace from each diff
    file_diffs = [diff.strip() for diff in file_diffs]
    return file_diffs
