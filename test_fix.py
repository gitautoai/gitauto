#!/usr/bin/env python3
"""Quick test to verify the fix for Pydantic model serialization."""

import datetime
import json
from schemas.supabase.fastapi.schema_public_latest import Coverages
from utils.objects.truncate_value import truncate_value

# Create a sample coverage record
coverage_record = Coverages(
    id=1,
    branch_coverage=85.5,
    branch_name="main",
    created_at=datetime.datetime(2024, 1, 1, 12, 0, 0),
    created_by="test_user",
    full_path="src/example.py",
    level="file",
    owner_id=12345,
    repo_id=67890,
    updated_at=datetime.datetime(2024, 1, 1, 12, 0, 0),
    updated_by="test_user"
)

# Test truncate_value with the Pydantic model
truncated = truncate_value(coverage_record)
print("Truncated successfully:", json.dumps(truncated, default=str, indent=2))