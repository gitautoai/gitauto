#!/usr/bin/env python3
"""Test script to verify Pydantic model serialization works with truncate_value."""

import json
from datetime import datetime
from schemas.supabase.fastapi.schema_public_latest import RepoCoverageInsert
from utils.objects.truncate_value import truncate_value

def test_pydantic_serialization():
    """Test that Pydantic models can be serialized after truncation."""
    # Create a sample RepoCoverageInsert instance
    sample_data = RepoCoverageInsert(
        branch_name="main",
        created_by="test-user",
        owner_id=123456,
        owner_name="test-owner",
        repo_id=789012,
        repo_name="test-repo",
        created_at=datetime(2023, 1, 1, 12, 0, 0)
    )
    
    # Truncate the value (this should convert it to a dict)
    truncated = truncate_value(sample_data)
    
    # Try to serialize it with json.dumps (this should not fail)
    try:
        json_str = json.dumps(truncated, indent=2, default=str)
        print("✅ Serialization successful!")
        print(f"Truncated data type: {type(truncated)}")
        print(f"JSON output:\n{json_str}")
        return True
    except Exception as e:
        print(f"❌ Serialization failed: {e}")
        return False

if __name__ == "__main__":
    test_pydantic_serialization()
