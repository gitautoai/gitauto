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

result = should_skip_go(content)
print(f"Result: {result} (should be True)")
