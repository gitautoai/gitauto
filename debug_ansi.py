from utils.logs.remove_ansi_escape_codes import remove_ansi_escape_codes

# Test the problematic line
test_line = "[2K[1G[1myarn run v1.22.22[22m"
print(f"Original: {repr(test_line)}")

result = remove_ansi_escape_codes(test_line)
print(f"After ANSI removal: {repr(result)}")

# Test each step
import re
standard_ansi = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")
bracket_ansi = re.compile(r"\[[0-9;]*[a-zA-Z]")

print(f"Standard ANSI matches: {standard_ansi.findall(test_line)}")
print(f"Bracket ANSI matches: {bracket_ansi.findall(test_line)}")
