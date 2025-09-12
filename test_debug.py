from utils.files.should_skip_ruby import should_skip_ruby

print("=== Testing class with constant (should return False) ===")
content1 = """class MyClass
  CONSTANT = 'value'
end"""
result1 = should_skip_ruby(content1)
print(f'Result: {result1}')
print(f'Expected: False')
print(f'Test passes: {result1 is False}')
print()

print("=== Testing single-line class (should return True) ===")
content2 = """class MyComponent; end"""
result2 = should_skip_ruby(content2)
print(f'Result: {result2}')
print(f'Expected: True')
print(f'Test passes: {result2 is True}')
print()

print("=== Testing empty class (should return True) ===")
content3 = """class CustomError < StandardError
end"""
result3 = should_skip_ruby(content3)
print(f'Result: {result3}')
print(f'Expected: True')
print(f'Test passes: {result3 is True}')
print()

print("=== Testing class with methods (should return False) ===")
content4 = """class Calculator
  def initialize
    @value = 0
  end

  def add(a, b)
    a + b
  end
end"""
result4 = should_skip_ruby(content4)
print(f'Result: {result4}')
print(f'Expected: False')
print(f'Test passes: {result4 is False}')
print()

print("=== Testing module with attr (should return True) ===")
content5 = """module UserModule
  attr_accessor :id, :name, :email
end"""
result5 = should_skip_ruby(content5)
print(f'Result: {result5}')
print(f'Expected: True')
print(f'Test passes: {result5 is True}')
