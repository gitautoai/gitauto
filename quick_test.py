import sys
sys.path.insert(0, '.')
from utils.files.should_skip_go import should_skip_go

content = """package main

type Outer struct {
    Inner struct {
        Value string
        Count int
    }
    Name string
}"""

print("Result:", should_skip_go(content))
