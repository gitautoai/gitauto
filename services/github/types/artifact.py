from typing import TypedDict

from services.github.types.common import BaseGitHubEntity


class Artifact(BaseGitHubEntity):
    """GitHub Actions artifact type
    
    Example values:
    - id: 2846035038
    - node_id: "MDg6QXJ0aWZhY3QyODQ2MDM1MDM4"
    - name: "coverage-report"
    - size_in_bytes: 7446
    - url: "https://api.github.com/repos/gitautoai/sample-flutter-getwidget/actions/artifacts/2846035038"
    - archive_download_url: "https://api.github.com/repos/gitautoai/sample-flutter-getwidget/actions/artifacts/2846035038/zip"
    - expired: False
    - created_at: "2025-03-29T00:00:00Z"
    - updated_at: "2025-03-29T00:00:00Z"
    - expires_at: "2025-04-28T00:00:00Z"
    """
    name: str
    size_in_bytes: int
    archive_download_url: str
    expired: bool
    created_at: str
    updated_at: str
    expires_at: str