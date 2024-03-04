import re
import subprocess
import tempfile


def apply_patch(original_text: str, diff_text: str) -> str:
    """ Apply a diff using the patch command via temporary files """
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as original_file:
        original_file_name: str = original_file.name
        original_file.write(s=original_text)
        original_file.flush()  # Ensure the file is written to disk

    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as diff_file:
        diff_file_name: str = diff_file.name
        diff_file.write(s=diff_text)
        diff_file.flush()

    subprocess.run(args=['patch', original_file_name, diff_file_name], check=True)

    with open(file=original_file_name, mode='r', encoding='utf-8') as modified_file:
        modified_text: str = modified_file.read()

    subprocess.run(args=['rm', original_file_name, diff_file_name], check=True)

    return modified_text


def extract_file_name(diff_text: str) -> str:
    match = re.search(pattern=r'^\+\+\+ (.+)$', string=diff_text, flags=re.MULTILINE)
    if match:
        return match.group(1)
    raise ValueError("No file name found in the diff text.")


def split_diffs(diff_text: str) -> list[str]:
    # Split the diff text into parts for each file
    file_diffs: list[str] = re.split(pattern=r'(?=^---\s)', string=diff_text, flags=re.MULTILINE)
    return file_diffs
