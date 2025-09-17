# Check the current function
with open("utils/logs/remove_pytest_sections.py", "r") as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    print(f"{i:2d}: {line.rstrip()}")
