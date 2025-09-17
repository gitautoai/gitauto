from utils.files.should_skip_php import should_skip_php

# Test the failing case
content = """<?php
class MyClass
{
    public $property;
}"""

result = should_skip_php(content)
print(f"Result: {result}")
print("Expected: True")
