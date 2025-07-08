#!/usr/bin/env python3
import json
from datetime import datetime
from schemas.supabase.fastapi.schema_public_latest import Coverages
from utils.objects.truncate_value import truncate_value

# Create a sample coverage record
coverage_record = Coverages(
    id=1,
    branch_coverage=85.5,
    branch_name="main",
    created_at=datetime(2023, 1, 1, 12, 0, 0),
    created_by="test_user",
    full_path="src/example.py",
    level="file",
    owner_id=12345,
    repo_id=67890,
    updated_at=datetime(2023, 1, 1, 12, 0, 0),
    updated_by="test_user"
)

# Test truncate_value and JSON serialization
truncated = truncate_value(coverage_record)
json_str = json.dumps(truncated, indent=2, default=str)
print("JSON serialization successful!")