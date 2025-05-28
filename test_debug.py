from utils.files.filter_code_files import filter_code_files

# Test the specific failing case
filenames = [
    "main.py",
    "testing.py",
    "contest.py",
    "respect.py",
    "mockingbird.py",
    "stubborn.py",
    "fixtures.py"
]

result = filter_code_files(filenames)
print(f"Result: {result}")
print(f"Expected: ['main.py', 'testing.py', 'contest.py', 'respect.py']")