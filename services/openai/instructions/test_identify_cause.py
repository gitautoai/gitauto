import re
from unittest import mock

import pytest

from services.openai.instructions.identify_cause import IDENTIFY_CAUSE


def test_identify_cause_exists():
    """Test that IDENTIFY_CAUSE constant exists and is a string."""
    assert IDENTIFY_CAUSE is not None
    assert isinstance(IDENTIFY_CAUSE, str)
    assert len(IDENTIFY_CAUSE) > 0


def test_identify_cause_content_structure():
    """Test that IDENTIFY_CAUSE contains expected structural elements."""
    # Check for key phrases that define the instruction's purpose
    assert "GitHub Actions" in IDENTIFY_CAUSE
    assert "Workflow" in IDENTIFY_CAUSE
    assert "Check Run" in IDENTIFY_CAUSE
    assert "expert" in IDENTIFY_CAUSE
    
    # Check for input requirements
    assert "pull request" in IDENTIFY_CAUSE
    assert "error log" in IDENTIFY_CAUSE
    assert "workflow file content" in IDENTIFY_CAUSE
    
    # Check for output requirements
    assert "Markdown format" in IDENTIFY_CAUSE
    assert "identify the cause" in IDENTIFY_CAUSE
    assert "plan to fix" in IDENTIFY_CAUSE


def test_identify_cause_markdown_headers():
    """Test that IDENTIFY_CAUSE contains all required markdown headers."""
    required_headers = [
        "## What is the Error?",
        "## Why did the Error Occur?",
        "## Where is the Error Located?",
        "## How to Fix the Error?",
        "## Why Fix it This Way?"
    ]
    
    for header in required_headers:
        assert header in IDENTIFY_CAUSE, f"Missing required header: {header}"


def test_identify_cause_language_requirement():
    """Test that IDENTIFY_CAUSE mentions language adaptation requirement."""
    assert "language that is used in the input" in IDENTIFY_CAUSE
    assert "Japanese" in IDENTIFY_CAUSE
    assert "plan should be in Japanese" in IDENTIFY_CAUSE


def test_identify_cause_minimalist_approach():
    """Test that IDENTIFY_CAUSE emphasizes minimal changes."""
    assert "absolutely necessary changes" in IDENTIFY_CAUSE
    assert "minimizing code modifications" in IDENTIFY_CAUSE
    assert "Unnecessary changes can confuse reviewers" in IDENTIFY_CAUSE
    assert "skilled engineer avoids that" in IDENTIFY_CAUSE


def test_identify_cause_response_quality():
    """Test that IDENTIFY_CAUSE specifies response quality requirements."""
    assert "clear" in IDENTIFY_CAUSE
    assert "specific" in IDENTIFY_CAUSE
    assert "concise" in IDENTIFY_CAUSE
    assert "direct" in IDENTIFY_CAUSE


def test_identify_cause_no_empty_lines_at_start_end():
    """Test that IDENTIFY_CAUSE doesn't have unnecessary whitespace."""
    assert not IDENTIFY_CAUSE.startswith('\n')
    assert not IDENTIFY_CAUSE.endswith('\n\n')


def test_identify_cause_proper_formatting():
    """Test that IDENTIFY_CAUSE has proper formatting structure."""
    lines = IDENTIFY_CAUSE.split('\n')
    
    # Should have multiple lines
    assert len(lines) > 10
    
    # Should contain empty lines for proper formatting
    empty_lines = [i for i, line in enumerate(lines) if line.strip() == '']
    assert len(empty_lines) > 0


def test_identify_cause_header_format():
    """Test that markdown headers are properly formatted."""
    # Find all markdown headers
    headers = re.findall(r'^## .+$', IDENTIFY_CAUSE, re.MULTILINE)
    
    # Should have exactly 5 headers
    assert len(headers) == 5
    
    # Each header should start with "## " and end with "?"
    for header in headers:
        assert header.startswith("## ")
        assert header.endswith("?")


def test_identify_cause_immutable():
    """Test that IDENTIFY_CAUSE behaves as an immutable constant."""
    original_value = IDENTIFY_CAUSE
    
    # Attempt to modify should not affect the original
    modified = IDENTIFY_CAUSE + " extra text"
    assert IDENTIFY_CAUSE == original_value
    assert modified != IDENTIFY_CAUSE


def test_identify_cause_import():
    """Test that IDENTIFY_CAUSE can be imported correctly."""
    # This test ensures the import works and the constant is accessible
    from services.openai.instructions.identify_cause import IDENTIFY_CAUSE as imported_constant
    
    assert imported_constant == IDENTIFY_CAUSE
    assert isinstance(imported_constant, str)
    assert len(imported_constant) > 0