import os
import re
import subprocess
import tempfile

import re

_hdr_pat = re.compile("^@@ -(\d+),?(\d+)? \+(\d+),?(\d+)? @@$")

def apply_raw_patch(original_text: str, diff_text: str) -> str:
  if(diff_text.startswith('```diff\n')):
      diff_text = diff_text[len('```diff\n'):]
  if(diff_text.endswith('\n```')):
        diff_text = diff_text[:-len('\n```')]
  print(diff_text)
  s = original_text.splitlines(True)
  p = diff_text.splitlines(True)
  t = ''
  i = sl = 0
  (midx,sign) = (1,'+')
  while i < len(p) and p[i].startswith(("---","+++")): i += 1 # skip header lines
  while i < len(p):
    m = _hdr_pat.match(p[i])
    if not m: raise Exception("Cannot process diff")
    i += 1
    l = int(m.group(midx))-1 + (m.group(midx+1) == '0')
    t += ''.join(s[sl:l])
    sl = l
    while i < len(p) and p[i][0] != '@':
      if i+1 < len(p) and p[i+1][0] == '\\': line = p[i][:-1]; i += 2
      else: line = p[i]; i += 1
      if len(line) > 0:
        if line[0] == sign or line[0] == ' ': t += line[1:]
        sl += (line[0] != sign)
  t += ''.join(s[sl:])
  return t

def apply_patch(original_text: str, diff_text: str) -> str:
    return apply_raw_patch(original_text, diff_text)
    """ Apply a diff using the patch command via temporary files """
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as original_file:
        original_file_name: str = original_file.name
        if original_text:
            original_file.write(
                original_text if original_text.endswith('\n') else original_text + '\n'
            )

    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as diff_file:
        diff_file_name: str = diff_file.name
        diff_file.write(diff_text if diff_text.endswith('\n') else diff_text + '\n')

    try:
        # New file
        if original_text == "" and "+++ " in diff_text:
            lines: list[str] = diff_text.split(sep='\n')
            new_content_lines: list[str] = [
                line[1:] if line.startswith('+') else line for line in lines[3:]
            ]
            new_content: str = '\n'.join(new_content_lines)
            with open(file=original_file_name, mode='w', encoding='utf-8') as new_file:
                new_file.write(new_content)

        # Modified or deleted file
        else:
            with open(file=diff_file_name, mode='r', encoding='utf-8') as input_diff:
                subprocess.run(
                    args=['patch', '-u', original_file_name],
                    input=input_diff.read(),
                    text=True,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

        print("Patch applied successfully.")
        with open(file=original_file_name, mode='r', encoding='utf-8') as modified_file:
            modified_text: str = modified_file.read()
            print(f"{modified_text=}\n")

    except subprocess.CalledProcessError as e:
        print("Failed to apply patch.")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}\n")
        print(f"Command: {' '.join(e.cmd)}")
        print(f"Exit status: {e.returncode}")
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
