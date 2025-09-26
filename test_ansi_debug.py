from utils.logs.remove_ansi_escape_codes import remove_ansi_escape_codes

# Test the specific line that's causing issues
input_line = "[2K[1G[1myarn run v1.22.22[22m"
result = remove_ansi_escape_codes(input_line)
print(f"Input: {repr(input_line)}")
print(f"Output: {repr(result)}")
print(f"Expected: {repr('yarn run v1.22.22')}")
print(f"Match: {result == 'yarn run v1.22.22'}")
