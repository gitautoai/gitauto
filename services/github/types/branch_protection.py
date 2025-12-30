from typing import TypedDict


class StatusCheckContext(TypedDict):
    context: str  # "CircleCI Checks"
    app_id: int  # 12345


class RequiredStatusChecks(TypedDict):
    strict: bool  # True
    contexts: list[str]  # ["ci/circleci: test", "Codecov"]
    checks: list[StatusCheckContext]


class BranchProtection(TypedDict):
    required_status_checks: RequiredStatusChecks
