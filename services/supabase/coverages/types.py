from typing import TypedDict, Optional
from datetime import datetime


class CoverageRecord(TypedDict):
    """Type for coverage records returned from the database"""

    id: int
    owner_id: int
    repo_id: int
    primary_language: Optional[str]
    package_name: Optional[str]
    level: str
    full_path: str
    statement_coverage: Optional[float]
    function_coverage: Optional[float]
    branch_coverage: Optional[float]
    path_coverage: Optional[float]
    line_coverage: Optional[float]
    uncovered_lines: Optional[str]
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    github_issue_url: Optional[str]
    uncovered_functions: Optional[str]
    uncovered_branches: Optional[str]
    branch_name: str
    file_size: Optional[int]
    is_excluded_from_testing: Optional[bool]
