from utils.files.should_skip_go import should_skip_go

def test_simple():
    content = """package main

const MaxRetries = 3"""
    result = should_skip_go(content)
    print(f"Result: {result}")
