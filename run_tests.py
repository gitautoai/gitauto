import subprocess
import sys

# Run the remove_pytest_sections tests
result = subprocess.run([
    sys.executable, "-m", "pytest",
    "utils/logs/test_remove_pytest_sections.py",
    "-v"
], capture_output=True, text=True)

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print(f"\nReturn code: {result.returncode}")
