from utils.files.should_skip_rust import should_skip_rust

# Test the failing case
content = """/* Outer comment start
/* Inner comment */
Still in outer comment */
const VALUE: i32 = 42;"""

result = should_skip_rust(content)
print(f"Result: {result}, Expected: True")
