from typing import TypedDict


class Artifact(TypedDict):
    id: int  # ex) 2846035038
    node_id: str  # ex) "MDg6QXJ0aWZhY3QyODQ2MDM1MDM4"
    name: str  # ex) "coverage-report"
    size_in_bytes: int  # ex) 7446
    url: str  # ex) "https://api.github.com/repos/gitautoai/sample-flutter-getwidget/actions/artifacts/2846035038"
    archive_download_url: str  # ex) "https://api.github.com/repos/gitautoai/sample-flutter-getwidget/actions/artifacts/2846035038/zip"
    expired: bool  # ex) False
    created_at: str  # ex) "2025-03-29T00:00:00Z"
    updated_at: str  # ex) "2025-03-29T00:00:00Z"
    expires_at: str  # ex) "2025-04-28T00:00:00Z"
