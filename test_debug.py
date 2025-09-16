import sys
sys.path.append('.')
from utils.files.should_skip_rust import should_skip_rust

# Test the failing case
content = """const TEMPLATE: &str = "array[index] access pattern";
const EXAMPLE: &str = "variable[0] in string";"""

result = should_skip_rust(content)
print(f'Result: {result}')
print(f'Expected: True')
print(f'Test passes: {result is True}')
