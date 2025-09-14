from utils.files.should_skip_go import should_skip_go

content = """package main

type User struct {
    ID       int64
    Name     string
    Email    *string
    Tags     []string
    Metadata map[string]interface{}
    Config   *Config
}"""

print("Testing content:")
print(repr(content))
print("\nResult:", should_skip_go(content))

# Let's trace through line by line
lines = content.split("\n")
for i, line in enumerate(lines):
    print(f"Line {i}: {repr(line.strip())}")
