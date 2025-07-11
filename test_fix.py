#!/usr/bin/env python3
"""Quick test to verify the fix works"""

import sys
import os
sys.path.insert(0, os.getcwd())

from unittest.mock import patch, MagicMock
from services.supabase.issues.get_issue import get_issue

def test_mock_setup():
    """Test that our mock setup works correctly"""
    sample_issue_data = {
        "id": 1,
        "owner_type": "Organization",
        "owner_name": "test-owner",
        "repo_name": "test-repo",
        "issue_number": 123,
        "installation_id": 456,
        "merged": False,
        "created_at": "2024-01-01T00:00:00Z",
        "owner_id": 789,
        "repo_id": 101112,
        "created_by": "test-user",
        "run_id": None,
    }
    
    with patch("services.supabase.issues.get_issue.supabase") as mock_supabase:
        # Setup mock with correct return format
        mock_chain = mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.eq.return_value
        mock_chain.execute.return_value = ((None, [sample_issue_data]), None)
        
        # Execute
        result = get_issue(
            owner_type="Organization",
            owner_name="test-owner",
            repo_name="test-repo",
            issue_number=123,
        )
        
        # Verify
        print(f"Result: {result}")
        print(f"Result type: {type(result)}")
        if result:
            print(f"Result ID: {result.get('id')}")
            print("✅ Test passed!")
        else:
            print("❌ Test failed - result is None")

if __name__ == "__main__":
    test_mock_setup()
