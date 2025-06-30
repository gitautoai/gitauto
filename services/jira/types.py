from typing import TypedDict


class JiraIssue(TypedDict):
    id: str
    key: str
    title: str
    body: str
    comments: list[str]


class JiraUser(TypedDict):
    id: str
    displayName: str
    email: str


class JiraOwner(TypedDict):
    id: int
    name: str


class JiraRepo(TypedDict):
    id: int
    name: str


class JiraPayload(TypedDict):
    cloudId: str
    projectId: str
    issue: JiraIssue
    creator: JiraUser
    reporter: JiraUser
    owner: JiraOwner
    repo: JiraRepo
