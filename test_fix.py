#!/usr/bin/env python3
import sys
sys.path.append('.')
from utils.files.should_skip_php import should_skip_php

def test_closing_statements():
    # Test various closing statements - covers line 155
    content = """<?php
class MyClass {
    public $prop;
}

$array = [
    'value'
];

?>"""
    result = should_skip_php(content)
    print(f"Result: {result}")
    assert result is True
    print("Test passed!")

if __name__ == "__main__":
    test_closing_statements()
