#!/usr/bin/env python3

from utils.files.should_skip_go import should_skip_go

# Test the failing case
content = '''package main

var template = `multiline
string content
continues here`

const VALUE = "test"'''

result = should_skip_go(content)
print(f"Result: {result} (expected: True)")
