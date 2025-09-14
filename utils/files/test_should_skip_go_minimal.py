from utils.files.should_skip_go import should_skip_go


def test_simple_case():
    # Simple constants should be skipped
    content = """package main

const MaxRetries = 3"""
    assert should_skip_go(content) is True

