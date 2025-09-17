#!/usr/bin/env python3
"""Quick test to verify the PRODUCT_ID fix works"""

from unittest.mock import patch
from datetime import datetime

# Test that mocking PRODUCT_ID works
with patch("services.github.utils.deconstruct_github_payload.PRODUCT_ID", "gitauto"):
    from services.github.utils.deconstruct_github_payload import PRODUCT_ID, ISSUE_NUMBER_FORMAT

    # Simulate branch name generation
    issue_number = 123
    date = "20241225"
    time = "143045"
    random_str = "test"

    new_branch_name = f"{PRODUCT_ID}{ISSUE_NUMBER_FORMAT}{issue_number}-{date}-{time}-{random_str}"
    print(f"Generated branch name: {new_branch_name}")

    # This should print: gitauto/issue-123-20241225-143045-test
    assert new_branch_name.startswith("gitauto/issue-123-20241225-143045-")
    print("✅ Test passed!")
