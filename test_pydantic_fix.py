#!/usr/bin/env python3
"""Quick test to verify Pydantic model serialization fix."""

import json
from schemas.supabase.fastapi.schema_public_latest import RepoCoverageInsert
from utils.objects.truncate_value import truncate_value

# Create a test RepoCoverageInsert object
coverage_data = RepoCoverageInsert(
    owner_id=123456,
    owner_name="test-owner",
    repo_id=789012,
    repo_name="test-repo",
    branch_name="main",
    created_by="test-user"
)

# Test if truncate_value can handle it
truncated = truncate_value(coverage_data)
print("Truncated data:", json.dumps(truncated, indent=2))