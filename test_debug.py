from utils.files.should_skip_ruby import should_skip_ruby

# Test the failing case
content1 = """class MyClass
  CONSTANT = 'value'
end"""

result1 = should_skip_ruby(content1)
print(f'Test 1 - Class with constant:')
print(f'Content: {repr(content1)}')
print(f'Result: {result1}')
print(f'Expected: False')
print(f'Test passes: {result1 is False}')
print()

# Test single-line class
content2 = """class MyComponent; end"""
result2 = should_skip_ruby(content2)
print(f'Test 2 - Single-line class: {result2} (expected: True)')
print(f'Test passes: {result2 is True}')