from utils.prompts.identify_cause import IDENTIFY_CAUSE


def test_identify_cause_is_string():
    """Test that IDENTIFY_CAUSE is a string."""
    assert isinstance(IDENTIFY_CAUSE, str)


def test_identify_cause_not_empty():
    """Test that IDENTIFY_CAUSE is not empty."""
    assert IDENTIFY_CAUSE.strip() != ""


def test_identify_cause_contains_required_headers():
    """Test that IDENTIFY_CAUSE contains all required markdown headers."""
    required_headers = [
        "## What is the Error?",
        "## Why did the Error Occur?",
        "## Where is the Error Located?",
        "## How to Fix the Error?",
        "## Why Fix it This Way?",
    ]

    for header in required_headers:
        assert header in IDENTIFY_CAUSE, f"Missing required header: {header}"


def test_identify_cause_contains_role_description():
    """Test that IDENTIFY_CAUSE contains the role description."""
    assert "GitHub Actions, Workflow, and Check Run expert" in IDENTIFY_CAUSE


def test_identify_cause_contains_language_instruction():
    """Test that IDENTIFY_CAUSE contains language adaptation instruction."""
    assert "language that is used in the input" in IDENTIFY_CAUSE
    assert (
        "if the input is mainly in Japanese, the plan should be in Japanese"
        in IDENTIFY_CAUSE
    )


def test_identify_cause_contains_minimization_guidance():
    """Test that IDENTIFY_CAUSE contains guidance about minimizing changes."""
    assert "absolutely necessary changes" in IDENTIFY_CAUSE
    assert "minimizing code modifications" in IDENTIFY_CAUSE


def test_identify_cause_contains_output_format_instruction():
    """Test that IDENTIFY_CAUSE contains output format instruction."""
    assert "Markdown format" in IDENTIFY_CAUSE


def test_identify_cause_contains_response_quality_guidance():
    """Test that IDENTIFY_CAUSE contains guidance about response quality."""
    assert "clear, specific, concise, and direct" in IDENTIFY_CAUSE


def test_identify_cause_headers_order():
    """Test that the headers appear in the correct order."""
    headers = [
        "## What is the Error?",
        "## Why did the Error Occur?",
        "## Where is the Error Located?",
        "## How to Fix the Error?",
        "## Why Fix it This Way?",
    ]

    for i in range(len(headers) - 1):
        assert IDENTIFY_CAUSE.find(headers[i]) < IDENTIFY_CAUSE.find(headers[i + 1])
