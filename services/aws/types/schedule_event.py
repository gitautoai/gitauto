from typing import TypedDict


class ScheduleEventDetail(TypedDict):
    ownerId: int
    ownerType: str
    ownerName: str
    repoId: int
    repoName: str
    triggerType: str
    scheduleTime: str
    includeWeekends: bool


class ScheduleEvent(TypedDict):
    version: str
    id: str
    detail_type: str  # "detail-type" in JSON becomes "detail_type" in Python
    source: str
    account: str
    time: str
    region: str
    resources: list[str]
    detail: ScheduleEventDetail
